'''Trains a simple deep NN on the MNIST dataset.
Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop

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

batch_size = 128
epochs = 20

# the data, shuffled and split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# x_train is a 60000 grayscale images, 28 x 28 in size
# x_test is 10000 images
# y_train is 60000 numbers (single digits between 0 and 9) that corresponds to what is in the x_train images
# y_test is the numbers that corresponds to x_test

# turn 2D array into 1D
x_train = x_train.reshape(x_train.shape[0], x_train.shape[1] * x_train.shape[2])
x_test = x_test.reshape(x_test.shape[0], x_test.shape[1] * x_test.shape[2])

# convert data type
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')

# normalize
x_train /= 255
x_test /= 255

print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
num_classes = max(y_train) + 1
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

num_layers = 1
layer_size = 512 * 1
dropout_rate = 0.2

model = Sequential()
model.add(Dense(layer_size, activation='relu', input_shape=(x_train.shape[1],)))
model.add(Dropout(dropout_rate))

i = 0
while i < num_layers:
	model.add(Dense(layer_size, activation='relu'))
	model.add(Dropout(dropout_rate))
	i += 1

model.add(Dense(num_classes, activation='softmax'))

model.summary()

model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test))

score = model.evaluate(x_test, y_test, verbose=0)

print('Test loss:', score[0])
print('Test accuracy:', score[1])