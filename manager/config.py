# -*- coding: iso-8859-1 -*-
import os

# Statement for enabling the development environment
DEBUG = False

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the database settings

MONGODB_SETTINGS = {'host': 'localhost',
                    'port': 27017,
                    'username': '',
                    'password': '',
                    'db': 'app_manager'}


# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection against *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"

# Celery Config
CELERY_BROKER_URL = 'pyamqp://'
CELERY_RESULT_BACKEND = 'rpc://'
BROKER_HEARTBEAT = 0
CELERY_TIMEZONE = 'Europe/Amsterdam'