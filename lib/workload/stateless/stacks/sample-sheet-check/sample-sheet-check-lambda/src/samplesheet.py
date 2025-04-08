#!/usr/bin/env python3

"""
Sample-sheet samplesheet to be used in the checker script
"""

# Standards
from copy import deepcopy
from typing import List

import pandas as pd
import collections
from scipy.spatial import distance

from src.logger import get_logger
from src.errors import SampleSheetFormatError, SampleDuplicateError, SampleNotFoundError, \
    ColumnNotFoundError, LibraryNotFoundError, MultipleLibraryError, GetMetaDataError, SimilarIndexError, \
    SampleSheetHeaderError, MetaDataError, InvalidColumnError, SampleNameFormatError, OverrideCyclesError, \
    ApiCallError
from src.globals import SAMPLE_REGEX_OBJS, SAMPLESHEET_REGEX_OBJS, OVERRIDE_CYCLES_OBJS, \
    MIN_INDEX_HAMMING_DISTANCE
from src.globals import METADATA_COLUMN_NAMES, REQUIRED_SAMPLE_SHEET_DATA_COLUMN_NAMES, \
    VALID_SAMPLE_SHEET_DATA_COLUMN_NAMES
from src.metadata import get_metadata_record_from_array_of_field_name

logger = get_logger()


class Sample:
    """
    Sample on the sequencer
    """

    # Initialise attributes
    def __init__(self, sample_id, sample_name, index, index2, lane, project):
        """
        Initialise the sample object
        :param sample_id:
        :param sample_name:
        :param index:
        :param index2:
        :param lane:
        :param project
        """

        # Corresponds to the Sample_ID column in the sample sheet
        # And Sample_ID (SampleSheet) in the metadata excel sheet
        self.unique_id = sample_id
        self.index = index  # The i7 index
        self.index2 = index2  # The i5 index - could be None if a single indexed flowcell
        self.lane = lane  # The lane of the sample
        self.project = project  # This may be useful at some point
        self.sample_name = sample_name

        # Initialise read cycles and override_cycles
        self.read_cycle_counts = []
        self.override_cycles = None

        # Initialise library
        self.sample_id = None
        self.library_id = None

        # Initialise year for easy usage
        self.year = None

        # Initialise library_df for easy reference
        self.library_series = None

        # Now calculate sample_id, library_id and year
        self.set_sample_id_and_library_id_from_unique_id()
        self.set_year_from_library_id()

        # Run checks on sample id and library id
        self.check_unique_library_id_format()
        self.check_library_id_format()
        self.check_sample_id_format()
        self.check_sample_name_format()

    def __str__(self):
        return self.unique_id

    def set_sample_id_and_library_id_from_unique_id(self):
        """
        From the unique_id, return the library id
        MDX200001_L2000001 to [MDX200001, L2000001]
        Use unique_id regex to ungroup each
        Assumes fullmatch check has already been done
        :return:
        """

        unique_id_regex_obj = SAMPLE_REGEX_OBJS["unique_id"].match(self.unique_id)

        # Check unique id regex match is not None
        if unique_id_regex_obj is None:
            logger.error(f"Could not split sample and library id from {self.unique_id}")
            raise SampleNameFormatError

        # Sample ID is the first group and the library ID is the second group
        self.sample_id = unique_id_regex_obj.group(1)
        self.library_id = unique_id_regex_obj.group(2)

    def check_sample_name_format(self):
        """
        Ensure that the sample name is not null
        :return:
        """
        if self.sample_name is None or self.sample_name == "":
            logger.error("Sample ID {} did not have corresponding Sample_Name".format(self.sample_id))
            raise SampleNameFormatError

        # Check if the Sample_Name column is the library_id from the Sample_ID column ignoring the "_topup" / "_rerun"
        clean_unique_id = SAMPLE_REGEX_OBJS["topup"].sub('', self.unique_id)
        clean_sample_name = SAMPLE_REGEX_OBJS["topup"].sub('', self.sample_name)
        if not clean_unique_id.endswith(clean_sample_name):
            logger.error(f"Sample_Name ({self.sample_name}) is not the libraryID defined in the "
                         f"Sample_ID ({self.unique_id}) format")
            raise SampleNameFormatError

    def check_sample_id_format(self):
        """
        Ensure that the sample id is of the expected format
        :return:
        """
        sample_regex_obj = SAMPLE_REGEX_OBJS["sample_id"].fullmatch(self.sample_id)
        if sample_regex_obj is None:
            logger.error("Sample ID {} did not match the expected regex".format(self.sample_id))
            raise SampleNameFormatError

    def check_library_id_format(self):
        """
        Ensure that the library id is of the expected format
        :return:
        """
        library_regex_obj = SAMPLE_REGEX_OBJS["library_id"].fullmatch(self.library_id)

        if library_regex_obj is None:
            logger.error("Library ID {} did not match the expected regex".format(self.library_id))
            raise SampleNameFormatError

    def check_unique_library_id_format(self):
        """
        Ensure that the sample id and the library id combined match the expected regex
        :return:
        """

        unique_regex_obj = SAMPLE_REGEX_OBJS["unique_id_full_match"].fullmatch(self.unique_id)

        if unique_regex_obj is None:
            logger.error("Sample / Library ID {} did not match the expected regex".format(self.unique_id))

    def set_year_from_library_id(self):
        """
        Get the year from the library id by appending 20 on the end
        :return:
        """
        year_re_match = SAMPLE_REGEX_OBJS.get("year").match(self.library_id)
        if year_re_match is None:
            logger.error("Could not get library ID from \"{}\"".format(self.library_id))
            raise SampleNameFormatError
        # Year is truncated with 20
        self.year = '20{}'.format(year_re_match.group(1))

    def set_override_cycles(self):
        """
        Extract from the library metadata sheet the override cycles count and set as sample attribute
        :return:
        """
        self.override_cycles = self.library_series["override_cycles"]

    def set_metadata_row_for_sample(self, metadata_df):
        """
        :param metadata_df: metadata data frame
        :return:
        """
        library_id_column_var = METADATA_COLUMN_NAMES["library_id"]
        sample_id_column_var = METADATA_COLUMN_NAMES["sample_id"]
        library_id_var = SAMPLE_REGEX_OBJS["topup"].sub('', self.library_id)
        sample_id_var = self.sample_id

        # Query for specific dataframe value
        library_row = metadata_df.loc[
            (metadata_df['library_id'] == library_id_var) & (metadata_df["sample_id"] == sample_id_var)]

        # Check result_df exist
        number_of_rows = len(library_row)
        if number_of_rows == 0:
            logger.error("Got no rows back for library id '{}' and sample id '{}'"
                         "in columns {} and {} respectively".format(library_id_var, sample_id_var,
                                                                    library_id_column_var, sample_id_column_var))
            raise LibraryNotFoundError

        # Check library_row is just one row
        if not number_of_rows == 1:
            logger.error("Got multiple rows back for library id '{}' and sample id '{}'"
                         "in columns {} and {} respectively".format(library_id_var, sample_id_var,
                                                                    library_id_column_var, sample_id_column_var))
            raise MultipleLibraryError

        # Set the library df
        self.library_series = library_row.squeeze()


class SampleSheet:
    """
    SampleSheet object
    """

    def __init__(self, samplesheet_path=None, header=None, reads=None, settings=None, data=None, samples=None):
        self.samplesheet_path = samplesheet_path
        self.header = header
        self.reads = reads
        self.settings = settings
        self.data = data
        self.samples = samples

        self.metadata_df = pd.DataFrame()

        # Ensure that header, reads, settings are all None or all Not None
        if not (self.header is None and self.reads is None and self.settings is None):
            if not (self.header is not None and self.reads is not None and self.settings is not None):
                logger.error("header, reads and settings configurations need to either all be set or all be 'None'")
                raise NotImplementedError
            else:
                settings_defined = True
        else:
            settings_defined = False

        # Check we haven't double defined the configuration settings
        if not (bool(self.samplesheet_path is not None) ^ settings_defined):
            """
            We can't have the samplesheet_path defined and the sections also defined
            """
            logger.error("Specify only the samplesheet path OR header, reads, settings")
            raise NotImplementedError
        # Check we haven't double defined the data settings
        elif not (
                bool(self.samplesheet_path is not None) ^ bool(self.samples is not None) ^ bool(self.data is not None)):
            """
            Only one of samplesheet_path and samples can be specified
            Can we confirm this is legit
            """
            logger.error("Specify only the samplesheet path OR data OR samples. The latter two options"
                         "will also need to have header, reads and settings defined")
            raise NotImplementedError

        # If there's a samplesheet path, we need to read it
        if self.samplesheet_path is not None:
            self.read()

    def read(self):
        """
        Read in the sample sheet object as a list of dicts
        :return:
        """
        with open(self.samplesheet_path, "r") as samplesheet_csv_h:
            # Read samplesheet in
            sample_sheet_sections = {}
            current_section = None
            current_section_item_list = []

            for line in samplesheet_csv_h.readlines():
                # Check if blank line
                if line.strip().rstrip(",") == "":
                    continue
                # Check if the current line is a header
                header_match_obj = SAMPLESHEET_REGEX_OBJS["section_header"].match(line.strip())
                if header_match_obj is not None and current_section is None:
                    # First line, don't need to write out previous section to obj
                    # Set current section to first group
                    current_section = header_match_obj.group(1)
                    current_section_item_list = []
                elif header_match_obj is not None and current_section is not None:
                    # A header further down, write out previous section and then reset sections
                    sample_sheet_sections[current_section] = current_section_item_list
                    # Now reset sections
                    current_section = header_match_obj.group(1)
                    current_section_item_list = []
                # Make sure the first line is a section
                elif current_section is None and header_match_obj is None:
                    logger.error("Top line of csv was not a section header. Exiting")
                    raise SampleSheetFormatError
                else:  # We're in a section
                    if not current_section == "Data":
                        # Strip trailing slashes from line
                        current_section_item_list.append(line.strip().rstrip(","))
                    else:
                        # Don't strip trailing slashes from line
                        current_section_item_list.append(line.strip())

            # Write out the last section
            sample_sheet_sections[current_section] = current_section_item_list

        # Now iterate through sections and map them to the appropriate objects
        for section_name, section_str_list in sample_sheet_sections.items():
            if section_name == "Header":
                # Convert to dict
                self.header = {line.split(",", 1)[0]: line.split(",", 1)[-1]
                               for line in section_str_list}
            elif section_name == "Settings":
                # Convert to dict
                self.settings = {line.split(",", 1)[0]: line.split(",", 1)[-1]
                                 for line in section_str_list}
            elif section_name == "Reads":
                # List type
                self.reads = section_str_list
            elif section_name == "Data":
                # Convert to dataframe
                self.data = pd.DataFrame(columns=section_str_list[0].split(","),
                                         data=[row.split(",") for row in
                                               section_str_list[1:]])
                # Ensure each of the required SAMPLE_SHEET_DATA_COLUMNS exists
                for column in REQUIRED_SAMPLE_SHEET_DATA_COLUMN_NAMES["v1"]:
                    if column not in self.data.columns.tolist():
                        logger.error("Could not find column \"{}\" in samplesheet".format(column))
                        raise ColumnNotFoundError
                # Ensure each of the columns are valid columns
                for column in self.data.columns.tolist():
                    if column not in VALID_SAMPLE_SHEET_DATA_COLUMN_NAMES["v1"]:
                        logger.error("Could not find column \"{}\" in samplesheet".format(column))
                        raise InvalidColumnError
                # Strip Ns from index and index2
                self.data['index'] = self.data['index'].apply(lambda x: x.rstrip("N"))
                if 'index2' in self.data.columns.tolist():
                    self.data['index2'] = self.data['index2'].apply(lambda x: x.rstrip("N"))
                # TO then also add sample attributes
                # Write out each sample
                self.convert_data_to_samples()
            else:
                # We're not familiar with how to handle this section
                raise NotImplementedError

    def convert_data_to_samples(self):
        """
        Take the data attribute to create a samples objects
        :return:
        """
        # Ensure this function has not been called inappropriately
        if self.data is None:
            logger.error("Tried to convert data attribute to samples object when data wasn't defined")
            raise ValueError

        if self.samples is None:
            self.samples = []

        for row_index, sample_row in self.data.iterrows():
            # Set default lane to 1, so we can still compare indexes across
            lane = sample_row["Lane"] if "Lane" in sample_row.keys() else 1

            index2 = sample_row["index2"] if "index2" in sample_row.keys() else None
            project = sample_row["Sample_Project"] if "Sample_Project" in sample_row.keys() else None

            self.samples.append(
                Sample(
                    lane=lane,
                    sample_name=sample_row["Sample_Name"],
                    sample_id=sample_row["Sample_ID"],
                    index=sample_row["index"],
                    index2=index2,
                    project=project
                )
            )

    def add_sample(self, new_sample_to_add):
        """
        Add sample to the list of samples
        :param new_sample_to_add:
        :return:
        """
        for sample in self.samples:
            if sample.id == new_sample_to_add.id:
                logger.error("Sample with ID: {} already exists in sample sheet".format(sample.id))
                raise SampleDuplicateError
        self.samples.append(new_sample_to_add)

    def remove_sample(self, sample_id_to_remove):
        """
        Remove sample with this Sample_ID
        :param sample_id_to_remove:
        :return:
        """
        for sample in self.samples:
            if sample.id == sample_id_to_remove:
                sample_to_remove = sample
                break
        else:
            logger.error("Could not find sample {} when removing sample from sample sheet".format(sample_id_to_remove))
            raise SampleNotFoundError

        self.samples.remove(sample_to_remove)

    def get_lanes(self):
        """
        Iterate through samples and get the set of lanes in the samples
        :return:
        """
        lanes = set()

        # For the purposes of testing, we'll just return '1' if lane is not specified
        if "Lane" not in self.data.columns.tolist():
            logger.info("Attempting to get 'lanes' but no lanes defined, "
                        "returning set(1) for purpose of checking indexes")
            return {1}

        for sample in self:
            lanes.add(sample.lane)

        return lanes

    def write(self, samplesheet_h):
        """
        Write samplesheet to file handle
        :param samplesheet_h:
        :return:
        """
        # Write out header
        samplesheet_h.write("[Header]\n")
        samplesheet_h.write("\n".join(map(str, ["{},{}".format(key, value)
                                                for key, value in self.header.items()])))
        # Add new line before the next section
        samplesheet_h.write("\n\n")
        # Write out reads
        samplesheet_h.write("[Reads]\n")
        samplesheet_h.write("\n".join(self.reads))
        # Add new line before the next section
        samplesheet_h.write("\n\n")
        # Write out settings
        samplesheet_h.write("[Settings]\n")
        samplesheet_h.write("\n".join(map(str, ["{},{}".format(key, value)
                                                for key, value in self.settings.items()])))
        # Add new line before the next section
        samplesheet_h.write("\n\n")
        # Write out data
        samplesheet_h.write("[Data]\n")
        self.data.to_csv(samplesheet_h, index=False, header=True, sep=",")
        # Add final new line
        samplesheet_h.write("\n")

    def check_sample_uniqueness(self):
        """
        Ensure all samples are unique
        :return:
        """

        for s_i, sample in self.samples:
            for s2_i, sample2 in self.samples:
                # Check we already haven't done this comparison
                if s_i >= s2_i:
                    continue
                if sample.id == sample2.id:
                    logger.error("Found two samples with the same id: '{}'".format(sample.id))
                    raise SampleDuplicateError

    def __iter__(self):
        yield from self.samples

    def set_metadata_from_api(self, auth_header):
        library_id_array = []

        for sample in self:

            # check that the primary library for the topup exists
            if SAMPLE_REGEX_OBJS["topup"].search(sample.library_id) is not None:
                logger.info("{} is a top up sample. Investigating the previous sample".format(sample.unique_id))
                orig_unique_id = SAMPLE_REGEX_OBJS["topup"].sub('', sample.unique_id)
                unique_id_regex_obj = SAMPLE_REGEX_OBJS["unique_id"].match(orig_unique_id)

                # Sample ID is the first group and the library ID is the second group
                topup_sample_id = unique_id_regex_obj.group(1)
                topup_library_id = unique_id_regex_obj.group(2)
                # Appending these original sample/library id to the search query
                library_id_array.append(topup_library_id)
            else:
                library_id_array.append(sample.library_id)

        try:
            metadata_response = get_metadata_record_from_array_of_field_name(auth_header=auth_header,
                                                                             field_name='library_id',
                                                                             value_list=library_id_array)
        except Exception as e:
            raise ApiCallError("Fail to fetch metadata api for library id in the sample sheet")

        # Convert api result to panda dataframe
        # Replicate what the old portal does
        metadata_response = [
            {
                "library_id": metadata["libraryId"],
                "sample_id": metadata["sample"]["sampleId"],
                "override_cycles": metadata["overrideCycles"],
                "assay": metadata["assay"],
                "type": metadata["type"],
                "subject_id": metadata["subject"]["subjectId"],
            }
            for metadata in metadata_response
        ]
        self.metadata_df = pd.json_normalize(metadata_response)

        has_error = False
        error_samples = []
        metadata_df = self.metadata_df

        for sample in self.samples:
            try:
                sample.set_metadata_row_for_sample(metadata_df=metadata_df)
            except LibraryNotFoundError:
                logger.error("Error trying to find library id in tracking sheet for sample {}".format(sample.sample_id))
                error_samples.append(sample.sample_id)
                has_error = True
            except MultipleLibraryError:
                logger.error("Got multiple rows from tracking sheet for sample {}".format(sample.sample_id))
                error_samples.append(sample.sample_id)
                has_error = True
            except ApiCallError:
                logger.error("API call fail")
                has_error = True
            else:
                # Now we can set other things that may need to be done
                # Once we can confirm the metadata
                sample.set_override_cycles()

        if has_error:
            raise GetMetaDataError("The following samples had issues - {}".format(", ".join(map(str, error_samples))))


def get_years_from_samplesheet(samplesheet):
    """
    Get a unique list of years used.
    Tells us which metadata sheets we'll need to access
    :param samplesheet:  Samplesheet object
    :return:
    """
    years = set()
    for sample in samplesheet:
        years.add(sample.year)
    return years


def check_samplesheet_header_metadata(samplesheet):
    """
    # Check that Assay and Experiment Name are defined in the SampleSheet header
    :param samplesheet:
    :return:
    """
    logger.info("Checking SampleSheet metadata")
    has_error = False
    required_keys = ["Assay", "Experiment Name"]

    for key in required_keys:
        if samplesheet.header.get(key, None) is None:
            logger.error("{} not defined in Header!".format(key))
            has_error = True

    if has_error:
        raise SampleSheetHeaderError

    return


def check_metadata_correspondence(samplesheet):
    """
    Checking sample sheet data against metadata df
    :param samplesheet:
    :return:
    """
    logger.info("Checking SampleSheet data against metadata")
    has_error = False

    for sample in samplesheet:
        # exclude 10X samples for now, as they usually don't comply
        if sample.library_series["type"] == '10X':
            logger.debug("Not checking metadata columns as this sample is '10X'")
            continue

        # check presence of subject ID
        if sample.library_series["subject_id"] == '':
            logger.error(f"No subject ID for {sample.sample_id}")
            raise SampleNotFoundError

        # check that the primary library for the topup exists
        if SAMPLE_REGEX_OBJS["topup"].search(sample.library_id) is not None:
            logger.info("{} is a top up sample. Investigating the previous sample".format(sample.unique_id))
            orig_unique_id = SAMPLE_REGEX_OBJS["topup"].sub('', sample.unique_id)
            try:
                # Recreate the original sample object
                orig_sample = Sample(
                    sample_id=orig_unique_id,
                    sample_name=sample.sample_name,
                    index=None,
                    index2=None,
                    lane=None,
                    project=None
                )
                # Try get metadata for sample row
                orig_sample.set_metadata_row_for_sample(metadata_df=samplesheet.metadata_df)
            except LibraryNotFoundError:
                logger.error("Could not find library of original sample")
                has_error = True
            except MultipleLibraryError:
                logger.error("It seems that there is multiple libraries for the original sample")
                has_error = True
            except ApiCallError:
                logger.error("API call fails")
                has_error = True

    if not has_error:
        return
    else:
        raise MetaDataError


def check_sample_sheet_for_index_clashes(samplesheet):
    """
    Ensure that two given indexes are not within one hamming distance of each other
    :param samplesheet:
    :return:
    """
    logger.debug("Checking SampleSheet for index clashes")
    has_error = False

    lanes = samplesheet.get_lanes()

    for lane in lanes:
        for s_i, sample in enumerate(samplesheet.samples):
            # Ensures samples are in the same lane
            if not sample.lane == lane:
                continue
            logger.debug(f"Comparing indexes of sample {sample}")
            for s2_i, sample_2 in enumerate(samplesheet.samples):
                # Reset for each sample we're comparing against
                sample_has_i7_error = False
                # Ensures samples are in the same lane
                if not sample_2.lane == lane:
                    continue
                # Ensures we only do half of the n^2 logic.
                if s2_i <= s_i:
                    # We've already done this comparison
                    # OR they're the same sample
                    continue

                logger.debug(f"Checking indexes of sample {sample} against {sample_2}")
                if sample.unique_id == sample_2.unique_id:
                    # We're testing the sample on itself, next!
                    continue

                # i7 check
                # Strip i7 to min length of the two indexes
                try:
                    compare_two_indexes(sample.index, sample_2.index)
                except SimilarIndexError:
                    # Not a failure - we might have different i5 indexes for the sample
                    logger.debug("i7 indexes {} and {} are too similar to run in the same lane".format(sample.index,
                                                                                                       sample_2.index))
                    logger.debug("This may be okay if i5 indexes are different enough")
                    sample_has_i7_error = True

                # We may not have an i5 index - continue on to next sample if so
                if sample.index2 is None or sample_2.index2 is None:
                    # If the i7 was too close then this is a fail
                    if sample_has_i7_error:
                        logger.error("i7 indexes {} and {} are too similar to run in the same lane".format(sample.index,
                                                                                                           sample_2.index))
                        has_error = True
                    continue

                # i5 check
                # Strip i5 to min length of the two indexes
                try:
                    compare_two_indexes(sample.index2, sample_2.index2)
                except SimilarIndexError:
                    logger.debug("i5 indexes {} and {} are too similar to run in the same lane."
                                 "This might be okay if i7 indexes are different enough".format(sample.index2,
                                                                                                sample_2.index2))
                    if sample_has_i7_error:
                        logger.error("i7 indexes {} and {} are too similar to run in the same lane"
                                     "with i5 indexes {} and {} are too similar to run in the same lane ".format(
                            sample.index,
                            sample_2.index,
                            sample.index2,
                            sample_2.index2)
                        )
                        has_error = True

    if not has_error:
        return
    else:
        raise SimilarIndexError


def check_internal_override_cycles(samplesheet):
    """
    For each sample in the samplesheet, compare a given samples override cycles attributes with those
    of the indexes of the samples.
    i.e
    If the sample has the override cycles Y151;I8;I8;Y151, we should expect the non-N lengths of i7 and i5 to both be 8.
    :param samplesheet:
    :return:
    """
    for sample in samplesheet:
        # Check override cycles attribute exists
        if not sample.override_cycles:
            logger.warning("Could not find override cycles for sample \"{}\"".format(sample.unique_id))
            continue
        index_count = 0
        for cycle_set in sample.override_cycles.split(";"):
            # Makes sure that the cycles completes a full match
            if OVERRIDE_CYCLES_OBJS["indexes"].match(cycle_set) is None:
                logger.debug("Not an index cycle, skipping")
                continue
            # Get the length of index
            index_length = int(OVERRIDE_CYCLES_OBJS["indexes"].match(cycle_set).group(1).replace("I", ""))
            index_count += 1
            # Get index valuex
            if index_count == 1:
                # Check against sample's i7 value
                i7_length = len(sample.index.replace("N", ""))
                if not i7_length == index_length:
                    logger.warning(f"Sample '{sample.sample_id}' override cycle value '{sample.override_cycles}' "
                                   f"does not match sample i7 '{sample.index}")
            elif index_count == 2 and sample.index2 is not None and not sample.index2 == "":
                # Check against samples' i5 value
                i5_length = len(sample.index2.replace("N", ""))
                if not i5_length == index_length:
                    logger.warning(f"Sample '{sample.sample_id}' override cycle value '{sample.override_cycles}' "
                                   f"does not match sample i5 '{sample.index2}")
        # Make sure that if sample.index2 is not None but the override cycles count
        # only made it to '1' then we throw a warning
        if index_count == 1 and sample.index2 is not None and not sample.index2 == "":
            logger.warning(f"Override cycles '{sample.override_cycles}' suggests only one index "
                           f"but sample '{sample.sample_id}' has a second index '{sample.index2}'")


def check_global_override_cycles(samplesheet) -> List:
    """
    Check that the override cycles exists,
    matches the reads entered in the samplesheet
    and is consistent with all other samples in the sample sheet.
    :param samplesheet:
    :return:
    """
    for sample in samplesheet:
        # We've already initialised this attribute
        if not len(sample.read_cycle_counts) == 0:
            continue
        # for Y151;I8N2;I8N2;Y151 to ["Y151", "I8N2", "I8N2", "Y151"]
        if not sample.override_cycles:
            logger.warning("Could not find override cycles for sample \"{}\"".format(sample.unique_id))
            continue
        for cycle_set in sample.override_cycles.split(";"):
            # Makes sure that the cycles completes a fullmatch
            if OVERRIDE_CYCLES_OBJS["cycles_full_match"].fullmatch(cycle_set) is None:
                logger.error("Couldn't interpret override cycles section {} from {}".format(
                    cycle_set, sample.override_cycles
                ))
            read_cycles_sum = 0
            # Run regex over each set
            for re_match in OVERRIDE_CYCLES_OBJS["cycles"].findall(cycle_set):
                # re_match is a tuple like ('Y', '151') or ('N', '')
                if re_match[-1] == "":
                    read_cycles_sum += 1
                else:
                    read_cycles_sum += int(re_match[-1])
            sample.read_cycle_counts.append(read_cycles_sum)
    # Now we ensure all samples have the same read_cycle counts
    num_read_index_per_sample = set([len(sample.read_cycle_counts)
                                     for sample in samplesheet
                                     if not len(sample.read_cycle_counts) == 0])
    # Check the number of segments for each section are even the same
    if len(num_read_index_per_sample) > 1:
        logger.error("Found an error with override cycles matches")
        for num_read_index in num_read_index_per_sample:
            samples_with_this_num_read_index = [sample.sample_id
                                                for sample in samplesheet
                                                if len(sample.read_cycle_counts) == num_read_index]
            logger.error("The following samples have {} read/index sections: {}".
                         format(num_read_index, ", ".join(map(str, samples_with_this_num_read_index))))
        raise OverrideCyclesError
    elif len(num_read_index_per_sample) == 0:
        logger.error("Found no override cycles matches")
        raise OverrideCyclesError
    else:
        logger.info("Override cycles check 1/2 complete - "
                    "All samples have the correct number of override cycles sections - {}".
                    format(list(num_read_index_per_sample)[0]))

    # For each segment - check that the counts are the same
    section_cycle_counts = []
    for read_index in range(list(num_read_index_per_sample)[0]):
        num_cycles_in_read_per_sample = set([sample.read_cycle_counts[read_index]
                                             for sample in samplesheet
                                             if not len(sample.read_cycle_counts) == 0])
        if len(num_cycles_in_read_per_sample) > 1:
            logger.error("Found an error with override cycles matches for read/index section {}".format(read_index + 1))
            for num_cycles in num_cycles_in_read_per_sample:
                samples_with_this_cycle_count_in_this_read_index_section = \
                    [sample.sample_id
                     for sample in samplesheet
                     if sample.read_cycle_counts[read_index] == num_cycles]
                logger.error("The following samples have this this read count for this read index section: {}\n"
                             "CycleCount: {}\n"
                             "Samples: {}".
                             format(read_index + 1,
                                    num_cycles,
                                    ", ".join(map(str, samples_with_this_cycle_count_in_this_read_index_section))))
            raise OverrideCyclesError
        else:
            section_cycle_counts.append(list(num_cycles_in_read_per_sample)[0])
    else:
        logger.info("Override cycles check 2/2 complete - "
                    "All samples have the identical number of cycles per section - \"{}\"".
                    format(", ".join(map(str, section_cycle_counts))))

    return section_cycle_counts


def compare_two_indexes(first_index, second_index):
    """
    Ensure that the hamming distance between the two indexes
    is more than 1
    If one index is longer than the other - strip the longer one from the right
    # scipy.spatial.distance.hamming
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.hamming.html
    :param first_index:
    :param second_index:
    :return:
    """

    min_index_length = min(len(first_index), len(second_index))
    first_index = first_index[0:min_index_length]
    second_index = second_index[0:min_index_length]

    # Ensure that both the indexes are the same length
    if not len(first_index) == len(second_index):
        logger.error("Index lengths {} and {} are not the same".format(
            first_index, second_index
        ))
        raise SimilarIndexError

    # hamming distance returns a float - we then multiple this by the index length
    h_float = distance.hamming(list(first_index), list(second_index))

    if not h_float * min_index_length >= MIN_INDEX_HAMMING_DISTANCE:
        logger.debug("Indexes {} and {} are too similar".format(first_index, second_index))
        raise SimilarIndexError
    else:
        return


def get_grouped_samplesheets(samplesheet):
    """
    Get samples sorted by their override-cycles metric.
    Write out each samplesheet.
    :param samplesheet:
    :return:
    """
    grouped_samplesheets = collections.defaultdict()

    override_cycles_list = set([sample.override_cycles
                                for sample in samplesheet])

    for override_cycles in override_cycles_list:
        samples_unique_ids_subset = [sample.unique_id
                                     for sample in samplesheet
                                     if sample.override_cycles == override_cycles]

        # Create new samplesheet from old sheet
        override_cycles_samplesheet = deepcopy(samplesheet)

        # Truncate data
        override_cycles_samplesheet.data = override_cycles_samplesheet.data. \
            query("Sample_ID in @samples_unique_ids_subset")

        # Ensure we haven't just completely truncated everything
        if override_cycles_samplesheet.data.shape[0] == 0:
            logger.error("Here are the list of sample ids "
                         "that were meant to have the Override cycles setting \"{}\": {}".format(
                override_cycles, ", ".join(map(str, samples_unique_ids_subset))))
            logger.error("We accidentally filtered our override cycles samplesheet to contain no samples")
            raise ValueError

        # Append OverrideCycles setting to Settings in Samplesheet
        override_cycles_samplesheet.settings["OverrideCycles"] = override_cycles

        # Append SampleSheet to list of grouped sample sheets
        grouped_samplesheets[override_cycles] = override_cycles_samplesheet

    return grouped_samplesheets
