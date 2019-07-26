import time

FILTER_CONST = 0.1

class PerfTimer(object):

	def __init__(self):
		self.t = None
		self.lt = None
		self.fps = -1
		self.fps_filtered = -1

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

	def get_framerate(self):
		return self.fps_filtered

mine = PerfTimer()

def tick():
	global mine
	mine.tick()

def get_framerate()
	global mine
	return mine.get_framerate()
