import os, sys, shutil, glob
import numpy as np
from tensorflow.python import keras
import augmentation

# https://stanford.edu/~shervine/blog/keras-how-to-generate-data-on-the-fly
class GenericDataGenerator(keras.utils.Sequence):
	'Generates data for Keras'
	def __init__(self, list_IDs, labels, batch_size=32, dim=(32,32,32), n_channels=1,
				 n_classes=10, shuffle=True):
		'Initialization'
		self.dim = dim
		self.batch_size = batch_size
		self.labels = labels
		self.list_IDs = list_IDs
		self.n_channels = n_channels
		self.n_classes = n_classes
		self.shuffle = shuffle
		self.on_epoch_end()

	def __len__(self):
		'Denotes the number of batches per epoch'
		return int(np.floor(len(self.list_IDs) / self.batch_size))

	def __getitem__(self, index):
		'Generate one batch of data'
		# Generate indexes of the batch
		indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

		# Find list of IDs
		list_IDs_temp = [self.list_IDs[k] for k in indexes]

		# Generate data
		X, y = self.__data_generation(list_IDs_temp)

		return X, y

	def on_epoch_end(self):
		'Updates indexes after each epoch'
		self.indexes = np.arange(len(self.list_IDs))
		if self.shuffle == True:
			np.random.shuffle(self.indexes)

	def __data_generation(self, list_IDs_temp):
		'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
		# Initialization
		X = np.empty((self.batch_size, *self.dim, self.n_channels))
		y = np.empty((self.batch_size), dtype=int)

		# Generate data
		for i, ID in enumerate(list_IDs_temp):
			# Store sample
			X[i,] = np.load('data/' + ID + '.npy')

			# Store class
			y[i] = self.labels[ID]

		return X, keras.utils.to_categorical(y, num_classes=self.n_classes)

class TrainingImageSetDataGenerator(keras.utils.Sequence):

	def __init__(self, dirpath, validation_every = 5, validation_skip = 3, batchsize=16, augcnt = 3):
		self.dirpath = dirpath
		self.batch_size = batchsize
		self.augcnt = augcnt
		self.previmg = None
		self.previmgidx = -1

		self.filelist = []
		self.validationlist = []

		allpaths = dirpath.split(';')
		for singlepath in allpaths:
			g = glob.glob(os.path.join(singlepath, "*.jpg"))
			i = 0
			flen = len(g)
			while i < flen:
				j = i + validation_skip
				addMain = True
				if j < flen and validation_every > 0:
					if (j % validation_every) == 0:
						addMain = False
				if addMain:
					self.filelist.append(g[i])
				else:
					self.validationlist.append(g[i])
				i += 1

		self._randomize_augmentations()

	def _randomize_augmentations(self):
		self.auglist = augmentation.get_random_augs(self.augcnt)
		self.auglist.append(augmentation.AUG_NONE)
		auglist2 = self.auglist.copy()
		for flipaug in auglist2:
			self.auglist.append(flipaug + augmentation.AUG_FLIP)

	def get_validation_list(self):
		return self.validationlist.copy()

	def on_epoch_end(self):
		self._randomize_augmentations()

	def __len__(self):
		return int(np.ceil(len(self.filelist * len(self.auglist)) / float(self.batch_size)))

	def __getitem__(self, idx):
		images = []
		usercontrols = []

		imgperimg = len(self.auglist)

		i = 0
		while i < self.batch_size:
			j = (idx * self.batch_size) + i
			imgidx = int(floor(float(j) / float(imgperimg)))
			imgidxstart = imgidx * imgperimg
			augidx = j - imgidxstart
			if self.previmgidx != imgidx or self.previmg is None:
				fpath = self.filelist[imgidx]
				imgfile = AugmentedImage(fpath, xform=True)
				self.previmgidx = imgidx
				self.previmg = imgfile
			else:
				imgfile = self.previmg
			imgfile.reload()
			imgfile.augment(auglist[augidx])
			images.append(imgfile.img_cv2.copy())
			throttle = imgfile.get_normalized_throttle()
			steering = imgfile.get_normalized_steering()
			usercontrols.append((throttle, steering))
			i += 1

		return np.array(images), np.array(usercontrols)

class ValidationImageSetDataGenerator(keras.utils.Sequence):

	def __init__(self, filelist, batchsize=16):
		self.filelist = filelist
		self.batch_size = batchsize

	def __len__(self):
		return int(np.ceil(len(self.filelist) / float(self.batch_size)))

	def __getitem__(self, idx):
		batch_files = self.filelist[idx * self.batch_size:(idx + 1) * self.batch_size]

		images = []
		usercontrols = []
		for f in batch_files:
			imgfile = TaggedImage(f)
			imgfile.load_img_cv2()
			imgfile.transform()
			images.append(imgfile.img_cv2.copy())
			throttle = imgfile.get_normalized_throttle()
			steering = imgfile.get_normalized_steering()
			usercontrols.append((throttle, steering))

		return np.array(images), np.array(usercontrols)