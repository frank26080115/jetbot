#!/usr/bin/env python3

import time
import datetime
import subprocess
import RPi.GPIO as GPIO

but_pin = 13
prev_btn_val = GPIO.HIGH
time_rise = False
time_fall = False
prev_pulse = False
flag_pressed = False

def btn_event(channel):
	global but_pin
	global prev_btn_val
	global time_rise
	global time_fall
	global flag_pressed
	print("event\n")
	v = GPIO.input(but_pin)
	t = datetime.datetime.now()
	if v == GPIO.HIGH and prev_btn_val == GPIO.LOW:
		time_rise = t
		if time_fall != False:
			prev_pulse = time_rise - time_fall
		time_fall = False
	elif v == GPIO.LOW and prev_btn_val == GPIO.HIGH:
		time_fall = t
		flag_pressed = True
	prev_btn_val = v

if __name__ == '__main__':
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(but_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
	GPIO.add_event_detect(but_pin, GPIO.BOTH, callback=btn_event, bouncetime=10)
	print("setup\n")
	while True:
		now = datetime.datetime.now()
		if flag_pressed:
			flag_pressed = False
			subprocess.run("sync") # flush cache to disk
			print("sync\n")
			# todo: issue lock command to motor driver
		if time_fall != False:
			timediff = now - time_fall
			if timediff.total_seconds() > 3:
				print("shutdown\n")
				subprocess.run("shutdown now", shell=True)
				while True:
					time.sleep(1)
					# do nothing, wait for shutdown
		time.sleep(1)

finally:
	GPIO.cleanup()
