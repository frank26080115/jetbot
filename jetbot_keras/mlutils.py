import os, sys
import itertools
import math
import numpy as np
import cv2
import PIL, PIL.Image

def cv2_to_pil(img):
	img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	return PIL.Image.fromarray(img)

def norm_img(img):
    return (img - img.mean() / np.std(img))/255.0

def rgb2gray(rgb):
    '''
    take a numpy rgb image return a new single channel image converted to greyscale
    '''
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

'''
BINNING
functions to help converte between floating point numbers and categories.
'''

def clamp(n, min, max):
    if n < min:
        return min
    if n > max:
        return max
    return n

def linear_bin(a, N=15, offset=1, R=2.0):
    '''
    create a bin of length N
    map val A to range R
    offset one hot bin by offset, commonly R/2
    '''
    a = a + offset
    b = round(a / (R/(N-offset)))
    arr = np.zeros(N)
    b = clamp(b, 0, N - 1)
    arr[int(b)] = 1
    return arr


def linear_unbin(arr, N=15, offset=-1, R=2.0):
    '''
    preform inverse linear_bin, taking
    one hot encoded arr, and get max value
    rescale given R range and offset
    '''
    b = np.argmax(arr)
    a = b *(R/(N + offset)) + offset
    return a


def map_range(x, X_min, X_max, Y_min, Y_max):
    ''' 
    Linear mapping between two ranges of values 
    '''
    X_range = X_max - X_min
    Y_range = Y_max - Y_min
    XY_ratio = X_range/Y_range

    y = ((x-X_min) / XY_ratio + Y_min) // 1

    return int(y)

'''
ANGLES
'''
def norm_deg(theta):
    while theta > 360:
        theta -= 360
    while theta < 0:
        theta += 360
    return theta

DEG_TO_RAD = math.pi / 180.0

def deg2rad(theta):
    return theta * DEG_TO_RAD

'''
VECTORS
'''
def dist(x1, y1, x2, y2):
    return math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))

