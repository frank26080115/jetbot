import os, sys, shutil, glob
import time, datetime
import math, random
import numpy as np
import cv2
import PIL, PIL.Image
import mlutils

def parse_usercontrol(str):
	stickmid = 128
	y = int(str[0:3]) - 128
	x = int(str[3:]) - 128
	ang = axis_vector(x, y)
	y = -y # stick Y axis is inverted
	return y, x, ang

def parse_joystick(str):
	magpart = float(str[0:3])
	angpart = float(str[3:])
	return magpart, angpart

def polar2usercontrol(m, a):
	x = m * np.cos(np.radians(a))
	y = m * np.sin(np.radians(a))
	return x, y

def axis_vector(x, y, maglim = 2.0):
	y = -y # stick Y axis is inverted
	mag = math.sqrt((x*x) + (y*y))
	theta = math.atan2(x, y)
	ang = math.degrees(theta)
	if mag > maglim:
		mag = maglim
	return mag, ang

class TaggedImage(object):

	def __init__(self, fpath, whichstick = "default", flipstick = False):
		self.img_cv2 = None
		self.img_pil = None
		self.hastransformed = False
		self.whichstick = whichstick
		self.fpath = fpath
		self.dpath = os.path.dirname(fpath)
		self.fname = os.path.basename(fpath)
		self.tag = os.path.splitext(self.fname)[0]
		splitparts = self.tag.split('_')
		self.time = time.strptime(splitparts[0], "%Y%m%d%H%M%S")
		self.sequence = int(splitparts[1])
		self.btns = int("0x" + splitparts[3], 16)
		self.stickmagnitude_dpad, self.stickangle_dpad   = parse_joystick(splitparts[4])
		self.stickmagnitude_left, self.stickangle_left   = parse_joystick(splitparts[5])
		self.stickmagnitude_right, self.stickangle_right = parse_joystick(splitparts[6])
		if whichstick == "default":
			self.throttle, self.steering, self.stickangle = parse_usercontrol(splitparts[2])
		elif whichstick == "left":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
			self.stickangle = self.stickangle_left
		elif whichstick == "right":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
			self.stickangle = self.stickangle_right
		elif whichstick == "ltrs":
			lt, ls = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
			rt, rs = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
			self.throttle = lt
			self.steering = rs
			self.stickangle = self.stickangle_right
		elif whichstick == "lsrt":
			lt, ls = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
			rt, rs = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
			self.throttle = rt
			self.steering = ls
			self.stickangle = self.stickangle_left
		elif whichstick == "dpad":
			self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_dpad, self.stickangle_dpad)
			self.stickangle = self.stickangle_dpad
		elif whichstick == "max":
			if self.stickmagnitude_dpad >= self.stickmagnitude_left and self.stickmagnitude_dpad >= self.stickmagnitude_right:
				self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_dpad, self.stickangle_dpad)
				self.stickangle = self.stickangle_dpad
			elif self.stickmagnitude_left >= self.stickmagnitude_dpad and self.stickmagnitude_left >= self.stickmagnitude_right:
				self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_left, self.stickangle_left)
				self.stickangle = self.stickangle_left
			else:
				self.throttle, self.steering = polar2usercontrol(self.stickmagnitude_right, self.stickangle_right)
				self.stickangle = self.stickangle_right
		else:
			raise ValueError("Unknown value for parameter \"whichstick\", must be one of the accepted values (left, right, dpad, ltrs, lsrt, max) or default (auto)")
		if flipstick:
			self.stickangle = -1 * self.stickangle
			self.steering = -1 * self.steering
		self.extra = ""
		try:
			self.extra = self.tag[53:]
		except:
			pass

	def load_img_cv2(self, mode=-1):
		self.img_cv2 = cv2.imread(self.fpath, mode)
		height, width, channels = self.img_cv2.shape
		self.iheight = height
		self.iwidth = width
		self.ichannels = channels
		return self.img_cv2

	def load_img_pil(self):
		self.img_pil = PIL.Image.open(self.fpath)
		height, width, channels = self.img_pil.shape
		self.iheight = height
		self.iwidth = width
		self.ichannels = channels
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

	def get_normalized_throttle(self):
		x = float(self.throttle) / 128.0
		x = np.clip(x, -1.0, 1.0)
		return x

	def get_normalized_steering(self):
		x = float(self.steering) / 128.0
		x = np.clip(x, -1.0, 1.0)
		return x

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
		if self.img_cv2 is None:
			if self.img_pil is None:
				pass
			else:
				self.img_pil.save(fp, "JPEG")
		else:
			cv2.imwrite(fp, self.img_cv2)

	def transform(self):
		if self.hastransformed:
			return

		self.img_cv2 = cv2.resize(self.img_cv2, (160, 120))

		self.hastransformed = True
		pass
