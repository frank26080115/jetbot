from tensorflow.python import keras

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

class TaggedImageSetDataGenerator(keras.utils.Sequence):

	def __init__(self, data, batchsize=128):
		self.data = data
		self.batch_size = batchsize

	def __len__(self):
		return int(np.ceil(len(self.data) / float(self.batch_size)))

	def __getitem__(self, idx):
		if self.batch_size > 0:
			batch_data = self.data[idx * self.batch_size:(idx + 1) * self.batch_size]

			images = []
			usercontrols = []
			for data in batch_data:
				data.load_img_cv2()
				data.transform()
				images.append(data.img_cv2)
				throttle = data.throttle
				steering = data.steering
				usercontrols.append((throttle, steering))

			return np.array(images), np.array(usercontrols)
		else:
			data = self.data[idx]
			data.load_img_cv2()
			data.transform()
			return (data.img_cv2, (data.throttle, data.steering))