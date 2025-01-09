import pandas as pd

from src.errors import FileContentError, SimilarIndexError, SampleSheetHeaderError, SampleNameFormatError, \
    MetaDataError, OverrideCyclesError, GetMetaDataError
from src.logger import get_logger
from src.samplesheet import SampleSheet, check_sample_sheet_for_index_clashes, check_samplesheet_header_metadata, \
    get_years_from_samplesheet, check_metadata_correspondence, check_global_override_cycles, \
    check_internal_override_cycles

logger = get_logger()


def construct_sample_sheet(sample_sheet_path: str):
    """
    Constructing and parse sample sheet content.

    Return
    ----------
    sample_sheet : SampleSheet
        sample sheet data to be checked

    """

    try:
        return SampleSheet(sample_sheet_path)

    except:
        logger.error("Unable to parse SampleSheet from the given file.")
        raise FileContentError


def run_sample_sheet_content_check(sample_sheet):
    """
    Run check for the samplesheet.

    Parameters
    ----------
    sample_sheet : SampleSheet
        sample sheet data to be checked

    Return
    ----------
    error_message : str
        any error message that stops the check

    """
    logger.info("Check samplesheet content")

    # Run some consistency checks
    logger.info("Get all years of samples in samplesheets")
    years = get_years_from_samplesheet(sample_sheet)
    if len(list(years)) == 1:
        logger.info("SampleSheet contains IDs from year: {}".format(list(years)[0]))
    else:
        logger.info("SampleSheet contains IDs from {} years: {}".format(len(years), ', '.join(map(str, list(years)))))

    logger.info('----------check_sample_sheet_header_metadata----------')
    check_samplesheet_header_metadata(sample_sheet)
    logger.info('----------check_sample_sheet_for_index_clashes----------')
    check_sample_sheet_for_index_clashes(sample_sheet)


def run_sample_sheet_check_with_metadata(sample_sheet: SampleSheet, auth_header: str):
    """
    Run check for the sample sheet.

    Parameters
    ----------
    sample_sheet : SampleSheet
        sample sheet data to be checked
    auth_header : str
        JWT token to fetch on data-portal API

    Return
    ----------
    error_message : str
        any error message that stops the check

    """

    logger.info("Check sample sheet against metadata")

    # Run through checks with metadata integrate
    logger.info('----------set_metadata_by_library_id----------')
    sample_sheet.set_metadata_from_api(auth_header)

    logger.info('----------check_metadata_correspondence----------')
    check_metadata_correspondence(sample_sheet)

    # FIXME: This is not implemented yet (current metadata does not have override cycles)
    logger.info('----------check_global_override_cycles----------')
    check_global_override_cycles(sample_sheet)
    logger.info('----------check_internal_override_cycles----------')
    check_internal_override_cycles(sample_sheet)

    logger.info("Info on the value_counts of the sample sheet (by assay, type and override cycles)")
    sample_sheet_df = pd.DataFrame([{"assay": sample.library_series['assay'],
                                     "type": sample.library_series['type'],
                                     "override_cycles": sample.library_series['override_cycles']}
                                    for sample in sample_sheet])
    logger.info(f"Value Counts:\n{sample_sheet_df.value_counts()}")
