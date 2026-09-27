"""Flight Delay Time Statistics Dashboard.

Portado a local del laboratorio 4.8 de IBM Developer Skills Network DV0101EN
("Dash Components"). Se mantiene el codigo del laboratorio y solo se ajusta lo
que era especifico del Cloud IDE (Theia):

  * Los datos se leen de un archivo local en vez de la URL de S3.
  * No se usa `python3.8`, cualquier Python 3.8+ sirve.
  * Se abre http://127.0.0.1:8050 en el navegador en lugar de "Launch Application".

Ejecutar en desarrollo:
    python flight_delay.py        ->  http://0.0.0.0:10000

Ejecutar en produccion (Linux / plataforma de despliegue):
    gunicorn flight_delay:server  ->  usa el objeto WSGI `server` de este modulo
"""

from pathlib import Path

# Import required libraries
import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.graph_objects import Figure

# Read the airline data into pandas dataframe
# (en el laboratorio esta ruta era la URL publica de cf-courses-data.s3;
#  se guarda el CSV junto al script para que arranque sin internet)
DATA_FILE = Path(__file__).with_name('airline_data.csv')

airline_data = pd.read_csv(DATA_FILE,
                           encoding="ISO-8859-1",
                           dtype={'Div1Airport': str, 'Div1TailNum': str,
                                  'Div2Airport': str, 'Div2TailNum': str})

# Create a dash application
app = dash.Dash(__name__)

# Build dash app layout
app.layout = html.Div(children=[html.H1('Flight Delay Time Statistics',
                                style={'textAlign': 'center', 'color': '#503D36',
                                       'font-size': 30}),
                                html.Div(["Input Year: ", dcc.Input(id='input-year', value='2010',
                                type='number', style={'height': '35px', 'font-size': 30}), ],
                                style={'font-size': 30}),
                                html.Br(),
                                html.Br(),
                                # Segment 1
                                html.Div([
                                        html.Div(dcc.Graph(id='carrier-plot')),
                                        html.Div(dcc.Graph(id='weather-plot'))
                                ], style={'display': 'flex'}),
                                # Segment 2
                                html.Div([
                                        html.Div(dcc.Graph(id='nas-plot')),
                                        html.Div(dcc.Graph(id='security-plot'))
                                ], style={'display': 'flex'}),
                                # Segment 3
                                html.Div(dcc.Graph(id='late-plot'), style={'width': '65%'})
                                ])

""" Compute_info function description

This function takes in airline data and selected year as an input and performs computation for creating charts and plots.

Arguments:
    airline_data: Input airline data.
    entered_year: Input year for which computation needs to be performed.

Returns:
    Computed average dataframes for carrier delay, weather delay, NAS delay, security delay, and late aircraft delay.

"""


def compute_info(airline_data, entered_year):
    # Select data
    df = airline_data[airline_data['Year'] == int(entered_year)]
    # Compute delay averages
    avg_car = df.groupby(['Month', 'Reporting_Airline'])['CarrierDelay'].mean().reset_index()
    avg_weather = df.groupby(['Month', 'Reporting_Airline'])['WeatherDelay'].mean().reset_index()
    avg_NAS = df.groupby(['Month', 'Reporting_Airline'])['NASDelay'].mean().reset_index()
    avg_sec = df.groupby(['Month', 'Reporting_Airline'])['SecurityDelay'].mean().reset_index()
    avg_late = df.groupby(['Month', 'Reporting_Airline'])['LateAircraftDelay'].mean().reset_index()
    return avg_car, avg_weather, avg_NAS, avg_sec, avg_late


"""Callback Function

Function that returns fugures using the provided input year.

Arguments:

    entered_year: Input year provided by the user.

Returns:

    List of figures computed using the provided helper function `compute_info`.
"""
# Callback decorator


@app.callback([
               Output(component_id='carrier-plot', component_property='figure'),
               Output(component_id='weather-plot', component_property='figure'),
               Output(component_id='nas-plot', component_property='figure'),
               Output(component_id='security-plot', component_property='figure'),
               Output(component_id='late-plot', component_property='figure')
               ],
               Input(component_id='input-year', component_property='value'))
# Computation to callback function and return graph
def get_graph(entered_year):

    # El campo de entrada puede quedar vacio (None) o no numerico al escribir en
    # el navegador; sin esta guarda int(entered_year) lanzaria ValueError y el
    # callback se romperia. Nota: px.line() sin data_frame falla en plotly 7.x,
    # por eso la figura vacia se construye con go.Figure.
    try:
        int(entered_year)
    except (TypeError, ValueError):
        blank = Figure()
        blank.update_layout(title='Enter a valid year (2010-2020)',
                            xaxis={'visible': False}, yaxis={'visible': False})
        return [blank, blank, blank, blank, blank]

    # Compute required information for creating graph from the data
    avg_car, avg_weather, avg_NAS, avg_sec, avg_late = compute_info(airline_data, entered_year)

    # Line plot for carrier delay
    carrier_fig = px.line(avg_car, x='Month', y='CarrierDelay', color='Reporting_Airline',
                          title='Average carrrier delay time (minutes) by airline')
    # Line plot for weather delay
    weather_fig = px.line(avg_weather, x='Month', y='WeatherDelay', color='Reporting_Airline',
                          title='Average weather delay time (minutes) by airline')
    # Line plot for nas delay
    nas_fig = px.line(avg_NAS, x='Month', y='NASDelay', color='Reporting_Airline',
                      title='Average NAS delay time (minutes) by airline')
    # Line plot for security delay
    sec_fig = px.line(avg_sec, x='Month', y='SecurityDelay', color='Reporting_Airline',
                      title='Average security delay time (minutes) by airline')
    # Line plot for late aircraft delay
    late_fig = px.line(avg_late, x='Month', y='LateAircraftDelay', color='Reporting_Airline',
                       title='Average late aircraft delay time (minutes) by airline')

    return [carrier_fig, weather_fig, nas_fig, sec_fig, late_fig]


# ---------------------------------------------------------------------------
# Arranque: desarrollo local y produccion
# ---------------------------------------------------------------------------
# El objeto WSGI que busca gunicorn (y la mayoria de las plataformas de
# despliegue) se llama `server` y Dash ya lo expone en `app.server`.
server = app.server

# El laboratorio usa `app.run_server(...)`, el metodo de Dash 1.x/2.x. Desde
# Dash 3 ese nombre ya no existe y `app.run(...)` es su equivalente (aqui hay
# Dash 4.4.1). Ojo: no sirve `hasattr(app, 'run_server')`, porque Dash no
# devuelve AttributeError sino que lanza ObsoleteAttributeException desde
# dash/_obsolete.py, y hasattr() solo absorbe AttributeError. Por eso se prueba
# con try/except: si el atributo no existe, se registra el alias hacia
# `app.run` y la ultima linea del script sigue siendo la del enunciado.
try:
    _ = app.run_server  # Dash 1.x / 2.x
except Exception:       # Dash >= 3: ObsoleteAttributeException
    setattr(app, 'run_server', app.run)

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=10000)  # type: ignore[attr-defined]
