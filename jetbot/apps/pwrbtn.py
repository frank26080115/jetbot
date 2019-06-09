#!/usr/bin/env python3

import time
import datetime
import subprocess
import RPi.GPIO as GPIO

but_pin = 13
flag_pressed = False

# def btn_event(channel):
	# global but_pin
	# global flag_pressed
	# print("event")
	# v = GPIO.input(but_pin)
	# t = datetime.datetime.now()
	# if v == GPIO.LOW:
		# flag_pressed = True

if __name__ == '__main__':
	try:
		print("setup")
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(but_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
		while GPIO.input(but_pin) == GPIO.LOW:
			print("waiting for initial released state")
			time.sleep(1)
		GPIO.add_event_detect(but_pin, GPIO.BOTH, bouncetime=10)
		while True:
			if GPIO.event_detected(but_pin):
				#flag_pressed = False
				#subprocess.run("sync") # flush cache to disk
				print("event")
				# todo: issue lock command to motor driver
			elif GPIO.input(but_pin) == GPIO.LOW:
				heldcnt = 0
				heldlimit = 400
				while GPIO.input(but_pin) == GPIO.LOW and heldcnt < heldlimit:
					heldcnt += 1
					time.sleep(0.01)
				if heldcnt >= heldlimit:
					print("shutdown")
					#subprocess.run("shutdown now", shell=True)
					quit()
					#while True:
					#	time.sleep(1)
					#	# do nothing, wait for shutdown
			else:
				time.sleep(1)

	finally:
		try:
			print("cleanup")
			GPIO.cleanup()
		except:
			print("exception while cleaning up")
