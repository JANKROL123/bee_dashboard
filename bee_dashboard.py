import os
from dash import ctx, Dash, html, dcc, Input, Output, State
from flask import send_file, request

ROOT = os.getcwd()

app = Dash(__name__)


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


app.layout = html.Div([

    dcc.Store(id="selected-folder", data=ROOT),
    dcc.Store(id="image-list"),
    dcc.Store(id="image-index", data=0),

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


from dash import ALL

@app.server.route("/image")
def serve_image():

    path = request.args.get("path")

    return send_file(path)

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

    trigger = ctx.triggered_id

    if trigger == "prev":
        return (index - 1) % len(images)

    if trigger == "next":
        return (index + 1) % len(images)

    return index

@app.callback(
    Output("file-list", "children"),
    Input("image-list", "data"),
    Input("image-index", "data")
)
def show_image(images, index):

    if not images:
        return html.H3("Brak zdjęć")

    image = images[index]

    return html.Div(
        [

            html.H3(f"{index+1}/{len(images)}"),

            html.H4(os.path.basename(image)),

            html.Img(
                src=f"/image?path={image}",
                style={
                    "maxWidth": "100%",
                    "maxHeight": "650px",
                    "objectFit": "contain"
                }
            )

        ]
    )

if __name__ == "__main__":
    app.run(debug=True)