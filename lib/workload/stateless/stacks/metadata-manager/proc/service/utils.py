import logging
import os
from django.core.management import call_command

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_model_history(minutes: int = None):
    """
    The function will clean history for which where models have a history feature enabled

    When django uses the `save()` function, history table might be populated despite no changes (e.g.
    update_or_create). The history feature provided by django-simple-history track all signal that django sends to
    save model thus create duplicates. This clean function will remove these duplicates and only retain changes.

    Ref: https://django-simple-history.readthedocs.io/en/latest/utils.html
    """
    logger.info(f'removing duplicate history records for the last {minutes} minutes if any')
    call_command("clean_duplicate_history", "--auto", minutes=minutes, stdout=open(os.devnull, 'w'))
