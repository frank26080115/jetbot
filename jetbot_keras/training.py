import os, datetime
import models
import pilots
from datagenerators import TrainingImageSetDataGenerator, ValidationImageSetDataGenerator

from clize import run

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

def train(pilot_name, datapath, savepath, *, oldmodelpath="", loadweights="", epochs=100, steps=100, verbose=1, use_early_stop=True, min_delta=.0005, patience=5, validation_every = 5, validation_skip = 3, batchsize=16, augcnt = 3):
	"""Train a neural network model, using a set of images, and saves the resulting model to a file

	:param pilot_name: name of the pilot class, such as KerasLinear, KerasCategorical, KerasLatent, etc
	:param datapath: path to a directory containing the training data images, multiple paths can be specified if they are seperated by a semicolon
	:param savepath: path to where the Keras model will be saved
	:param oldmodelpath: optional path to existing Keras model
	:param loadweights: optional path to existing Keras model, to be loaded via the load_weights function
	:param epochs: Number of epochs for training
	:param steps: Total number of steps (batches of samples) to yield from generator before declaring one epoch finished and starting the next epoch
	:param verbose: Enables/disables verbose output during the training,  0 = silent, 1 = progress bar, 2 = one line per epoch
	:param use_early_stop: Stop training when val_loss has stopped improving
	:param min_delta: Minimum change in val_loss to qualify as an improvement, i.e. an absolute change of less than min_delta, will count as no improvement
	:param patience: Number of epochs with no improvement after which training will be stopped
	:param validation_every: From the dataset, use every X images for validation instead of training
	:param validation_skip: Skip X images in the dataset before the very first validation image is extracted from the total dataset
	:param batchsize: Batch size for training and validation
	:param augcnt: Number of different augmentations to perform on each training image
	"""
	pilot = get_pilot_by_name(pilot_name)

	datapath = datapath.strip(' ;"')
	savepath = savepath.strip(' "')
	if savepath.lower().endswith(".h5") == False:
		savepath = savepath + ".h5"

	print("Keras model will be saved to \"%s\"" % os.path.abspath(savepath))

	print("Start Loading Data Generators")
	starttime = datetime.datetime.now()

	train_gen = TrainingImageSetDataGenerator(datapath, validation_every = validation_every, validation_skip = validation_skip, batchsize = batchsize, augcnt = augcnt)
	validation_data = train_gen.get_validation_list()
	validation_gen = ValidationImageSetDataGenerator(validation_data, batchsize = batchsize)

	deltatime = datetime.datetime.now() - starttime
	print("Loading training data files took %u seconds" % int(round(deltatime.total_seconds())))

	print("Training data: %u images" % (train_gen.__len__() * batchsize))
	if train_gen.__len__() <= 0:
		print("No dataset found, quitting")
		quit()
	print("Validation data: %u images" % (validation_gen.__len__() * batchsize))

	if oldmodelpath is not None and len(oldmodelpath) > 0:
		print("Loading existing model from \"%s\"" % os.path.abspath(oldmodelpath))
		pilot.load_model(oldmodelpath)
	if loadweights is not None and len(loadweights) > 0:
		print("Loading existing weights from \"%s\"" % os.path.abspath(loadweights))
		pilot.load_weights(loadweights)

	print("Start Training")

	trainstarttime = datetime.datetime.now()
	print(trainstarttime)

	hist = pilot.train(train_gen, validation_gen, savepath, epochs=epochs, steps=steps, verbose=verbose, min_delta=min_delta, patience=patience, use_early_stop=use_early_stop)

	trainendtime = datetime.datetime.now()
	print("Finished Training")
	deltatime = datetime.datetime.now() - trainstarttime
	if deltatime.total_seconds() <= 120:
		print("Training took %u seconds" % deltatime.total_seconds())
	else:
		print("Training time =  ", deltatime)
	print(hist)

	try:
		outpath = savepath + ".tflite"
		print("Converting to tflite \"%s\"" % outpath)
		tflite.keras_model_to_tflite(savepath, outpath)
	except Exception as e:
		print("Failed to convert to tflite, error: %s" % str(e))

	try:
		print("Converting to frozen TensorFlow pb file \"%s.pb\"" % savepath)
		models.convert_keras_model_to_tensorrt(savepath)
	except Exception as e:
		print("Failed to convert to TensorRT uff, error: %s" % str(e))

	print("All Done!")

if __name__ == "__main__":
	run(train)