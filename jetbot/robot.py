import time, datetime
import traitlets
from traitlets.config.configurable import SingletonConfigurable
from Adafruit_MotorHAT import Adafruit_MotorHAT
from .motor import Motor


class Robot(SingletonConfigurable):
	
	left_motor = traitlets.Instance(Motor)
	right_motor = traitlets.Instance(Motor)

	# config
	i2c_bus = traitlets.Integer(default_value=1).tag(config=True)
	left_motor_channel = traitlets.Integer(default_value=1).tag(config=True)
	left_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)
	right_motor_channel = traitlets.Integer(default_value=2).tag(config=True)
	right_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)

	braketime = None

	def __init__(self, *args, **kwargs):
		super(Robot, self).__init__(*args, **kwargs)
		self.motor_driver = Adafruit_MotorHAT(i2c_bus=self.i2c_bus)
		self.left_motor = Motor(self.motor_driver, channel=self.left_motor_channel, alpha=self.left_motor_alpha)
		self.right_motor = Motor(self.motor_driver, channel=self.right_motor_channel, alpha=self.right_motor_alpha)

	def set_motors(self, left_speed, right_speed):
		self.left_motor.value = left_speed
		self.right_motor.value = right_speed
		# traitlets will check if the value has changed and send the correct commands
		# but just in case, we handle full-stop explicitly
		if left_speed == 0 and right_speed == 0:
			self.left_motor._motor.setSpeed(0)
			self.right_motor._motor.setSpeed(0)
			# we want to brake when initially coming to a stop
			# but we also want to release the brake after a certain amount of time
			now = datetime.datetime.now()
			if self.braketime == None:
				self.braketime = datetime.datetime.now()
				self.left_motor._motor.run(Adafruit_MotorHAT.BRAKE)
				self.right_motor._motor.run(Adafruit_MotorHAT.BRAKE)
			else:
				timedelta = now - self.braketime
				if timedelta.total_seconds() > 2:
					self.left_motor._motor.run(Adafruit_MotorHAT.RELEASE)
					self.right_motor._motor.run(Adafruit_MotorHAT.RELEASE)
				else:
					self.left_motor._motor.run(Adafruit_MotorHAT.BRAKE)
					self.right_motor._motor.run(Adafruit_MotorHAT.BRAKE)
		else:
			braketime = None

	def forward(self, speed=1.0, duration=None):
		self.set_motors(speed, speed)

	def backward(self, speed=1.0):
		self.set_motors(-speed, -speed)

	def left(self, speed=1.0):
		self.set_motors(-speed, speed)

	def right(self, speed=1.0):
		self.set_motors(speed, -speed)

	def stop(self):
		self.set_motors(0, 0)

	def motor_i2c_send(self, regAdr, regVal):
		self.motor_driver._pwm.i2c.write8(regAdr, regVal)

	# this will cause the Teensy to ignore all motor commands and stop the robot
	def motors_makeSafe(self):
		self.motor_i2c_send(0xFF, 0x00) # implemented on the Teensy

	# this will "unlock" the Teensy, it will start to respond to all motor commands again
	def motors_makeUnsafe(self):
		self.motor_i2c_send(0xFF, 0x55) # implemented on the Teensy
		self.stop() # force change of speed variables
