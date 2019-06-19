# output from
# gst-inspect-1.0 nvarguscamerasrc
#
#  name                : The name of the object
#                        flags: readable, writable
#                        String. Default: "nvarguscamerasrc0"
#  parent              : The parent of the object
#                        flags: readable, writable
#                        Object of type "GstObject"
#  typefind            : Run typefind before negotiating (deprecated, non-functional)
#                        flags: readable, writable, deprecated
#                        Boolean. Default: false
#  do-timestamp        : Apply current stream time to buffers
#                        flags: readable, writable
#                        Boolean. Default: true
#  sensor-id           : Set the id of camera sensor to use. Default 0.
#                        flags: readable, writable
#                        Integer. Range: 0 - 255 Default: 0
#  blocksize           : Size in bytes to read per buffer (-1 = default)
#                        flags: readable, writable
#                        Unsigned Integer. Range: 0 - 4294967295 Default: 4096
#  num-buffers         : Number of buffers to output before sending EOS (-1 = unlimited)
#                        flags: readable, writable
#                        Integer. Range: -1 - 2147483647 Default: -1
#  silent              : Produce verbose output ?
#                        flags: readable, writable
#                        Boolean. Default: true
#  timeout             : timeout to capture in seconds (Either specify timeout or num-buffers, not both)
#                        flags: readable, writable
#                        Unsigned Integer. Range: 0 - 2147483647 Default: 0
#  wbmode              : White balance affects the color temperature of the photo
#                        flags: readable, writable
#                        Enum "GstNvArgusCamWBMode" Default: 1, "auto"
#                           (0): off              - GST_NVCAM_WB_MODE_OFF
#                           (1): auto             - GST_NVCAM_WB_MODE_AUTO
#                           (2): incandescent     - GST_NVCAM_WB_MODE_INCANDESCENT
#                           (3): fluorescent      - GST_NVCAM_WB_MODE_FLUORESCENT
#                           (4): warm-fluorescent - GST_NVCAM_WB_MODE_WARM_FLUORESCENT
#                           (5): daylight         - GST_NVCAM_WB_MODE_DAYLIGHT
#                           (6): cloudy-daylight  - GST_NVCAM_WB_MODE_CLOUDY_DAYLIGHT
#                           (7): twilight         - GST_NVCAM_WB_MODE_TWILIGHT
#                           (8): shade            - GST_NVCAM_WB_MODE_SHADE
#                           (9): manual           - GST_NVCAM_WB_MODE_MANUAL
#  saturation          : Property to adjust saturation value
#                        flags: readable, writable
#                        Float. Range:               0 -               2 Default:               1
#  exposuretimerange   : Property to adjust exposure time range in nanoseconds
#                        Use string with values of Exposure Time Range (low, high)
#                        in that order, to set the property.
#                        eg: exposuretimerange="34000 358733000"
#                        flags: readable, writable
#                        String. Default: null
#  gainrange           : Property to adjust gain range
#                        Use string with values of Gain Time Range (low, high)
#                        in that order, to set the property.
#                        eg: gainrange="1 16"
#                        flags: readable, writable
#                        String. Default: null
#  ispdigitalgainrange : Property to adjust digital gain range
#                        Use string with values of ISP Digital Gain Range (low, high)
#                        in that order, to set the property.
#                        eg: ispdigitalgainrange="1 8"
#                        flags: readable, writable
#                        String. Default: null
#  tnr-strength        : property to adjust temporal noise reduction strength
#                        flags: readable, writable
#                        Float. Range:              -1 -               1 Default:              -1
#  tnr-mode            : property to select temporal noise reduction mode
#                        flags: readable, writable
#                        Enum "GstNvArgusCamTNRMode" Default: 1, "NoiseReduction_Fast"
#                           (0): NoiseReduction_Off - GST_NVCAM_NR_OFF
#                           (1): NoiseReduction_Fast - GST_NVCAM_NR_FAST
#                           (2): NoiseReduction_HighQuality - GST_NVCAM_NR_HIGHQUALITY
#  ee-mode             : property to select edge enhnacement mode
#                        flags: readable, writable
#                        Enum "GstNvArgusCamEEMode" Default: 1, "EdgeEnhancement_Fast"
#                           (0): EdgeEnhancement_Off - GST_NVCAM_EE_OFF
#                           (1): EdgeEnhancement_Fast - GST_NVCAM_EE_FAST
#                           (2): EdgeEnhancement_HighQuality - GST_NVCAM_EE_HIGHQUALITY
#  ee-strength         : property to adjust edge enhancement strength
#                        flags: readable, writable
#                        Float. Range:              -1 -               1 Default:              -1
#  aeantibanding       : property to set the auto exposure antibanding mode
#                        flags: readable, writable
#                        Enum "GstNvArgusCamAeAntiBandingMode" Default: 1, "AeAntibandingMode_Auto"
#                           (0): AeAntibandingMode_Off - GST_NVCAM_AEANTIBANDING_OFF
#                           (1): AeAntibandingMode_Auto - GST_NVCAM_AEANTIBANDING_AUTO
#                           (2): AeAntibandingMode_50HZ - GST_NVCAM_AEANTIBANDING_50HZ
#                           (3): AeAntibandingMode_60HZ - GST_NVCAM_AEANTIBANDING_60HZ
#  exposurecompensation: property to adjust exposure compensation
#                        flags: readable, writable
#                        Float. Range:              -2 -               2 Default:               0
#  aelock              : set or unset the auto exposure lock
#                        flags: readable, writable
#                        Boolean. Default: false
#  awblock             : set or unset the auto white balance lock
#                        flags: readable, writable
#                        Boolean. Default: false
#  maxperf             : set or unset the max performace
#                        flags: readable, writable
#                        Boolean. Default: false

class CamSrcOption:
	def __init__(self, name, friendlyname, hasval2, rangemin, rangemax, otheracceptable, defaultval):
		self.name            = name
		self.friendlyname    = friendlyname
		self.value           = None
		self.value2          = None
		self.hasval2         = hasval2
		self.rangemin        = rangemin
		self.rangemax        = rangemax
		self.otheracceptable = otheracceptable
		self.defaultval      = defaultval

class CamSrcOptGen:
	def __init__(self):
		self.OptionList = dict()
		self._add_option("blocksize"             , "Size in bytes to read per buffer"                            , False, 0, 4294967295, -1, int(-1))
		self._add_option("num-buffers"           , "Number of buffers to output before sending EOS"              , False, 0, 2147483647, -1, int(-1))
		self._add_option("silent"                , "Produce verbose output"                                      , False, False, True, None, True)
		self._add_option("timeout"               , "Timeout to capture in seconds"                               , False, 0, 2147483647, None, int(0))
		self._add_option("wbmode"                , "White balance affects the color temperature of the photo"    , False, 0, 9, None, int(1))
		self._add_option("saturation"            , "saturation"                                                  , False, 0, 2, None, float(1.0))
		self._add_option("exposuretimerange"     , "exposure time range in nanoseconds"                          , True , 0, None, None, int(0))
		self._add_option("gainrange"             , "gain range"                                                  , True , 0, None, None, int(0))
		self._add_option("ispdigitalgainrange"   , "digital gain range"                                          , True , 0, None, None, int(0))
		self._add_option("tnr-strength"          , "temporal noise reduction strength"                           , False, -1.0, 1.0, None, float(-1))
		self._add_option("tnr-mode"              , "temporal noise reduction mode"                               , False, 0, 2, None, int(1))
		self._add_option("ee-strength"           , "edge enhancement strength"                                   , False, -1.0, 1.0, None, float(-1))
		self._add_option("ee-mode"               , "edge enhancement mode"                                       , False, 0, 2, None, int(1))
		self._add_option("aeantibanding"         , "auto exposure antibanding mode"                              , False, 0, 3, None, int(1))
		self._add_option("exposurecompensation"  , "exposure compensation"                                       , False, -2.0, 2.0, None, float(0.0))
		self._add_option("aelock"                , "auto exposure lock"                                          , False, False, True, None, False)
		self._add_option("awblock"               , "auto white balance lock"                                     , False, False, True, None, False)
		self._add_option("maxperf"               , "max performace"                                              , False, False, True, None, False)

	def _add_option(self, name, friendlyname, hasval2, rangemin, rangemax, otheracceptable, defaultval):
		self.OptionList.update({name: CamSrcOption(name, friendlyname, hasval2, rangemin, rangemax, otheracceptable, defaultval)})

	def set_opt(self, name, value, value2=None):
		opt = None
		if name == "digigain" or name == "digigainrange":
			name = "ispdigitalgain"
		if name == "exposuretime" or name == "gain" or name == "ispdigitalgain":
			name = name + "range"
			if value2 == None:
				value2 = value
		if name not in self.OptionList:
			raise ValueError("Invalid attribute name, \"%s\" does not exist" % name)
		opt = self.OptionList[name]

		if value == None and value2 != None:
			raise ValueError("Cannot specify a second value without a primary value")
		if value2 != None and opt.hasval2 == False:
			raise ValueError("Cannot specify a second value for \"%s\" property" % name)
		if value2 == None and opt.hasval2 == True:
			raise ValueError("Two values must be specified for the \"%s\" property" % name)

		if opt.rangemin != None:
			if value != None:
				if (isinstance(value, int) or isinstance(value, float)) and (isinstance(opt.rangemin, int) or isinstance(opt.rangemin, float)):
					if value < opt.rangemin:
						if otheracceptable != None:
							if value != otheracceptable:
								raise ValueError("Value (%s) is less than minimum (%s) allowed" % (str(value),str(opt.rangemin)))
				elif isinstance(opt.rangemin, bool) and isinstance(value, bool) == False:
					raise ValueError("Value is not a boolean")
			if value2 != None:
				if (isinstance(value2, int) or isinstance(value2, float)) and (isinstance(opt.rangemin, int) or isinstance(opt.rangemin, float)):
					if value2 < opt.rangemin:
						if otheracceptable != None:
							if value2 != otheracceptable:
								raise ValueError("Second value (%s) is less than minimum (%s) allowed" % (str(value2),str(opt.rangemin)))
				elif isinstance(opt.rangemin, bool) and isinstance(value2, bool) == False:
					raise ValueError("Second value is not a boolean")
		if opt.rangemax != None:
			if value != None:
				if (isinstance(value, int) or isinstance(value, float)) and (isinstance(opt.rangemax, int) or isinstance(opt.rangemax, float)):
					if value > opt.rangemax:
						if otheracceptable != None:
							if value != otheracceptable:
								raise ValueError("Value (%s) is more than maximum (%s) allowed" % (str(value),str(opt.rangemax)))
				elif isinstance(opt.rangemin, bool) and isinstance(value, bool) == False:
					raise ValueError("Value is not a boolean")
			if value2 != None:
				if (isinstance(value2, int) or isinstance(value2, float)) and (isinstance(opt.rangemax, int) or isinstance(opt.rangemax, float)):
					if value2 > opt.rangemax:
						if otheracceptable != None:
							if value2 != otheracceptable:
								raise ValueError("Second value (%s) is more than maximum (%s) allowed" % (str(value2),str(opt.rangemax)))
				elif isinstance(opt.rangemin, bool) and isinstance(value2, bool) == False:
					raise ValueError("Second value is not a boolean")
		if value != None and value2 != None:
			if (isinstance(value, int) or isinstance(value, float)) == False:
				raise ValueError("First value (%s) must be a number" % str(value))
			if (isinstance(value2, int) or isinstance(value2, float)) == False:
				raise ValueError("Second value (%s) must be a number" % str(value2))
			if value > value2:
				raise ValueError("First value (%s) of the range must be less than or equal to the second value (%s) of the range" % (str(value),str(value2)))
		opt.value = value
		opt.value2 = value2
		self.OptionList[name] = opt

	def get_opt(self, name):
		if name not in self.OptionList:
			raise ValueError("Invalid attribute name, \"%s\" does not exist" % name)
		opt = self.OptionList[name]
		if opt.value == None:
			if opt.hasval2:
				return None, None
			return None
		if opt.value2 == None:
			return opt.value
		else:
			return opt.value, opt.value2

	def unset_opt(self, name):
		if name not in self.OptionList:
			raise ValueError("Invalid attribute name, \"%s\" does not exist" % name)
		opt = self.OptionList[name]
		opt.value = None
		opt.value2 = None

	def generate_str(self):
		str = ""
		if self.OptionList["timeout"].value != None and self.OptionList["num-buffers"].value != None:
			if self.OptionList["timeout"].value != self.OptionList["timeout"].defaultval and self.OptionList["num-buffers"].value != self.OptionList["num-buffers"].defaultval:
				raise ValueError("Cannot specify both \"timeout\" and \"num-buffers\", please only specify one or the other")
		for key, opt in self.OptionList.items():
			if key == "aelock" or key == "awblock":
				s = self._generate_optstr(key, opt)
				if len(s) > 0:
					s += " "
				str += s
		for key, opt in self.OptionList.items():
			if key != "aelock" and key != "awblock":
				s = self._generate_optstr(key, opt)
				if len(s) > 0:
					s += " "
				str += s
		return str.strip()

	def _generate_optstr(self, key, opt):
		str = ""
		if opt.value != None:
			str += key + "="
			if isinstance(opt.defaultval, bool):
				if opt.value == True:
					str += "true"
					return str
				elif opt.value == False:
					str += "false"
					return str
				else:
					raise ValueError("Value of \"%s\" (%s) must be a boolean" % (key, str(opt.value)))
			else:
				if opt.value2 != None and "range" in key:
					str += "\""
					if isinstance(opt.defaultval, int):
						str += "%d " % round(opt.value)
						str += "%d"  % round(opt.value2)
					elif isinstance(opt.defaultval, float):
						str += "%.8f " % opt.value
						str += "%.8f"  % opt.value2
					str += "\""
					return str
				else:
					if isinstance(opt.defaultval, int):
						str += "%d" % round(opt.value)
					elif isinstance(opt.defaultval, float):
						str += "%.8f" % opt.value
					return str
		return str

	NoiseReduction_Off           = 0
	GST_NVCAM_NR_OFF             = 0
	NoiseReduction_Fast          = 1
	GST_NVCAM_NR_FAST            = 1
	NoiseReduction_HighQuality   = 2
	GST_NVCAM_NR_HIGHQUALITY     = 2

	EdgeEnhancement_Off          = 0
	GST_NVCAM_EE_OFF             = 0
	EdgeEnhancement_Fast         = 1
	GST_NVCAM_EE_FAST            = 1
	EdgeEnhancement_HighQuality  = 2
	GST_NVCAM_EE_HIGHQUALITY     = 2

	AeAntibandingMode_Off        = 0
	GST_NVCAM_AEANTIBANDING_OFF  = 0
	AeAntibandingMode_Auto       = 1
	GST_NVCAM_AEANTIBANDING_AUTO = 1
	AeAntibandingMode_50HZ       = 2
	GST_NVCAM_AEANTIBANDING_50HZ = 2
	AeAntibandingMode_60HZ       = 3
	GST_NVCAM_AEANTIBANDING_60HZ = 3

	GST_NVCAM_WB_MODE_OFF              = 0
	GST_NVCAM_WB_MODE_AUTO             = 1
	GST_NVCAM_WB_MODE_INCANDESCENT     = 2
	GST_NVCAM_WB_MODE_FLUORESCENT      = 3
	GST_NVCAM_WB_MODE_WARM_FLUORESCENT = 4
	GST_NVCAM_WB_MODE_DAYLIGHT         = 5
	GST_NVCAM_WB_MODE_CLOUDY_DAYLIGHT  = 6
	GST_NVCAM_WB_MODE_TWILIGHT         = 7
	GST_NVCAM_WB_MODE_SHADE            = 8
	GST_NVCAM_WB_MODE_MANUAL           = 9