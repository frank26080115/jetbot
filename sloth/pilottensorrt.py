import os, errno
from collections import namedtuple
from pilots import KerasPilot
import json
import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
from pathlib import Path
import tensorflow as tf
import tensorrt as trt

HostDeviceMemory = namedtuple('HostDeviceMemory', 'host_memory device_memory')

class TensorRTLinear(KerasPilot):
	'''
	Uses TensorRT to do the inference.
	'''
	def __init__(self, image_width=160, image_height=120, image_depth=3, *args, **kwargs):
		super(TensorRTLinear, self).__init__(*args, **kwargs)
		self.logger = trt.Logger(trt.Logger.WARNING)
		self.image_width = image_width
		self.image_height = image_height
		self.image_depth = image_depth
		self.engine = None
		self.inputs = None
		self.outputs = None
		self.bindings = None
		self.stream = None

	def compile(self):
		print('Nothing to compile')

	def load(self, model_path):
		uff_model = Path(model_path)
		frozen_path = Path('%s/%s.pb' % (uff_model.parent.as_posix(), uff_model.stem))
		if os.path.exists(uff_model) == False or os.path.isfile(uff_model) == False:
			if os.path.exists(frozen_path) and os.path.isfile(frozen_path):
				if uffconverter.convert_to_uff(frozen_path):
					pass
				else:
					raise OSError(errno.ENOENT, "UFF file not found and cannot be generated, path: \"%s\"" % model_path, model_path)
			else:
				raise OSError(errno.ENOENT, "Frozen graph file not found, needed for conversion to UFF, path: \"%s\"" % frozen_path, frozen_path)
		metadata_path = Path('%s/%s.metadata' % (uff_model.parent.as_posix(), uff_model.stem))
		with open(metadata_path.as_posix(), 'r') as metadata, trt.Builder(self.logger) as builder, builder.create_network() as network, trt.UffParser() as parser:
			metadata = json.loads(metadata.read())
			# Configure inputs and outputs
			print('Configuring I/O')
			input_names = metadata['input_names']
			output_names = metadata['output_names']
			for name in input_names:
				parser.register_input(name, (self.image_depth, self.image_height, self.image_width))

			for name in output_names:
				parser.register_output(name)

			# Parse network
			print('Parsing TensorRT Network')
			parser.parse(uff_model.as_posix(), network)
			print('Building CUDA Engine')
			self.engine = builder.build_cuda_engine(network)
			# Allocate buffers
			print('Allocating Buffers')
			self.inputs, self.outputs, self.bindings, self.stream = TensorRTLinear.allocate_buffers(self.engine)
			print('Ready')

	def run(self, image):
		# Channel first image format
		image = image.transpose((2,0,1))
		# Flatten it to a 1D array.
		image = image.ravel()
		# The first input is the image. Copy to host memory.
		image_input = self.inputs[0] 
		np.copyto(image_input.host_memory, image)
		with self.engine.create_execution_context() as context:
			[throttle, steering] = TensorRTLinear.infer(context=context, bindings=self.bindings, inputs=self.inputs, outputs=self.outputs, stream=self.stream)
			return steering[0], throttle[0]

	@classmethod
	def allocate_buffers(cls, engine):
		inputs = []
		outputs = []
		bindings = []
		stream = cuda.Stream()
		for binding in engine:
			size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
			dtype = trt.nptype(engine.get_binding_dtype(binding))
			# Allocate host and device buffers
			host_memory = cuda.pagelocked_empty(size, dtype)
			device_memory = cuda.mem_alloc(host_memory.nbytes)
			bindings.append(int(device_memory))
			if engine.binding_is_input(binding):
				inputs.append(HostDeviceMemory(host_memory, device_memory))
			else:
				outputs.append(HostDeviceMemory(host_memory, device_memory))

		return inputs, outputs, bindings, stream

	@classmethod
	def infer(cls, context, bindings, inputs, outputs, stream, batch_size=1):
		# Transfer input data to the GPU.
		[cuda.memcpy_htod_async(inp.device_memory, inp.host_memory, stream) for inp in inputs]
		# Run inference.
		context.execute_async(batch_size=batch_size, bindings=bindings, stream_handle=stream.handle)
		# Transfer predictions back from the GPU.
		[cuda.memcpy_dtoh_async(out.host_memory, out.device_memory, stream) for out in outputs]
		# Synchronize the stream
		stream.synchronize()
		# Return only the host outputs.
		return [out.host_memory for out in outputs]
