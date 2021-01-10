Installation
------------
To install the latest code from the **main branch**, assuming you have a [Python](http://www.python.org/) distribution with [pip](https://pip.pypa.io/en/stable/installing/):

    $ pip install https://github.com/rubengonzlez17/apiFlask

To install a **development** version clone the repo, cd to the directory and::

    $ pip install -e .
Deployment
----------
***Step-by-step deployment***

Once installed the flask server might be started with the command::

    $ manager
    
Or using [Gunicorn](https://github.com/benoitc/gunicorn) instead::

    $ gunicorn --workers 4 --bind 0.0.0.0:8000 --timeout 600 manager.app:app
    
To start the Celery queue, cd into the directory and in windows you might need [gevent](https://pypi.org/project/gevent/):

    $ celery -A manager.app.celery worker --pool=gevent

To clear all queued tasks, cd into the directory and::

    $ celery -A manager.app.celery purge -f
    

***Scripts for deployment***

Alternately you can start the server by running the following command, specifying the port::
    
    $ ./startServer.sh <PORT>
    

Or you can stop the server by running the following command, specifying the port::

    $ ./stopServer.sh <PORT>

To finish, the loading data must be started by running the following command, specifying the port:: 

    $ ./run_tasks.sh <PORT>
Monitoring
----------
To monitor incoming tasks, assuming you have [flower](https://pypi.org/project/flower/) installed:

    $ flower --host=0.0.0.0 --port=5555

---