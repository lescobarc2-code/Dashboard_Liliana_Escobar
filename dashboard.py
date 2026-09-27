# %%
# ===== 4.1 Dependencias y trazabilidad del entorno =====
import sys

import pandas as pd
import plotly
import plotly.express as px
from plotly.graph_objects import Figure

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

print('Python :', sys.version.split()[0])
print('pandas :', pd.__version__)
print('plotly :', plotly.__version__)
print('dash   :', dash.__version__)




# %%
# ===== 5. Lectura del conjunto de datos =====
from pathlib import Path
import urllib.request

RUTA_LOCAL = Path('airline_data.csv')
URL_ORIGEN = ('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/'
              'IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/'
              'Data%20Files/airline_data.csv')

if not RUTA_LOCAL.exists():          # respaldo: fuente original del laboratorio
    print('airline_data.csv no encontrado; descargando del origen...')
    urllib.request.urlretrieve(URL_ORIGEN, RUTA_LOCAL)

airline_data = pd.read_csv(
    RUTA_LOCAL,
    encoding='ISO-8859-1',
    dtype={'Div1Airport': str, 'Div1TailNum': str,
           'Div2Airport': str, 'Div2TailNum': str},
)

print(f'Dimensiones : {airline_data.shape[0]:,} filas x {airline_data.shape[1]} columnas')
print(f'Tamano disco: {RUTA_LOCAL.stat().st_size / 1e6:.1f} MB')
airline_data.head(3)




# %%
# ===== 5.1 Perfil y calidad del conjunto de datos =====
VARS_DELAY = ['CarrierDelay', 'WeatherDelay', 'NASDelay',
              'SecurityDelay', 'LateAircraftDelay']

anios = sorted(airline_data['Year'].unique())
print(f'Rango de anios   : {anios[0]} - {anios[-1]}  ({len(anios)} anios distintos)')
print(f'Aerolineas       : {airline_data["Reporting_Airline"].nunique()} codigos distintos')
print(f'Meses presentes  : {sorted(int(m) for m in airline_data["Month"].unique())}')

calidad = pd.DataFrame({
    'tipo'     : airline_data[VARS_DELAY].dtypes.astype(str),
    'no_nulos' : airline_data[VARS_DELAY].notna().sum(),
    'pct_nulos': (airline_data[VARS_DELAY].isna().mean() * 100).round(1),
})
print('\nCobertura de las variables de retraso (minutos):')
print(calidad.to_string())


# %%
# ===== 5.2 Que significa el valor ausente en las causas de retraso? =====
causas_vacias = airline_data[VARS_DELAY].isna().all(axis=1)
con_causa     = ~causas_vacias
vacios_parciales = airline_data[VARS_DELAY].isna().any(axis=1) & con_causa

print(f'Filas con las cinco causas vacias : {causas_vacias.sum():,}')
print(f'Filas con al menos una causa      : {con_causa.sum():,}')
print(f'Filas con vacios parciales        : {vacios_parciales.sum():,}')

contraste = (airline_data
             .assign(causas_vacias=causas_vacias)
             .groupby('causas_vacias')['ArrDelay']
             .agg(vuelos='count', media='mean', mediana='median', maximo='max')
             .round(2))
contraste.index = ['con causa reportada', 'sin causa reportada']

print('\nRetraso de llegada (ArrDelay, minutos) segun el estado de las causas:')
print(contraste.to_string())


# 

# %%
# ===== 6. y 7. Aplicacion y layout completo =====
app = dash.Dash(__name__)

app.layout = html.Div(children=[

    # --- Titulo ---
    html.H1('Flight Delay Time Statistics',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 30}),

    # --- Entrada: anio a analizar ---
    html.Div(['Input Year: ',
              dcc.Input(id='input-year', value='2010', type='number',
                        style={'height': '35px', 'font-size': 30})],
             style={'font-size': 30}),
    html.Br(),
    html.Br(),

    # --- Segmento 1: retraso por aerolinea y por clima ---
    html.Div([
        html.Div(dcc.Graph(id='carrier-plot')),
        html.Div(dcc.Graph(id='weather-plot')),
    ], style={'display': 'flex'}),

    # --- Segmento 2: retraso del sistema aereo nacional y por seguridad ---
    html.Div([
        html.Div(dcc.Graph(id='nas-plot')),
        html.Div(dcc.Graph(id='security-plot')),
    ], style={'display': 'flex'}),

    # --- Segmento 3: retraso por aeronave tardia ---
    html.Div(dcc.Graph(id='late-plot'), style={'width': '65%'}),
])


def recorrer(componente):
    """Devuelve el id de todos los componentes con id dentro del arbol del layout."""
    encontrados = []
    identificador = getattr(componente, 'id', None)
    if identificador:
        encontrados.append(identificador)
    hijos = getattr(componente, 'children', None)
    if isinstance(hijos, (list, tuple)):
        for hijo in hijos:
            encontrados += recorrer(hijo)
    elif hijos is not None and not isinstance(hijos, str):
        encontrados += recorrer(hijos)
    return encontrados


print('Aplicacion creada :', type(app).__name__)
print('Componentes con id:', sorted(recorrer(app.layout)))




# %%
# ===== 8. Funcion auxiliar de calculo =====
def compute_info(airline_data, entered_year):
    """Promedios mensuales de retraso por aerolinea para un anio dado.

    Argumentos:
        airline_data: DataFrame con el historico de vuelos.
        entered_year: anio seleccionado por el usuario.

    Devuelve:
        Cinco DataFrames (carrier, weather, NAS, security, late aircraft),
        cada uno con columnas Month, Reporting_Airline y la variable de retraso.
    """
    df = airline_data[airline_data['Year'] == int(entered_year)]

    avg_car     = df.groupby(['Month', 'Reporting_Airline'])['CarrierDelay'].mean().reset_index()
    avg_weather = df.groupby(['Month', 'Reporting_Airline'])['WeatherDelay'].mean().reset_index()
    avg_NAS     = df.groupby(['Month', 'Reporting_Airline'])['NASDelay'].mean().reset_index()
    avg_sec     = df.groupby(['Month', 'Reporting_Airline'])['SecurityDelay'].mean().reset_index()
    avg_late    = df.groupby(['Month', 'Reporting_Airline'])['LateAircraftDelay'].mean().reset_index()

    return avg_car, avg_weather, avg_NAS, avg_sec, avg_late


prueba = compute_info(airline_data, 2010)
print('Tablas devueltas :', len(prueba))
print('Forma de cada una:', [t.shape for t in prueba])
prueba[0].head(3)




# %%
# ===== 9. Callback con cinco salidas =====
@app.callback([
    Output(component_id='carrier-plot',  component_property='figure'),
    Output(component_id='weather-plot',  component_property='figure'),
    Output(component_id='nas-plot',      component_property='figure'),
    Output(component_id='security-plot', component_property='figure'),
    Output(component_id='late-plot',     component_property='figure'),
], Input(component_id='input-year', component_property='value'))
def get_graph(entered_year):
    """Devuelve las cinco figuras del tablero para el anio seleccionado."""

    # Guarda: la casilla puede quedar vacia (None) o con texto no numerico.
    try:
        int(entered_year)
    except (TypeError, ValueError):
        vacia = Figure()
        vacia.update_layout(title='Introduzca un anio valido (2010-2020)',
                            xaxis={'visible': False}, yaxis={'visible': False})
        return [vacia] * 5

    # Calculo delegado en la funcion auxiliar
    avg_car, avg_weather, avg_NAS, avg_sec, avg_late = compute_info(airline_data, entered_year)

    carrier_fig  = px.line(avg_car, x='Month', y='CarrierDelay', color='Reporting_Airline',
                           title='Average carrier delay time (minutes) by airline')
    weather_fig  = px.line(avg_weather, x='Month', y='WeatherDelay', color='Reporting_Airline',
                           title='Average weather delay time (minutes) by airline')
    nas_fig      = px.line(avg_NAS, x='Month', y='NASDelay', color='Reporting_Airline',
                           title='Average NAS delay time (minutes) by airline')
    sec_fig      = px.line(avg_sec, x='Month', y='SecurityDelay', color='Reporting_Airline',
                           title='Average security delay time (minutes) by airline')
    late_fig     = px.line(avg_late, x='Month', y='LateAircraftDelay', color='Reporting_Airline',
                           title='Average late aircraft delay time (minutes) by airline')

    return [carrier_fig, weather_fig, nas_fig, sec_fig, late_fig]


print('Salidas registradas en el callback:')
for clave in sorted(app.callback_map):
    print('  -', clave)


#

# %%
# ===== 9.1 Prueba del callback como funcion pura =====
for escenario in ['2010', '2020', '1990', '']:
    try:
        figuras = get_graph(escenario)
        detalle = [f'{len(f.data)} series' for f in figuras]
        print(f'get_graph({escenario!r:>6}) -> OK   :', detalle)
    except Exception as error:                      # noqa: BLE001
        print(f'get_graph({escenario!r:>6}) -> FALLO:', type(error).__name__, error)

# %%
# ===== 9.2 Vista previa de las figuras generadas para 2010 =====
from IPython.display import display

figuras = get_graph('2010')
etiquetas = ['Carrier', 'Weather', 'NAS', 'Security', 'Late aircraft']

print('Series por figura:', {e: len(f.data) for e, f in zip(etiquetas, figuras)})

for etiqueta, figura in zip(etiquetas[:2], figuras[:2]):   # las otras tres son analogas
    figura.update_layout(height=320, margin={'l': 40, 'r': 10, 't': 50, 'b': 30},
                         title=f'{etiqueta} delay - 2010')
    display(figura)

# 
# %%
# ===== 10.1 Servidor Dash en un hilo, dentro del cuaderno =====
import socket
import threading
import time

from IPython.display import IFrame, Markdown, display
from werkzeug.serving import make_server

PUERTO = 8050
# El registro se conserva si la celda se reejecuta: asi los tableros ya abiertos
# en otros puertos siguen siendo accesibles y detenibles.
_servidores = _servidores if '_servidores' in globals() else {}


def puerto_activo(puerto):
    """True si algo responde en 127.0.0.1:<puerto>."""
    with socket.socket() as conexion:
        return conexion.connect_ex(('127.0.0.1', puerto)) == 0


def lanzar_dashboard(app, puerto=PUERTO, alto=820):
    """Sirve una aplicacion Dash en un hilo demonio y devuelve el marco embebido.

    Admite varias llamadas con puertos distintos y detecta el caso delicado: si
    se reejecuta la celda del layout, la aplicacion es un objeto NUEVO y el
    servidor anterior estaria sirviendo una version obsoleta. En ese caso se
    apaga el servidor viejo y se levanta uno nuevo.
    """
    registrado = _servidores.get(puerto)

    if registrado is not None and registrado['app'] is not app:
        registrado['servidor'].shutdown()
        del _servidores[puerto]
        print(f'El puerto {puerto} servia una version anterior del tablero: se reinicia.')

    if puerto in _servidores:
        print(f'El puerto {puerto} ya sirve esta misma aplicacion; se reutiliza.')
    elif puerto_activo(puerto):
        print(f'El puerto {puerto} ya responde y no lo gestiona el cuaderno '
              f'(lo inicio una version anterior de esta celda).')
    else:
        servidor = make_server('127.0.0.1', puerto, app.server, threaded=True)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        _servidores[puerto] = {'servidor': servidor, 'app': app}
        for _ in range(50):                 # hasta 5 s de espera activa
            if puerto_activo(puerto):
                break
            time.sleep(0.1)

    print(f'Dashboard disponible en http://127.0.0.1:{puerto}/')
    return IFrame(f'http://127.0.0.1:{puerto}/', width='100%', height=alto)


def detener_dashboard(puerto=None):
    """Detiene un tablero concreto o todos los que gestiona el cuaderno."""
    objetivos = [puerto] if puerto is not None else list(_servidores)
    if not objetivos:
        print('No hay servidores gestionados por el cuaderno.')
        return
    for p in objetivos:
        registrado = _servidores.pop(p, None)
        if registrado is not None:
            registrado['servidor'].shutdown()
            print(f'Servidor del puerto {p} detenido; el puerto quedo libre.')


display(lanzar_dashboard(app))
display(Markdown(f'**[Abrir el dashboard en una pestana del navegador](http://127.0.0.1:{PUERTO}/)**'))


# 
# %%
# ===== 11.1 Perfil del rango 2010-2020 =====
rango = airline_data[airline_data['Year'].between(2010, 2020)]

perfil_anual = (rango
    .groupby('Year')
    .agg(aerolineas      = ('Reporting_Airline', 'nunique'),
         registros       = ('Reporting_Airline', 'size'),
         meses_cubiertos = ('Month', 'nunique'),
         retraso_carrier = ('CarrierDelay', 'mean'),
         retraso_late    = ('LateAircraftDelay', 'mean'))
    .round(2))

perfil_anual

# %%
# ===== 11.2 Cuantos registros aporta cada aerolinea en 2010 y en 2020 =====
for anio in (2010, 2020):
    conteo = (airline_data[airline_data['Year'] == anio]
              .groupby('Reporting_Airline')
              .size()
              .sort_values(ascending=False))
    print(f'--- {anio}: {len(conteo)} aerolineas, '
          f'de {conteo.min()} a {conteo.max()} registros por aerolinea ---')
    print(conteo.head(5).to_string(), '\n')

# 
# 

# %%
# ===== 12.2 Datos y vocabulario del ejemplo =====
ANIO_MIN, ANIO_MAX = 2010, 2020

# Etiquetas legibles para el usuario final.
# OJO: ninguna debe coincidir con 'Aerolinea' ni con 'Anio', porque esas dos son
# nombres de columna de las tablas agregadas: pandas crearia columnas duplicadas.
ETIQUETAS_CAUSA = {
    'CarrierDelay': 'Retraso de la aerolinea',
    'WeatherDelay': 'Clima',
    'NASDelay': 'Sistema aereo nacional',
    'SecurityDelay': 'Seguridad',
    'LateAircraftDelay': 'Aeronave tardia',
}

# Subconjunto del rango que pide el enunciado
vuelos = airline_data[airline_data['Year'].between(ANIO_MIN, ANIO_MAX)].copy()

# Subconjunto con alguna causa reportada: es el unico sobre el que tiene sentido
# promediar las causas (ver la advertencia de la seccion 5.3)
vuelos_con_causa = vuelos[vuelos[VARS_DELAY].notna().any(axis=1)].copy()
vuelos_con_causa['periodo'] = pd.to_datetime(
    dict(year=vuelos_con_causa['Year'].astype(int),
         month=vuelos_con_causa['Month'].astype(int), day=1))

# Una sola aerolinea por vez: las seis con mas registros del rango
AEROLINEAS = (vuelos.groupby('Reporting_Airline').size()
              .sort_values(ascending=False).head(6).index.tolist())
OPCIONES_AEROLINEA = [{'label': a, 'value': a} for a in AEROLINEAS]


def tarjeta(titulo, valor):
    """Tarjeta de indicador (KPI) reutilizable."""
    return html.Div([
        html.Div(titulo, style={'fontSize': 13, 'color': '#666666'}),
        html.Div(valor, style={'fontSize': 24, 'fontWeight': 'bold', 'color': '#503D36'}),
    ], style={'flex': '1', 'border': '1px solid #dddddd', 'borderRadius': '8px',
              'padding': '10px 14px', 'backgroundColor': '#fafafa'})


print(f'Vuelos {ANIO_MIN}-{ANIO_MAX}   : {len(vuelos):,}')
print(f'  con causa reportada: {len(vuelos_con_causa):,} '
      f'({len(vuelos_con_causa) / len(vuelos):.1%})')
print(f'Aerolineas del ejemplo: {AEROLINEAS}')


# %%
# ===== 12.3 El tablero: una entrada y dos salidas =====
app2 = dash.Dash('ejemplo_simple')

app2.layout = html.Div([

    html.H1('Un ejemplo simple',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 30}),

    # UNICA entrada: la aerolinea (seleccion unica, sin opcion de vaciar)
    dcc.Dropdown(id='e-aerolinea', options=OPCIONES_AEROLINEA,
                 value=AEROLINEAS[0], clearable=False,
                 style={'width': '40%', 'margin': '0 auto'}),

    # SALIDA 1: los indicadores
    html.Div(id='e-kpis', style={'display': 'flex', 'gap': '12px', 'padding': '12px 1%'}),

    # SALIDA 2: la serie mensual
    html.Div(dcc.Graph(id='e-serie', style={'height': '52vh'}), style={'padding': '0 1%'}),
])

print('Dashboard 2 -> puerto 8051')
print('Componentes con id:', sorted(recorrer(app2.layout)))


# %%
# ===== 12.4 El callback: una entrada, dos salidas =====
@app2.callback(
    Output('e-kpis', 'children'),
    Output('e-serie', 'figure'),
    Input('e-aerolinea', 'value'),
)
def actualizar_ejemplo(aerolinea):
    """Recalcula los indicadores y la serie para la aerolinea elegida."""
    datos = vuelos[vuelos['Reporting_Airline'] == aerolinea]
    con_causa = datos[datos[VARS_DELAY].notna().any(axis=1)]

    # Guarda: un filtro sin datos no debe romper el callback.
    if not len(datos):
        return [], Figure()

    kpis = [
        tarjeta('Vuelos', f'{len(datos):,}'),
        tarjeta('Retraso medio de llegada', f"{datos['ArrDelay'].mean():,.1f} min"),
        tarjeta('Con causa reportada', f'{len(con_causa) / len(datos):.0%}'),
    ]

    serie = (vuelos_con_causa[vuelos_con_causa['Reporting_Airline'] == aerolinea]
             .groupby('periodo')[VARS_DELAY].mean().reset_index())
    figura = px.line(serie, x='periodo', y=VARS_DELAY,
                     title=f'{aerolinea}: duracion media del retraso por causa (minutos)')
    figura.for_each_trace(
        lambda traza: traza.update(name=ETIQUETAS_CAUSA.get(traza.name, traza.name)))
    figura.update_layout(height=400, yaxis_title='Minutos', xaxis_title='Mes',
                         legend_title_text='Causa')

    return kpis, figura


print('Callbacks registrados en el dashboard 2:')
for clave in sorted(app2.callback_map):
    print('  -', clave[:70], '...')


# %%
# ===== 12.5 Prueba del callback y puesta en marcha =====
kpis, figura = actualizar_ejemplo('AA')      # el callback es una funcion normal
print('Tarjetas de indicador :', len(kpis))
print('Series en el grafico  :', [traza.name for traza in figura.data])
print('Primer mes de la serie:', figura.data[0].x[0])

# Caso limite: un valor que no corresponde a ninguna aerolinea del subconjunto
kpis_vacio, figura_vacia = actualizar_ejemplo('ZZ')
print('Filtro sin datos      -> tarjetas:', len(kpis_vacio),
      '| series:', len(figura_vacia.data))

display(lanzar_dashboard(app2, puerto=8051))
display(Markdown('**[Abrir el ejemplo simple en una pestana](http://127.0.0.1:8051/)**'))

