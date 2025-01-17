import os, math, random
from taggedimage import TaggedImage
import cv2
import numpy as np
from scipy.signal import convolve2d
from PIL import Image
import pyblur
import pyblur.LinearMotionBlur
from pyblur.LinearMotionBlur import LineKernel as LineKernel

AUG_FLIP               = "a" # 
AUG_BLUR               = "b" # 
AUG_MOTION_BLUR        = "c" # 
AUG_CONTRAST_HDR       = "d" # 
AUG_CROP_LEFT          = "e" # 
AUG_CROP_RIGHT         = "f" # 
AUG_DIM                = "g" # 
AUG_BRIGHT             = "h" # 
AUG_NOISE_GAU          = "i" # 
AUG_NOISE_UNI          = "j" # 
AUG_NOISE_TOP_GAU      = "k" # 
AUG_NOISE_TOP_UNI      = "l" # 
AUG_CONTRAST           = "m" # 
AUG_CONTRAST_FLATTEN   = "n" # 
AUG_HUE_SHIFT          = "o" # 
AUG_NONE               = "0" # 

possible_augs = []

def build_all_possible_augs():
	global possible_augs

	if len(possible_augs) > 0:
		return possible_augs

	i = 0
	limit = ord(AUG_HUE_SHIFT[0]) - ord('a')
	bitlimit = (1 << limit) - 1
	while i <= bitlimit:
		str = ""
		for bitidx in range(limit):
			bit = 1 << bitidx
			mask = i & bit
			if mask != 0 and bitidx >= (ord(AUG_CROP_LEFT[0]) - ord('a')) and (bitidx % 2) == 0:
				mask2 = i & (1 << (bitidx + 1))
				if mask2 != 0:
					mask = 0
			if mask != 0:
				str += chr(ord('a') + bitidx)
		if len(str) <= 0:
			str += AUG_NONE

		if str not in possible_augs:
			possible_augs.append(str)

		i += 1

	return possible_augs

def get_random_augs(num, augcnt = 2, must = [], ignore = [AUG_FLIP, AUG_MOTION_BLUR, AUG_CROP_LEFT, AUG_CROP_RIGHT, AUG_NOISE_UNI, AUG_NOISE_TOP_UNI]):
	res = []
	arr = build_all_possible_augs()
	arr = arr.copy();
	cnt = 0
	tries = 500
	while cnt < num and len(arr) > 0 and tries > 0:
		try:
			r = random.randint(0, len(arr))
			x = arr[r]
			del arr[r]
			if len(x) >= augcnt:
				ig = False
				for ign in ignore:
					if ign in x:
						ig = True
						break
				if ig == False:
					gotmust = True
					for m in must:
						if m not in x:
							gotmust = False
							break
					if gotmust:
						res.append(x)
						cnt += 1
		except:
			pass
		tries += 1
	return res

class AugmentedImage(TaggedImage):

	def __init__(self, fpath, whichstick="default", xform=False):
		TaggedImage.__init__(self, fpath, whichstick)
		TaggedImage.load_img_cv2(self)
		if xform:
			TaggedImage.transform(self)
		self.orig_img = self.img_cv2.copy()
		self.orig_steering = self.steering
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
			elif a == AUG_CONTRAST_HDR:
				self.contrast_hdr()
			elif a == AUG_HUE_SHIFT:
				self.hue_shift()
			elif a in "1234567890":
				self.augs += a # do nothing but put in file name
			i += 1

	def flip(self):
		self.img_cv2 = cv2.flip(self.img_cv2, 1)
		self.steering = -1 * self.steering
		self.augs += AUG_FLIP

	def brighter(self, gain = 0):
		if gain == 0:
			gain = np.random.uniform(1, 2.0)
		hsv = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2HSV)  # convert it to hsv
		hsv[:, :, 2] = np.clip(hsv[:, :, 2] * gain, 0, 255)
		self.img_cv2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self.augs += AUG_BRIGHT

	def dimmer(self, gain = 0):
		if gain == 0:
			gain = np.random.uniform(0.5, 1.0)
		hsv = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2HSV)  # convert it to hsv
		hsv[:, :, 2] = np.clip(hsv[:, :, 2] * gain, 0, 255)
		self.img_cv2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self.augs += AUG_DIM

	def crop(self, start_x, final_width):
		final_height = round(final_width * self.iheight / self.iwidth)
		start_y = self.iheight - final_height
		cropped_img = self.img_cv2[start_y:start_y+final_height, start_x:start_x+final_width]
		resized_img = cv2.resize(cropped_img,(self.iwidth, self.iheight), interpolation = cv2.INTER_CUBIC)
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
		self.convert_to_pil()
		#try:
		#dim = int(min([3, 5, 7, 9], key=lambda x:dim)) # finds closest value in the list
		dim = int(round(dim))
		if dim % 2 == 0:
			dim += 1

		if angle > 90:
			angle -= 180

		# calculate a valid angle
		angle += 90 # 0 being forward, but the valid line angles are between 0 and 180
		kernelCenter = int(math.floor(dim/2))
		numDistinctLines = kernelCenter * 4
		validLineAngles = np.linspace(0,180, numDistinctLines, endpoint = False)
		lineAngle = int(min(validLineAngles, key=lambda x:abs(x-angle))) # finds closest value in the list

		kernel = LineKernel(dim, lineAngle, linetype)

		pil_img = np.array(self.img_pil, dtype="uint8")
		blurred_img = pil_img.copy()

		for i in range(self.ichannels):
			blurred_img[:,:,i] = convolve2d(pil_img[:,:,i], kernel, mode='same', fillvalue=255.0).astype("uint8")

		if self.ichannels == 1:
			return Image.fromarray(blurred_img)
		elif self.ichannels == 3:
			return Image.fromarray(blurred_img, 'RGB')
		else:
			raise Exception("Invalid number of colour channels while doing motion blur")
		#except:
		#	return self.img_pil

	def motion_blur(self):
		if self.throttle < 0:
			return False

		# TODO: calculate parameters based on steering and throttle
		blur_dim = self.throttle
		blur_angle = self.stickangle * 0.5
		blurred_img = self._motion_blur_nC(dim = blur_dim, angle = blur_angle)
		self.img_pil = blurred_img
		self.convert_to_cv2()
		self.augs += AUG_MOTION_BLUR
		return True

	def noise(self, stddev, nt, mean = 0, y_start = 0, y_end = 0):
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
		if y_start == 0 and (y_end >= (self.iheight - 1) or y_end == 0):
			noisy_img = np.add(self.img_cv2, arr)
		else:
			yi = y_start
			while yi < y_end and yi < self.iheigh:
				noisy_img[yi,:,:] = np.add(self.img_cv2[yi,:,:], arr[yi,:,:])
				yi += 1
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

	def contrast_hdr(self):
		hsv = cv2.cvtColor(self.img_cv2.copy(), cv2.COLOR_BGR2HSV)
		s_min = np.min(hsv[:,:,1])
		s_max = np.max(hsv[:,:,1])
		s_diff = s_max - s_min
		v_min = np.min(hsv[:,:,2])
		v_max = np.max(hsv[:,:,2])
		v_diff = v_max - v_min
		hsv[:,:,1] = np.subtract(hsv[:,:,1], s_min)
		hsv[:,:,2] = np.subtract(hsv[:,:,2], v_min)
		hsv = hsv.astype('float32')
		hsv[:,:,1] = np.multiply(hsv[:,:,1], float(255.0 / float(s_diff)))
		hsv[:,:,2] = np.multiply(hsv[:,:,2], float(255.0 / float(v_diff)))
		hsv[:,:,1] = np.round(hsv[:,:,1])
		hsv[:,:,2] = np.round(hsv[:,:,2])
		hsv[:,:,1] = np.clip(hsv[:,:,1], 0.0, 255.0)
		hsv[:,:,2] = np.clip(hsv[:,:,2], 0.0, 255.0)
		hsv = hsv.astype('uint8')
		self.img_cv2 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self.augs += AUG_CONTRAST_HDR

	def hue_shift(self, shift=None):
		if shift is None:
			shift = np.random.uniform(-10, 10)
		self.img_cv2 = img_hue_shift(self.img_cv2, shift)
		self.augs += AUG_HUE_SHIFT

	def save(self):
		self.save_to(os.path.join(self.dpath, "aug_" + self.augs))

	def reload(self):
		self.img_cv2 = self.orig_img
		self.convert_to_pil()
		self.steering = self.orig_steering
		self.augs = ""

def img_hue_shift(img, shift):
	shift = int(round(shift)) + 180
	hsv = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2HSV)
	hue = hsv[:,:,0].astype('float32')
	hue_shifted = np.add(hue, shift)
	hue_shifted = np.round(hue_shifted).astype('uint8')
	hue_shifted = np.mod(hue_shifted, 180)
	hsv[:,:,0] = hue_shifted
	ret = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
	return ret
