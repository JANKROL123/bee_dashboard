import os
import cv2
import base64
import numpy as np
from PIL import Image
from io import BytesIO


def put_bee_frames_on_file(image_path, json_bee_data):

    # Reading image and its size
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    frame_area = width * height
 
    # Creating mask
    mask = np.zeros((height, width), dtype=np.uint8)
    
    for pred in json_bee_data["predictions"]:
        points = np.array([[p["x"], p["y"]] for p in pred["points"]], dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)

    # Compute coverage
    bee_pixels = np.count_nonzero(mask)
    coverage = (bee_pixels / frame_area) * 100

    # Visual overlay
    overlay = image.copy()
    overlay[mask == 255] = (0, 255, 0)
    blended = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    cv2.putText(blended, f"Coverage: {coverage:.2f}%",
        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (55, 205, 55), 3)

    return blended


def numpy_to_base64(image_array):
    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    
    # Convert to PIL Image
    pil_image = Image.fromarray(image_array)
    
    # Save to BytesIO
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG", quality=95)
    
    # Encode to base64
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/jpeg;base64,{img_str}"
