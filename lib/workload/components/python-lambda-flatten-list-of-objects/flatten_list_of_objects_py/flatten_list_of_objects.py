#!/usr/bin/env python3

"""
Given a list of objects, flatten the list of objects into a single list.

[
  {
    "a": 1
  },
  {
    "b": 2
  }
]

To

{
  "a": 1,
  "b": 2
}
"""
from typing import Dict, List


def handler(event, context) -> Dict:
    """
    Flatten a list of objects
    :param event:
    :param context:
    :return:
    """

    # Get the list of objects
    object_list: List[Dict] = event.get("object_list")
    object_dict = {}

    # Update the new object list
    for object_iter in object_list:
        object_dict.update(object_iter)

    return {
        "flattened_object": object_dict
    }

# if __name__ == "__main__":
#   import json
#   print(
#     json.dumps(
#       handler(
#         {
#           "object_list": [
#             {
#               "a": 1
#             },
#             {
#               "b": 2
#             }
#           ]
#         },
#         None
#       ),
#       indent=4
#     )
#   )
#
#   # {
#   #     "flattened_object": {
#   #         "a": 1,
#   #         "b": 2
#   #     }
#   # }
