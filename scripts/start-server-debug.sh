#!/bin/bash
echo "Ready to start the web server in debug mode"
cd /code
if [ -d "/opt/invenio/var/instance/python/lib/python3.9/site-packages/cernopendata" ]; then
  echo "The installation directory is still there... let's overwrite it"
  cp /code/cernopendata/setup.py /code/setup.py
  pip install -e .
fi

if [ "$1"  == "worker" ]; then
  echo "Starting the celery worker"
  celery -A cernopendata.celery worker --beat --loglevel=INFO --concurrency=1
else
  echo "Starting the web server"
  export INVENIO_CERN_SYNC_KEYCLOAK_BASE_URL=https://auth.cern.ch/
  cernopendata run -h 0.0.0.0 --reload;
fi
echo "THE WEB SERVICE DIED!!! Let's sleep for a bit to give some time to debug"
sleep 600