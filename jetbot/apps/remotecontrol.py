import evdev
from evdev import InputDevice, categorize, ecodes, KeyEvent

from jetbot import Robot
from jetbot import Camera
import jetbot.utils.teensyadc as teensyadc
from cv2 import imencode

import time, os, sys, math, datetime, subprocess
import pwd, grp
import signal, select

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
NN_STEERING = "NN_STEERING"
NN_THROTTLE = "NN_THROTTLE"

axis = {
		"ABS_RZ": 128,
		"ABS_Z": 128,
		"ABS_Y": 128,
		"ABS_X": 128,
		"ABS_RX": 128,
		"ABS_RY": 128,
		"ABS_HAT0X": 0,
		"ABS_HAT0Y": 0,
		"NN_STEERING": 0,
		"NN_THROTTLE": 0,
	}

dualshock = None
cam = None
camproc = None
nnproc = None
robot = None
capidx = 0
continuouscap = False
continuouscaptime = None
neuralnet_latched = False

def get_dualshock4():
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		dn = device.name.lower().strip()
		if dn == "wireless controller":
			return device

def gamepad_event_handler(event, is_remotecontrol=True, is_cameracapture=False):
	global axis
	global cam
	global robot
	global continuouscap
	global continuouscaptime
	global neuralnet_latched

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
					neuralnet_latched = False
					try:
						robot.motors_makeSafe()
					except Exception:
						pass
					end_cam_proc()
					end_nn_proc()
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
			elif event.code == L1:
				if is_remotecontrol:
					start_cam_proc()
				elif is_cameracapture:
					continuouscap = not continuouscap
					continuouscaptime = datetime.datetime.now()
			elif event.code == TRIANGLE:
				neuralnet_latched = False
		elif event.value == KeyEvent.key_up:
			pass

def run(remotecontrol=True, cameracapture=False):
	global dualshock
	global robot
	global axis
	global continuouscap
	global continuouscaptime
	global neuralnet_latched
	global nnproc

	prevShutter = False
	meaningful_input_time = None
	neuralnet_input_time = None
	cam_cap_time = None
	last_speed_debug_time = datetime.datetime.now()
	last_tick_debug_time = datetime.datetime.now()

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

		now = datetime.datetime.now()
		delta_time = now - last_tick_debug_time
		if delta_time.total_seconds() > 5:
			last_tick_debug_time = now
			sys.stderr.write("tick %s" % (str(now)))

		while dualshock != None:
			now = datetime.datetime.now()
			delta_time = now - last_tick_debug_time
			if delta_time.total_seconds() > 5:
				last_tick_debug_time = now
				sys.stderr.write("tick %s" % (str(now)))

			try:
				event = dualshock.read_one()
				if event != None:
					gamepad_event_handler(event, is_remotecontrol=remotecontrol, is_cameracapture=cameracapture)
				else:
					time.sleep(0)
					all_btns = dualshock.active_keys()
					if remotecontrol:
						meaningful_input = False # meaningful input means any buttons pressed or the stick has been moved

						if TRIANGLE in all_btns:
							neuralnet_latched = False

						mag_dpad, ang_dpad = axis_vector(axis[DPAD_X], axis[DPAD_Y])
						mag_left, ang_left = axis_vector(axis_normalize(axis[LEFT_X], curve=0), axis_normalize(axis[LEFT_Y], curve=0))
						mag_right, ang_right = axis_vector(axis_normalize(axis[RIGHT_X], curve=0), axis_normalize(axis[RIGHT_Y], curve=0))
						now = datetime.datetime.now()
						if mag_dpad != 0 or mag_left > 0.1 or mag_right > 0.1:
							meaningful_input = True
							if meaningful_input_time == None:
								print("meaningful input!")
							meaningful_input_time = now
						elif meaningful_input_time != None: # user may have let go, check for timeout
							delta_time = now - meaningful_input_time
							if delta_time.total_seconds() > 2:
								print("No meaningful input, stopping robot motors")
								meaningful_input = False
								meaningful_input_time = None
								if robot != None:
									robot.stop()
							else:
								meaningful_input = True

						use_nn = False
						if SQUARE in all_btns:
							neuralnet_latched = True
						if TRIANGLE in all_btns:
							neuralnet_latched = False
						if neuralnet_latched or CROSS in all_btns:
							use_nn = True

						if meaningful_input == False and nnproc is not None: # remote control inputs always override neural net inputs
							while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
								line = sys.stdin.readline()
								if line:
									try:
										axis[NN_THROTTLE] = int(line[0:3])
										axis[NN_STEERING] = int(line[3:])
										neuralnet_input_time = now
									except:
										pass

						if neuralnet_input_time != None and use_nn:
							delta_time = now - neuralnet_input_time
							if delta_time.total_seconds() < 5:
								meaningful_input = True
								meaningful_input_time = now

						if meaningful_input:
							left_speed = 0
							right_speed = 0
							ignore_dpad = False
							#ignore_rightstick = True

							if use_nn:
								start_nn_proc() # this will check if process has already started
								left_speed, right_speed = axis_mix(axis_normalize(axis[NN_STEERING]), axis_normalize(255 - axis[NN_THROTTLE]))
							elif mag_dpad != 0 and ignore_dpad == False:
								left_speed, right_speed = axis_mix(float(axis[DPAD_X]) / 3.0, axis[DPAD_Y])
							#elif mag_left > mag_right or ignore_rightstick == True:
							#	left_speed, right_speed = axis_mix(axis_normalize(axis[LEFT_X]), axis_normalize(axis[LEFT_Y]))
							#	if ignore_rightstick == False:
							#		left_speed /= 2
							#		right_speed /= 2
							else:
							#	left_speed, right_speed = axis_mix(axis_normalize(axis[RIGHT_X]), axis_normalize(axis[RIGHT_Y]))
								left_speed, right_speed = axis_mix(axis_normalize(axis[RIGHT_X]), axis_normalize(axis[LEFT_Y]))
							if robot != None:
								robot.set_motors(left_speed, right_speed)
							delta_time = now - last_speed_debug_time
							if delta_time.total_seconds() >= 1:
								if use_nn:
									print("nn -> ", end="")
								print("leftmotor: %.2f      rightmotor: %.2f" % (left_speed, right_speed))
								last_speed_debug_time = now
					elif cameracapture:
						now = datetime.datetime.now()
						need_cap = False

						if L1 in all_btns:
							if prevShutter == False:
								if continuouscaptime != None:
									timedelta = now - continuouscaptime
									if timedelta.total_seconds() > 0.5:
										continuouscap = not continuouscap
								else:
									continuouscap = not continuouscap
							prevShutter = True
						else:
							prevShutter = False

						if continuouscap:
							cam_cap_time = now
							need_cap = L1
						else:
							if cam_cap_time != None:
								timedelta = now - cam_cap_time
								if timedelta.total_seconds() < 1:
									#need_cap = OTHERCODE
									pass
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
								if cam_frame_timedelta.total_seconds() >= 0.01:
									break
								event = dualshock.read_one()
								if event != None:
									gamepad_event_handler(event, is_remotecontrol=False, is_cameracapture=True)

			except OSError:
				print("DualShock4 disconnected")
				dualshock = None
				if remotecontrol:
					end_cam_proc()
					if robot != None:
						robot.stop()

def axis_normalize(v, curve=1.8, deadzone_inner=16, deadzone_outer=16):
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
	y = -y # stick Y axis is inverted
	left = y
	right = y
	left += x
	right -= x
	left = min(1.0, max(-1.0, left))
	right = min(1.0, max(-1.0, right))
	return left, right

def axis_vector(x, y, maglim = 2.0):
	y = -y # stick Y axis is inverted
	mag = math.sqrt((x*x) + (y*y))
	theta = math.atan2(x, y)
	ang = math.degrees(theta)
	if mag > maglim:
		mag = maglim
	return mag, ang

def flip_axis(x):
	return 255 - x

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
			cam = Camera.instance(width=960, height=720)
			print("\r\nCamera initialized!")
		except Exception as ex:
			sys.stderr.write("Exception initializing camera: " + str(ex))
			cam = None
			return

	try:
		fp = os.path.join(path, fn + '.jpg')
		with open(fp, 'wb') as f:
			f.write(bytes(imencode('.jpg', cam.value)[1]))
		teensyadc.set_camera_led()
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
		name += "_%03u%03u" % (int(round(axis_normalize(flip_axis(axis[LEFT_Y])) * 127.0)) + 127, int(round(axis_normalize(axis[RIGHT_X]) * 127.0)) + 127)

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
	camproc = subprocess.Popen(['python3', '/home/jetbot/jetbot/jetbot/apps/remotecamera.py', str(os.getpid())])
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

def start_nn_proc():
	global nnproc
	if nnproc != None:
		return
	print("starting neuralnetwork process...", end=" ")
	nnproc = subprocess.Popen(['python3', '/home/jetbot/jetbot/jetbot/apps/neuralnetwork.py', str(os.getpid())])
	print(" done!")

def end_nn_proc():
	global nnproc
	if nnproc == None:
		return
	try:
		nnproc.kill()
		nnproc = None
	except Exception as ex:
		sys.stderr.write("Exception while trying to kill neuralnetwork process: " + str(ex))
	finally:
		print("ended neuralnetwork process")

if __name__ == '__main__':
	run()
