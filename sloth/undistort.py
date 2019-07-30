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

def get_fisheye(w, h):
	# default array used for 960x720 sized images
	K = np.array([[461.7677813956804, 0.0, 474.3547962904648], [0.0, 461.66062750808965, 367.67234166766383], [0.0, 0.0, 1.0]])
	D = np.array([[-0.04240781305741471], [0.03569991906059936], [-0.053169853982769216], [0.02261778256931271]])

	#if w == 320 and h == 240:
	#	K = np.array([[154.27313042496635, 0.0, 157.3615921926801], [0.0, 154.34611553735263, 122.27211232886417], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04935738444407236], [0.036172016490058426], [-0.028170803556029824], [0.0012180695886859578]])
	#	return K, D
	#if w == 400 and h == 300:
	#	K = np.array([[192.3156577975489, 0.0, 197.34040476787825], [0.0, 192.3089869254393, 152.82112648879982], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04183321517174177], [0.04004140052155198], [-0.064699213018229], [0.030340538500491083]])
	#	return K, D
	#if w == 640 and h == 480:
	#	K = np.array([[307.8193430204958, 0.0, 316.05529828337734], [0.0, 307.7699115082266, 244.973183984406], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04398082568993452], [0.04170140360992785], [-0.06073726915527277], [0.025993771729803026]])
	#	return K, D
	if w == 960 and h == 720:
		return K, D
	#if w == 1440 and h == 1080:
	#	K = np.array([[692.61252600642, 0.0, 711.6609925070823], [0.0, 692.4262906244954, 551.7159525670836], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04358830534385897], [0.0392236314103496], [-0.05784538358534761], [0.024817640466716435]])
	#	return K, D
	#if w == 1920 and h == 1440:
	#	K = np.array([[923.3899955977995, 0.0, 948.9671800112689], [0.0, 923.0757175466225, 735.746949823105], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04461213742165873], [0.043328752857679655], [-0.0639633579070324], [0.02781090260755046]])
	#	return K, D
	#if w == 2132 and h == 1600:
	#	K = np.array([[1025.2907479072994, 0.0, 1053.0953541904605], [0.0, 1025.6511308209797, 817.7431281203461], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04515273274998822], [0.04634260457098287], [-0.06885504969271129], [0.030284976860302525]])
	#	return K, D
	#if w == 2400 and h == 1800:
	#	K = np.array([[1153.927020986111, 0.0, 1186.3562846418206], [0.0, 1153.6204213647693, 919.7261700474405], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.04293655619137124], [0.0402232676222165], [-0.06388231836303418], [0.029614036795687013]])
	#	return K, D
	#if w == 2668 and h == 2000:
	#	K = np.array([[1283.0732943748085, 0.0, 1318.8016088333911], [0.0, 1281.7650508735032, 1022.5244851141557], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.0421615804593537], [0.035638607104154875], [-0.055197116642335155], [0.024821086267362513]])
	#	return K, D
	#if w == 3200 and h == 2400:
	#	K = np.array([[1538.6512626578424, 0.0, 1581.1070964591445], [0.0, 1538.4937701796555, 1226.373969520894], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.044362169073866545], [0.044764436116093265], [-0.06545744855031475], [0.028076690104269653]])
	#	return K, D
	#if w == 3284 and h == 2464:
	#	K = np.array([[1577.3001936280589, 0.0, 1623.5452973945912], [0.0, 1577.8349885743621, 1261.135746057396], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.03980867420541008], [0.030500803495548307], [-0.04768901609792906], [0.02061468852918644]])
	#	return K, D
	#if w == 4096 and h == 3072:
	#	K = np.array([[1968.1952789231757, 0.0, 2027.7349094967167], [0.0, 1968.0725836811157, 1567.710908868167], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.03434352605668292], [0.014663131652816627], [-0.02922878219208023], [0.01284620566088984]])
	#	return K, D
	#if w == 6400 and h == 4800:
	#	K = np.array([[3082.4690815530525, 0.0, 3181.0597422957717], [0.0, 3080.1187022540043, 2437.4968946526083], [0.0, 0.0, 1.0]])
	#	D = np.array([[-0.036791969257355304], [0.017169185996439615], [-0.021105185566915374], [0.003583009110310196]])
	#	return K, D

	r = float(h) / 720.0
	K[0] = np.multiply(K[0], r)
	K[1] = np.multiply(K[1], r)

	return K, D
