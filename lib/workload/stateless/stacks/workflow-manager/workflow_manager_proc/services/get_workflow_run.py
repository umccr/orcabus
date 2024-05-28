# import django

# django.setup()

# # --- keep ^^^ at top of the module
import datetime
from workflow_manager.models.workflow_run import WorkflowRun

default_time_window = datetime.timedelta(hours=1)

def handler(event, context):
    """event will be
    {
        portal_run_id: "",
        status: "",  # optional
        timestamp: "" # optional
        time_window: "" # currenty not used, defaults 1h
    }
    """
    print(f"Processing {event}, {context}")
    portal_run_id = event['portal_run_id']
    status = event.get('status', None)
    timestamp = event.get('timestamp', None)
    # time_window = event.get('time_window', None)  # FIXME: make configurable later?

    qs = WorkflowRun.objects.filter(
        portal_run_id = portal_run_id
    )
    if status:
        qs.filter(
            status = status
        )
    if timestamp:
        dt = datetime.datetime.fromisoformat(str(timestamp))
        start_t = dt - default_time_window
        end_t = dt + default_time_window
        qs.filter(
            timestamp__range=[start_t, end_t]
        )

    workflow_runs = []
    for w in qs.all():
        workflow_runs.append(w)

    return workflow_runs  # FIXME: need to deserialise in future
