#!/usr/bin/python
# coding:utf-8

activate_this = '/var/www/Tyou/py/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/Tyou')
from app import app as application

