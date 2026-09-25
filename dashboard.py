"""Dashboard interactivo de retrasos de vuelos (tarea).

Ejecutar en desarrollo:
    python dashboard.py        ->  http://127.0.0.1:8050

Ejecutar en produccion (lo hace la plataforma de despliegue):
    gunicorn dashboard:server  ->  usa el objeto WSGI `server` de este modulo
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

# --------------------------------------------------------------------- datos
# Los datos viajan CON el repositorio y se leen desde la carpeta del archivo.
# NO uses rutas absolutas: en el servidor las rutas son distintas.
DATA_FILE = Path(__file__).with_name("airline_data.csv")

df = pd.read_csv(
    DATA_FILE,
    encoding="ISO-8859-1",
    # Estos campos traen ceros a la izquierda: deben leerse como texto.
    dtype={
        "Div1Airport": str,
        "Div1TailNum": str,
        "Div2Airport": str,
        "Div2TailNum": str,
    },
)

app = Dash(__name__)

# -------------------------------------------------------------------- layout
# TODO 1: construye app.layout con:
#   * html.H1  -> el titulo del tablero
#   * dcc.Input(id="input-year", type="number", value=2010, ...)
#   * cinco dcc.Graph con estos id EXACTOS:
#       carrier-plot, weather-plot, nas-plot, security-plot, late-plot
#   * bloques html.Div con style={"display": "flex"} para ordenarlos
app.layout = html.Div(children=[
    # ... aqui va tu layout ...
])


# ------------------------------------------------------------------ calculos
def compute_info(datos, entered_year):
    """Devuelve 5 tablas (una por causa de retraso) para el ano pedido.

    Cada tabla debe tener las columnas: Month, Reporting_Airline y el
    promedio de la causa correspondiente.
    """
    # TODO 2: filtra por ano y agrupa por ["Month", "Reporting_Airline"]
    #         con .mean() sobre: CarrierDelay, WeatherDelay, NASDelay,
    #         SecurityDelay y LateAircraftDelay
    raise NotImplementedError


# ------------------------------------------------------------------ callback
# TODO 3: un UNICO callback que reciba el ano y devuelva las cinco figuras.
#         Recuerda: el numero de Output debe coincidir con el numero de
#         elementos que retorna la funcion, y en el mismo orden.
#
# @app.callback(
#     [Output("carrier-plot", "figure"), ..., Output("late-plot", "figure")],
#     Input("input-year", "value"),
# )
# def get_graph(entered_year):
#     # RF5: si entered_year es None o no es numerico, devuelve figuras vacias
#     #      con un mensaje en vez de lanzar una excepcion.
#     ...

# --------------------------------------------------------------- produccion
# RF9: objeto WSGI que consumira gunicorn. gunicorn IMPORTA este modulo y
# busca una variable llamada `server`; nunca ejecuta el bloque __main__.
server = app.server

if __name__ == "__main__":
    # debug=True recarga el servidor al guardar: comodo en desarrollo,
    # y NUNCA se usa en produccion.
    app.run(debug=True, port=8050)
