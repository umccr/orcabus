#!/usr/bin/env python3

"""
Find complement dna/rna library

Ensure we have a tumor dna, normal dna and tumor rna library

Return library object (library_id, orcabus_id) for each library
"""

#!/usr/bin/env python3

"""
Given a library object and a list of complementary library objects, find a matching pair for the library object.

The library objects must match on 'workflow' and 'type' attributes, but must be the opposite phenotype.
"""

from typing import Dict, List, Tuple, Optional


def find_complement_library_pairs(library: Dict, complement_libraries: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
    """
    Given a library object and a list of complementary library objects, find a matching pair for the library object
    within the complement library list.
    :param library:
    :param complement_libraries:
    :return:
    """

    if library['type'].lower() == "wgs":
        # Get only
        dna_normal_libraries = list(
            filter(
                lambda lib_iter_: (
                    lib_iter_['type'].lower() == "wgs" and
                    lib_iter_['phenotype'] == 'normal'
                ),
                complement_libraries
            )
        )

        # Unlikely if we have just run oncoanalyser dna
        # FIXME - also handle duplicate cases
        if len(dna_normal_libraries) == 0:
            return None, None, None

        # Get the rna library
        rna_normal_libraries = list(
            filter(
                lambda lib_iter_: (
                    lib_iter_['type'].lower() == "rna" and
                    lib_iter_['phenotype'] == 'normal'
                ),
                complement_libraries
            )
        )

        # FIXME - also handle duplicate cases
        if len(rna_normal_libraries) == 0:
            return None, None, None

        return library, dna_normal_libraries[0], rna_normal_libraries[0]

    elif library['type'].lower() == "rna":
        # Get dna tumor library
        dna_tumor_libraries = list(
            filter(
                lambda lib_iter_: (
                    lib_iter_['type'].lower() == "wgs" and
                    lib_iter_['phenotype'] == 'tumor'
                ),
                complement_libraries
            )
        )

        if len(dna_tumor_libraries) == 0:
            return None, None, None

        # Get dna normal library
        dna_normal_libraries = list(
            filter(
                lambda lib_iter_: (
                    lib_iter_['type'].lower() == "wgs" and
                    lib_iter_['phenotype'] == 'normal'
                ),
                complement_libraries
            )
        )

        if len(dna_normal_libraries) == 0:
            return None, None, None

        return dna_tumor_libraries[0], dna_normal_libraries[0], library

    return None, None, None


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

    dna_tumor_library, dna_normal_library, rna_tumor_library = (
        find_complement_library_pairs(library_obj, complement_libraries)
    )

    if dna_tumor_library is None:
        return {
            'successful_pairing': False,
            'tumor_dna_library': None,
            'normal_dna_library': None,
            'tumor_rna_library': None
        }

    return {
        'successful_pairing': True,
        'tumor_dna_library': dna_tumor_library,
        'normal_dna_library': dna_normal_library,
        'tumor_rna_library': rna_tumor_library
    }
