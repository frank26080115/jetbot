from __future__ import print_function
import keras
from keras.datasets import cifar10
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
import numpy as np
import cv2
import os

import ijsv

#colorspace = "rgb" # 76.01
#colorspace = "lab" # 77.36
colorspace = "ijsv" # 73.93

# the following bit of code solves an error that says "failed to create cublas handle: CUBLAS_STATUS_ALLOC_FAILED"
# it forces the tensorflow session to start "with allow_growth = True"
import tensorflow as tf
from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
config.log_device_placement = False  # to log device placement (on which device the operation ran)
                                    # (nothing gets printed in Jupyter, only if you run it standalone)
sess = tf.Session(config=config)
set_session(sess)  # set this TensorFlow session as the default session for Keras
# now tensorflow will correctly allocate memory on the GPU

batch_size = 32
num_classes = 10
epochs = 100
num_predictions = 20
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'keras_cifar10_trained_model_%s.h5' % (colorspace)

# The data, split between train and test sets:
(x_train, y_train), (x_test, y_test) = cifar10.load_data()
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

if colorspace == "rgb" or colorspace == "lab":
	in_shape = x_train.shape[1:]
elif colorspace == "ijsv":
	in_shape = (x_train.shape[1], x_train.shape[2], 4)
else:
	raise Exception("not a valid colorspace")

model = Sequential()
model.add(Conv2D(32, (3, 3), padding='same', input_shape=in_shape))
model.add(Activation('relu'))
model.add(Conv2D(32, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(64, (3, 3), padding='same'))
model.add(Activation('relu'))
model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

# initiate RMSprop optimizer
opt = keras.optimizers.rmsprop(lr=0.0001, decay=1e-6)

# Let's train the model using RMSprop
model.compile(loss='categorical_crossentropy',
			  optimizer=opt,
			  metrics=['accuracy'])

if colorspace == "lab":
	print("Converting colorspace to CIELab... ")
	x_train_lab = []
	x_test_lab = []
	c = 0
	for i in x_train:
		j = cv2.cvtColor(i, cv2.COLOR_RGB2Lab)
		x_train_lab.append(j)
		c += 1
	for i in x_test:
		j = cv2.cvtColor(i, cv2.COLOR_RGB2Lab)
		x_test_lab.append(j)
		c += 1
	x_train = np.array(x_train_lab)
	x_test = np.array(x_test_lab)
	print("done! (%u)" % c)
elif colorspace == "ijsv":
	print("Converting colorspace to IJSV... ")
	x_train_ijsv = []
	x_test_ijsv = []
	c = 0
	for i in x_train:
		j = cv2.cvtColor(i, cv2.COLOR_RGB2HSV)
		j = ijsv.convert_HSV_to_IJSV(j)
		x_train_ijsv.append(j)
		c += 1
	for i in x_test:
		j = cv2.cvtColor(i, cv2.COLOR_RGB2HSV)
		j = ijsv.convert_HSV_to_IJSV(j)
		x_test_ijsv.append(j)
		c += 1
	x_train = np.array(x_train_ijsv)
	x_test = np.array(x_test_ijsv)
	print("done! (%u)" % c)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

model.fit(x_train, y_train,
		  batch_size=batch_size,
		  epochs=epochs,
		  validation_data=(x_test, y_test),
		  shuffle=True)

# Save model and weights
if not os.path.isdir(save_dir):
	os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

# Score trained model.
scores = model.evaluate(x_test, y_test, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])