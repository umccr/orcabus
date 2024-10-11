#!/usr/bin/env python3

"""
Generate a portal run id
"""

# Imports
from datetime import timezone, datetime
import os


def handler(event, context):
    """
    Generate a portal run id
    """
    return {
        "portal_run_id": datetime.now(timezone.utc).strftime('%Y%m%d') + os.urandom(4).hex()
    }


# if __name__ == '__main__':
#     import json
#     print(json.dumps(handler(None, None), indent=4))
#
# # {
# #     "portal_run_id": "20240923e75c96f6"
# # }