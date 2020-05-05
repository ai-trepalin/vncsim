import cv2 as cv
import numpy as np
from . import detect_text, detect_boxes
from typing import NamedTuple, Sequence, Tuple


#---- CONFIGURATION

class ButtonFeatureConfig(NamedTuple):
    text_detector_config: detect_text.DetectTextConfig
    box_detector_config: detect_boxes.DetectBoxesConfig
    min_width: int
    min_height: int
    max_width: int
    max_height: int


DefaultButtonFeatureConfig = ButtonFeatureConfig(
    text_detector_config=detect_text.DefaultDetectTextConfig,
    box_detector_config=detect_boxes.DefaultDetectBoxesConfig,
    min_width=80,
    min_height=30,
    max_width=450,
    max_height=100
)


#---- IMPLEMENTATION

class ButtonFeature:
    config: ButtonFeatureConfig = None
    image: np.array = None
    button_text_detector: detect_text.DetectText = None
    button_boxes_detector: detect_boxes.DetectBoxes = None

    def __init__(self,
                 image_data: np.array,
                 button_text_detector: detect_text.DetectText,
                 button_boxes_detector: detect_boxes.DetectBoxes,
                 config: ButtonFeatureConfig = DefaultButtonFeatureConfig):
        self.image = image_data
        self.config = config
        self.button_text_detector = button_text_detector
        self.button_boxes_detector = button_boxes_detector

    def mark_buttons(self) -> np.array:
        boxes = self.button_boxes_detector.samples(self.image)
        image_copy = self.image.copy()
        for (x1, y1, x2, y2) in boxes:
            cv.rectangle(image_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if self.config.min_width < x2 - x1 < self.config.max_width \
                    and self.config.min_height < y2 - y1 < self.config.max_height:
                roi = self.image[y1:y2, x1:x2]
                text_samples = self.button_text_detector.samples(roi)
                for (text, (tx1, ty1, tx2, ty2)) in text_samples:
                    cv.rectangle(image_copy, (x1 + tx1, y1 + ty1), (x1 + tx2, y1 + ty2), (0, 0, 255), 2)
        return image_copy

    def buttons(self) -> Sequence[Tuple[str, Tuple[int, int, int, int]]]:
        boxes = self.button_boxes_detector.samples(self.image)
        print(f"Buttons: found {len(boxes)} boxes")
        found_buttons = []

        index = 1
        for (x1, y1, x2, y2) in boxes:
            if self.config.min_width < x2 - x1 < self.config.max_width \
                    and self.config.min_height < y2 - y1 < self.config.max_height:
                roi = self.image[y1:y2, x1:x2]
                text_samples = self.button_text_detector.samples(roi)
                if len(text_samples) is 0:
                    continue
                print(f"{index} - found {len(text_samples)} text_boxes")
                button_text = ''
                for sample in text_samples:
                    print(f"\t- {sample[0]}")
                    button_text += sample[0]
                index += 1
                found_buttons.append((button_text, (x1, y1,x2, y2)))

        return found_buttons
