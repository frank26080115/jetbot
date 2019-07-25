import numpy as np
import cv2

class FisheyeUndistorter(object):

	def __init__(self, dim1, K, D, bal=0.0, dim2=None, dim3=None):
		if not dim2:
			dim2 = dim1
		if not dim3:
			dim3 = dim1
		scaled_K = K
		scaled_K[2][2] = 1.0  # Except that K[2][2] is always 1.0
		# This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
		new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, dim2, np.eye(3), balance=bal)
		map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
		# save the maps in memory to speed up image processing
		self.map1 = map1
		self.map2 = map2

	def undistort_image(self, img):
		new_img = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
		return new_img

class PerspectiveUndistorter(object):

	# horizon is a percentage of the vertical resolution
	# angle is the persepective angle at the edge of the image, relative to a vertical line, 0 means camera is pointed straight down but it is not the camera angle, needs to be calibrated
	# vstretch is how much to stretch the image vertically
	def __init__(self, width, height, horizon = 0.0, angle = 45, vstretch = 1.8):
		self.orig_width = int(width)
		self.orig_height = int(height)
		self.horizon = horizon
		self.angle = angle
		self.vstretch = vstretch
		self.start_y = int(float(height) * horizon)
		expand = float(height - self.start_y) * np.tan(np.deg2rad(angle))
		self.start_x = int(round(expand))
		self.final_width = int(round(self.orig_width + (2 * self.start_x)))

		# initialzie a list of coordinates that will be ordered
		# such that the first entry in the list is the top-left,
		# the second entry is the top-right, the third is the
		# bottom-right, and the fourth is the bottom-left

		# these two boxes define the source and targed bounding boxes of the perspective transform

		srcBox = [[self.start_x, self.start_y],
		          [self.start_x + self.orig_width, self.start_y],
		          [self.final_width, self.orig_height],
		          [0, self.orig_height]]

		dstBox = [[0, self.start_y],
		          [self.final_width, self.start_y],
		          [self.final_width, self.orig_height],
		          [0, self.orig_height]]

		# generate matrix to be used later
		self.M = cv2.getPerspectiveTransform(np.array(srcBox, dtype = "float32"), np.array(dstBox, dtype = "float32"))

	def undistort_image(self, img_arr):
		canvas = np.zeros((self.orig_height, self.final_width, 3), np.uint8) # create a black canvas wider than original image
		canvas[ 0:self.orig_height, self.start_x:self.start_x + self.orig_width ] = img_arr # draw image into center of black canvas
		res = cv2.warpPerspective(canvas, self.M, (self.final_width, self.orig_height)) # do the warp using the matrix
		res = res[self.start_y:self.orig_height, 0:self.final_width] # crop away the horizon
		newheight = int(round(float(self.orig_height - self.start_y) * self.vstretch)) # calculate new image height
		res = cv2.resize(res, (self.final_width, newheight)) # stretch the image vertically
		return res

def get_fisheye_k():
	return np.array([[461.76777548950287, 0.0, 474.354800420152], [0.0, 461.6606215930893, 367.6723298568177], [0.0, 0.0, 1.0]])

def get_fisheye_d():
	return np.array([[-0.042407758362037334], [0.03569968680651657], [-0.05316951772974894], [0.022617628027210103]])
