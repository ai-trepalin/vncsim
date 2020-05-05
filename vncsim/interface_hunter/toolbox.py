from PIL import Image
from typing import Tuple
import numpy as np


# Converts PIL Image to numpy array.
def pil_to_cv2(buffer: Image) -> np.array:
    img = np.array(buffer)
    img = img[:, :, ::-1].copy()
    return img


# Scale coordinates by scale factor.
def scaled_coords(scale_factor: int, x1: int, y1: int, x2: int, y2: int) ->\
        Tuple[int, int, int, int]:
    return(
        round(x1 / scale_factor),
        round(y1 / scale_factor),
        round(x2 / scale_factor),
        round(y2 / scale_factor)
    )
