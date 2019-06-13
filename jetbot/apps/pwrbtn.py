#!/usr/bin/env python3

import time
import datetime
import subprocess
import RPi.GPIO as GPIO

but_pin = 13

if __name__ == '__main__':
	try:
		print("setup")
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(but_pin, GPIO.IN)
		time.sleep(0.1)
		waspressed = False
		while GPIO.input(but_pin) == GPIO.HIGH:
			GPIO.setup(but_pin, GPIO.IN)
			waspressed = True
			print("waiting for initial released state")
			time.sleep(1)
		if waspressed:
			print("release has occured")
		while True:
			if GPIO.input(but_pin) == GPIO.HIGH:
				heldcnt = 0
				heldlimit = 400
				print("press")
				subprocess.run("sync") # flush cache to disk
				while GPIO.input(but_pin) == GPIO.HIGH and heldcnt < heldlimit:
					heldcnt += 1
					time.sleep(0.01)
				if heldcnt >= heldlimit:
					print("shutdown")
					subprocess.run("shutdown now", shell=True)
					quit()
					while True: # do nothing, wait for shutdown
						time.sleep(1)
				else:
					print("short press")
			else:
				time.sleep(1)

	finally:
		try:
			print("cleanup")
			GPIO.cleanup()
		except:
			print("exception while cleaning up")
