

def to_camel_case_key_dict(data: dict) -> dict:
    """
    Convert dictionary keys from snake_case to camelCase.
    """
    def snake_to_camel(word):
        components = word.split('_')
        # We capitalize the first letter of each component except the first one
        # with the 'title' method and join them together.
        return components[0] + ''.join(x.title() for x in components[1:])

    new_data = {}
    for key, value in data.items():
        new_key = snake_to_camel(key)
        new_data[new_key] = value
    return new_data
