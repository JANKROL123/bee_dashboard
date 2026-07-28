
import os
import cv2
import signal
import base64
import threading
import numpy as np
import pandas as pd
import multiprocessing
import setproctitle
import json
from multiprocessing import Condition
from dash import Dash, html, dcc, callback, Output, Input, State

from PIL import Image
from io import BytesIO

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
IMAGE_FOLDER = "images"

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


def join_process_and_terminate(process: multiprocessing.process.BaseProcess):
    """
    Whenever the given process exits, send SIGTERM to self.
    This function is synchronous; for async usage see the other two.
    """
    process.join()
    # sys.exit() raises, killing only the current thread
    # os._exit() is private, and also doesn't allow the thread to gracefully exit
    os.kill(os.getpid(), signal.SIGTERM)


def terminate_when_process_dies(process: multiprocessing.process.BaseProcess):
    """
    Whenever the given process exits, send SIGTERM to self.
    This function is asynchronous.
    """
    threading.Thread(target=join_process_and_terminate, args=(process,)).start()


def terminate_when_parent_process_dies():
    """
    Whenever the parent process exits, send SIGTERM to self.
    This function is asynchronous.
    """
    terminate_when_process_dies(multiprocessing.parent_process())

def start_dash(host: str, port: int, server_is_started: Condition):
    # Set the process title.
    setproctitle.setproctitle('dnb-dash')
    # When the parent dies, follow along.
    terminate_when_parent_process_dies()

    # The following is the minimal sample code from dash itself:
    # https://dash.plotly.com/minimal-app

    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

    app = Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        dcc.Upload(
            id="upload-image",
            children=html.Div([
                "Drag and Drop or ",
                html.A("Select files")
            ]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px"
            },
            multiple=True
        ),
        html.Div(id="output-image-upload"),
    ])

    @callback(Output("output-image-upload", "children"),
              Input("upload-image", "contents"),
              State("upload-image", "filename"))
    def update_output(list_of_contents, list_of_names):
        if list_of_contents is not None:
            file_path = list_of_names[0]
            pred_json_path = f"images/{file_path[:-4]}.json"
            if os.path.exists(pred_json_path):
                with open(pred_json_path, "r") as file:
                    json_bee_data = json.load(file)
                blended_image = put_bee_frames_on_file(f"{IMAGE_FOLDER}/{file_path}", json_bee_data)
                
                image_base64 = numpy_to_base64(blended_image)
                
                return html.Div([
                    html.H5(f"Processed: {file_path}"),
                    html.Img(src=image_base64, style={"maxWidth": "100%", "height": "auto"}),
                    html.Hr()
                ])

            else:
                print("Prediction file does not exist")
                return None

    with server_is_started:
        server_is_started.notify()

    # debug cannot be True right now with nuitka: https://github.com/Nuitka/Nuitka/issues/2953
    app.run(debug=False, host=host, port=port)
