import cv2
import numpy as np
from visionpilot import VisionProcessor

from clize import run

def analyze_file(fpath, verbose=False):
	img = cv2.imread(fpath, -1)
	if verbose:
		print("Image file \"%s\" shape is %ux%u" % (fpath, img.shape[1], img.shape[0]))
	return analyze_image(img, verbose=verbose)

def analyze_image(img, verbose=False):
	vision = VisionProcessor(img)
	vision.convertToHsv()

	hsv = vision.img
	hue = hsv[:,:,0]
	sat = hsv[:,:,1]
	val = hsv[:,:,2]

	hue_max = np.max(hue)
	hue_min = np.min(hue)
	hue_avg = np.mean(hue)
	hue_std = np.std(hue)

	sat_max = np.max(sat)
	sat_min = np.min(sat)
	sat_avg = np.mean(sat)
	sat_std = np.std(sat)

	val_max = np.max(val)
	val_min = np.min(val)
	val_avg = np.mean(val)
	val_std = np.std(val)

	if verbose:
		print("HUE: min=%.1f  max=%.1f  avg=%.1f  std=%.1f" % (hue_min, hue_max, hue_avg, hue_std))
		print("SAT: min=%.1f  max=%.1f  avg=%.1f  std=%.1f" % (sat_min, sat_max, sat_avg, sat_std))
		print("VAL: min=%.1f  max=%.1f  avg=%.1f  std=%.1f" % (val_min, val_max, val_avg, val_std))
		pass

	s_start = sat_avg + (sat_std / 2.0)
	largest_areas = []
	largest_contours = []
	i = 0
	s = 0
	area_sum = 0
	while s <= 254.0:
		s = int(round(s_start)) + i
		hsv_min = np.array([0, s, 0])
		hsv_max = np.array([180, 255, 255])
		masked = cv2.inRange(hsv.copy(), hsv_min, hsv_max)
		contours, hierarchy = cv2.findContours(masked, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
		try:
			largest_contour = sorted_contours[0]
			area = cv2.contourArea(largest_contour)
		except:
			largest_contour = None
			area = 0
		largest_areas.append(area)
		largest_contours.append(largest_contour)
		if verbose:
			#print("contour[%u] area = %.1f" % (s, area))
			pass
		i += 1

	largest_areas = np.array(largest_areas)
	c_max = np.max(largest_areas)
	c_avg = np.mean(largest_areas)
	c_std = np.std(largest_areas)

	if verbose:
		print("contour max=%.1f  avg=%.1f  std=%.1f" % (c_max, c_avg, c_std))

	nearest = (np.abs(largest_areas - c_avg)).argmin()
	s = int(round(s_start)) + nearest

	if verbose:
		print("nearest index is = %u , best saturation limit is = %u" % (nearest, s))

	h, w, c = hsv.shape
	mask = np.zeros((h, w, 1), np.uint8)
	cv2.drawContours(mask, [largest_contours[nearest]], -1, 255, -1) # creates a mask of the largest contour
	mean_img = cv2.mean(hsv.copy(), mask.copy()) # average the pixels of the image where the mask is covering
	obj_hue = int(round(mean_img[0]))
	obj_sat = int(round(mean_img[1]))
	obj_val = int(round(mean_img[2]))

	hsv_val_array = hsv.copy()[:,:,2]
	val_mask = hsv_val_array[np.where(mask[:,:,0] == 255)]
	obj_val_min = np.min(val_mask)
	obj_val_min = int(round(obj_val_min))

	if verbose:
		print("object hue=%u  sat=%u  val=%u  val_min=%u" % (obj_hue, obj_sat, obj_val, obj_val_min))
		pass

	min_val_range = 16
	if obj_val_min <= val_avg:
		val_range = val_avg - obj_val_min
		if val_range < min_val_range:
			val_range = min_val_range
		best_val = val_avg - (val_range * 1.5)
		if best_val < 0:
			best_val = 0
	else:
		val_range = obj_val_min - val_avg
		best_val = val_avg + (val_range / 3.0)

	best_val = int(round(best_val))

	if verbose:
		print("suggested val=%u" % best_val)

	return obj_hue, s, best_val

if __name__ == "__main__":
	run(analyze_file)
