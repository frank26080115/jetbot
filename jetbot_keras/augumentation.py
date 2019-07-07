import os
from dataset import TaggedImage
import cv2
import numpy as np
from scipy.signal import convolve2d
from PIL import Image
import pyblur

AUG_CROP_LEFT    = "a"
AUG_CROP_RIGHT   = "b"
AUG_BLUR         = "c"
AUG_MOTION_BLUR  = "d"
AUG_DIM          = "e"
AUG_BRIGHT       = "f"
AUG_FLIP         = "g"
AUG_NOISE_GAU    = "h"
AUG_NOISE_UNI    = "i"
AUG_NOISE_TOP_GAU = "j"
AUG_NOISE_TOP_UNI = "k"
AUG_CONTRAST     = "l"
AUG_CONTRAST_FLATTEN = "m"
AUG_NONE         = "0"
AUG_NONE_0       = "0"
AUG_NONE_1       = "1"
AUG_NONE_2       = "2"
AUG_NONE_3       = "3"
AUG_NONE_4       = "4"
AUG_NONE_5       = "5"
AUG_NONE_6       = "6"
AUG_NONE_7       = "7"
AUG_NONE_8       = "8"
AUG_NONE_9       = "9"

class AugmentedImage(TaggedImage):

	def __init__(self, fpath, whichstick="auto"):
		TaggedImage.__init__(self, fpath, whichstick)
		super.load_img_cv2()
		self.augs = ""

	def augment(self, augs):
		augcnt = len(augs)
		i = 0
		while i < augcnt:
			a = "" + augs[i]
			if a == AUG_FLIP:
				self.flip()
			elif a == AUG_CROP_LEFT:
				self.crop_left()
			elif a == AUG_CROP_RIGHT:
				self.crop_right()
			elif a == AUG_BLUR:
				self.blur()
			elif a == AUG_MOTION_BLUR:
				self.motion_blur()
			elif a == AUG_DIM:
				self.dimmer()
			elif a == AUG_BRIGHT:
				self.brighter()
			elif a == AUG_NOISE_GAU:
				self.noise_gau()
			elif a == AUG_NOISE_UNI:
				self.noise_uni()
			elif a == AUG_CONTRAST:
				self.contrast()
			elif a == AUG_CONTRAST_FLATTEN:
				self.contrast_flatten()
			elif a in "1234567890":
				self.augs += a # do nothing but put in file name
			i += 1

	def flip(self):
		self.img_cv2 = cv2.flip(self.img_cv2, 0)
		self.steering = -1 * self.steering
		self.augs += AUG_FLIP

	def brighter(self, gain = 0):
		if gain == 0:
			gain = np.random.uniform(1, 1.5)
		hsv = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2HSV)  # convert it to hsv
		hsv[:, :, 2] = np.clip(hsv[:, :, 2] * gain, 0, 255)
		self.img_cv2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self.augs += AUG_BRIGHT

	def dimmer(self, gain = 0):
		if gain == 0:
			gain = np.random.uniform(0.1, 1.0)
		hsv = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2HSV)  # convert it to hsv
		hsv[:, :, 2] = np.clip(hsv[:, :, 2] * gain, 0, 255)
		self.img_cv2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self.augs += AUG_DIM

	def crop(self, start_x, final_width):
		final_width / self.iwidth = final_height / self.iheight
		final_height = round(final_width * self.iheight / self.iwidth)
		start_y = self.iheight - final_height
		cropped_img = self.img_cv2[start_y:start_y+final_height, start_x:start_x+final_width]
		resized_img = cv2.resize(cropped_img,(width, height), interpolation = cv.INTER_CUBIC)
		return resized_img

	def crop_left(self, area = 0.75):
		final_width = round(area * self.iwidth)
		self.img_cv2 = self.crop(0, final_width)
		self.augs += AUG_CROP_LEFT

	def crop_right(self, area = 0.75):
		final_width = round(area * self.iwidth)
		self.img_cv2 = self.crop(self.iwidth - final_width, final_width)
		self.augs += AUG_CROP_RIGHT

	def blur(self, min_kernal_size=2, max_kernal_size=3):
		kernal_size = random.randint(min_kernal_size, max_kernal_size)
		kernel = np.ones((kernal_size, kernal_size), np.float32) / (kernal_size ** 2)
		blurred_img = cv2.filter2D(self.img_cv2, -1, kernel)
		self.img_cv2 = blurred_img
		self.augs += AUG_BLUR

	def _motion_blur_nC(self, dim = 3, angle = 0, linetype = "full"):
		super.convert_to_pil()
		dim = round(dim)

		# calculate a valid angle
		angle += 90 # 0 being forward, but the valid line angles are between 0 and 180
		kernelCenter = int(math.floor(dim/2))
		numDistinctLines = kernelCenter * 4
		validLineAngles = np.linspace(0,180, numDistinctLines, endpoint = False)
		lineAngle = int(min(validLineAngles, key=lambda x:abs(x-angle))) # finds closest value in the list

		kernel = pyblur.LineKernel(dim, lineAngle, linetype)

		for i in xrange(self.ichannels):
			blurred_img[:,:,i] = convolve2d(self.img_pil[:,:,i], kernel, mode='same', fillvalue=255.0).astype("uint8")

		if self.ichannels == 1:
			return Image.fromarray(blurred_img)
		elif self.ichannels == 3:
			return Image.fromarray(blurred_img, 'RGB')
		else:
			raise Exception("Invalid number of colour channels while doing motion blur")

	def motion_blur(self):
		if self.throttle < 0:
			return

		# TODO: calculate parameters based on steering and throttle
		blur_dim = self.throttle * 0.5
		blur_angle = self.stickangle * 0.5
		blurred_img = self._motion_blur_nC(dim = blur_dim, angle = blur_angle)
		self.img_pil = blurred_img
		super.convert_to_cv2()
		self.augs += AUG_MOTION_BLUR

	def noise(self, stddev, nt, mean = 0, y_start = 0, y_end = 0):
		height, width, channels = self.img_cv2.shape
		if y_end <= 0:
			y_end = self.iheight
		arr = self.img_cv2.copy()
		noisy_img = arr.copy()
		if nt == AUG_NOISE_GAU:
			cv2.randn(arr, mean, stddev)
		elif nt == AUG_NOISE_UNI:
			cv2.randu(arr, mean, stddev)
		else:
			raise Exception("Invalid noise type specified")
		if y_start == 0 and y_end == height:
			noisy_img = np.add(self.img_cv2, arr)
		else:
			yi = y_start
			while yi < y_end:
				noisy_img[yi,:,:] = np.add(self.img_cv2[yi,:,:], arr[yi,:,:])
		return np.clip(noisy_img, 0.0, 255.0)

	def noise_gau(self, stddev = 150):
		self.img_cv2 = self.noise(stddev, AUG_NOISE_GAU)
		self.augs += AUG_NOISE_GAU

	def noise_uni(self, stddev = 1.0):
		self.img_cv2 = self.noise(stddev, AUG_NOISE_UNI)
		self.augs += AUG_NOISE_UNI

	def noise_top_gau(self, stddev = 150, chunk = 0.5):
		horizon = round(self.iheight * chunk)
		self.img_cv2 = self.noise(stddev, AUG_NOISE_GAU, y_end = horizon)
		self.augs += AUG_NOISE_GAU

	def noise_top_uni(self, stddev = 1.0, chunk = 0.5):
		horizon = round(self.iheight * chunk)
		self.img_cv2 = self.noise(stddev, AUG_NOISE_UNI, y_end = horizon)
		self.augs += AUG_NOISE_UNI

	def _contrast(self, alpha, beta):
		new_img = self.img_cv2.copy()
		new_img = np.multiply(new_img, alpha)
		new_img = np.add(new_img, beta)
		return np.clip(new_img, 0.0, 255.0)

	def contrast(self, alpha = 1.3, beta = 0.0):
		self.img_cv2 = self._contrast(alpha, beta)
		self.augs += AUG_CONTRAST

	def contrast_flatten(self, alpha = 0.8, beta = 0.0):
		self.img_cv2 = self._contrast(alpha, beta)
		self.augs += AUG_CONTRAST_FLATTEN

	def save(self):
		self.save_to(os.path.join(self.dpath, "aug_" + self.augs))