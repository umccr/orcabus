import logging

from sequence_run_manager_proc.services.v2_samplesheet_parser.util import HEADER_REGEX_MATCH, pascal_case_to_snake_case
from sequence_run_manager_proc.services.v2_samplesheet_parser.models import SampleSheetModel
logger = logging.getLogger(__name__)

def parse_samplesheet(samplesheet: str) -> dict:
    """
    Parse a samplesheet v2 into a JSON string
    https://help.connected.illumina.com/run-set-up/overview/sample-sheet-structure
    
    Args:
        samplesheet (str): The samplesheet content to parse
        
    Returns:
        str: JSON string of either validated model or raw parsed data
        
    Raises:
        ValueError: If CSV parsing fails
    
    input example:
    [Header]
    FileFormatVersion,2
    RunName,my-illumina-sequencing-run
    RunDescription,A test run
    InstrumentPlatform,NovaSeq 6000
    InstrumentType,NovaSeq

    [Reads]
    Read1Cycles,151
    Read2Cycles,151
    Index1Cycles,10
    Index2Cycles,10

    [BCLConvert_Settings]
    BarcodeMismatchesIndex1,1
    BarcodeMismatchesIndex2,1
    OverrideCycles,Y151;I10;I8N2;Y151
    CreateFastqForIndexReads,False
    NoLaneSplitting,False
    FastqCompressionFormat,gzip

    [BCLConvert_Data]
    Lane,Sample_ID,index,index2,Sample_Project
    1,MyFirstSample,AAAAAAAAAA,CCCCCCCC,SampleProject
    1,MySecondSample,GGGGGGGGGG,TTTTTTTT,SampleProject

    [Cloud_Data]
    Sample_ID,LibraryName
    MyFirstSample,MyFirstSample_AAAAAAAAAA_CCCCCCCC
    MySecondSample,MySecondSample_GGGGGGGGGG_TTTTTTTT
    
    output example:
    {
        "header": {
            "file_format_version": "2",
            "run_name": "my-illumina-sequencing-run",
            "run_description": "A test run", 
            "instrument_platform": "NovaSeq 6000",
            "instrument_type": "NovaSeq"
        },
        "Reads": {
            "Read1Cycles": 151,
            "Read2Cycles": 151, 
            "Index1Cycles": 10,
            "Index2Cycles": 10
        },
        "bclconvert_settings": {
            "barcode_mismatches_index_1": 1,
            "barcode_mismatches_index_2": 1,   
            "override_cycles": "Y151;I10;I8N2;Y151",
            "create_fastq_for_index_reads": False,
            "no_lane_splitting": False,
            "fastq_compression_format": "gzip"
        },
        "bclconvert_data": [
            {
                "lane": 1,
                "sample_id": "MyFirstSample",
                "index": "AAAAAAAAAA",
                "index2": "CCCCCCCC",
                "sample_project": "SampleProject"
            },
            {
                "lane": 1,
                "sample_id": "MySecondSample",
                "index": "GGGGGGGGGG",
                "index2": "TTTTTTTT",
                "sample_project": "SampleProject"
            }
        ]
    }
    """
    
    samplesheet_lines = samplesheet.split("\n")
    section_header = None
    section_data_dict = {}
    sample_sheet_data = {}
    
    try:
        # read through each line and group into sections
        for line in samplesheet_lines:
            # Strip ending of line
            line = line.strip()
            
            # Skip empty values
            if line == "":
                continue
            # Skip line if it's all commas
            if line.count(",") == len(line):
                continue
            
            # Check if line is a header
            if HEADER_REGEX_MATCH.match(line):
                section_header = pascal_case_to_snake_case(line.strip("[]"))
                section_data_dict[section_header] = []
                continue
            
            # Add line to section data
            section_data_dict[section_header].append(line)
    
        # parse and sanitise section data
        for section_header, section_data in section_data_dict.items():
            if section_header.endswith("_data"):
                keys = list(map(lambda x: pascal_case_to_snake_case(x.strip()), section_data[0].split(",")))
                sanitised_section_values = []
                for line in section_data[1:]:
                    values = line.split(",")
                    section_values = {}
                    for key, value in zip(keys, values):
                        section_values[key] = value if value != "" else None
                    sanitised_section_values.append(section_values)
                sample_sheet_data[section_header] = sanitised_section_values
            else:
                sample_sheet_data[section_header] = {}
                for line in section_data:
                    key, value = line.split(",")
                    sanitised_key = pascal_case_to_snake_case(key.strip())
                    sample_sheet_data[section_header][sanitised_key] = value if value != "" else None
        
        # Perform exception to Sequence model library_prep_kits and convert to a list
        if "sequencing" in sample_sheet_data.keys():
            if "library_prep_kits" in sample_sheet_data["sequencing"].keys():
                sample_sheet_data["sequencing"]["library_prep_kits"] = (
                    sample_sheet_data["sequencing"]["library_prep_kits"].split(";")
                )

        # map to models
        try:
            sample_sheet_model = SampleSheetModel(**sample_sheet_data)
            return sample_sheet_model.model_dump()
        except Exception as e:
            logger.error(f"Error parsing and validating samplesheet: {str(e)}")
            logger.debug(f"Sample sheet data: {sample_sheet_data}")
            return sample_sheet_data
    except Exception as e:
        # This is for CSV parsing errors - should be raised
        logger.error(f"CSV parsing error: {e}")
        raise ValueError(f"Failed to parse samplesheet: {str(e)}")

