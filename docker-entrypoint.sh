#!/bin/bash

tmux new -d -s celery
tmux send-keys -t "celery" C-z 'celery -A canalservice worker -n log@%h --loglevel=INFO -B' Enter
pip3 install -r requirements.txt || true

# uwsgi --module=canalservice.wsgi:application --http-socket=:8000
gunicorn canalservice.wsgi:application -b :8000