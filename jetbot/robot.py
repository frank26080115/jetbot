import time, datetime
import traitlets
from traitlets.config.configurable import SingletonConfigurable
from Adafruit_MotorHAT import Adafruit_MotorHAT

class Robot(SingletonConfigurable):

	# config
	i2c_bus = traitlets.Integer(default_value=1).tag(config=True)
	left_motor_channel = traitlets.Integer(default_value=1).tag(config=True)
	left_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)
	right_motor_channel = traitlets.Integer(default_value=2).tag(config=True)
	right_motor_alpha = traitlets.Float(default_value=1.0).tag(config=True)
	brake_speed = traitlets.Integer(default_value=255).tag(config=True)

	CONST_FORWARD   = Adafruit_MotorHAT.FORWARD
	CONST_BACKWARD  = Adafruit_MotorHAT.BACKWARD
	CONST_BRAKE     = Adafruit_MotorHAT.RELEASE
	CONST_RELEASE   = Adafruit_MotorHAT.BRAKE

	braketime = None

	def __init__(self, *args, **kwargs):
		super(Robot, self).__init__(*args, **kwargs)
		self.motor_driver = Adafruit_MotorHAT(i2c_bus=self.i2c_bus)
		self.left_motor = self.motor_driver.getMotor(self.left_motor_channel)
		self.right_motor = self.motor_driver.getMotor(self.right_motor_channel)

	def set_motors(self, left_speed, right_speed):
		# check if one motor is much slower than the other, apply brake because the momentum is ruining the turn radius
		if abs(left_speed) >= abs(right_speed) * 2 and abs(right_speed) <= 0.1:
			self.left_motor.setSpeed(self.map_speed(left_speed, self.left_motor_alpha))
			if left_speed >= 0:
				self.left_motor.run(self.CONST_FORWARD)
			else:
				self.left_motor.run(self.CONST_BACKWARD)
			self.right_motor.setSpeed(self.brake_speed)
			self.right_motor.run(self.CONST_BRAKE)
		elif abs(right_speed) >= abs(left_speed) * 2 and abs(left_speed) <= 0.1:
			self.right_motor.setSpeed(self.map_speed(right_speed, self.right_motor_alpha))
			if right_speed >= 0:
				self.right_motor.run(self.CONST_FORWARD)
			else:
				self.right_motor.run(self.CONST_BACKWARD)
			self.left_motor.setSpeed(self.brake_speed)
			self.left_motor.run(self.CONST_BRAKE)
		else: # both motors running at similar speeds
			self.left_motor.setSpeed(self.map_speed(left_speed, self.left_motor_alpha))
			self.right_motor.setSpeed(self.map_speed(right_speed, self.right_motor_alpha))
			if left_speed >= 0:
				self.left_motor.run(self.CONST_FORWARD)
			else:
				self.left_motor.run(self.CONST_BACKWARD)
			if right_speed >= 0:
				self.right_motor.run(self.CONST_FORWARD)
			else:
				self.right_motor.run(self.CONST_BACKWARD)

		# traitlets will check if the value has changed and send the correct commands
		# but just in case, we handle full-stop explicitly
		if abs(left_speed) <= (1.0 / 128.0) and abs(right_speed) <= (1.0 / 128.0):
			# we want to brake when initially coming to a stop
			# but we also want to release the brake after a certain amount of time
			now = datetime.datetime.now()
			if self.braketime is None:
				self.braketime = datetime.datetime.now()
				self.left_motor.setSpeed(self.brake_speed)
				self.right_motor.setSpeed(self.brake_speed)
				self.left_motor.run(self.CONST_BRAKE)
				self.right_motor.run(self.CONST_BRAKE)
			else:
				timedelta = now - self.braketime
				if timedelta.total_seconds() > 5:
					self.left_motor.setSpeed(0)
					self.right_motor.setSpeed(0)
					self.left_motor.run(self.CONST_RELEASE)
					self.right_motor.run(self.CONST_RELEASE)
				else:
					self.left_motor.run(self.CONST_BRAKE)
					self.right_motor.run(self.CONST_BRAKE)
		else:
			braketime = None

	def map_speed(self, speed, alpha, beta=0):
		abs_speed = abs(speed)
		mapped_value = int(round(255.0 * (alpha * abs_speed + beta)))
		mapped_speed = min(max(abs(mapped_value), 0), 255)
		return mapped_speed

	def forward(self, speed=1.0):
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
