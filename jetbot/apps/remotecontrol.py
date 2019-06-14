import evdev
from evdev import InputDevice, categorize, ecodes, KeyEvent 
import asyncio

import jetbot.camera as camera
import cv2

import time, os, sys, math, datetime

CROSS     = 305
TRIANGLE  = 307
CIRCLE    = 306
SQUARE    = 304
L1        = 308
R1        = 309
L2        = 310
R2        = 311
L3        = 314
R3        = 315
SHARE     = 312
OPTION    = 313
TPAD      = 317
PSHOME    = 316
LEFT_X    = "ABS_X"   # 0 is left
LEFT_Y    = "ABS_Y"   # 0 is up
RIGHT_X   = "ABS_Z"   # 0 is left
RIGHT_Y   = "ABS_RZ"  # 0 is up
L2_ANALOG = "ABS_RX"  # 0 is released
R2_ANALOG = "ABS_RY"  # 0 is released
DPAD_X    = "ABS_HAT0X" # -1 is left
DPAD_Y    = "ABS_HAT0Y" # -1 is up

axis = {
		"ABS_RZ": 128,
		"ABS_Z": 128,
		"ABS_Y": 128,
		"ABS_X": 128,
		"ABS_RX": 128,
		"ABS_RY": 128,
		"ABS_HAT0X": 0,
		"ABS_HAT0Y": 0,
	}

dev = None
cam = None
capidx = 0

def get_dualshock4():
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		dn = device.name.lower().strip()
		if dn == "wireless controller":
			return device

def event_handler(event):
	global axis
	global cam
	if event.type == ecodes.EV_ABS: 
		absevent = categorize(event) 
		axiscode = ecodes.bytype[absevent.event.type][absevent.event.code]
		if "ABS_" in axiscode:
			axis[axiscode] = absevent.event.value
	elif event.type == ecodes.EV_KEY:
		btnevent = categorize(event) 
		if event.value == KeyEvent.key_down:
			if event.code == R1:
				snapname = get_snap_name(event.code)
				print("saving pic: " + snapname)
				cam_capture(snapname)
			if event.code == PSHOME:
				if cam != None:
					try:
						cam.stop()
						time.sleep(1)
						del cam
					finally:
						cam = None
		elif event.value == KeyEvent.key_up:
			abc = 1

def run():
	global cam
	global dev
	global axis
	while True:
		dev = get_dualshock4()
		if dev != None:
			print("DualShock4 found, %s" % str(dev))
		else:
			time.sleep(2)
		while dev != None:
			try:
				event = dev.read_one()
				if event != None:
					event_handler(event)
				else:
					time.sleep(0)

			except OSError:
				print("DualShock4 disconnected")
				dev = None

def axis_normalize(v, curve=2.1, deadzone_inner=8, deadzone_outer=8):
	limit = 255
	center = limit / 2.0
	m = 1
	if v < center:
		m = -1
		v = 255 - v
	v -= center + deadzone_inner
	r = limit - deadzone_outer
	r -= center + deadzone_inner
	v = v / r

	v = (math.exp(v * curve) - math.exp(0)) / (math.exp(curve) - math.exp(0))

	if v < 0.0:
		return 0 * m
	elif v > 1.0:
		return 1.0 * m
	else:
		return v * m

def axis_mix(x, y):
	left = -y
	right = -y
	left += x
	right -= x
	left = min(1.0, max(-1.0, left))
	right = min(1.0, max(-1.0, right))
	return left, right

def axis_vector(x, y):
	mag = math.sqrt((x*x) + (y*y))
	theta = math.atan2(x, -y)
	ang = math.degrees(theta)
	if mag > 1.0:
		mag = 1.0
	return mag, ang

def cam_capture(fn):
	global cam
	global capidx

	capidx += 1

	path = "/home/jetbot/camerasnaps"
	try:
		os.makedirs(path)
	except FileExistsError:
		path = path
	except Exception as ex:
		print("Exception creating directory '%s', error: %s" % (path, str(ex)))
		return

	if cam == None:
		try:
			cam = camera.Camera()
		except Exception as ex:
			print("Exception initializing camera: " + str(ex))
			cam = None
			return

	try:
		fp = os.path.join(path, fn + '.jpg')
		with open(fp, 'wb') as f:
			f.write(bytes(cv2.imencode('.jpg', cam.value)[1]))
	except Exception as ex:
		print("Exception writing to file '%s', error: %s" % (fp, str(ex)))

def get_snap_name(initiating_key=None):
	global dev
	global capidx
	global axis

	now = datetime.datetime.now()

	keybitmap = 0
	try:
		all_btns = dev.active_keys()
		for b in all_btns:
			bb = b - 304
			keybitmap |= 1 << bb
	except:
		keybitmap = keybitmap

	if initiating_key != None:
		bb = initiating_key - 304
		keybitmap |= 1 << bb

	name = "%04u%02u%02u%02u%02u%02u_%08u" % (now.year, now.month, now.day, now.hour, now.minute, now.second, capidx)

	try:
		name += "_%08X" % keybitmap

		mag, ang = axis_vector(axis[DPAD_X], axis[DPAD_Y])
		if ang < 0:
			ang = 360 + ang
		name += "_%03u%03u" % (round(mag * 100.0), round(ang))

		mag, ang = axis_vector(axis_normalize(axis[LEFT_X]), axis_normalize(axis[LEFT_Y]))
		if ang < 0:
			ang = 360 + ang
		name += "_%03u%03u" % (round(mag * 100.0), round(ang))

		mag, ang = axis_vector(axis_normalize(axis[RIGHT_X]), axis_normalize(axis[RIGHT_Y]))
		if ang < 0:
			ang = 360 + ang
		name += "_%03u%03u" % (round(mag * 100.0), round(ang))
	except Exception as ex:
		print ("Exception while generating snap name: " + str(ex))

	return name