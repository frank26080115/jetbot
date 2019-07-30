import cv2
import numpy as np
import os
import glob
from clize import run

CHECKERBOARD = (6,9)

subpix_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
calibration_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_CHECK_COND + cv2.fisheye.CALIB_FIX_SKEW

objp = np.zeros((1, CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

def calibrate(dirpath, width, height):
	_img_shape = None
	objpoints = [] # 3d point in real world space
	imgpoints = [] # 2d points in image plane.
	images = glob.glob(os.path.join(dirpath, '*.jpg'))
	#print("# found %u files" % len(images))
	for fname in images:
		img = cv2.imread(fname)
		img = cv2.resize(img, (width,height))
		if _img_shape == None:
			_img_shape = img.shape[:2]
		else:
			assert _img_shape == img.shape[:2], "All images must share the same size."
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		# Find the chess board corners
		ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)
		# If found, add object points, image points (after refining them)
		if ret == True:
			objpoints.append(objp)
			cv2.cornerSubPix(gray, corners, (3,3), (-1,-1), subpix_criteria)
			imgpoints.append(corners)

	N_OK = len(objpoints)
	#print("# found %u points" % N_OK)
	K = np.zeros((3, 3))
	D = np.zeros((4, 1))

	rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
	tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]

	try:
		rms, _, _, _, _ = cv2.fisheye.calibrate(
				objpoints,
				imgpoints,
				gray.shape[::-1],
				K,
				D,
				rvecs,
				tvecs,
				calibration_flags,
				(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
			)

		print("if w == %u and h == %u:" % (width, height))
		print("\tK = np.array(" + str(K.tolist()) + ")")
		print("\tD = np.array(" + str(D.tolist()) + ")")
		print("\treturn K, D")
	except:
		print("# failed for size %u x %u" % (width, height))

def calibrate_all(dirpath):
	v_res = [120, 240, 300, 480, 720, 1080, 1440, 1600, 1800, 2000, 2400, 2464, 3072, 4800]
	for v in v_res:
		h_res = int(round(v / 3.0) * 4)
		calibrate(dirpath, h_res, v)

if __name__ == "__main__":
	run(calibrate_all)