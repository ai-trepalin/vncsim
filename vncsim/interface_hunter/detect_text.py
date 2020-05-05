import numpy as np
import cv2
import pytesseract
from imutils.object_detection import non_max_suppression
from typing import NamedTuple, Sequence, Tuple


#---- CONFIGURATION

class DetectTextConfig(NamedTuple):
	east_detector_pb_path: str
	min_confidence: float
	conv_width: int
	conv_height: int
	margin: int
	scale: float
	tesseract_config: str


DefaultDetectTextConfig = DetectTextConfig(
	east_detector_pb_path='./proto/frozen_east_text_detection.pb',
	min_confidence=0.5,
	conv_width=256,
	conv_height=64,
	margin=10,
	scale=2.0,
	tesseract_config='-l eng --oem 1 --psm 7'
)


#---- IMPLEMENTATION

class DetectText:
	config: DetectTextConfig = None
	net: cv2.dnn = None

	def __init__(self, config: DetectTextConfig = DefaultDetectTextConfig):
		self.config = config

		# load the pre-trained EAST text detector
		print((
			"[INFO] loading EAST text detector...\n"
			f"Model protobuf: {self.config.east_detector_pb_path}\n"
			f"Tesseract config: {self.config.tesseract_config}\n"
		))
		self.net = cv2.dnn.readNet(config.east_detector_pb_path)

	def samples(self, image) -> Sequence[Tuple[str, Tuple[int, int, int, int]]]:
		result_boxes = []
		rects = []
		confidences = []
		orig = image.copy()

		(orig_h, orig_w) = orig.shape[:2]
		(h, w) = image.shape[:2]

		rw = w / float(self.config.conv_width)
		rh = h / float(self.config.conv_height)
		image = cv2.resize(
			image,
			(self.config.conv_width, self.config.conv_height)
		)
		(h, w) = image.shape[:2]

		layer_names = [
			"feature_fusion/Conv_7/Sigmoid",
			"feature_fusion/concat_3"
		]

		# construct a blob from the image and then perform a forward pass of
		# the model to obtain the two output layer sets
		blob = cv2.dnn.blobFromImage(
			image, self.config.scale, (w, h),
			(123.68, 116.78, 103.94),
			swapRB=True, crop=False
		)
		self.net.setInput(blob)
		(scores, geometry) = self.net.forward(layer_names)

		(num_rows, num_cols) = scores.shape[2:4]

		# loop over the number of rows
		for y in range(0, num_rows):
			# extract the scores (probabilities), followed by the geometrical
			# data used to derive potential bounding box coordinates that
			# surround text
			scores_data = scores[0, 0, y]
			xdata_0 = geometry[0, 0, y]
			xdata_1 = geometry[0, 1, y]
			xdata_2 = geometry[0, 2, y]
			xdata_3 = geometry[0, 3, y]
			angles_data = geometry[0, 4, y]

			# loop over the number of columns
			for x in range(0, num_cols):
				# if our score does not have sufficient probability, ignore it
				if scores_data[x] < self.config.min_confidence:
					continue

				# compute the offset factor as our resulting feature maps will
				# be 4x smaller than the input image
				(offset_x, offset_y) = (x * 4.0, y * 4.0)

				# extract the rotation angle for the prediction and then
				# compute the sin and cosine
				angle = angles_data[x]
				cos = np.cos(angle)
				sin = np.sin(angle)

				# use the geometry volume to derive the width and height
				# of the bounding box
				h = xdata_0[x] + xdata_2[x]
				w = xdata_1[x] + xdata_3[x]

				# compute both the starting and ending (x, y)-coordinates
				# for the text prediction bounding box
				end_x = int(offset_x + (cos * xdata_1[x]) + (sin * xdata_2[x]))
				end_y = int(offset_y - (sin * xdata_1[x]) + (cos * xdata_2[x]))
				start_x = int(end_x - w)
				start_y = int(end_y - h)

				# add the bounding box coordinates and probability score to
				# our respective lists
				rects.append((start_x, start_y, end_x, end_y))
				confidences.append(scores_data[x])

		# apply non-maxima suppression to suppress weak,
		# overlapping bounding boxes
		boxes = non_max_suppression(np.array(rects), probs=confidences)

		# Sort frames from left to right.
		boxes = sorted(boxes, key=lambda tup: tup[0])

		# loop over the bounding boxes
		for (start_x, start_y, end_x, end_y) in boxes:
			# scale the bounding box coordinates based on the respective ratios
			start_x = max(0, int(start_x * rw) - self.config.margin)
			start_y = max(0, int(start_y * rh) - self.config.margin)
			end_x = min(orig_w, int(end_x * rw) + self.config.margin)
			end_y = min(orig_h, int(end_y * rh) + self.config.margin)

			# extract the actual padded ROI
			roi = orig[start_y:end_y, start_x:end_x]

			# use english & ltsm only
			# psm=7, Treat the image as a single text line.
			text = pytesseract.image_to_string(
				roi, config=self.config.tesseract_config)

			result_boxes.append((text, (start_x, start_y, end_x, end_y)))

		return result_boxes
