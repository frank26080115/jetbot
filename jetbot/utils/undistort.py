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
		self.map1 = map1
		self.map2 = map2

	def undistort_image(self, img):
		new_img = cv2.remap(img, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
		return new_img
