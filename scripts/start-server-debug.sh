#!/bin/bash
echo "Ready to start the web server in debug mode"
cd /code

if [ "$1"  == "worker" ]; then
  echo "Starting the celery worker"
  celery -A cernopendata.celery worker --beat --loglevel=INFO --concurrency=1
else
  echo "Starting the web server"
  export INVENIO_CERN_SYNC_KEYCLOAK_BASE_URL=https://auth.cern.ch/
  # Only watch the application sources. Without these exclusions the reloader
  # recursively watches the virtualenv and the standard library as well, which
  # is thousands of inotify watches and overflows the kernel queue
  # ("Inotify queue overflowed; filesystem events were lost"). Only /code is
  # bind-mounted for development, so the rest never needs watching.
  cernopendata run -h 0.0.0.0 --reload \
    --exclude-patterns "/opt/invenio/src/.venv*:/usr/local/lib/python3*";
fi
echo "THE WEB SERVICE DIED!!! Let's sleep for a bit to give some time to debug"
sleep 600
