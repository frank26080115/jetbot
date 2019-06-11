from smbus2 import SMBus

bus = None

batt_divider = 71.159

I2C_SLAVE_ADDR = 0x60

def get_bus():
	global bus
	try:
		bus = SMBus(1)
	except Exception as err:
		sys.stderr.write('battery init exception\n' + str(err))
		bus = None
	except:
		sys.stderr.write('battery init unknown error\n' + sys.exc_info()[0])
		bus = None
	return bus

def read_buff(adr, len=16):
	global bus
	global I2C_SLAVE_ADDR
	if bus == None:
		get_bus()
	if bus == None:
		return None
	try:
		data = bus.read_i2c_block_data(I2C_SLAVE_ADDR, adr, len)
		return data
	except Exception as err:
		try:
			bus.close()
		finally:
			bus = None
		sys.stderr.write('battery read exception\n' + str(err))
		bus = None
		return None
	except:
		try:
			bus.close()
		finally:
			bus = None
		sys.stderr.write('battery read unknown error\n' + sys.exc_info()[0])
		bus = None
		return None

def read_buff_adc10():
	len = 7
	data = read_buff(0xD0, len * 2)
	if data == None:
		return None
	i = 0
	j = 0
	data16 = []
	while i < len:
		v = data[j + 1]
		v <<= 8
		v += data[j]
		data16.append(v)
		i += 1
		j += 2
	return data16

def read_buff_adc8():
	len = 7
	data = read_buff(0xE0, len)
	return data

def read_adc10(chan):
	len = 7
	data = read_buff(0xD0, len * 2)
	if data == None:
		return -1
	j = chan * 2
	v = data[j + 1]
	v <<= 8
	v += data[j]
	return v

def read_adc8(chan):
	len = 7
	data = read_buff(0xE0, len)
	if data == None:
		return -1
	return data[chan]

def read_batt_volts():
	global batt_divider
	raw = read_adc10(6)
	if raw < 0:
		return -1
	return raw / batt_divider

def set_batt_divider(x):
	global batt_divider
	batt_divider = x
