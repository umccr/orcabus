import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    # Log the received event in CloudWatch
    logger.info("Starting webhook handler")
    logger.info(json.dumps(event))

    body = event.get("body", None)
    if body:
        logger.info(body)
        # TODO: forward according event to EventBus
        return {"statusCode": 200}
    else:
        return {"statusCode": 500, "message": "Internal server error"}
