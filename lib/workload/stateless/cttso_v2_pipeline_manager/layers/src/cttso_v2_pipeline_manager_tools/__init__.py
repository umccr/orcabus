#!/usr/bin/env python

# Miscellaneous utility functions

# Imports
from uuid import uuid4
import hashlib
from datetime import datetime


# Functions
def generate_portal_run_id():
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
