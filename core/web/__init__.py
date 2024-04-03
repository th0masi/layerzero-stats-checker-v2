from core.web import views
from core.web.app import app as _flask_app
from core.web.views import blueprint

app = _flask_app
app.register_blueprint(blueprint)
