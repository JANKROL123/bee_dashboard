from roboflow import Roboflow
from dotenv import load_dotenv
import os
import json

load_dotenv()

API_KEY = os.getenv("API_KEY")

# Roboflow model initialization
rf = Roboflow(api_key=API_KEY)
project = rf.workspace().project("beedetection-jr2a8")
model = project.version("1").model

# Image folder
input_folder = "images/public_source/pub_subset_7"


# Results CSV
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith((".jpg", ".png", "jpeg"))]

for i, filename in enumerate(sorted(image_files), start=1):
    image_path = os.path.join(input_folder, filename)
    print(f"Predykcja: {filename}")

    # Prediction
    result = model.predict(image_path).json()
    json_result_file = filename.split(".")[0] + ".json"
    with open(f"images/public_source/pub_subset_7/{json_result_file}", "w") as f:
        json.dump(result, f)

print(f"Saving to JSON files completed")
