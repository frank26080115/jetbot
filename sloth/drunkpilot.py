import visionpilot
from visionpilot import VisionPilot
from datetime import datetime
import numpy as np

class DrunkPilot(VisionPilot):

	def set_drunkenness(self, period = 1.0, amplitude = 32.0, jitter = 0.5, noise = 0.3):
		self.period = abs(period)
		self.amplitude = abs(amplitude)
		self.noise = abs(noise)
		self.jitter = abs(jitter)
		self.jitter_now = 0.0
		self.t = 0.0
		self.last_time = datetime.now()

	def run(self, img_arr):
		steering, throttle = self.process(img_arr)

		now = datetime.now()
		delta_time = now - self.last_time
		self.last_time = now

		t_inc = 360.0 * (delta_time.total_seconds() / self.period) * (1.0 + self.jitter_now)
		self.t += t_inc
		if self.t >= 360.0:
			self.t -= 360.0
			self.amplitude_pos = 1.0 + np.random.uniform(-self.noise, self.noise)
			self.amplitude_neg = 1.0 + np.random.uniform(-self.noise, self.noise)
			self.jitter_now = np.random.uniform(-self.jitter, self.jitter)
		s_off = np.sin(np.deg2rad(self.t)) * self.amplitude
		if self.t <= 180:
			s_off *= self.amplitude_pos
		else:
			s_off *= self.amplitude_neg
		steering += s_off

		steering /= 128.0
		throttle /= 128.0

		return np.clip(steering, -1.0, 1.0), np.clip(throttle, -1.0, 1.0)
