#!/bin/bash
######################################################
#         Manager_API Server Stop         #
# Authored by Rubén González, rubengonzlez17 @ GitHub #
######################################################
if [ "$#" -ne 1 ]; then
  echo "You need to specify the parameter: <PORT(8000 or 8001)>"
  exit
fi
if [ "$1" == "8000" ]; then
  echo "PORT 8000"
elif [ "$1" == "8001" ]; then
  echo "PORT 8001"
else
  echo "This port is invalid..."
  exit
fi

if [[ `lsof -ti tcp:"$1"` ]]; then
  pid=`ps ax | grep gunicorn | grep python | grep "$1" | awk '{split($0,a," "); print a[1]}' | head -n 1`
  if [ -z "$pid" ]; then
    echo "No Gunicorn Manager_API servers running on port "$1"..."
  else
    echo "One Gunicorn Manager_API server running on port "$1", so its process will be killed!"
    kill $pid
  fi

  pid_workers=`ps ax | grep celery | grep worker | awk '{split($0,a," "); print a[1]}' | head -n 1`
  if [ -z "$pid_workers" ]; then
    echo "No celery workers running......"
  else
    echo "One Celery Workers running, so its process will be killed!"
    echo "Deleting all queued tasks"
    nohup celery -A manager.app.celery purge -f &
    echo "Killing active workers"
    kill $pid_workers
  fi
  sleep 15
  echo "Stopping rabbitmq on the server.."
  `service rabbitmq-server stop`
fi