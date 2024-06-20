from uuid import uuid4
import datetime

def generate_portal_run_id()->str:
        return f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}{str(uuid4())[:8]}"