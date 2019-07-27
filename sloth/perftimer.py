import time, sys

FILTER_CONST = 0.1

class PerfTimer(object):

	def __init__(self):
		self.t = None
		self.lt = None
		self.fps = -1
		self.fps_filtered = -1
		self.max = 0
		self.min = sys.float_info.max

	def tick(self):
		self.t = time.perf_counter()
		if self.lt is None:
			self.lt = time.perf_counter()
			return
		delta = self.t - self.lt
		self.fps = 1.0 / float(delta)
		if self.fps_filtered < 0:
			self.fps_filtered = self.fps
		self.fps_filtered = (self.fps_filtered * (1.0 - FILTER_CONST)) + (self.fps * FILTER_CONST)
		self.lt = self.t
		if self.fps > self.max:
			self.max = self.fps
		if self.fps < self.min:
			self.min = self.fps

	def get_framerate(self):
		return self.fps_filtered

	def get_stats(self):
		return self.min, self.max

	def reset_stats(self):
		self.max = 0
		self.min = sys.float_info.max


mine = PerfTimer()

def tick():
	global mine
	mine.tick()

def get_framerate():
	global mine
	return mine.get_framerate()

def get_stats(self):
	global mine
	return mine.get_stats()

def reset_stats(self):
	global mine
	mine.reset_stats()
