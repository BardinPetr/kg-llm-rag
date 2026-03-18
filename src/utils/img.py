import cv2
import numpy as np


def scale_image(image, max_height, max_width=None, ratio=16 / 9):
    max_width = max_width or int(max_height * ratio)
    h, w = image.shape[:2]

    if w <= max_width and h <= max_height:
        return image

    scale = min(max_width / w, max_height / h)
    new_w, new_h = int(w * scale), int(h * scale)
    scaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    corners = np.array([
        image[0, 0], image[0, -1],
        image[-1, 0], image[-1, -1]
    ])
    bg_color = np.median(corners, axis=0).astype(np.uint8)

    canvas = np.full((max_height, max_width, image.shape[2]) if len(image.shape) == 3
                     else (max_height, max_width), bg_color, dtype=image.dtype)

    y_offset = (max_height - new_h) // 2
    x_offset = (max_width - new_w) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = scaled

    return canvas
