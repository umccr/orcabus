from django.db.models import enums


def get_value_from_human_readable_label(choices: enums.ChoicesType, human_readable: str) -> str:
    """
    Convert human-readable enum choices to the value of its stored model if exist
    """
    for choice in choices:
        if choice[1] == human_readable:
            return choice[0]
    return human_readable
