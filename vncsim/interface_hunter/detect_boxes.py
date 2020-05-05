import numpy as np
import cv2 as cv
from typing import NamedTuple, Sequence, Tuple
from . import toolbox


#---- CONFIGURATION

class DetectBoxesConfig(NamedTuple):
    nearest_scale: int


DefaultDetectBoxesConfig = DetectBoxesConfig(
    nearest_scale=200
)


#---- IMPLEMENTATION

class DetectBoxes:
    config = None

    def __init__(self, config: DetectBoxesConfig = DefaultDetectBoxesConfig):
        self.config = config

    @staticmethod
    def angle_cos(p0, p1, p2) -> float:
        d1, d2 = (p0 - p1).astype('float'), (p2 - p1).astype('float')
        return abs(np.dot(d1, d2) / np.sqrt(np.dot(d1, d1) * np.dot(d2, d2)))

    # noinspection PyShadowingBuiltins
    def samples(self, img) -> Sequence[Tuple[int, int, int, int]]:
        img = cv.GaussianBlur(img, (5, 5), 0)
        boxes_dict = {}
        boxes = []
        for gray in cv.split(img):
            for thrs in range(0, 255, 26):
                if thrs == 0:
                    bin = cv.Canny(gray, 0, 50, apertureSize=5)
                    bin = cv.dilate(bin, None)
                else:
                    _retval, bin = cv.threshold(
                        gray, thrs, 255, cv.THRESH_BINARY
                    )
                contours, _hierarchy = cv.findContours(
                    bin, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE
                )

                for cnt in contours:
                    cnt_len = cv.arcLength(cnt, True)
                    cnt = cv.approxPolyDP(cnt, 0.02 * cnt_len, True)
                    if len(cnt) == 4 and cv.contourArea(cnt) > 1000\
                            and cv.isContourConvex(cnt):
                        cnt = cnt.reshape(-1, 2)
                        max_cos = np.max([
                            DetectBoxes.angle_cos(
                                cnt[i],
                                cnt[(i + 1) % 4],
                                cnt[(i + 2) % 4]
                            ) for i in range(4)
                        ])
                        if max_cos < 0.1:
                            x, y, w, h = cv.boundingRect(cnt)
                            start_x, start_y, end_x, end_y = x, y, x + w, y + h
                            key = '%d_%d_%d_%d' % toolbox.scaled_coords(
                                self.config.nearest_scale,
                                start_x, start_y, end_x, end_y
                            )
                            boxes_dict[key] = (start_x, start_y, end_x, end_y)

        for key in boxes_dict:
            boxes.append(boxes_dict[key])

        return boxes
