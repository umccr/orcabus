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
        # Need to both be of the same type
        if not library['type'] == complement_library['type']:
            continue

        # Need to be of different phenotypes
        if library['phenotype'] == complement_library['phenotype']:
            continue

        # Can be different workflows IF
        # The 'research' workflow is the tumor and the 'clinical' workflow is the normal
        # But do not allow clinical tumors to be matched with research normals
        # Or if they are the same workflow, but different phenotypes
        if (
            # Special case for research
            (
                (
                        library['workflow'] == 'research' and
                        complement_library['workflow'] == 'clinical'
                ) and (
                        library['phenotype'] == 'tumor' and
                        complement_library['phenotype'] == 'normal'
                )
            ) or
            # Complement case
            (
                (
                        library['workflow'] == 'clinical' and
                        complement_library['workflow'] == 'research'
                ) and (
                        library['phenotype'] == 'normal' and
                        complement_library['phenotype'] == 'tumor'
                )
            ) or
            # Standard clinical+clinical or research+research
            (
                (
                        library['workflow'] == complement_library['workflow']
                )
            )
        ):
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

    # Filter out empty complement libraries
    complement_libraries = list(
        filter(
            lambda comp_lib_iter_: (
                comp_lib_iter_ is not None and
                not comp_lib_iter_['orcabus_id'] == library_obj['orcabus_id']
            ),
            complement_libraries
        )
    )

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
