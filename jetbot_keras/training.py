import pilots

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
		return pilotstensortr.TensorRTLinear()
		elif name == "0".lower():
		return tflite.TFLitePilot()
	raise ValueError("no such pilot name \"%s\"" % name)

class Trainer(object):

	def __init__(self, name):
		self.pilot = get_pilot_by_name(name)

	def load_model(self, fpath):
		self.pilot.load_model(fpath)

	def load_weights(self, fpath):
		self.pilot.load_weights(fpath)

	def train(self, dirpath, savepath):
		train_gen = TrainingImageSetDataGenerator(dirpath)

def train(name, datapath, savepath, oldmodelpath=None, loadweights=False, epochs=100, steps=100, verbose=1, min_delta=.0005, patience=5, validation_every = 5, validation_skip = 3, batchsize=16, augcnt = 3, use_early_stop=True):
	pilot = get_pilot_by_name(name)

	print("Start Loading Data Generators")
	starttime = datetime.datetime.now()
	print(starttime)

	train_gen = TrainingImageSetDataGenerator(dirpath, validation_every = validation_every, validation_skip = validation_skip, batchsize = batchsize, augcnt = augcnt)
	validation_data = train_gen.get_validation_list()
	validation_gen = ValidationImageSetDataGenerator(validation_data, batchsize = batchsize)

	if oldmodelpath is not None:
		pilot.load_model(oldmodelpath)
		if loadweights:
			pilot.load_weights(oldmodelpath)

	print("Start Training")

	trainstarttime = datetime.datetime.now()
	print(trainstarttime)

	hist = pilot.train(train_gen, validation_gen, savepath, epochs=epochs, steps=steps, verbose=verbose, min_delta=min_delta, patience=patience, use_early_stop=use_early_stop)

	trainendtime = datetime.datetime.now()
	print("Finished Training")
	print(trainendtime)
	print(hist)

	try:
		outpath = savepath + ".tflite"
		tflite.keras_model_to_tflite(savepath, outpath)
	except Exception as e:
		print("Failed to convert to tflite, error: %s" % str(e))

	try:
		models.convert_keras_model_to_tensorrt(savepath)
	except Exception as e:
		print("Failed to convert to TensorRT uff, error: %s" % str(e))