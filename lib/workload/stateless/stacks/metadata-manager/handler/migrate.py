# -*- coding: utf-8 -*-
"""migrate lambda module

Convenience AWS lambda handler for Django database migration command hook
"""
import json
import logging
from django.core.management import execute_from_command_line

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context) -> dict[str, str]:
    logger.info(f"Processing event: {json.dumps(event, indent=4)}")

    resp = {
        "StackId": event.get('StackId'),
        "RequestId": event.get('RequestId'),
        "LogicalResourceId": event.get('LogicalResourceId'),
        "PhysicalResourceId": event.get("PhysicalResourceId")
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
        "Data": {"Message": "Migration complete."},
    }
