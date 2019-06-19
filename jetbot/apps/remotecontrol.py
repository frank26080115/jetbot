import evdev
from evdev import InputDevice, categorize, ecodes, KeyEvent

from jetbot import Robot
from jetbot import Camera
from cv2 import imencode

import time, os, sys, math, datetime, subprocess
import pwd, grp

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
OTHERCODE = 320
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

dualshock = None
cam = None
camproc = None
robot = None
capidx = 0

def get_dualshock4():
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		dn = device.name.lower().strip()
		if dn == "wireless controller":
			return device

def event_handler(event, is_remotecontrol=True, is_cameracapture=False):
	global axis
	global cam
	global robot

	if event.type == ecodes.EV_ABS: 
		absevent = categorize(event) 
		axiscode = ecodes.bytype[absevent.event.type][absevent.event.code]
		if "ABS_" in axiscode:
			axis[axiscode] = absevent.event.value

	if is_cameracapture and cam == None:
		snapname = get_snap_name(OTHERCODE)
		print("saving single pic: " + snapname)
		cam_capture(snapname)

	if event.type == ecodes.EV_KEY:
		btnevent = categorize(event) 
		if event.value == KeyEvent.key_down:
			if event.code == TPAD:
				if is_remotecontrol:
					try:
						robot.motors_makeSafe()
					except Exception:
						pass
					end_cam_proc()
				elif is_cameracapture:
					pass
			elif event.code == PSHOME:
				if is_remotecontrol:
					try:
						robot.motors_makeUnsafe()
					except Exception:
						pass
			elif event.code == R1:
				if is_remotecontrol:
					start_cam_proc()
				elif is_cameracapture:
					snapname = get_snap_name(event.code)
					print("saving single pic: " + snapname)
					cam_capture(snapname)
			elif event.code == R2:
				if is_remotecontrol:
					start_cam_proc()
		elif event.value == KeyEvent.key_up:
			pass

def run(remotecontrol=True, cameracapture=False):
	global dualshock
	global robot
	global axis
	meainingful_input_time = None
	cam_cap_time = None
	last_speed_debug_time = datetime.datetime.now()

	print("Remote Control script running! ", end=" ")
	if remotecontrol:
		print("in RC mode")
	elif cameracapture:
		print("in CAMERA mode")
	else:
		print("unknown mode, quitting")
		quit()

	if remotecontrol:
		try:
			robot = Robot()
		except Exception as ex:
			sys.stderr.write("Failed to initialize motor drivers, error: %s" % (str(ex)))
			robot = None

	while True:
		dualshock = get_dualshock4()
		if dualshock != None:
			print("DualShock4 found, %s" % str(dualshock))
		else:
			time.sleep(2)
		while dualshock != None:
			try:
				event = dualshock.read_one()
				if event != None:
					event_handler(event, is_remotecontrol=remotecontrol, is_cameracapture=cameracapture)
				else:
					time.sleep(0)
					all_btns = dualshock.active_keys()
					if remotecontrol:
						meainingful_input = False # meaningful input means any buttons pressed or the stick has been moved
						mag_dpad, ang_dpad = axis_vector(axis[DPAD_X], axis[DPAD_Y])
						mag_left, ang_left = axis_vector(axis_normalize(axis[LEFT_X], curve=0), axis_normalize(axis[LEFT_Y], curve=0))
						mag_right, ang_right = axis_vector(axis_normalize(axis[RIGHT_X], curve=0), axis_normalize(axis[RIGHT_Y], curve=0))
						now = datetime.datetime.now()
						if len(all_btns) > 0 or mag_dpad != 0 or mag_left > 0.1 or mag_right > 0.1:
							meainingful_input = True
							if meainingful_input_time == None:
								print("meaningful input!")
							meainingful_input_time = now
						elif meainingful_input_time != None: # user may have let go, check for timeout
							delta_time = now - meainingful_input_time
							if delta_time.total_seconds() > 2:
								print("No meaningful input, stopping robot motors")
								meainingful_input = False
								meainingful_input_time = None
								if robot != None:
									robot.stop()
							else:
								meainingful_input = True

						if meainingful_input:
							left_speed = 0
							right_speed = 0
							ignore_dpad = False
							ignore_rightstick = True
							if mag_dpad != 0 and ignore_dpad == False:
								left_speed, right_speed = axis_mix(axis[DPAD_X], axis[DPAD_Y])
								left_speed /= 4
								right_speed /= 4
							elif mag_left > mag_right or ignore_rightstick == True:
								left_speed, right_speed = axis_mix(axis_normalize(axis[LEFT_X]), axis_normalize(axis[LEFT_Y]))
								if ignore_rightstick == False:
									left_speed /= 2
									right_speed /= 2
							else:
								left_speed, right_speed = axis_mix(axis_normalize(axis[RIGHT_X]), axis_normalize(axis[RIGHT_Y]))
							if robot != None:
								robot.set_motors(left_speed, right_speed)
							delta_time = now - last_speed_debug_time
							if delta_time.total_seconds() >= 1:
								print("leftmotor: %.2f      rightmotor: %.2f" % (left_speed, right_speed))
								last_speed_debug_time = now
					elif cameracapture:
						now = datetime.datetime.now()
						need_cap = False
						if R2 in all_btns:
							cam_cap_time = now
							need_cap = R2
						else:
							if cam_cap_time != None:
								timedelta = now - cam_cap_time
								if timedelta.total_seconds() < 5:
									need_cap = OTHERCODE
								else:
									cam_cap_time = None
						if need_cap != False:
							snapname = get_snap_name(need_cap)
							print("saving running pic: " + snapname)
							cam_capture(snapname)
							cam_frame_time = now
							while True:
								now = datetime.datetime.now()
								cam_frame_timedelta = now - cam_frame_time
								if cam_frame_timedelta.total_seconds() >= 0.25:
									break
								event = dualshock.read_one()
								if event != None:
									event_handler(event, is_remotecontrol=False, is_cameracapture=True)

			except OSError:
				print("DualShock4 disconnected")
				dualshock = None
				if remotecontrol:
					end_cam_proc()

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

	if curve != 0:
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

def axis_vector(x, y, maglim = 2.0):
	mag = math.sqrt((x*x) + (y*y))
	theta = math.atan2(x, -y)
	ang = math.degrees(theta)
	if mag > maglim:
		mag = maglim
	return mag, ang

def cam_capture(fn):
	global cam
	global capidx

	capidx += 1

	path = "/home/jetbot/camerasnaps"
	try:
		os.makedirs(path)
	except FileExistsError:
		pass
	except Exception as ex:
		print("Exception creating directory '%s', error: %s" % (path, str(ex)))
		return

	if cam == None:
		try:
			print("Initializing camera...")
			cam = Camera.instance(width=960, height=720, flipmode=2)
			print("\r\nCamera initialized!")
		except Exception as ex:
			sys.stderr.write("Exception initializing camera: " + str(ex))
			cam = None
			return

	try:
		fp = os.path.join(path, fn + '.jpg')
		with open(fp, 'wb') as f:
			f.write(bytes(imencode('.jpg', cam.value)[1]))
		try:
			uid = pwd.getpwnam("jetbot").pw_uid
			gid = grp.getgrnam("jetbot").gr_gid
			os.chown(fp, uid, gid)
		except Exception as ex:
			sys.stderr.write("Exception changing ownership of file '%s', error: %s" % (fp, str(ex)))
	except Exception as ex:
		sys.stderr.write("Exception writing to file '%s', error: %s" % (fp, str(ex)))

def get_snap_name(initiating_key=None):
	global dualshock
	global capidx
	global axis

	now = datetime.datetime.now()

	keybitmap = 0
	try:
		all_btns = dualshock.active_keys()
		for b in all_btns:
			bb = b - 304
			keybitmap |= 1 << bb
	except:
		pass

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

		mag, ang = axis_vector(axis_normalize(axis[LEFT_X]), axis_normalize(axis[LEFT_Y]), maglim=1.0)
		if ang < 0:
			ang = 360 + ang
		name += "_%03u%03u" % (round(mag * 100.0), round(ang))

		mag, ang = axis_vector(axis_normalize(axis[RIGHT_X]), axis_normalize(axis[RIGHT_Y]), maglim=1.0)
		if ang < 0:
			ang = 360 + ang
		name += "_%03u%03u" % (round(mag * 100.0), round(ang))
	except Exception as ex:
		sys.stderr.write ("Exception while generating snap name: " + str(ex))

	return name

def start_cam_proc():
	global camproc
	if camproc != None:
		return
	print("starting camera process...", end=" ")
	camproc = subprocess.Popen(['python3', '/home/jetbot/jetbot/jetbot/apps/remotecamera.py'])
	print(" done!")

def end_cam_proc():
	global camproc
	if camproc == None:
		return
	try:
		camproc.kill()
		camproc = None
	except Exception as ex:
		sys.stderr.write("Exception while trying to kill camera process: " + str(ex))
	finally:
		print("ended camera process")

def set_camera_instance(c):
	global cam
	cam = c

def get_camera_instance():
	global cam
	return cam

if __name__ == '__main__':
	run()
