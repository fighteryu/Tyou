#!/usr/bin/python
# coding:utf-8

import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/Tyou')
from config import update_path
update_path()
from app import app as application

