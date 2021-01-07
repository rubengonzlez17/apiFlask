# -*- coding: iso-8859-1 -*-

import os
from flask import Flask
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from celery import Celery
from manager import config

__author__ = """rubengonzlez17@usal.es"""
__version__ = '0.1.0'


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


os.environ["PYTHONIOENCODING"] = "ISO-8859-1"

app = Flask(__name__, template_folder='../templates')

# Configurations
app.config.from_object(config)


CORS(app)

# Celery
celery = make_celery(app)

# Set up MongoEngine
db = MongoEngine(app)

# Import a module/component using its blueprint handler variable
from .player.player_controller import player as player_module

# Register blueprint(s)
app.register_blueprint(player_module)

# Build the database:
# This will create the database file using SQLAlchemy
# db.create_all()

try:
    data_path = os.environ['manager']
except KeyError:
    import tempfile
    data_path = tempfile.gettempdir()
