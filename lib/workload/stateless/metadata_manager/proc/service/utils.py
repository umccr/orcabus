import logging

from django.core.management import call_command

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_model_history():
    """
    The function will clean history for which where models have a history feature enabled

    When django uses the `save()` function, history table might be populated despite no changes. The history
    feature provided by django-simple-history track all signal that django sends so history table may have a lot of
    duplicates. This clean function will remove these duplicates and only retain changes.
    """
    logger.info('removing duplicate history records')
    call_command("clean_duplicate_history", "--auto")
    logger.info('remove duplicated history completed')
