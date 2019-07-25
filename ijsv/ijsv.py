import numpy as np
import cv2
from clize import run

def convert_HSV_to_IJSV(img_arr):
	height, width, depth = img_arr.shape
	res = np.zeros((height, width, 4), np.uint8)
	hue = img_arr[:,:,0]
	sat = img_arr[:,:,1]
	val = img_arr[:,:,2]
	res[:,:,2] = sat
	res[:,:,3] = val
	y = 0
	while y < height:
		row = np.multiply(hue[y,:], 2)
		rad_arr = np.deg2rad(row)
		row_i = np.cos(rad_arr)
		row_j = np.sin(rad_arr)
		row_i = np.multiply(row_i, 127)
		row_j = np.multiply(row_j, 127)
		row_i = np.add(row_i, 127)
		row_j = np.add(row_j, 127)
		row_i = np.round(row_i)
		row_j = np.round(row_j)
		row_i = row_i.astype(np.uint8)
		row_j = row_j.astype(np.uint8)
		res[y,:,0] = row_i
		res[y,:,1] = row_j
		y += 1
	return res

def convert_IJSV_to_HSV(img_arr):
	height, width, depth = img_arr.shape
	res = np.zeros((height, width, 3), np.uint8)
	hue_i = img_arr[:,:,0]
	hue_j = img_arr[:,:,1]
	sat = img_arr[:,:,2]
	val = img_arr[:,:,3]
	res[:,:,1] = sat
	res[:,:,2] = val
	y = 0
	while y < height:
		row_i = hue_i[y,:]
		row_j = hue_j[y,:]
		row_i = row_i.astype(np.float64)
		row_j = row_j.astype(np.float64)
		row_i = np.subtract(row_i, 127)
		row_j = np.subtract(row_j, 127)
		hue_row = np.arctan2(row_j, row_i)
		hue_row = np.rad2deg(hue_row)
		hue_row = np.add(hue_row, 360)
		hue_row = np.mod(hue_row, 360)
		hue_row = np.divide(hue_row, 2)
		hue_row = np.round(hue_row)
		hue_row = hue_row.astype(np.uint8)
		res[y,:,0] = hue_row
		y += 1
	return res

def test(fpath):
	img = cv2.imread(fpath, -1)
	img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	img2 = convert_HSV_to_IJSV(img)
	cv2.imshow("intermediate", img2)
	img3 = convert_IJSV_to_HSV(img2)
	img4 = cv2.cvtColor(img3, cv2.COLOR_HSV2BGR)
	cv2.imshow("converted", img4)
	cv2.waitKey()

if __name__ == "__main__":
	run(test)
