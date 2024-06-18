#!/usr/bin/env python3

# Imports
from uuid import uuid4
import hashlib
from datetime import datetime
from typing import Dict


# Functions
def generate_portal_run_id() -> str:
    """
    Generate portal run id if it doesn't exist
    Returns:
    YYYYMMDDabcd1234
    """
    # Initialise hashlib
    h = hashlib.new('sha256')

    # Update with uuid4
    h.update(str(uuid4()).encode())

    return datetime.utcnow().strftime('%Y%m%d') + h.hexdigest()[:8]


def handler(event, context) -> Dict:
    return {"portal_run_id": generate_portal_run_id()}


#
# if __name__ == "__main__":
#     print(handler(None, None))
#     # {'portal_run_id': '202405233347b4b9'}
