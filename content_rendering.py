import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key
import plotly.graph_objs as go
from datetime import datetime

# Replace these imports with your actual imports
from davinci.services.auth import get_secret
from davinci.utils.global_config import ENV

# Initialize a session using Amazon DynamoDB
boto3_login = {
    "verify": False,
    "service_name": 'dynamodb',
    "region_name": 'us-east-1',
    "aws_access_key_id": get_secret("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": get_secret("AWS_SECRET_ACCESS_KEY")
}
dynamodb = boto3.resource(**boto3_login)
table_name = f'summary_table_{ENV}'
table = dynamodb.Table(table_name)


def render_main_layout():
    '''
    Initial/main skeleton of the page layout objects
    '''
    return html.Div(children=[
        dcc.Store(id='dynamodb-data', storage_type='session'),  # Store data in session

        dbc.Modal(
            [
                dbc.ModalHeader("Table Data Details"),
                dbc.ModalBody(id="row-selection-modal-content"),
            ],
            id="row-selection-modal",
            is_open=False,
            size="lg",
            backdrop=True,
            scrollable=True,
            centered=True,
            keyboard=True,
            fade=True,
        ),

        html.Div(children=[
            html.Div(children=[
                html.Img(src=f'assets/logo.png?v={str(datetime.now())}', height='100px', className='logoStyle'),
            ], className='logoStyleDiv'),
            html.Div(children=[
                html.Div(className='mainTitle', children='DynamoDB Table Data Viewer'),
                html.Div(className='mainTagline', children='Visualize Your Table Data'),
            ], className='mainTitleTagDiv')
        ], style={"height": "110px", "width": "95%", 'padding': '10px', 'margin': '10px'}),

        html.Hr(style={'clear': 'both', 'margin': '25px 0 20px 0'}),

        html.Div(children=[
            dcc.Dropdown(options=render_table_list(), id="table-dropdown", clearable=False,
                         placeholder="Select a Table", className="form_dropdown_style"),
        ], className="controls_parent"),

        dash_table.DataTable(
            id='data-table',
            columns=[
                {'name': 'TimeStamp', 'id': 'TimeStamp'},
                {'name': 'CreatedRecords', 'id': 'CreatedRecords'},
                {'name': 'ModifiedRecords', 'id': 'ModifiedRecords'},
                {'name': 'DeletedRecords', 'id': 'DeletedRecords'}
            ],
            data=[],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        ),

        dcc.Graph(id='line-plot')
    ], style={"margin": "20px 0 20px 5px"})


def render_table_list():
    '''
    Fetch unique table names from DynamoDB and create dropdown options
    '''
    response = table.scan()
    items = response['Items']
    table_names = list(set(item['TableName'] for item in items))
    return [{'label': name, 'value': name} for name in table_names]


def update_table_and_plot(table_name):
    '''
    Fetch last 8 entries from DynamoDB for the selected table and update the table and plot
    '''
    if table_name:
        response = table.query(
            KeyConditionExpression=Key('TableName').eq(table_name),
            ScanIndexForward=False,  # Descending order
            Limit=8
        )
        items = response['Items']
        items.sort(key=lambda x: x['TimeStamp'], reverse=False)  # Sort by TimeStamp ascending

        df = pd.DataFrame(items)
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], format='%Y%m%d%H%M')

        figure = {
            'data': [
                go.Scatter(
                    x=df['TimeStamp'],
                    y=df['CreatedRecords'],
                    mode='lines+markers',
                    name='Created Records'
                ),
                go.Scatter(
                    x=df['TimeStamp'],
                    y=df['ModifiedRecords'],
                    mode='lines+markers',
                    name='Modified Records'
                ),
                go.Scatter(
                    x=df['TimeStamp'],
                    y=df['DeletedRecords'],
                    mode='lines+markers',
                    name='Deleted Records'
                )
            ],
            'layout': go.Layout(
                title=f'{table_name} Records Over Time',
                xaxis={'title': 'TimeStamp'},
                yaxis={'title': 'Records'},
                margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                hovermode='closest'
            )
        }
        return df.to_dict('records'), figure
    return [], {}