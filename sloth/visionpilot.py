import os
from datetime import datetime
import cv2
import numpy as np
import undistort
from undistort import FisheyeUndistorter, PerspectiveUndistorter
from clize import run

class VisionProcessor(object):

	# input image must already have all distortions applied
	def __init__(self, img):
		# image expected to be a cv2 BRG image
		self.img = img.copy()
		self.original_img = img.copy()
		self.height, self.width, self.channels = img.shape
		self.colorspace = "bgr"
		self.failed = False

	def convertToHsv(self):
		self.hsv_image = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
		self.img = self.hsv_image.copy()
		self.colorspace = "hsv"

	# try to create a mask around colourful objects, assuming the background is dark grey
	# can work with all colours, but the hue range should be narrowed down if the colour is known
	def maskRange(self, color_h_center = 55 / 2, color_h_range = 10, s_min = 110, v_min = 32):
		if self.colorspace == "bgr":
			self.convertToHsv()
		if color_h_range > 90: # limit the range
			color_h_range = 90
		h_max = color_h_center + color_h_range
		h_min = color_h_center - color_h_range
		masked_img = self.hsv_image
		if color_h_range >= 90: # detect any colourful object
			hsv_min = np.array([0, s_min, v_min])
			hsv_max = np.array([180, 255, 255])
			masked_img = cv2.inRange(masked_img.copy(), hsv_min, hsv_max)
		elif h_max <= 180 and h_min >= 0: # normal case
			hsv_min = np.array([h_min, s_min, v_min])
			hsv_max = np.array([h_max, 255, 255])
			masked_img = cv2.inRange(masked_img.copy(), hsv_min, hsv_max)
		elif h_max > 180: # center value just under 180, but coverage is above 180
			hsv_min = np.array([h_min, s_min, v_min])
			hsv_max1 = np.array([180, 255, 255])
			hsv_max2 = np.array([h_max - 180, 255, 255])
			masked_img1 = cv2.inRange(masked_img.copy(), hsv_min, hsv_max1)
			masked_img2 = cv2.inRange(masked_img.copy(), hsv_min, hsv_max2)
			cv2.bitwise_or(masked_img1, masked_img2, masked_img)
		elif h_min < 0: # center value just above 0, but coverage is under 0
			hsv_min1 = np.array([0, s_min, v_min])
			hsv_min2 = np.array([180 + h_min, s_min, v_min])
			hsv_max = np.array([h_max, 255, 255])
			masked_img1 = cv2.inRange(masked_img.copy(), hsv_min1, hsv_max)
			masked_img2 = cv2.inRange(masked_img.copy(), hsv_min2, hsv_max)
			cv2.bitwise_or(masked_img1, masked_img2, masked_img)

		self.img = masked_img.copy() # image is now a mask, a single channel, 0 for false, 255 for true
		self.height, self.width = self.img.shape
		self.colorspace = "mask"

	def findLargestContour(self, horizon = 0.33):
		start_y = int(round(float(self.height) * horizon)) # calculate the horizon in terms of Y coordinates
		contours, hierarchy = cv2.findContours(self.img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # finds all contours
		if horizon <= start_y:
			filtered = contours
		else:
			filtered = []
			# run through all contours, make sure they are below the view horizon
			for c in contours:
				x,y,w,h = cv2.boundingRect(c)
				if y >= start_y or (y + (h / 2)) >= start_y: # all or mostly below horizon
					filtered.append(c.copy())
			if len(filtered) <= 0: # got nothing?
				self.largest_contour = None
				self.failed = True
				return None
		sorted_contours = sorted(filtered, key=cv2.contourArea, reverse=True) # sort to find largest
		if len(sorted_contours) <= 0:
			self.largest_contour = None
			self.failed = True
			return None
		self.largest_contour = sorted_contours[0].copy()
		self.rect_x, self.rect_y, self.rect_w, self.rect_h = cv2.boundingRect(self.largest_contour)
		[vx, vy, x0, y0] = cv2.fitLine(self.largest_contour, cv2.DIST_L2, 0, 0.01, 0.01)
		self.line_vx = vx
		self.line_vy = vy
		self.line_x0 = x0
		self.line_y0 = y0
		if vx > 0 or vx < 0:
			self.line_lefty = int(((-x0) * vy / vx) + y0)
			self.line_righty = int(((self.width - x0) * vy / vx) + y0)
		else:
			self.line_lefty = 0
			self.line_righty = 0
		return self.largest_contour

	def visualize(self):
		if self.largest_contour is None or self.failed:
			return None
		oh, ow, oc = self.original_img.shape
		mask = np.zeros((oh, ow, 1), np.uint8)
		cv2.drawContours(mask, [self.largest_contour], -1, 255, -1) # creates a mask of the largest contour
		hsv_img = cv2.cvtColor(self.original_img.copy(), cv2.COLOR_BGR2HSV)
		mean_img = cv2.mean(hsv_img, mask) # average the pixels of the image where the mask is covering
		hue = mean_img[0] # we only care about the hue
		hue += 180 + 90 # flip the hue to the opposite color
		hue %= 180
		try:
			cv2.rectangle(hsv_img, (self.rect_x, self.rect_y), (self.rect_x + self.rect_w, self.rect_y + self.rect_h), (hue, 255, 255), 2)
		except:
			pass
		try:
			if self.line_vx > 0 or self.line_vx < 0:
				cv2.line(hsv_img, (self.width - 1, self.line_righty), (0, self.line_lefty), (hue, 255, 255), 2)
			else:
				cv2.line(hsv_img, (self.line_x0, 0), (self.line_x0, self.height - 1), (hue, 255, 255), 2)
		except:
			pass
		return cv2.cvtColor(hsv_img.copy(), cv2.COLOR_HSV2BGR)

	def get_angle(self):
		if self.largest_contour is None or self.failed:
			return 0
		vx = self.line_vx
		vy = -self.line_vy # flip to cartesian coordinates
		angle = np.arctan2(vx, vy) # calc angle relative to vertical, positive is clockwise
		angle = int(round(np.rad2deg(angle)[0]))
		angle += 360
		angle %= 360
		if angle > 90:
			angle = -(180 - angle)
		elif angle > 180:
			angle -= 180
		elif angle > 270:
			angle = -(360 - angle)
		angle += 360
		angle %= 360
		if angle > 180:
			angle = -(360 - angle)
		return angle

	def get_line_equation(self):
		if self.largest_contour is None or self.failed:
			return 0, 0
		m = float(self.line_vy) / float(self.line_vx)
		b = float(self.line_y0) - (m * float(self.line_x0))
		return m, b

	def get_centroid(self):
		if self.largest_contour is None or self.failed:
			return 0, 0
		x = float(self.rect_x) + float((self.rect_w) / 2.0)
		y = float(self.rect_y) + float((self.rect_h) / 2.0)
		return x, y

	def get_centroid_on_line(self):
		if self.largest_contour is None or self.failed:
			return 0, 0
		x = float(self.rect_x) + float((self.rect_w) / 2.0)
		m, b = get_line_equation(self)
		y = (m * x) + b
		return x, y


class VisionPilot(object):

	def __init__(self, ang_hori_thresh = 60, ang_vert_thresh = 15, ang_steer_coeff = 1.5, offset_steer_coeff = 140, dist_throttle_coeff = 0.5, steer_max = 128, throttle_max = 128, savedir=""):
		self.ang_hori_thresh = int(round(ang_hori_thresh))
		self.ang_vert_thresh = int(round(ang_vert_thresh))
		self.ang_steer_coeff = float(ang_steer_coeff)
		self.offset_steer_coeff = float(offset_steer_coeff)
		self.dist_throttle_coeff = float(dist_throttle_coeff)
		self.steer_max = float(steer_max)
		self.throttle_max = float(throttle_max)
		self.save_dir = savedir
		self.save_cnt = 0
		if self.save_dir is not None:
			if len(self.save_dir) > 0:
				try:
					os.makedirs(self.save_dir)
				except FileExistsError:
					pass

	# returns values good for driving directly
	def process(self, img_arr):
		self.proc = VisionProcessor(img_arr)
		self.proc.convertToHsv()
		self.proc.maskRange()
		contour = self.proc.findLargestContour()
		if contour is None:
			return 32, 128

		angle = self.proc.get_angle()
		m, b = self.proc.get_line_equation()
		cx, cy = self.proc.get_centroid()

		if angle >= -self.ang_hori_thresh and angle <= self.ang_hori_thresh: # near vertical line
			x = get_line_x_for_y(self.proc.height, m, b)
			x = (x + cx) / 2.0
			throttle = self.throttle_max
			mid = float(self.proc.width) / 2.0
			dx = x - mid
			px = dx / mid
			ang_component = angle * self.ang_steer_coeff
			offset_component = px * self.offset_steer_coeff
			steering = ang_component + offset_component
			#print("angle %f , ang_co %f , offset_co %f" % (angle, ang_component, offset_component))
			if ((angle > self.ang_vert_thresh and steering < 0) or (angle < -self.ang_vert_thresh and steering > 0)) and cy < self.proc.height * 0.6:
				steering = 0
			if steering > self.steer_max:
				steering = self.steer_max
			elif steering < -self.steer_max:
				steering = -self.steer_max
		else: # near horizontal line
			if angle < 0:
				steering = -self.steer_max / 2
			elif angle > 0:
				steering = self.steer_max / 2
			delta_y = float(self.proc.height) - cy
			py = delta_y / float(self.proc.height)
			throttle = py * (self.dist_throttle_coeff * float(self.throttle_max))

		self.steering = steering
		self.throttle = throttle

		self.save_training(img_arr)

		return float(steering), float(throttle)

	# returns values good for neural networks
	def run(self, img_arr):
		steering, throttle = self.process(img_arr)
		steering /= 127.0
		throttle /= 127.0
		return np.clip(steering, -1.0, 1.0), np.clip(throttle, -1.0, 1.0)

	def save_visualization(self, fpath):
		if self.proc is None:
			return False
		x = self.proc.visualize()
		if x is not None:
			cv2.imwrite(fpath, x)
			return True
		return False

	def save_training(self, img_arr):
		if self.save_dir is None:
			return
		if len(self.save_dir) <= 0:
			return
		now = datetime.now()
		fname = "%04u%02u%02u%02u%02u%02u_%08u" % (now.year, now.month, now.day, now.hour, now.minute, now.second, self.save_cnt)
		fname += "_%03u%03u" % (int(round(self.throttle)), int(round(self.steering)))
		fpath = os.path.join(self.save_dir, fname)
		cv2.imwrite(fpath + ".jpg", self.img)
		self.save_cnt += 1

def get_line_x_for_y(y, m, b):
	if m == 0:
		return y
	x = (y - b) / m
	return x

def calc_circles(x_2, y_2, img_width, img_height, m, b):
	# TODO work in progress function
	x_1 = float(img_width) / 2
	y_1 = float(img_height)
	r_1 = abs(m * x_1 + y_1 - b) / np.sqrt(np.power(m, 2) + 1.0)
	g = -(np.power(x_1, 2) - np.power(x_2, 2) + np.power(y_1 - y_2, 2)) / (2.0 * (x_1 - x_2))
	r_2 = g - x_1
	r_1 /= float(img_height)
	r_2 /= float(img_height)
	if m > 0:
		r_1 = -abs(r_1)
	return r_1, r_2

def test(img_path):
	img = cv2.imread(img_path, -1)
	fisheye = FisheyeUndistorter((img.shape[1], img.shape[0]), undistort.get_fisheye_k(), undistort.get_fisheye_d(), bal = 0.0)
	img2 = fisheye.undistort_image(img)
	cv2.imshow("fisheye", img2)
	warper = PerspectiveUndistorter(img.shape[1], img.shape[0])
	img3 = warper.undistort_image(img2)
	cv2.imshow("warp", img3)
	img = img3

	proc = VisionProcessor(img)
	proc.convertToHsv()
	cv2.imshow("HSV", proc.img)
	proc.maskRange()
	cv2.imshow("mask", proc.img)
	proc.findLargestContour()
	cv2.imshow("contour", proc.img)
	vis = proc.visualize()
	if vis is not None:
		cv2.imshow("visualization", vis)
		angle = proc.get_angle()
		m, b = proc.get_line_equation()
		cx, cy = proc.get_centroid()
		print("angle %u cx %u cy %u" % (int(round(angle)), int(round(cx)), int(round(cy))))
		pilot = VisionPilot()
		steering, throttle = pilot.process(img)
		print("steering %u throttle %u" % (int(round(steering)), int(round(throttle))))
	else:
		print("Nothing to visualize")
	cv2.waitKey()

if __name__ == "__main__":
	run(test)
