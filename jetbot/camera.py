import traitlets
from traitlets.config.configurable import SingletonConfigurable
import atexit
from cv2 import VideoCapture, CAP_GSTREAMER
import threading
import numpy as np
from jetbot.utils.undistort import undistort_image

class Camera(SingletonConfigurable):
    
    value = traitlets.Any()
    
    # config
    width = traitlets.Integer(default_value=224).tag(config=True)
    height = traitlets.Integer(default_value=224).tag(config=True)
    fps = traitlets.Integer(default_value=21).tag(config=True)
    capture_width = traitlets.Integer(default_value=3280).tag(config=True)
    capture_height = traitlets.Integer(default_value=2464).tag(config=True)
    flipmode = traitlets.Integer(default_value=2).tag(config=True) # Frank: my robot has an upside-down camera to make the cable neater

    def __init__(self, *args, **kwargs):
        self.value = np.empty((self.height, self.width, 3), dtype=np.uint8)
        super(Camera, self).__init__(*args, **kwargs)

        self.undistort = False
        self.undistort_dim = None
        self.undistort_k = None
        self.undistort_d = None
        self.undistort_balance = 0
        self.undistort_dim2 = None
        self.undistort_dim3 = None

        try:
            self.cap = VideoCapture(self._gst_str(), CAP_GSTREAMER)

            re, image = self.cap.read()

            if not re:
                raise RuntimeError('Could not read image from camera.')

            self.value = image
            self.start()
        except:
            self.stop()
            raise RuntimeError(
                'Could not initialize camera.  Please see error trace.')

        atexit.register(self.stop)

    def _capture_frames(self):
        while True:
            re, image = self.cap.read()
            if re:
                self.value = self.post_process_image(image)
            else:
                break
                
    def _gst_str(self):
        return 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=%d ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
                self.capture_width, self.capture_height, self.fps, self.flipmode, self.width, self.height)
    
    def start(self):
        if not self.cap.isOpened():
            self.cap.open(self._gst_str(), CAP_GSTREAMER)
        if not hasattr(self, 'thread') or not self.thread.isAlive():
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.start()

    def stop(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'thread'):
            self.thread.join()
            
    def restart(self):
        self.stop()
        self.start()

    def enable_undistort(self, balance=0.0, dim2=None, dim3=None):
        self.undistort_balance = balance
        self.undistort_dim2 = dim2
        self.undistort_dim3 = dim3
        if self.width == self.height:
            self.undistort_dim = (self.width, self.height)
            self.undistort_k = np.array([[346.7104965474094, 0.0, 379.81851823551904], [0.0, 462.1778768584941, 355.5060529230117], [0.0, 0.0, 1.0]])
            self.undistort_d = np.array([[-0.04498282438799088], [0.07821348164549044], [-0.15085637279264702], [0.092845374923209]])
            self.undistort = True
        else:
            asp_self = self.height / self.width
            asp_shouldbe = 3 / 4
            if round(asp_self * 100) == round(asp_shouldbe * 100):
                self.undistort_dim = (self.width, self.height)
                self.undistort_k = np.array([[460.70753878093376, 0.0, 505.24222903420747], [0.0, 461.22079408566924, 357.7314598652513], [0.0, 0.0, 1.0]])
                self.undistort_d = np.array([[-0.016987487065241266], [-0.014653716767538133], [-0.02029760249000433], [0.016954509783374646]])
                self.undistort = True
            else:
                # allow the caller to load up the required parameters manually
                if self.undistort_dim != None and self.undistort_k != None and self.undistort_d != None:
                    self.undistort = True
                else:
                    self.undistort = False

    def disable_undistort(self):
        self.undistort = False

    def post_process_image(self, img):
        if self.undistort:
            img = undistort_image(img, self.undistort_dim, self.undistort_k, self.undistort_d, balance=self.undistort_balance, dim2=self.undistort_dim2, dim3=self.undistort_dim3)
        return img