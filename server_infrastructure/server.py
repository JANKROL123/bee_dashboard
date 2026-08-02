import os
import cv2
import time
import signal
import base64
import threading
import numpy as np
import pandas as pd
import multiprocessing
import setproctitle
import json
from flask import send_file, request
from multiprocessing import Condition
from dash import ALL, Dash, html, dcc, callback, Output, Input, State, callback_context

from PIL import Image
from io import BytesIO

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
IMAGE_FOLDER = "images"
ROOT = os.getcwd()

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

def build_tree(path, root=ROOT):
    children = []

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return html.Div("Brak dostępu")

    for entry in entries:

        full = os.path.join(path, entry)

        if os.path.isdir(full):

            relative = os.path.relpath(full, root)

            children.append(
                html.Details(
                    [
                        html.Summary(
                            html.Button(
                                "📁 " + entry,
                                id={
                                    "type": "folder",
                                    "path": relative
                                },
                                style={
                                    "border": "none",
                                    "background": "white",
                                    "cursor": "pointer",
                                    "fontSize": "15px"
                                }
                            )
                        ),

                        html.Div(
                            build_tree(full, root),
                            style={
                                "marginLeft": "20px",
                                "borderLeft": "1px solid lightgray",
                                "paddingLeft": "8px"
                            }
                        )
                    ],
                    open=False
                )
            )

    return children

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

        dcc.Store(id="selected-folder", data=ROOT),
        dcc.Store(id="image-list"),
        dcc.Store(id="image-index", data=0),
        dcc.Store(id="coverage-mode", data=False),

        html.H2("Przeglądarka plików"),

        html.Div([

            html.Div(
                build_tree(ROOT),
                style={
                    "width": "35%",
                    "overflow": "auto",
                    "height": "700px",
                    "borderRight": "1px solid gray",
                    "padding": "10px"
                }
            ),

            html.Div(
            [

                html.Div(id="file-list"),

                html.Img(
                    id="current-image",
                    n_clicks=0,
                    style={
                        "maxWidth": "100%",
                        "maxHeight": "650px",
                        "objectFit": "contain",
                        "cursor": "pointer"
                    }
                ),


                html.Br(),

                html.Button("◀", id="prev"),

                html.Button(
                    "▶",
                    id="next",
                    style={"marginLeft": "10px"}
                )

            ],
            style={
                "width": "65%",
                "padding": "20px"
            }
            )

        ],
        style={
            "display": "flex"
        })

    ])


    @app.server.route("/image")
    def serve_image():

        path = request.args.get("path")
        coverage = request.args.get("coverage") == "1"

        if not coverage:
            return send_file(path)

        json_path = os.path.splitext(path)[0] + ".json"

        with open(json_path, "r") as f:
            json_bee_data = json.load(f)

        image = put_bee_frames_on_file(path, json_bee_data)


        _, buffer = cv2.imencode(".png", image)

        return send_file(
            BytesIO(buffer.tobytes()),
            mimetype="image/png"
        )

    @app.callback(
        Output("selected-folder", "data"),
        Input({"type": "folder", "path": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def choose_folder(clicks):

        from dash import callback_context

        ctx = callback_context

        if not ctx.triggered:
            return ROOT

        path = ctx.triggered_id["path"]

        return os.path.join(ROOT, path)



    @app.callback(
        Output("image-list", "data"),
        Output("image-index", "data", allow_duplicate=True),
        Input("selected-folder", "data"),
        prevent_initial_call=True
    )
    def load_images(folder):

        extensions = (".jpg", ".jpeg", ".png")

        images = []

        for f in sorted(os.listdir(folder)):
            if f.lower().endswith(extensions):
                images.append(os.path.join(folder, f))

        return images, 0



    @app.callback(
        Output("image-index", "data", allow_duplicate=True),
        Input("prev", "n_clicks"),
        Input("next", "n_clicks"),
        State("image-index", "data"),
        State("image-list", "data"),
        prevent_initial_call=True
    )
    def change_image(prev, nxt, index, images):

        if not images:
            return 0

        trigger = callback_context.triggered_id

        if trigger == "prev":
            return (index - 1) % len(images)

        if trigger == "next":
            return (index + 1) % len(images)

        return index

    @app.callback(
        Output("file-list", "children"),
        Input("image-list", "data"),
        Input("image-index", "data"),
        Input("coverage-mode", "data")
    )
    def show_image(images, index, coverage):

        if not images:
            return html.H3("Brak zdjęć")

        image = images[index]
        style = {
            "maxWidth": "100%",
            "maxHeight": "650px",
            "objectFit": "contain",
            "cursor": "pointer"
        }

        return html.Div(
            [

                html.H3(f"{index+1}/{len(images)}"),

                html.H4(os.path.basename(image)),

                html.Img(
                    id="current-image",
                    n_clicks=0,
                    src=f"/image?path={image}&coverage={int(coverage)}&t={time.time_ns()}",
                    style=style
                )

            ]
        )

    @app.callback(
        Output("coverage-mode", "data"),
        Input("current-image", "n_clicks"),
        State("coverage-mode", "data"),
        prevent_initial_call=True
    )
    def toggle_coverage(n_clicks, coverage):

        return not coverage
    
    with server_is_started:
        server_is_started.notify()

    # debug cannot be True right now with nuitka: https://github.com/Nuitka/Nuitka/issues/2953
    app.run(debug=False, host=host, port=port)
