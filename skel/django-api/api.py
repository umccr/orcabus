# -*- coding: utf-8 -*-
"""api module for wsgi to AWS lambda

See README https://github.com/logandk/serverless-wsgi
"""
import serverless_wsgi

from {{project_name}}.wsgi import application


def handler(event, context):
    return serverless_wsgi.handle_request(application, event, context)
