import os, glob, datetime
from shutil import copyfile
import undistort
import cv2
from undistort import FisheyeUndistorter, PerspectiveUndistorter
from visionpilot import VisionPilot
import augmentation
from clize import run

class VisionTrainer(object):

	def __init__(self, dpath, outpath="", shrink = None, hueshifts = 0, savepreview = False):
		self.dpath = dpath
		self.outpath = outpath
		self.fisheye = None
		self.warper = None
		self.pilot = None
		self.seqnum = 1
		self.hue_shifts = hueshifts
		self.save_preview = savepreview
		if shrink is not None:
			if shrink[0] <= 0 or shrink[1] <= 0:
				shrink = None
		self.shrink = shrink

	def process_dir(self):
		allpaths = self.dpath.split(';')
		for singlepath in allpaths:
			if self.outpath is None or len(self.outpath) <= 0:
				self.outpath_now = singlepath.strip("/\\") + "_out"
			else:
				self.outpath_now = self.outpath
			try:
				os.makedirs(self.outpath_now)
			except FileExistsError:
				pass
			g = glob.glob(os.path.join(singlepath, "*.jpg"))
			for imgfile in g:
				self.process_file(imgfile)

	def process_file(self, imgfile):
		img = cv2.imread(imgfile, -1)
		orig_img = img.copy()
		if self.fisheye is None:
			self.fisheye = FisheyeUndistorter((img.shape[1], img.shape[0]), undistort.get_fisheye_k(), undistort.get_fisheye_d(), bal = 0.0)
		img2 = self.fisheye.undistort_image(img)
		if self.warper is None:
			self.warper = PerspectiveUndistorter(img.shape[1], img.shape[0])
		img3 = self.warper.undistort_image(img2)
		if self.pilot is None:
			self.pilot = VisionPilot()
		steering, throttle = self.pilot.process(img3)
		steering = int(round(steering + 127))
		throttle = int(round(throttle + 127))
		now = datetime.datetime.now()
		fname = "%04u%02u%02u%02u%02u%02u_%08u" % (now.year, now.month, now.day, now.hour, now.minute, now.second, self.seqnum)
		self.seqnum += 1
		fname += "_%03u%03u" % (throttle, steering)
		fpath = os.path.join(self.outpath_now, fname)
		if self.save_preview:
			previewpath = os.path.join(os.path.dirname(imgfile), fname) + ".preview.jpg"
			if self.pilot.save_visualization(previewpath):
				print("Preview: " + previewpath)
		if self.hue_shifts <= 0:
			if self.shrink is None:
				copyfile(imgfile, fpath + ".jpg")
			else:
				img = cv2.resize(orig_img, self.shrink)
				cv2.imwrite(fpath + ".jpg", img)
		else:
			hue_divider = self.hue_shifts + 1
			hue_spacing = 180.0 / float(hue_divider)
			if self.shrink is None:
				shrunk_img = orig_img
			else:
				shrunk_img = cv2.resize(orig_img, self.shrink)
			h = 0
			while h < hue_divider:
				hue_shift = int(round(hue_spacing * float(h)))
				shifted_img = augmentation.img_hue_shift(shrunk_img, hue_shift)
				cv2.imwrite(fpath + ("_h%u" % hue_shift) + ".jpg", shifted_img)
				h += 1
		print("Saved: " + fpath)

def train(dpath, hueshifts=8, outwidth=160, outheight=120):
	x = VisionTrainer(dpath, hueshifts = hueshifts, shrink=(outwidth, outheight))
	x.process_dir()

if __name__ == "__main__":
	run(train)