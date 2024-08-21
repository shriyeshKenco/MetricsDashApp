import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key
import plotly.graph_objs as go
from datetime import datetime, timedelta

from davinci.services.auth import get_secret
from davinci.utils.global_config import ENV

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
            html.Div([
                dcc.RadioItems(
                    id='granularity-toggle',
                    options=[
                        {'label': 'Hourly', 'value': 'hourly'},
                        {'label': '3-Hourly', 'value': '3hourly'}
                    ],
                    value='hourly',  # Default value
                    labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                )
            ], style={'margin-top': '10px'}),
        ], className="controls_parent"),

        dash_table.DataTable(
            id='data-table',
            columns=[
                {'name': 'TimeStamp', 'id': 'TimeStamp'},
                {'name': 'CreatedRecords', 'id': 'CreatedRecords'},
                {'name': 'ModifiedRecords', 'id': 'ModifiedRecords'},
                {'name': 'DeletedRecords', 'id': 'DeletedRecords'},
                {'name': 'TriggerAlert', 'id': 'TriggerAlert'}
            ],
            data=[],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        ),

        html.Div(children=[
            dcc.Graph(id='created-plot', style={'width': '48%', 'display': 'inline-block'}),
            dcc.Graph(id='modified-plot', style={'width': '48%', 'display': 'inline-block'}),
            dcc.Graph(id='deleted-plot', style={'width': '48%', 'display': 'inline-block', 'margin-top': '20px'})
        ], style={'textAlign': 'center'})
    ], style={"margin": "20px 0 20px 5px"})


def render_table_list():
    """
    Fetch unique table names from DynamoDB and create dropdown options,
    handling pagination to retrieve all items.
    """
    table_names = set()
    response = table.scan()

    while 'LastEvaluatedKey' in response:
        items = response['Items']
        for item in items:
            table_names.add(item['TableName'])

        # Continue scanning with pagination token
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

    # Add the final batch of items
    items = response['Items']
    for item in items:
        table_names.add(item['TableName'])

    return [{'label': name, 'value': name} for name in table_names]


def update_table_and_plot(table_name, granularity='hourly'):
    if table_name:
        response = table.query(
            KeyConditionExpression=Key('TableName').eq(table_name),
            ScanIndexForward=False,  # Descending order
            Limit=240  # Fetch more entries to ensure proper aggregation
        )
        items = response['Items']
        items.sort(key=lambda x: x['TimeStamp'], reverse=False)  # Sort by TimeStamp ascending

        df = pd.DataFrame(items)
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], format='%Y%m%d%H%M')

        if granularity == '3hourly':
            # Create 3-hour non-overlapping windows
            df['Window'] = df['TimeStamp'].dt.floor('3H')

            # Group by these 3-hour windows and aggregate the necessary columns
            df_agg = df.groupby('Window').agg({
                'CreatedRecords': 'sum',
                'ModifiedRecords': 'sum',
                'DeletedRecords': 'sum',
                '3HourMeanCreatedRecords': 'sum',
                '3HourLowerBoundCreatedRecords': 'sum',
                '3HourUpperBoundCreatedRecords': 'sum',
                '3HourMeanModifiedRecords': 'sum',
                '3HourLowerBoundModifiedRecords': 'sum',
                '3HourUpperBoundModifiedRecords': 'sum',
                '3HourMeanDeletedRecords': 'sum',
                '3HourLowerBoundDeletedRecords': 'sum',
                '3HourUpperBoundDeletedRecords': 'sum',
                'TriggerAlert': 'max'  # Use max to simulate "any True" logic
            }).reset_index()

            # Update plots and table
            created_figure = {
                'data': [
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['CreatedRecords'],
                        mode='lines',
                        name='Created Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourMeanCreatedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourUpperBoundCreatedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourLowerBoundCreatedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Created Records (3-Hour Window)',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Created Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            modified_figure = {
                'data': [
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['ModifiedRecords'],
                        mode='lines',
                        name='Modified Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourMeanModifiedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourUpperBoundModifiedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourLowerBoundModifiedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Modified Records (3-Hour Window)',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Modified Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            deleted_figure = {
                'data': [
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['DeletedRecords'],
                        mode='lines',
                        name='Deleted Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourMeanDeletedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourUpperBoundDeletedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df_agg['Window'],
                        y=df_agg['3HourLowerBoundDeletedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Deleted Records (3-Hour Window)',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Deleted Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            return df_agg.to_dict('records'), created_figure, modified_figure, deleted_figure
        else:
            # Default hourly plot logic
            created_figure = {
                'data': [
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['CreatedRecords'],
                        mode='lines',
                        name='Created Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourMeanCreatedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourUpperBoundCreatedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourLowerBoundCreatedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Created Records Over Time',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Created Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            modified_figure = {
                'data': [
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['ModifiedRecords'],
                        mode='lines',
                        name='Modified Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourMeanModifiedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourUpperBoundModifiedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourLowerBoundModifiedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Modified Records Over Time',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Modified Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            deleted_figure = {
                'data': [
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['DeletedRecords'],
                        mode='lines',
                        name='Deleted Records',
                        line=dict(color='blue', width=2)
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourMeanDeletedRecords'],
                        mode='lines',
                        name='3-Hour Mean',
                        line=dict(dash='dot', color='orange')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourUpperBoundDeletedRecords'],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(dash='dot', color='green')
                    ),
                    go.Scatter(
                        x=df['TimeStamp'],
                        y=df['3HourLowerBoundDeletedRecords'],
                        mode='lines',
                        name='Lower Bound',
                        line=dict(dash='dot', color='red')
                    )
                ],
                'layout': go.Layout(
                    title=f'{table_name} - Deleted Records Over Time',
                    xaxis={'title': 'TimeStamp'},
                    yaxis={'title': 'Deleted Records'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 0},
                    hovermode='closest'
                )
            }

            return df.to_dict('records'), created_figure, modified_figure, deleted_figure

    return [], {}, {}, {}

