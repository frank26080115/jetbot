'''

pilots.py

Methods to create, use, save and load pilots. Pilots
contain the highlevel logic used to determine the angle
and throttle of a vehicle. Pilots can include one or more
models to help direct the vehicles motion.

'''

import os, sys
import numpy as np

from tensorflow.python import keras
from tensorflow.python.keras.layers import Input, Dense
from tensorflow.python.keras.models import Model, Sequential
from tensorflow.python.keras.layers import Convolution2D, MaxPooling2D, Reshape, BatchNormalization
from tensorflow.python.keras.layers import Activation, Dropout, Flatten, Cropping2D, Lambda
from tensorflow.python.keras.layers.merge import concatenate
from tensorflow.python.keras.layers import LSTM
from tensorflow.python.keras.layers.wrappers import TimeDistributed as TD
from tensorflow.python.keras.layers import Conv3D, MaxPooling3D, Cropping3D, Conv2DTranspose

from models import *
import mlutils


class KerasPilot(object):
	'''
	Base class for Keras models that will provide steering and throttle to guide a car.
	'''
	def __init__(self):
		self.model = None
		self.optimizer = "adam"

	def load(self, model_path):
		self.model = keras.models.load_model(model_path)

	def load_weights(self, model_path, by_name=True):
		self.model.load_weights(model_path, by_name=by_name)

	def shutdown(self):
		pass

	def compile(self):
		raise NotImplementedError("need to override \"compile\"")

	def set_optimizer(self, optimizer_type, rate, decay):
		if optimizer_type == "adam":
			self.model.optimizer = keras.optimizers.Adam(lr=rate, decay=decay)
		elif optimizer_type == "sgd":
			self.model.optimizer = keras.optimizers.SGD(lr=rate, decay=decay)
		elif optimizer_type == "rmsprop":
			self.model.optimizer = keras.optimizers.RMSprop(lr=rate, decay=decay)
		elif optimizer_type == "adagrad":
			self.model.optimizer = keras.optimizers.Adagrad(lr=rate, decay=decay)
		elif optimizer_type == "adadelta":
			self.model.optimizer = keras.optimizers.Adadelta(lr=rate, decay=decay)
		elif optimizer_type == "adamax":
			self.model.optimizer = keras.optimizers.Adamax(lr=rate, decay=decay)
		elif optimizer_type == "nadam":
			self.model.optimizer = keras.optimizers.Nadam(lr=rate, decay=decay)
		else:
			raise Exception("unknown optimizer type: %s" % optimizer_type)

	def train(self, train_gen, val_gen, saved_model_path, epochs=100, steps=100, verbose=1, min_delta=.0005, patience=5, use_early_stop=True):

		"""
		train_gen: generator that yields an array of images an array of
		"""

		#checkpoint to save model after each epoch
		save_best = keras.callbacks.ModelCheckpoint(saved_model_path,
													monitor='val_loss',
													verbose=verbose,
													save_best_only=True,
													mode='min')

		#stop training if the validation error stops improving.
		early_stop = keras.callbacks.EarlyStopping(monitor='val_loss',
												   min_delta=min_delta,
												   patience=patience,
												   verbose=verbose,
												   mode='auto')

		callbacks_list = [save_best]

		if use_early_stop:
			callbacks_list.append(early_stop)

		v_steps = val_gen.__len__()

		hist = self.model.fit_generator(
						train_gen,
						steps_per_epoch=steps,
						epochs=epochs,
						verbose=1,
						validation_data=val_gen,
						callbacks=callbacks_list,
						validation_steps=v_steps)
		return hist


class KerasCategorical(KerasPilot):
	'''
	The KerasCategorical pilot breaks the steering and throttle decisions into discreet
	angles and then uses categorical cross entropy to train the network to activate a single
	neuron for each steering and throttle choice. This can be interesting because we
	get the confidence value as a distribution over all choices.
	This uses the mlutils.linear_bin and mlutils.linear_unbin to transform continuous
	real numbers into a range of discreet values for training and runtime.
	The input and output are therefore bounded and must be chosen wisely to match the data.
	The default ranges work for the default setup. But cars which go faster may want to
	enable a higher throttle range. And cars with larger steering throw may want more bins.
	'''
	def __init__(self, input_shape=(120, 160, 3), throttle_range=0.5, roi_crop=(0, 0), *args, **kwargs):
		super(KerasCategorical, self).__init__(*args, **kwargs)
		self.model = default_categorical(input_shape, roi_crop)
		self.compile()
		self.throttle_range = throttle_range

	def compile(self):
		self.model.compile(optimizer=self.optimizer, metrics=['acc'],
				  loss={'angle_out': 'categorical_crossentropy',
						'throttle_out': 'categorical_crossentropy'},
				  loss_weights={'angle_out': 0.5, 'throttle_out': 1.0})

	def run(self, img_arr):
		if img_arr is None:
			print('no image')
			return 0.0, 0.0

		img_arr = img_arr.reshape((1,) + img_arr.shape)
		angle_binned, throttle = self.model.predict(img_arr)
		N = len(throttle[0])
		throttle = mlutils.linear_unbin(throttle, N=N, offset=0.0, R=self.throttle_range)
		angle_unbinned = mlutils.linear_unbin(angle_binned)
		return angle_unbinned, throttle



class KerasLinear(KerasPilot):
	'''
	The KerasLinear pilot uses one neuron to output a continous value via the
	Keras linear layer. One each for steering and throttle.
	The output is not bounded.
	'''
	def __init__(self, num_outputs=2, input_shape=(120, 160, 3), roi_crop=(0, 0), *args, **kwargs):
		super(KerasLinear, self).__init__(*args, **kwargs)
		self.model = default_n_linear(num_outputs, input_shape, roi_crop)
		self.compile()

	def compile(self):
		self.model.compile(optimizer=self.optimizer,
				loss='mse')

	def run(self, img_arr):
		img_arr = img_arr.reshape((1,) + img_arr.shape)
		outputs = self.model.predict(img_arr)
		steering = outputs[0]
		throttle = outputs[1]
		return steering[0][0], throttle[0][0]



class KerasRNN_LSTM(KerasPilot):
	def __init__(self, image_w=160, image_h=120, image_d=3, seq_length=3, num_outputs=2, *args, **kwargs):
		super(KerasRNN_LSTM, self).__init__(*args, **kwargs)
		image_shape = (image_h, image_w, image_d)
		self.model = rnn_lstm(seq_length=seq_length,
			num_outputs=num_outputs,
			image_shape=image_shape)
		self.seq_length = seq_length
		self.image_d = image_d
		self.image_w = image_w
		self.image_h = image_h
		self.img_seq = []
		self.compile()
		self.optimizer = "rmsprop"

	def compile(self):
		self.model.compile(optimizer=self.optimizer,
				  loss='mse')

	def run(self, img_arr):
		if img_arr.shape[2] == 3 and self.image_d == 1:
			img_arr = mlutils.rgb2gray(img_arr)

		while len(self.img_seq) < self.seq_length:
			self.img_seq.append(img_arr)

		self.img_seq = self.img_seq[1:]
		self.img_seq.append(img_arr)

		img_arr = np.array(self.img_seq).reshape(1, self.seq_length, self.image_h, self.image_w, self.image_d )
		outputs = self.model.predict([img_arr])
		steering = outputs[0][0]
		throttle = outputs[0][1]
		return steering, throttle



class Keras3D_CNN(KerasPilot):
	def __init__(self, image_w=160, image_h=120, image_d=3, seq_length=20, num_outputs=2, *args, **kwargs):
		super(Keras3D_CNN, self).__init__(*args, **kwargs)
		self.model = build_3d_cnn(w=image_w, h=image_h, d=image_d, s=seq_length, num_outputs=num_outputs)
		self.seq_length = seq_length
		self.image_d = image_d
		self.image_w = image_w
		self.image_h = image_h
		self.img_seq = []
		self.compile()

	def compile(self):
		self.model.compile(loss='mean_squared_error', optimizer=self.optimizer, metrics=['accuracy'])

	def run(self, img_arr):

		# if depth is 3 (colour) and input depth is 1 (monochrome)
		if img_arr.shape[2] == 3 and self.image_d == 1:
			img_arr = mlutils.rgb2gray(img_arr)

		while len(self.img_seq) < self.seq_length:
			self.img_seq.append(img_arr)

		self.img_seq = self.img_seq[1:]
		self.img_seq.append(img_arr)

		img_arr = np.array(self.img_seq).reshape(1, self.seq_length, self.image_h, self.image_w, self.image_d )
		outputs = self.model.predict([img_arr])
		steering = outputs[0][0]
		throttle = outputs[0][1]
		return steering, throttle



class KerasLatent(KerasPilot):
	def __init__(self, num_outputs=2, input_shape=(120, 160, 3), *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.model = default_latent(num_outputs, input_shape)
		self.compile()

	def compile(self):
		self.model.compile(optimizer=self.optimizer, loss={
			"img_out" : "mse", "n_outputs0" : "mse", "n_outputs1" : "mse"
		}, loss_weights={
			"img_out" : 100.0, "n_outputs0" : 2.0, "n_outputs1" : 1.0
		})

	def run(self, img_arr):
		img_arr = img_arr.reshape((1,) + img_arr.shape)
		outputs = self.model.predict(img_arr)
		steering = outputs[1]
		throttle = outputs[2]
		return steering[0][0], throttle[0][0]



def get_pilot_by_name(name):
	name = name.lower()
	if name == "KerasCategorical".lower():
		return pilots.KerasCategorical()
	elif name == "KerasLinear".lower():
		return pilots.KerasLinear()
	elif name == "KerasRNN_LSTM".lower():
		return pilots.KerasRNN_LSTM()
	elif name == "Keras3D_CNN".lower():
		return pilots.Keras3D_CNN()
	elif name == "KerasLatent".lower():
		return pilots.KerasLatent()
	elif name == "TensorRTLinear".lower():
		import pilottensorrt
		return pilottensorrt.TensorRTLinear()
	elif name == "TFLitePilot".lower():
		import tflite
		return tflite.TFLitePilot()
	raise ValueError("no such pilot name \"%s\"" % name)
