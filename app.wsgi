#!/usr/bin/python
# coding:utf-8

from config import update_path
update_path()
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/Tyou')
from app import app as application

