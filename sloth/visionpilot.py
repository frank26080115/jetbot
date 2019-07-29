import os
from datetime import datetime
import cv2
import numpy as np
import undistort
from undistort import FisheyeUndistorter, PerspectiveUndistorter
from perftimer import PerfTimer
from clize import run

class VisionProcessor(object):

	# input image must already have all distortions applied
	def __init__(self, img, edge_mask = None):
		# image expected to be a cv2 BRG image
		self.img = img.copy()
		self.original_img = img.copy()
		self.height, self.width, self.channels = img.shape
		self.colorspace = "bgr"
		self.failed = False
		self.masked_img = None
		self.contours = []
		self.sorted_contours = None
		self.farthest_cy = self.height
		self.farthest_ly = self.height
		self.edge_mask = edge_mask

	def convertToHsv(self):
		if self.colorspace == "bgr":
			self.hsv_image = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
		elif self.colorspace == "sat":
			self.restoreOrigImage()
		self.img = self.hsv_image.copy()
		self.colorspace = "hsv"

	def saturateHsv2Rgb(self):
		if self.colorspace == "bgr":
			self.convertToHsv()
		self.hsv_image[:,:,1] = np.full((self.height, self.width), 255, dtype=np.uint8)
		self.img = cv2.cvtColor(self.hsv_image.copy(), cv2.COLOR_HSV2BGR)
		self.colorspace = "sat"

	def restoreOrigImage(self):
		self.img = self.original_img.copy()
		self.colorspace = "bgr"

	# try to create a mask around colourful objects, assuming the background is dark grey
	# can work with all colours, but the hue range should be narrowed down if the colour is known
	# this function can be called repeatedly and the masks will be OR'ed (stacked)
	def maskRange(self, color_h_center = 30.0 / 2.0, color_h_range = 40.0, s_range = (0, 255), v_range = (64, 255)):
		if self.colorspace == "edges" or self.colorspace == "sat":
			self.restoreOrigImage()
		if self.colorspace == "bgr":
			self.convertToHsv()
		if color_h_range > 90: # limit the range
			color_h_range = 90

		self.color_hue = color_h_center
		h_max = int(round(color_h_center + color_h_range))
		h_min = int(round(color_h_center - color_h_range))
		s_rng = (int(round(s_range[0])), int(round(s_range[1])))
		v_rng = (int(round(v_range[0])), int(round(v_range[1])))

		hsv_min2 = None
		hsv_max2 = None
		if color_h_range >= 90: # detect any colourful object
			hsv_min1 = np.array([0, s_rng[0], v_rng[0]])
			hsv_max1 = np.array([180, s_rng[1], v_rng[1]])
		elif h_max <= 180 and h_min >= 0: # normal case
			hsv_min1 = np.array([h_min, s_rng[0], v_rng[0]])
			hsv_max1 = np.array([h_max, s_rng[1], v_rng[1]])
		elif h_max > 180: # center value just under 180, but coverage is above 180
			hsv_min1 = np.array([h_min, s_rng[0], v_rng[0]])
			hsv_max1 = np.array([180, s_rng[1], v_rng[1]])
			hsv_max2 = np.array([h_max - 180, s_rng[1], v_rng[1]])
		elif h_min < 0: # center value just above 0, but coverage is under 0
			hsv_min1 = np.array([0, s_rng[0], v_rng[0]])
			hsv_min2 = np.array([180 + h_min, s_rng[0], v_rng[0]])
			hsv_max1 = np.array([h_max, s_rng[1], v_rng[1]])

		masked_img1 = cv2.inRange(self.hsv_image, hsv_min1, hsv_max1)
		masked_img2 = None
		if hsv_min2 is not None:
			masked_img2 = cv2.inRange(self.hsv_image, hsv_min2, hsv_max1)
		if hsv_max2 is not None:
			masked_img2 = cv2.inRange(self.hsv_image, hsv_min2, hsv_max1)

		if self.masked_img is None:
			self.masked_img = masked_img1
		cv2.bitwise_or(self.masked_img, masked_img1, self.masked_img)
		if masked_img2 is not None:
			cv2.bitwise_or(self.masked_img, masked_img2, self.masked_img)

		self.img = self.masked_img.copy() # image is now a mask, a single channel, 0 for false, 255 for true
		self.colorspace = "mask"

	def cannyEdgeDetect(self, center_val = 127, val_spread = 110, morph_kernel_size = 10, blur = True, blur_kernel_size = 5):
		if self.colorspace == "hsv" or self.colorspace == "sat":
			self.img = cv2.cvtColor(self.img, cv2.COLOR_HSV2BGR)
		if blur:
			kernel = np.ones((blur_kernel_size, blur_kernel_size), np.float32) / (blur_kernel_size ** 2)
			src_img = cv2.filter2D(self.img, -1, kernel)
		else:
			src_img = self.img
		self.masked_img = cv2.Canny(src_img, center_val - val_spread, center_val + val_spread)
		kernel = np.ones((morph_kernel_size, morph_kernel_size), np.uint8)
		self.masked_img = cv2.morphologyEx(self.masked_img, cv2.MORPH_CLOSE, kernel)
		if self.edge_mask is not None:
			self.masked_img = np.bitwise_and(self.masked_img, self.edge_mask)
		self.img = self.masked_img.copy()
		self.colorspace = "edges"


	def findContours(self, limit = 3):
		contours, hierarchy = cv2.findContours(self.img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # finds all contours
		# remove impossibly big and incredibly small contours
		i = 0
		while i < len(contours):
			c = TapeContour(self, contours[i])
			to_add = True
			# large contour removal taken care of by the bitwise_and with edge_mask
			# calculate the size of a speckle, remove it if it's too small
			ratio = float(c.area) / float(self.width * self.height)
			limit_ratio = (20.0 * 20.0) / (1333.0 * 720.0)
			if ratio < limit_ratio:
				to_add = False
			if c.is_too_big:
				to_add = False
			if to_add:
				self.contours.append(c)
			i += 1
		#print("found %u contours" % len(self.contours))

		# remove overlaps
		keep_removing = True
		while keep_removing:
			keep_removing = False
			i = 0
			while i < len(self.contours) - 1:
				j = i + 1
				ci = self.contours[i]
				cj = self.contours[j]
				xsect, region = cv2.rotatedRectangleIntersection(ci.min_rect, cj.min_rect)
				if cv2.INTERSECT_NONE != xsect:
					if ci.area >= cj.area:
						del self.contours[j]
					else:
						del self.contours[i]
					keep_removing = True
					break
				i += 1

		self.sorted_contours = sorted(self.contours, key=self.calcRankedContourArea, reverse=True) # sort to find largest
		if len(self.sorted_contours) > 0:

			self.largest_contour = self.sorted_contours[0]
			# remove contours until we are under the limit set
			if limit > 0:
				while len(self.sorted_contours) > limit:
					del self.sorted_contours[-1]
			self.contours = self.sorted_contours

		#i = 0
		#for c in self.sorted_contours:
		#	print("contour [%u] rect %s %.f" % (i, str(c.min_rect), c.line_angle))
		#	i += 1

	def calcMeanAngle(self):
		cnt = 0
		area = 0.0
		sum = 0.0
		for c in self.contours:
			if c.is_narrow:
				ang = c.line_angle
				area += c.area
				sum += ang * c.area
				cnt += 1
		if cnt <= 0:
			return 0.0, cnt
		return (sum / float(area)), cnt

	def calcBestFit(self, add_mid = False):
		if self.contours is None or len(self.contours) <= 0:
			self.failed = True
			return
		if len(self.contours) == 1:
			add_mid = True
			pass # TODO

		mean_angle, mean_angle_cnt = self.calcMeanAngle()

		mid_base = (float(self.width) / 2.0, float(self.height))
		points_x = []
		points_y = []
		if add_mid:
			points_x.append(mid_base[0])
			points_y.append(mid_base[1])
		for c in self.contours:
			points_x.append(c.cx)
			points_y.append(c.cy)
			cyf = float(c.cy) / float(self.height)
			if cyf < self.farthest_cy:
				self.farthest_cy = cyf
		if add_mid:
			if len(points_x) > 4:
				to_add = len(points_x) - 3
				i = 0
				while i < to_add:
					points_x.append(mid_base[0])
					points_y.append(mid_base[1])
					i += 1

		points_x = np.array(points_x)
		points_y = np.array(points_y)
		self.poly = np.polyfit(points_x, points_y, 1)
		x0 = 0
		y0 = self.poly[1]
		vx = 1.0
		vy = self.poly[0]

		angle = np.arctan2(vx, -vy) # calc angle relative to vertical, positive is clockwise
		angle = int(round(np.rad2deg(angle)))
		fit_angle = get_forward_angle(angle)

		#print("fit_angle %.1f    mean_angle %.1f [%u]" % (fit_angle, mean_angle, mean_angle_cnt))

		use_fit_angle = False
		if mean_angle_cnt <= 0:
			use_fit_angle = True
		elif mean_angle_cnt == 0 and len(self.contours) >= 3:
			use_fit_angle = True
		else:
			if abs(mean_angle - fit_angle) < 45:
				use_fit_angle = True

		if use_fit_angle:
			self.line_angle = fit_angle
		else:
			self.line_angle = mean_angle
			i = 0
			while i < len(self.sorted_contours):
				c = self.sorted_contours[i]
				if c.is_narrow:
					x0 = c.cx
					y0 = c.cy
					vx = np.sin(np.deg2rad(mean_angle))
					vy = -np.cos(np.deg2rad(mean_angle))
					break
				i += 1

		self.line_vx = vx
		self.line_vy = vy
		self.line_x0 = x0
		self.line_y0 = y0
		if vx > 0 or vx < 0:
			self.line_lefty = int(round(((-x0) * vy / vx) + y0))
			self.line_righty = int(round(((self.width - x0) * vy / vx) + y0))
			min_ly = min(self.line_lefty, self.line_righty)
			self.farthest_ly = float(abs(self.height - min_ly)) / float(self.height)
		else:
			self.line_lefty = 0
			self.line_righty = 0

		if self.line_vx != 0:
			m, b = self.get_line_equation()
			x_bottom = get_line_x_for_y(self.height, m, b)
		else:
			x_bottom = self.line_x0
		mid = float(self.width) / 2.0
		dx = x_bottom - mid
		px = dx / mid
		self.x_bottom = px

	def visualize(self, line_thickness = 5, hue = 0):
		hsv_img = self.hsv_image.copy()
		if hue < 0:
			hue = int(self.color_hue + 90 + 180) % 180 # we only care about the hue, get its opposite
		hue = int(round(hue))
		if self.contours is None or len(self.contours) <= 0:
			return cv2.cvtColor(hsv_img.copy(), cv2.COLOR_HSV2BGR)
		for c in self.contours:
			c.visualize(hsv_img, (hue, 255, 255), line_thickness)
		try:
			if self.line_vx > 0 or self.line_vx < 0:
				cv2.line(hsv_img, (self.width - 1, self.line_righty), (0, self.line_lefty), (hue, 255, 255), line_thickness)
			else:
				cv2.line(hsv_img, (self.line_x0, 0), (self.line_x0, self.height - 1), (hue, 255, 255), line_thickness)
		except:
			pass
		return cv2.cvtColor(hsv_img.copy(), cv2.COLOR_HSV2BGR)

	def get_angle(self):
		if self.failed:
			return 0
		return self.line_angle

	def get_line_equation(self):
		if self.failed:
			return 0, 0
		m = float(self.line_vy) / float(self.line_vx)
		b = float(self.line_y0) - (m * float(self.line_x0))
		return m, b

	# this is used for sorting purposes, the contour closer to the robot is ranked as larger
	def calcRankedContourArea(self, contour):
		return contour.get_rankedArea()

class TapeContour(object):

	def __init__(self, parent, contour):
		self.parent = parent
		self.original_contour = contour
		self.min_rect = cv2.minAreaRect(contour)
		self.box_points = cv2.boxPoints(self.min_rect)
		(x, y), (width, height), rect_angle = self.min_rect
		self.cx = x
		self.cy = y
		self.width = width
		self.height = height
		self.area = width * height

		max_dim = max(width, height)
		min_dim = min(width, height)
		#diff_dim = max_dim - min_dim
		if min_dim * 1.5 < max_dim:
			self.is_narrow = True
		else:
			self.is_narrow = False

		if float(min_dim) / parent.width >= (150.0 / 1333.0):
			self.is_too_big = True
		else:
			self.is_too_big = False

		if width > height:
			line_angle = rect_angle + 90
		else:
			line_angle = rect_angle

		self.line_angle = get_forward_angle(line_angle)

	def get_rankedArea(self):
		factor = 0.5
		scale = (1.0 - factor) + (factor * (self.cy / float(self.parent.height)))
		return float(self.area) * scale

	def visualize(self, img, colour=(255, 0, 0), thickness = 3):
		box = np.int0(self.box_points)
		cv2.drawContours(img, [box], 0, colour, thickness)

class VisionPilot(object):

	def __init__(self, edge_mask = None, ang_steer_coeff = 2.2, offset_steer_coeff = 64, dist_throttle_coeff = 0.5, steer_max = 128, throttle_max = 128, savedir=""):
		self.perftimer = PerfTimer()
		self.edge_mask = edge_mask
		self.ang_steer_coeff = float(ang_steer_coeff)
		self.offset_steer_coeff = float(offset_steer_coeff)
		self.dist_throttle_coeff = float(dist_throttle_coeff)
		self.steer_max = float(steer_max)
		self.throttle_max = float(throttle_max)
		self.last_steering = 0
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
		self.proc = VisionProcessor(img_arr, edge_mask = self.edge_mask)
		self.proc.convertToHsv()
		self.proc.saturateHsv2Rgb()
		self.proc.cannyEdgeDetect()
		self.proc.maskRange() # finds normal
		self.proc.maskRange(color_h_range = 90, s_range = (0.0, 255.0 * 0.2), v_range = (255.0 * 0.90, 255.0)) # find white
		self.proc.findContours()
		self.proc.calcBestFit()

		if self.proc.failed:
			if self.last_steering >= 0:
				return 64, 127
			else:
				return -64, 127

		angle = self.proc.get_angle()

		throttle = float(self.throttle_max) * (self.proc.farthest_ly / self.dist_throttle_coeff)
		if throttle > self.throttle_max:
			throttle = self.throttle_max

		ang_component = angle * self.ang_steer_coeff
		offset_component = self.proc.x_bottom * self.offset_steer_coeff

		steering = ang_component + offset_component
		#print("angle %f , ang_co %f , offset_co %f" % (angle, ang_component, offset_component))

		if steering > self.steer_max:
			steering = self.steer_max
		elif steering < -self.steer_max:
			steering = -self.steer_max

		self.steering = steering
		self.throttle = throttle
		self.last_steering = steering

		self.save_training(img_arr)

		return float(steering), float(throttle)

	# returns values good for neural networks
	def run(self, img_arr):
		steering, throttle = self.process(img_arr)
		steering /= 127.0
		throttle /= 127.0
		self.perftimer.tick()
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
		fname += "_%03u%03u" % (int(round(self.throttle + 127)), int(round(self.steering + 127)))
		fpath = os.path.join(self.save_dir, fname)
		cv2.imwrite(fpath + ".jpg", self.img)
		self.save_cnt += 1

	def get_framerate(self):
		return self.perftimer.get_framerate()

def get_line_x_for_y(y, m, b):
	if m == 0:
		return y
	x = (y - b) / m
	return x

def get_forward_angle(angle):
	while angle < 0:
		angle += 360
	angle %= 360
	if angle >= 270:
		angle = -(360 - angle)
	elif angle >= 180:
		angle -= 180
	elif angle > 90:
		angle = -(180 - angle)
	return angle

def get_high_contrast_image(img_bgr):
	hsv = cv2.cvtColor(img_bgr.copy(), cv2.COLOR_BGR2HSV)
	hsv = hsv.astype('float32')
	min_s = np.min(hsv[:,:,1])
	max_s = np.max(hsv[:,:,1])
	min_v = np.min(hsv[:,:,2])
	max_v = np.max(hsv[:,:,2])

	hsv[:,:,1] = np.subtract(hsv[:,:,1], min_s)
	hsv[:,:,2] = np.subtract(hsv[:,:,2], min_v)
	hsv[:,:,1] = np.clip(hsv[:,:,1], 0.0, 255.0)
	hsv[:,:,2] = np.clip(hsv[:,:,2], 0.0, 255.0)

	multi_s = 255.0 / (max_s - min_s)
	multi_v = 255.0 / (max_v - min_v)
	hsv[:,:,1] = np.multiply(hsv[:,:,1], multi_s)
	hsv[:,:,2] = np.multiply(hsv[:,:,2], multi_v)

	hsv[:,:,1] = np.clip(hsv[:,:,1], 0.0, 255.0)
	hsv[:,:,2] = np.clip(hsv[:,:,2], 0.0, 255.0)
	return cv2.cvtColor(hsv.astype('uint8'), cv2.COLOR_HSV2BGR)

def test(img_path):
	img = cv2.imread(img_path, -1)
	fisheye = FisheyeUndistorter((img.shape[1], img.shape[0]), undistort.get_fisheye_k(), undistort.get_fisheye_d(), bal = 0.0)
	img2 = fisheye.undistort_image(img)
	img2 = get_high_contrast_image(img2)
	cv2.imshow("fisheye", img2)
	warper = PerspectiveUndistorter(img.shape[1], img.shape[0])
	img3 = warper.undistort_image(img2)
	cv2.imshow("warp", img3)
	img = img3
	edge_mask = warper.get_warp_edge_mask()

	proc = VisionProcessor(img, edge_mask = edge_mask)
	proc.convertToHsv()
	proc.saturateHsv2Rgb()
	cv2.imshow("saturated", proc.img)
	proc.cannyEdgeDetect()
	cv2.imshow("canny", proc.img)
	proc.maskRange()
	cv2.imshow("mask", proc.img)
	proc.findContours()
	proc.calcBestFit()
	cv2.imshow("contour", proc.img)
	vis = proc.visualize()
	if vis is not None:
		cv2.imshow("visualization", vis)
		angle = proc.get_angle()
		m, b = proc.get_line_equation()
		print("angle %u m %.4f b %.4f" % (int(round(angle)), m, b))
		pilot = VisionPilot()
		steering, throttle = pilot.process(img)
		print("steering %u throttle %u" % (int(round(steering)), int(round(throttle))))
	else:
		print("Nothing to visualize")
	cv2.waitKey()

if __name__ == "__main__":
	run(test)
