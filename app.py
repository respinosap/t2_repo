import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import datetime as dt

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard Energia"

server = app.server
app.config.suppress_callback_exceptions = True

# Se agrega esta linea para probar
# Se agrega segunda linea de prueba

# Load data from csv
def load_data():
    """
    Carga el archivo datos_energia.csv y lo convierte en un DataFrame de Pandas.
    La columna 'time' se convierte al formato datetime y se establece como índice.
    
    Returns:
        pd.DataFrame: DataFrame con los datos cargados y procesados.
    """
    try:
        # Leer el archivo CSV
        df = pd.read_csv('datos_energia.csv')
        
        # Convertir la columna 'time' a formato datetime
        df['time'] = pd.to_datetime(df['time'])
        
        # Establecer la columna 'time' como índice
        df.set_index('time', inplace=True)
        
        return df
    except FileNotFoundError:
        print("El archivo 'datos_energia.csv' no se encontró.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ocurrió un error al cargar los datos: {e}")
        return pd.DataFrame()

# Cargar datos
data = load_data()

# Verificar si los datos fueron cargados correctamente
if data.empty:
    raise ValueError("No se pudieron cargar los datos. Asegúrese de que 'datos_energia.csv' exista y esté correctamente formateado.")

# Graficar serie
def plot_series(data, initial_date, proy):
    data_plot = data.loc[initial_date:]
    data_plot = data_plot[:-(120 - proy)]
    fig = go.Figure([
        go.Scatter(
            name='Demanda energética',
            x=data_plot.index,
            y=data_plot['AT_load_actual_entsoe_transparency'],
            mode='lines',
            line=dict(color="#188463"),
        ),
        go.Scatter(
            name='Proyección',
            x=data_plot.index,
            y=data_plot['forecast'],
            mode='lines',
            line=dict(color="#bbffeb",),
        ),
        go.Scatter(
            name='Upper Bound',
            x=data_plot.index,
            y=data_plot['Upper bound'],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=data_plot.index,
            y=data_plot['Lower bound'],
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor="rgba(242, 255, 251, 0.3)",
            fill='tonexty',
            showlegend=False
        )
    ])

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis_title='Demanda total [MW]',
        hovermode="x"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#2cfec1"
    )
    fig.update_xaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')
    fig.update_yaxes(showgrid=True, gridwidth=0.25, gridcolor='#7C7C7C')

    return fig

def description_card():
    """
    :return: Un Div que contiene el título y las descripciones del dashboard.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H3("Pronóstico de producción energética"),
            html.Div(
                id="intro",
                children=(
                    "Esta herramienta contiene información sobre la demanda energética total en Austria cada hora "
                    "según lo publicado en ENTSO-E Data Portal. Adicionalmente, permite realizar pronósticos hasta "
                    "5 días en el futuro."
                )
            ),
        ],
    )

def generate_control_card():
    """
    :return: Un Div que contiene los controles para los gráficos.
    """
    return html.Div(
        id="control-card",
        children=[

            # Fecha inicial
            html.P("Seleccionar fecha y hora inicial:"),

            html.Div(
                id="componentes-fecha-inicial",
                children=[
                    html.Div(
                        id="componente-fecha",
                        children=[
                            dcc.DatePickerSingle(
                                id='datepicker-inicial',
                                min_date_allowed=min(data.index.date),
                                max_date_allowed=max(data.index.date),
                                initial_visible_month=min(data.index.date),
                                date=(max(data.index.date) - dt.timedelta(days=7)).strftime('%Y-%m-%d')
                            )
                        ],
                        style=dict(width='30%')
                    ),
                    
                    html.P(" ", style=dict(width='5%', textAlign='center')),
                    
                    html.Div(
                        id="componente-hora",
                        children=[
                            dcc.Dropdown(
                                id="dropdown-hora-inicial-hora",
                                options=[{"label": f"{i}:00", "value": i} for i in range(0, 24)],
                                value=(max(data.index) - dt.timedelta(days=7)).hour,
                                clearable=False
                            )
                        ],
                        style=dict(width='20%')
                    ),
                ],
                style=dict(display='flex')
            ),

            html.Br(),

            # Slider proyección
            html.Div(
                id="campo-slider",
                children=[
                    html.P("Ingrese horas a proyectar:"),
                    dcc.Slider(
                        id="slider-proyeccion",
                        min=0,
                        max=119,
                        step=1,
                        value=0,
                        marks={i: str(i) for i in range(0, 120, 10)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    )
                ]
            )     
     
        ]
    )

app.layout = html.Div(
    id="app-container",
    children=[
        
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[description_card(), generate_control_card()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        
        # Right column
        html.Div(
            id="right-column",
            className="eight columns",
            children=[

                # Grafica de la serie de tiempo
                html.Div(
                    id="model_graph",
                    children=[
                        html.B("Demanda energética total en Austria [MW]"),
                        html.Hr(),
                        dcc.Graph(
                            id="plot_series",  
                        )
                    ],
                ),

            
            ],
        ),
    ],
)

@app.callback(
    Output(component_id="plot_series", component_property="figure"),
    [
        Input(component_id="datepicker-inicial", component_property="date"),
        Input(component_id="dropdown-hora-inicial-hora", component_property="value"),
        Input(component_id="slider-proyeccion", component_property="value")
    ]
)
def update_output_div(date, hour, proy):

    if (date is not None) and (hour is not None) and (proy is not None):
        try:
            initial_date_str = f"{date} {int(hour):02d}:00"
            initial_date = pd.to_datetime(initial_date_str, format="%Y-%m-%d %H:%M")
            
            # Verificar que la fecha inicial esté en el rango de los datos
            if initial_date not in data.index:
                return go.Figure()

            # Graficar
            plot = plot_series(data, initial_date, int(proy))
            return plot
        except Exception as e:
            print(f"Error al actualizar la gráfica: {e}")
            return go.Figure()
    else:
        return go.Figure()

# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)