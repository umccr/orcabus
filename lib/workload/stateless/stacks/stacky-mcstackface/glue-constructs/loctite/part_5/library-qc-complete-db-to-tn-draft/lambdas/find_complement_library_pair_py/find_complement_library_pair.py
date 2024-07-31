#!/usr/bin/env python3

"""
Given a library object and a list of complementary library objects, find a matching pair for the library object.

The library objects must match on 'workflow' and 'type' attributes, but must be the opposite phenotype.
"""

from typing import Dict, List


def find_complement_library_pair(library: Dict, complement_libraries: List[Dict]):
    """
    Given a library object and a list of complementary library objects, find a matching pair for the library object
    within the complement library list.
    :param library:
    :param complement_libraries:
    :return:
    """
    for complement_library in complement_libraries:
        if library['workflow'] == complement_library['workflow'] and library['type'] == complement_library['type']:
            if library['phenotype'] != complement_library['phenotype']:
                return library, complement_library
    return None, None


def handler(event, context):
    """
    Lambda handler function
    :param event:
    :param context:
    :return:
    """

    library_obj: Dict = event['library_obj']
    complement_libraries: List[Dict] = event['complementary_library_obj_list']

    library, complement_library = find_complement_library_pair(library_obj, complement_libraries)

    if library is None:
        return {
            'successful_pairing': False,
            'tumor_library': None,
            'normal_library': None
        }

    if library['phenotype'] == 'tumor':
        tumor_library = library
        normal_library = complement_library
    else:
        tumor_library = complement_library
        normal_library = library

    return {
        'successful_pairing': True,
        'tumor_library': tumor_library,
        'normal_library': normal_library
    }
