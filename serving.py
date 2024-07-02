import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import dash
from flask_login import LoginManager
from davinci.services.auth import get_secret
from davinci.utils.global_config import SYSTEM
from davinci.dash.login import login_manager_user_loader_factory, User, DEV_USER

# DEVELOPER TODO: CHANGE THIS AS APPROPRIATE
# This will be the url path that your app is available at.
url_path = "/test/"

app = dash.Dash(
    __name__,
    meta_tags=[{
        'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.5, minimum-scale=0.7'
    }],
    # external_stylesheets=[dbc.themes.MINTY, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css'],
    prevent_initial_callbacks=True,
    suppress_callback_exceptions=True,
    title="DaVinci AI Labs",
    update_title=None,
    url_base_pathname=url_path,
    serve_locally=True,
)

server = app.server
load_user, login_manager = login_manager_user_loader_factory(server)