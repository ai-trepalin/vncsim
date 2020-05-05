import numpy as np
from . import detect_text, detect_boxes, button_feature
from typing import NamedTuple, Sequence, Tuple


#---- CONFIGURATION

class DialogFeatureConfig(NamedTuple):
    text_detector_config: detect_text.DetectTextConfig
    box_detector_config: detect_boxes.DetectBoxesConfig
    title_height: int
    min_width: int
    min_height: int
    max_width: int
    max_height: int


DefaultDialogFeatureConfig = DialogFeatureConfig(
    text_detector_config=detect_text.DefaultDetectTextConfig,
    box_detector_config=detect_boxes.DefaultDetectBoxesConfig,
    title_height=50,
    min_width=200,
    min_height=200,
    max_width=1000,
    max_height=700
)


#---- IMPLEMENTATION

class DialogFeature:
    config: DialogFeatureConfig = None
    image: np.array = None
    dialog_text_detector: detect_text.DetectText = None
    dialog_boxes_detector: detect_boxes.DetectBoxes = None
    button_text_detector: detect_text.DetectText = None
    button_boxes_detector: detect_boxes.DetectBoxes = None

    def __init__(self,
                 image_data: np.array,
                 dialog_text_detector: detect_text.DetectText,
                 dialog_boxes_detector: detect_boxes.DetectBoxes,
                 button_text_detector: detect_text.DetectText,
                 button_boxes_detector: detect_boxes.DetectBoxes,
                 config: DialogFeatureConfig = DefaultDialogFeatureConfig):
        self.image = image_data
        self.config = config
        self.dialog_text_detector = dialog_text_detector
        self.dialog_boxes_detector = dialog_boxes_detector
        self.button_text_detector = button_text_detector
        self.button_boxes_detector = button_boxes_detector

    def dialogs(self) -> Sequence[Tuple[str, Tuple[int, int, int, int], Sequence[Tuple[str, Tuple[int, int, int, int]]]]]:
        boxes = self.dialog_boxes_detector.samples(self.image)
        print(f"Dialog: found {len(boxes)} boxes")
        found_dialogs = []

        index = 1
        for (x1, y1, x2, y2) in boxes:
            if self.config.min_width < x2 - x1 < self.config.max_width \
                    and self.config.min_height < y2 - y1 < self.config.max_height:

                print(f"Dialog {index}")
                index+=1

                # Detect buttons.
                roi = self.image[y1:y2, x1:x2]
                button_detector = button_feature.ButtonFeature(
                    roi,
                    self.button_text_detector,
                    self.button_boxes_detector
                )
                buttons = button_detector.buttons()

                # Detect title and append to dialogs.
                if len(buttons) > 0:
                    dialog_title = ''
                    dialog_title_roi = self.image[y1:y1+self.config.title_height, x1:x2]
                    dialog_title_samples = self.dialog_text_detector.samples(dialog_title_roi)
                    for (sample, (_, _, _, _)) in dialog_title_samples:
                        dialog_title += ' ' + sample
                    print(f"Dialog title: {dialog_title}")

                    # Append to found dialogs.
                    found_dialogs.append((dialog_title, (x1, y1, x2, y2), buttons))

        return found_dialogs
