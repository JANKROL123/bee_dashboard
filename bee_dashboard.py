import os

from dash import Dash, html, dcc, Input, Output

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
            id="file-list",
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
    Output("file-list", "children"),
    Input("selected-folder", "data")
)
def show_files(folder):

    rows = []

    rows.append(html.H3(folder))

    try:
        entries = sorted(os.listdir(folder))
    except:
        return "Brak dostępu"

    for entry in entries:

        full = os.path.join(folder, entry)

        if os.path.isdir(full):
            rows.append(html.Div("📁 " + entry))
        else:
            rows.append(html.Div("📄 " + entry))

    return rows


if __name__ == "__main__":
    app.run(debug=True)