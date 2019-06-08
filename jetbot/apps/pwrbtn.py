import time
import datetime
import subprocess

but_pin = 18
prev_btn_val = GPIO.HIGH
time_rise = False
time_fall = False
flag_pressed = False

def btn_event(channel):
	global but_pin
	global prev_btn_val
	global time_rise
	global time_fall
	global flag_pressed
	subprocess.run("sync")
	v = GPIO.input(but_pin)
	t = datetime.datetime.now()
	if v == GPIO.HIGH and prev_btn_val == GPIO.LOW:
		time_rise = t
	elif v == GPIO.LOW and prev_btn_val == GPIO.HIGH:
		time_fall = t
		flag_pressed = True
	prev_btn_val = v

if __name__ == '__main__':
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(but_pin, GPIO.IN)
	GPIO.add_event_detect(but_pin, GPIO.BOTH, callback=btn_event, bouncetime=10)
	while True:
		now = datetime.datetime.now()
		if flag_pressed:
			flag_pressed = False
			subprocess.run("sync") # flush cache to disk
			# todo: issue lock command to motor driver
		if time_fall != False:
			timediff = now - time_fall
			if timediff.total_seconds() > 3:
				subprocess.run("shutdown now", shell=True)
				while True:
					time.sleep(1)
					# do nothing, wait for shutdown
		time.sleep(1)
