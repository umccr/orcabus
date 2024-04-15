# -*- coding: utf-8 -*-
"""migrate lambda module

Convenience AWS lambda handler for Django database migration command hook
"""

from django.core.management import execute_from_command_line


def handler(event, context) -> str:
    execute_from_command_line(["./manage.py", "migrate"])
    return "Migration complete."
