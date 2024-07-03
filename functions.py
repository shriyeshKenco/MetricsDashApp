import pandas as pd
from dash import dcc, Input, Output, State, callback, ctx, no_update
import json
from flask_login import current_user
from serving import app
from davinci.utils.global_config import ENV
import boto3
import json
from davinci.services.auth import get_secret
from content_rendering import render_main_layout, render_table_list, update_table_and_plot

def define_main_layout():
    '''
    Main layout of the entire app is defined/created
    '''
    return render_main_layout()

@app.callback(
    Output('data-table', 'data'),
    Output('line-plot', 'figure'),
    Input('table-dropdown', 'value')
)
def main_callback(table_name):
    '''
    Callback function to update the data table and plot based on the selected table name
    '''
    if table_name is None:
        raise PreventUpdate

    table_data, plot_figure = update_table_and_plot(table_name)
    return table_data, plot_figure