#!/usr/bin/env python3
import os
import argparse
import json
from utils.open_file_with_bee_frames import open_file_with_bee_frames

IMAGE_FOLDER = "images"

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", required=True)
args = parser.parse_args()
filename = args.filename
file_path = csv_path = os.path.join("images", filename)

if __name__ == "__main__":
    if os.path.exists(file_path) and file_path.endswith(".png"):
        pred_json_path = f"{file_path[:-4]}.json"
        if os.path.exists(pred_json_path):
            with open(pred_json_path, "r") as file:
                json_bee_data = json.load(file)
            open_file_with_bee_frames(file_path, json_bee_data)
        else:
            print("Prediction file does not exist")
    else:
        print("Given file does not exist or given format not supported")
