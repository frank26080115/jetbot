import os, sys, shutil
import time, datetime
import math, random
import numpy as np
import cv2
import PIL, PIL.Image
import mlutils

def parse_joystick(str):
	magpart = float(str[0:3])
	angpart = float(str[3:])
	return magpart, angpart

def polar2usercontrol(m, a):
	x = m * np.cos(np.radians(a))
	y = m * np.sin(np.radians(a))
	return x, y

class TaggedImage(object):

	def __init__(self, fpath, whichstick="auto"):
		self.img_cv2 = None
		self.img_pil = None
		self.fpath = fpath
		self.fname = os.path.basename(fpath)
		self.tag = os.path.splitext(self.fname)[0]
		splitparts = self.tag.split('_')
		self.time = time.strptime(splitparts[0], "%Y%m%d%H%M%S")
		self.sequence = int(splitparts[1])
		self.btns = int("0x" + splitparts[2], 16)
		self.stickmagnitude_dpad, self.stickangle_dpad   = parse_joystick(splitparts[3])
		self.stickmagnitude_left, self.stickangle_left   = parse_joystick(splitparts[4])
		self.stickmagnitude_right, self.stickangle_right = parse_joystick(splitparts[5])
		if whichstick == "left":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
		elif whichstick == "right":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
		elif whichstick == "ltrs":
			lt, ls = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
			rt, rs = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
			self.throttle = lt
			self.steering = rs
		elif whichstick == "lsrt":
			lt, ls = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
			rt, rs = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
			self.throttle = rt
			self.steering = ls
		elif whichstick == "dpad":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_dpad, self.stickangle_dpad)
		elif whichstick == "max" or whichstick == "auto":
			if self.stickmagnitude_dpad >= self.stickmagnitude_left and self.stickmagnitude_dpad >= self.stickmagnitude_right:
				self.throttle = self.stickmagnitude_dpad
				self.steering = self.stickangle_dpad
			elif self.stickmagnitude_left >= self.stickmagnitude_dpad and self.stickmagnitude_left >= self.stickmagnitude_right:
				self.throttle = self.stickmagnitude_left
				self.steering = self.stickangle_left
			else:
				self.throttle = self.stickmagnitude_right
				self.steering = self.stickangle_right
		else:
			raise ValueError("Unknown value for parameter \"whichstick\", must be one of the accepted values (left, right, dpad, ltrs, lsrt, max) or default (auto)")
		self.extra = ""
		try:
			self.extra = self.tag[53:]
		except:
			pass

	def load_img_cv2(self, mode=-1):
		self.img_cv2 = cv2.imread(self.fpath, mode)
		return self.img_cv2

	def load_img_pil(self):
		self.img_pil = PIL.Image.open(self.fpath)
		return self.img_pil

	def convert_to_pil(self):
		x = cv2.cvtColor(self.img_cv2, cv2.COLOR_BGR2RGB)
		self.img_pil = PIL.Image.fromarray(x)
		return self.img_pil

	def convert_to_cv2(self):
		x = self.img_pil.convert('RGB') 
		x = np.array(x) 
		self.img_cv2 = x[:, :, ::-1].copy() # Convert RGB to BGR 
		return self.img_cv2

	def unload_img(self):
		try:
			del self.img_cv2
		except:
			pass
		try:
			del self.img_pil
		except:
			pass

	def is_btn_pressed(self, bit):
		if bit >= 304:
			bit -= 304
		bp = 1 << bit
		if self.btns & bp != 0:
			return True
		else:
			return False

	def save_to(self, dirpath):
		try:
			os.makedirs(dirpath)
		except FileExistsError:
			pass
		fp = os.path.join(dirpath, self.fname)
		with open(fp, 'wb') as f:
			if self.img_cv2 != None:
				cv2.imwrite(fp, self.img_cv2)
			elif self.img_pil != None:
				self.img_pil.save(fp, "JPEG")

	def transform(self):
		if self.hastransformed:
			return

		self.img_cv2 = cv2.resize(self.img_cv2, (160, 120, 3))

		self.hastransformed = True
		pass

class ImageSet(object):

	def __init__(self):
		self.images = []

	def load_arr(self, arr):
		self.images = arr

	def load_dir(self, dirpath, whichstick="auto"):
		g = glob.glob(os.path.join(dirpath, "*.jpg"))
		arr = []
		for fname in g:
			arr.append(TaggedImage(fname, whichstick))
		self.images = arr

	def sort(self, reverse=False):
		self.images.sort(key=lambda x: x.sequence, reverse=reverse)

	def shuffle(self):
		random.shuffle(self.images)

	def get_subset(self, every, offset, invert=False):
		i = 0
		cnt = len(self.images)
		arr = []
		while i < cnt:
			j = i + offset
			to_add = False
			if (j % every) == 0:
				to_add = True
			if invert:
				to_add = !to_add
			if to_add:
				arr.append(self.images[j])
		new_set = ImageSet()
		new_set.load_arr(arr)
		return new_set

	def copy_to(self, dirpath):
		try:
			os.makedirs(dirpath)
		except FileExistsError:
			pass
		for f in self.images:
			try:
				shutil.copyfile(f.fpath, os.path.join(dirpath, f.fname))
			except Exception as ex:
				print("Exception copying file '%s' to '%s', error: %s" % (f.fpath, dirpath, str(ex)))

	def save_to(self, dirpath, xform=False):
		for f in self.images:
			if xform:
				f.transform()
			f.save_to(dirpath)