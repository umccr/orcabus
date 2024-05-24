#!/usr/bin/env python3

"""
Generate a uuid
"""

from uuid6 import uuid7
from typing import Dict


def handler(event, context) -> Dict:
    return {
        "uuid": str(uuid7())
    }


# if __name__ == "__main__":
#     print(handler(None, None))
#     # {'uuid': '018fa466-55cd-7d50-ad9f-27205203f435'}
