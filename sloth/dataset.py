import os, sys, shutil, glob
import time, datetime
import math, random
from taggedimage import TaggedImage
from augmentation import AugmentedImage, build_all_possible_augs

class ImageSet(object):

	def __init__(self):
		self.images = []
		self.augumented_images = []

	def load_arr(self, arr):
		for i in arr:
			self.images.append(i)
		self.augumented_images = []

	def load_dir(self, dirpath, whichstick="default", loadaugs = False):
		g = glob.glob(os.path.join(dirpath, "*.jpg"))
		arr = []
		for fname in g:
			arr.append(TaggedImage(fname, whichstick))
		if loadaugs:
			aug_arr = []
			ad = glob.glob(os.path.join(dirpath, "aug_*"))
			aug_name = os.path.basename(ad)[4:]
			flip = AUG_FLIP in aug_name
			for d in ad:
				g = glob.glob(os.path.join(d, "*.jpg"))
				for fname in g:
					i = TaggedImage(fname, whichstick, flip)
					aug_arr.append(i)
			self.augumented_images = aug_arr
		self.images = arr

	def sort(self, reverse=False):
		self.images.sort(key=lambda x: x.sequence, reverse=reverse)
		self.augumented_images.sort(key=lambda x: x.sequence, reverse=reverse)

	def shuffle(self):
		random.shuffle(self.images)
		random.shuffle(self.augumented_images)

	def get_subset(self, every, offset, invert=False, allow_aug=False):
		i = 0
		j = 0
		cnt1 = len(self.images)
		if allow_aug:
			cnt2 = len(self.augumented_images)
		else:
			cnt2 = 0
		cnt = cnt1 + cnt2
		arr = []
		while i < cnt and j < cnt:
			j = i + offset
			to_add = False
			if (j % every) == 0:
				to_add = True
			if invert:
				to_add = not to_add
			if to_add:
				if j < cnt1:
					arr.append(self.images[j])
				elif j < cnt and allow_aug:
					arr.append(self.augumented_images[j - cnt1])
			i += 1
		new_set = ImageSet()
		new_set.load_arr(arr)
		return new_set

	def augment_all(self, aug_list, transform = False):
		j = 0
		for i in self.images:
			aimg = AugmentedImage(i.fpath, whichstick = i.whichstick, xform = transform)
			for aug in aug_list:
				aimg.augment(aug)
				aimg.save()
				aimg.reload()
				j += 1
				print("Saved %d %s %s" % (j, aug, aimg.fname))

	def augment_all_possibilities(self, transform = False):
		possibilities = build_all_possible_augs()
		self.augment_all(possibilities, transform = transform)

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