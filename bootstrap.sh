#!/bin/bash

apt-get update
apt-get install -y python python-pip gunicorn nginx
pip install flask
