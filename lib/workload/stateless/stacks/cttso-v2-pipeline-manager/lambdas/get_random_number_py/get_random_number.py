#!/usr/bin/env python3

"""
Get a random number
"""

# Imports
import random
from typing import Dict

# Globals
MAX_NUMBER = 60



def handler(event, context) -> Dict[str, int]:
    """
    Get a random number
    """

    return {
        "random_number": random.randint(0, MAX_NUMBER)
    }


# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler({}, None),
#             indent=4
#         )
#     )