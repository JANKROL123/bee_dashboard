#!/usr/bin/env python3
import os
import json
from utils.functions import *
from dash import Dash, dcc, html, Input, Output, State, callback

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
IMAGE_FOLDER = "images"

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

if __name__ == "__main__":
    app.run(debug=True)
