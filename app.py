import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import pandas as pd


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


################################################################################
# APP INITIALIZATION
################################################################################
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# this is needed by gunicorn command in procfile
server = app.server


################################################################################
# PLOTS
################################################################################
df = pd.read_csv('all_data.csv',parse_dates=True)

figure_empty = {'layout': go.Layout(
                #  colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                #   template='plotly_dark',
                  paper_bgcolor='rgba(0, 0, 0, 0)',
                  plot_bgcolor='rgba(0, 0, 0, 0)',
                  margin={'b': 15},
                  hovermode='x',
                  autosize=True,
                  title={'text': 'Traffic density', 'font': {'color': 'grey'}, 'x': 0.5},
                  xaxis={'range': ['2022-01-01','2022-12-31']},
              )}

#### Organise labels for drop down

def get_stations(filename):
    df = pd.read_csv(filename)
    # list_station = 

    dict_list = []
    for i in zip(df.station,df.alias):
        dict_list.append({'label': i[1], 'value': i[0]})

    return dict_list


stations = get_stations('Dauerzaehlstellen.csv')

def get_figure(traces):
       min_day = min([min(trace.x) for trace in traces])
       max_day = max([max(trace.x) for trace in traces])
       min_day = shift_time_str(min_day,-1)
       max_day = shift_time_str(max_day,1)

       figure = {'data': traces,
              'layout': go.Layout(
                #  colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                #   template='plotly_dark',
                  paper_bgcolor='rgba(0, 0, 0, 0)',
                  plot_bgcolor='rgba(0, 0, 0, 0)',
                  margin={'b': 15},
                  hovermode='x',
                  autosize=True,
                  title={'text': 'Traffic density', 'font': {'color': 'grey'}, 'x': 0.5},
                  xaxis={'range': [min_day,max_day]},
              ),}
       return figure


def shift_time_str(date_str,day_shift):
    return (pd.to_datetime(date_str) + pd.Timedelta(days=day_shift)).strftime('%Y-%m-%d')

def query_data(df_,zähl,mydate):
    df = df_.copy(deep=True)
    date_past = shift_time_str(mydate,-7)
    date_future = shift_time_str(mydate,1)
    df = df.query(f'(Zählstelle == {zähl}) and (ds >= "{date_past}") and (ds <= "{date_future}")')
    return df
    

def get_traces(df_,zähl,mydate):
    df = query_data(df_,zähl,mydate)
   
    traces = []

    ## Past
    plt_data = df[df.ds <= mydate ]
    traces.append(go.Scatter(x=plt_data.ds,
                                 y=plt_data.y,
                                 mode='lines',
                                 opacity=0.7,
                                 name='Past actual',
                                 textposition='bottom center'))

    traces.append(go.Scatter(x=plt_data.ds,
                                 y=plt_data.yhat,
                                 mode='lines',
                                 opacity=0.7,
                                 name='Past model fit',
                                 textposition='bottom center'))
    
    ## Predictions
    plt_data = df[df.ds > mydate ]

    traces.append(go.Scatter(x=plt_data.ds,
                                 y=plt_data.y,
                                 mode='markers',
                                 opacity=0.7,
                                 name='Tomorrow actual',
                                 textposition='bottom center'))

    traces.append(go.Scatter(x=plt_data.ds,
                                 y=plt_data.yhat,
                                 mode='markers',
                                 opacity=0.7,
                                 name='Prediction',
                                 textposition='bottom center'))

 
    return traces


# fig = get_figure(LEGEND, SCORES)

################################################################################
# LAYOUT
################################################################################
app.layout = html.Div([
        html.Div(children=[
        html.H2(id="title",
            children="Neuefische Interactive Dash Plotly Dashboard",
        ),
        html.Img(src=r"assets/ampel.png", alt="image",
                 style={"width": 50, "height": 50})]),
        html.H3(
            id="subtitle",
            children="Add some fish text and click, and the chart will change",
        ),
        html.Div(children="Add some text you want (less than 10 characters)!"),
    
        dcc.Textarea(
            id="textarea-state-example",
            value="",
            style={"width": "100%", "height": 100},
        ),
        html.Button("Submit", id="textarea-state-example-button", n_clicks=0),
        html.Div(id="textarea-state-example-output", style={"whiteSpace": "pre-line"}),
        #  Drop down and graphic
        html.Div(
                  children=[
                        html.Div(className='div-for-dropdown',
                              children=[
                                    dcc.Dropdown(id='Zselector',
                                          options=stations,
                                          multi=False,
                                        #   style={'backgroundColor': '#1E1E1E'},
                                          className='Zselector')]),
                        dcc.Graph(id='timeseries', config={'displayModeBar': False}) 
                        ]
        ),
        html.Div([html.P(["Traffic light icon made by ", 
                          html.A("ultimatearm - Flaticon",
                                 href="https://www.flaticon.com/de/kostenlose-icons/ampel")
                     ])
                   ])
                   ])

################################################################################
# INTERACTION CALLBACKS
################################################################################
# https://dash.plotly.com/basic-callbacks
# @app.callback(
#     [
#         Output("textarea-state-example-output", "children"),
#         Output("bar-chart", "figure"),
#     ],
#     Input("textarea-state-example-button", "n_clicks"),
#     State("textarea-state-example", "value"),
# )
# def update_output(n_clicks, value):
#     fig = get_figure(LEGEND, SCORES)
#     if n_clicks > 0:
#         if 0 < len(value) < 10:
#             text = "you said: " + value
#             scores = [0.1 * n_clicks, 0.1]
#             fig = get_figure(LEGEND, scores)
#             return text, fig
#         else:
#             return "Please add a text between 0 and 10 characters!", fig
#     else:
#         return "", fig


@app.callback(Output('timeseries', 'figure'),
              [Input('Zselector', 'value')])

def update_timeseries(value):
    ''' Draw traces ...'''

    mydate = '2022-03-01'
    if value:
        traces = get_traces(df,value,mydate)
        figure = get_figure(traces)

    else:
        figure = figure_empty

    return figure



# Add the server clause:
if __name__ == "__main__":
    app.run_server()
