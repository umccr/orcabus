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

    command = event.get("command", None)
    args = event.get("args", [])

    whitelist_command = ["clean_duplicated_libraries"]

    if command not in whitelist_command:
        raise ValueError(f"Command {command} not accepted")


    res = execute_from_command_line(["./manage.py", command, *args])

    return res
