# -*- coding: utf-8 -*-
"""migrate lambda module

Convenience AWS lambda handler for Django database migration command hook
"""
import logging
from django.core.management import execute_from_command_line

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context) -> dict[str, str]:
    logger.info("Processing event:", event)

    resp = {
        "StackId": event.get('StackId'),
        "RequestId": event.get('RequestId'),
        "LogicalResourceId": event.get('LogicalResourceId'),
        "PhysicalResourceId": context.log_group_name,  # https://docs.aws.amazon.com/lambda/latest/dg/python-context
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
