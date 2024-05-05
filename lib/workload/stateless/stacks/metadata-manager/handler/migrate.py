# -*- coding: utf-8 -*-
"""migrate lambda module

Convenience AWS lambda handler for Django database migration command hook
"""
from typing import Dict

from django.core.management import execute_from_command_line


def handler(event, context) -> dict[str, str]:
    resp = {
        "StackId": event.get('StackId'),
        "RequestId": event.get('RequestId'),
        "LogicalResourceId": event.get('LogicalResourceId'),
        "PhysicalResourceId": context.get('logGroupName'),
    }

    if event.get('RequestType') == 'Delete':
        return {
            **resp,
            "Status": "SUCCESS",
        }

    execute_from_command_line(["./manage.py", "migrate"])
    return {
        **resp,
        "Status": 'SUCCESS',
        "Data": "Migration complete.",
    }
