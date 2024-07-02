# IMPORTANT! DO NOT ALTER THE BELOW LINE
from serving import app, server

# Other Imports
from flask_login import current_user

from davinci.dash.boilerplate import create_standard_layout, create_standard_callbacks
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from dash import Input, Output, State, html

# Define your app UI here
def render_layout():
    return html.Div('App')

# Callbacks should be defined like so:
# @app.callback(Output('id', 'attr'), Input('id', 'attr))
# def my_callback(val):
#   ...

### These two function calls create the sidebar and associated callbacks
### so that we have consistency across apps.
### app_name will connect to relevant security groups.
### It does not necessarily need to match the url path specified in serving.py
app.layout = create_standard_layout(use_loader=True)
create_standard_callbacks(app, render_layout, app_name='test') # DEVELOPER TODO: update 'test'

# For local development only. The app will
# get called via gunicorn on the Ec2.
if __name__ == '__main__':
    app.run(host="localhost", port="8051", debug=True, use_reloader=False)
