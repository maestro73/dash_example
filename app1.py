import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
from sqlalchemy import create_engine

engine = create_engine('postgresql://eaceror:zub3njkMd9tl9yApdPlc@database-dash.ch7ue6bqngjk.us-east-2.rds.amazonaws.com/database-dash')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('OCCURRED_ON_DATE',))

##filter function
def filter_df(df, exchange, leverage, start_date, end_date):
    return df[(df['Exchange']==exchange) &
              (df['Margin']==int(leverage)) &
              (df['Entry time']>=start_date) &
              (df['Entry time']<=end_date)].copy().sort_values('Entry time')

dfg=df.groupby(df['Entry time'].dt.to_period("M")).agg({'Entry balance':[('Open','first'),('Low','first')],
                                                               'Exit balance':[('Close','last'),('High','last')]})
dfg=dfg.droplevel(0, axis=1).reset_index()
dfg.rename(columns = {"Entry time" : "Date"}, inplace=True)
dfg['Date']=pd.to_datetime(dfg['Date'].astype('str'), format='%Y-%m')



app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max()
                                    ),
                                ],
                                style={'display': 'inline-block'}
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ],
                                style={'display': 'inline-block'}
                                
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                       'data': [go.Candlestick(x=dfg['Date'],
                                               open=dfg['Open'],
                                               high=dfg['High'],
                                               low=dfg['Low'],
                                               close=dfg['Close'])],
                        'layout': go.Layout(title=f"Overview of Monthly performance"
                                            )
            
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        style={'height': 500},
                        className="six columns card",
                        figure={'data': [go.Bar(name='Long', y=df['Pnl (incl fees)'], x=df['Entry time'], marker_color='red')],
                                'layout':go.Layout(title=f'PNL' )}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        style={'height': 500},
                        figure={
                       'data': [go.Scatter(x=df['Entry time'],
                                           y=df['BTC Price'])],
                        'layout': go.Layout(title=f"Dayly BTC Price")                        
                        }
                    ),
                    dcc.Graph(
                        id="balance",
                        style={'height': 500},
                        className="six columns card",
                        figure={
                       'data': [go.Scatter(x=df['Entry time'],
                                           y=df['Exit balance'])],
                       'layout': go.Layout(title=f"Balance overtime")                        

                        }
                    )
                ]
            )
        ]
    )        
])

### callback update dates
@app.callback(
    [
    dash.dependencies.Output('date-range', 'start_date'),
    dash.dependencies.Output('date-range', 'end_date')
    ],
    [
        dash.dependencies.Input('exchange-select', 'value'), # input with id date-picker-range and the start_date parameter
    ]
)

def update_dates(value):
    df1=df[df['Exchange']==value].copy()
    return [df1['Entry time'].min(), df1['Entry time'].max()]



##callback fro monthly chart, market-returns, strat-returns, market-vs-returns
@app.callback([
              dash.dependencies.Output('monthly-chart', 'figure'),
              dash.dependencies.Output('market-returns', 'children'),
              dash.dependencies.Output('strat-returns', 'children'),
              dash.dependencies.Output('strat-vs-market', 'children')
             ],
    [
        dash.dependencies.Input('exchange-select', 'value'), 
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date')
    ]
)

##update select and monthly chart
def update_monthy_chart(exchange, leverage, start_date, end_date):
    dff=filter_df(df, exchange, leverage, start_date, end_date)
    dffg=dff.groupby(dff['Entry time'].dt.to_period("M")).agg({'Entry balance':[('Open','first'),('Low','first')],
                                                               'Exit balance':[('Close','last'),('High','last')]})
    dffg=dffg.droplevel(0, axis=1).reset_index()
    dffg.rename(columns = {"Entry time" : "Date"}, inplace=True)
    dffg['Date']=pd.to_datetime(dffg['Date'].astype('str'), format='%Y-%m')
    btc_returns=calc_btc_returns(exchange, leverage, start_date, end_date)
    strat_returns=calc_strat_returns(exchange, leverage, start_date, end_date)
    strat_vs_market=(calc_btc_returns(exchange, leverage, start_date, end_date)-
                     calc_strat_returns(exchange, leverage, start_date, end_date))
    return { 
            'data': [go.Candlestick(x=dffg['Date'],
                    open=dffg['Open'],
                    high=dffg['High'],
                    low=dffg['Low'],
                    close=dffg['Close'])],
            'layout': go.Layout(title=f"Overview of Monthly performance")
            
        }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'


##update table
@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')


def calc_btc_returns(exchange, leverage, start_date, end_date):
    dff=filter_df(df,  exchange, leverage, start_date, end_date)
    btc_start_value = dff.head(1)['BTC Price'].values[0]
    btc_end_value = dff.tail(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(exchange, leverage, start_date, end_date):
    dff=filter_df(df,  exchange, leverage, start_date, end_date)
    start_value = dff.head(1)['Exit balance'].values[0]
    end_value = dff.tail(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

## Callback for pnl
@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)


def update_pnl(exchange, leverage, start_date, end_date):
    dff=filter_df(df, exchange, leverage, start_date, end_date)
    dffl=dff[dff['Trade type']=='Long']
    dffs=dff[dff['Trade type']=='Short']
    trace1 = go.Bar(x=dffl['Entry time'], y=dffl['Pnl (incl fees)'], name='Long', marker_color='Salmon')
    trace2 = go.Bar(x=dffs['Entry time'], y=dffs['Pnl (incl fees)'], name='Short', marker_color='black')

    return {
        'data': [trace1, trace2],
        'layout':go.Layout(title=f'PNL')}

##callback for btc price
@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)


def update_BTC(exchange, leverage, start_date, end_date):
    dff=filter_df(df, exchange, leverage, start_date, end_date)
    return{
        'data': [go.Scatter(x=dff['Entry time'], y=dff['BTC Price'])],
        'layout': go.Layout(title=f"Dayly BTC Price")}

##callback for balance
@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)

def update_BTC(exchange, leverage, start_date, end_date):
    dff=filter_df(df, exchange, leverage, start_date, end_date)
    return{
        'data': [go.Scatter(x=dff['Entry time'], y=dff['Exit balance'])],
        'layout': go.Layout(title=f"Balance overtime")}
                        
                        


if __name__ == "__main__":
    app.run_server(debug=True)
