#!/usr/bin/env python
#coding:utf-8
from .frontend import frontend
from .link import link
from .admin import adminor as admin
from .media import media
from .makesearch import makesearch
from .tool import tool
MODULES=((frontend, ""),
    (link, "/link"),
    (admin,'/admin'),
    (media,'/media'),
    (makesearch,'/search'),
    (tool,'/tool'),
)

