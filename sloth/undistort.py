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

	def get_warp_edge_mask(self):
		linewidth = 10
		blank = np.zeros((self.orig_height, self.orig_width, 3))
		rect = cv2.rectangle(blank, (0, -linewidth), (self.orig_width, self.orig_height + (2 * linewidth)), (255, 255, 255), thickness = linewidth)
		warped = self.undistort_image(rect)
		kernel = np.ones((10, 10), np.uint8)
		morphed = cv2.dilate(warped, kernel)
		(T, bin_img) = cv2.threshold(morphed, 32, 255, cv2.THRESH_BINARY_INV)
		return bin_img[:,:,0]

def get_fisheye(w, h, mode = 0):
	aspect_ratio_in = int(round(float(w) / float(h)) * 100)
	aspect_ratio_tolerance = 3

	DIM=(3280, 2464)
	aspect_ratio_check = int(round(float(DIM[0]) / float(DIM[1])) * 100)
	if aspect_ratio_check < aspect_ratio_in + aspect_ratio_tolerance and aspect_ratio_check > aspect_ratio_in - aspect_ratio_tolerance
		K=np.array([[1575.7203514109985, 0.0, 1634.414876706553], [0.0, 1578.292053875012, 1248.0302449939218], [0.0, 0.0, 1.0]])
		D=np.array([[-0.03179567051238011], [0.0025396904463175865], [-0.01724321137242627], [0.010624139597568343]])
		DIMOUT = DIM

	if mode == 1:
		DIM=(3280, 1848)
		aspect_ratio_check = int(round(float(DIM[0]) / float(DIM[1])) * 100)
		if aspect_ratio_check < aspect_ratio_in + aspect_ratio_tolerance and aspect_ratio_check > aspect_ratio_in - aspect_ratio_tolerance
			K=np.array([[1576.5137904246637, 0.0, 1642.499136508477], [0.0, 1576.3656256414863, 938.6022935744061], [0.0, 0.0, 1.0]])
			D=np.array([[-0.08510305029865232], [0.3326202942693721], [-0.7967822293200877], [0.6391687925881504]])
			DIMOUT = DIM

	if mode == 2:
		DIM=(1920, 1080)
		aspect_ratio_check = int(round(float(DIM[0]) / float(DIM[1])) * 100)
		if aspect_ratio_check < aspect_ratio_in + aspect_ratio_tolerance and aspect_ratio_check > aspect_ratio_in - aspect_ratio_tolerance
			K=np.array([[1581.6707532208197, 0.0, 984.2015555479232], [0.0, 1579.9935594740775, 553.3407862615908], [0.0, 0.0, 1.0]])
			D=np.array([[-0.08639411773309018], [0.11960309535080282], [0.6256429555549071], [-0.33836481413436487]])
			DIMOUT = DIM

	if mode <= 0 or mode >= 3:
		DIM=(1280, 720)
		aspect_ratio_check = int(round(float(DIM[0]) / float(DIM[1])) * 100)
		if aspect_ratio_check < aspect_ratio_in + aspect_ratio_tolerance and aspect_ratio_check > aspect_ratio_in - aspect_ratio_tolerance
			K=np.array([[787.3825331285426, 0.0, 659.4848969002352], [0.0, 787.9410368774925, 361.8520484544348], [0.0, 0.0, 1.0]])
			D=np.array([[-0.05605717972439883], [0.10390638162590304], [-0.238804974772405], [0.28898005951128075]])
			DIMOUT = DIM

	if w == DIMOUT[0] and h == DIMOUT[1]:
		return K, D

	r = float(h) / float(DIMOUT[1])
	K[0] = np.multiply(K[0], r)
	K[1] = np.multiply(K[1], r)

	return K, D
