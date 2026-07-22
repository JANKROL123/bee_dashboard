import os
import cv2
import numpy as np

def open_file_with_bee_frames(image_path, json_bee_data):

    os.makedirs("output", exist_ok=True)

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
    num_preds = len(json_bee_data.get("predictions", []))

    # Visual overlay
    overlay = image.copy()
    overlay[mask == 255] = (0, 255, 0)
    blended = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    cv2.putText(blended, f"Coverage: {coverage:.2f}%",
        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (55, 205, 55), 3)

    output_file = image_path.replace("images", "output")
    cv2.imwrite(output_file, blended)
    print(f"Saved in {output_file}")
