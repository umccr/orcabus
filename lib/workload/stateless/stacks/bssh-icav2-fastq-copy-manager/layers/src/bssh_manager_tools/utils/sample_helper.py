#!/usr/bin/env python3

# Standard imports
from typing import Dict
import pandas as pd
from pathlib import Path

# Wrapica imports
from wrapica.enums import DataType
from wrapica.project_data import (
    convert_project_id_and_data_path_to_icav2_uri
)


def get_sample_id_path_prefix_from_bssh_datasets_dict(
    sample_id: str,
    lane: int,
    datasets_dict: Dict
) -> Path:
    """
    From the DataSets dict, collect the sample_id as a key and then retunr the path attribute

    :param sample_id:
    :param datasets_dict:
    :param lane:

    :return:
    """
    return Path(datasets_dict.get(sample_id + f"_L{lane}").get('Path'))


def get_fastq_list_paths_from_bssh_output_and_fastq_list_csv(
    fastq_list_pd: pd.DataFrame,
    bssh_output_dict: Dict,
    project_id: str,
    run_output_path: Path
) -> pd.DataFrame:
    """
    Takes the SampleSheet.Samples key for bssh output dict and convert into a pandas DataFrame,

    fastq_list_pd:

    RGID,RGSM,RGLB,Lane,Read1File,Read2File
    CCGCGGTT.CTAGCGCT.1,TSPF-NA12878-10B-Rep1,UnknownLibrary,1,./TSPF-NA12878-10B-Rep1_S1_L001_R1_001.fastq.gz,./TSPF-NA12878-10B-Rep1_S1_L001_R2_001.fastq.gz
    AGTTCAGG.TCTGTTGG.1,TSPF-NA12878-10B-Rep2,UnknownLibrary,1,./TSPF-NA12878-10B-Rep2_S2_L001_R1_001.fastq.gz,./TSPF-NA12878-10B-Rep2_S2_L001_R2_001.fastq.gz
    TAATACAG.GTGAATAT.1,TSPF-NA12878-10B-Rep3,UnknownLibrary,1,./TSPF-NA12878-10B-Rep3_S3_L001_R1_001.fastq.gz,./TSPF-NA12878-10B-Rep3_S3_L001_R2_001.fastq.gz


    bssh_output_dict:
    {
      'Datasets': {
        'BCL Convert Reports': {
          'Name': 'BCL Convert Reports',
          'ProjectRef': 'OutputProject',
          'BioSampleInputRef': [],
          'Attributes': {},
          'Path': 'output/Reports',
          'Type': 'common.files',
          'Properties': [
            {
              'Content': 'report.html',
              'Type': 'string',
              'Name': 'ReportPath'
            }
          ]
        },
        'TSPF-NA12878-10B-Rep1_L1': {
          'Name': 'TSPF-NA12878-10B-Rep1_L1',
          'ProjectRef': 'OutputProject',
          'BioSampleInputRef': [
            'TSPF-NA12878-10B-Rep1'
          ],
          'Attributes': {
            'common_fastq': {
              'TotalReadsRaw': 0,
              'TotalReadsPF': 935644552,
              'IsPairedEnd': True,
              'MaxLengthRead2': 151,
              'MaxLengthRead1': 151,
              'TotalClustersRaw': 0,
              'TotalClustersPF': 467822276
            }
          },
          'Path': 'output/Samples/Lane_1/TSPF-NA12878-10B-Rep1',  // pragma: allowlist secret
          'Type': 'common.fastq',
          'Properties': [
            {
              'Content': '1',
              'Type': 'string',
              'Name': 'BaseSpace.Internal.FastqLaneNumber',
              'Description': 'The lane from which the fastq dataset is derived'
            }
          ]
        },
        'BCL Convert Logs': {
          'Name': 'BCL Convert Logs',
          'ProjectRef': 'OutputProject',
          'BioSampleInputRef': [],
          'Path': 'logs',
          'Attributes': {},
          'Type': 'common.files'
        },
        'TSPF-NA12878-10B-Rep3_L1': {
          'Name': 'TSPF-NA12878-10B-Rep3_L1',
          'ProjectRef': 'OutputProject',
          'BioSampleInputRef': [
            'TSPF-NA12878-10B-Rep3'
          ],
          'Attributes': {
            'common_fastq': {
              'TotalReadsRaw': 0,
              'TotalReadsPF': 907298290,
              'IsPairedEnd': True,
              'MaxLengthRead2': 151,
              'MaxLengthRead1': 151,
              'TotalClustersRaw': 0,
              'TotalClustersPF': 453649145
            }
          },
          'Path': 'output/Samples/Lane_1/TSPF-NA12878-10B-Rep3',  // pragma: allowlist secret
          'Type': 'common.fastq',
          'Properties': [
            {
              'Content': '1',
              'Type': 'string',
              'Name': 'BaseSpace.Internal.FastqLaneNumber',
              'Description': 'The lane from which the fastq dataset is derived'
            }
          ]
        },
        'TSPF-NA12878-10B-Rep2_L1': {
          'Name': 'TSPF-NA12878-10B-Rep2_L1',
          'ProjectRef': 'OutputProject',
          'BioSampleInputRef': [
            'TSPF-NA12878-10B-Rep2'
          ],
          'Attributes': {
            'common_fastq': {
              'TotalReadsRaw': 0,
              'TotalReadsPF': 900467320,
              'IsPairedEnd': True,
              'MaxLengthRead2': 151,
              'MaxLengthRead1': 151,
              'TotalClustersRaw': 0,
              'TotalClustersPF': 450233660
            }
          },
          'Path': 'output/Samples/Lane_1/TSPF-NA12878-10B-Rep2',  // pragma: allowlist secret
          'Type': 'common.fastq',
          'Properties': [
            {
              'Content': '1',
              'Type': 'string',
              'Name': 'BaseSpace.Internal.FastqLaneNumber',
              'Description': 'The lane from which the fastq dataset is derived'
            }
          ]
        }
      },
      'OutputVersion': '0.5.41',
      'BioSamples': {
        'TSPF-NA12878-10B-Rep1': {
          'UserSampleId': 'TSPF-NA12878-10B-Rep1',
          'ProjectRef': 'OutputProject',
          'Id': None,
          'Properties': []
        },
        'TSPF-NA12878-10B-Rep2': {
          'UserSampleId': 'TSPF-NA12878-10B-Rep2',
          'ProjectRef': 'OutputProject',
          'Id': None,
          'Properties': []
        },
        'TSPF-NA12878-10B-Rep3': {
          'UserSampleId': 'TSPF-NA12878-10B-Rep3',
          'ProjectRef': 'OutputProject',
          'Id': None,
          'Properties': []
        }
      },
      'SampleSheet': {
        'Samples': [
          {
            'Index2Name': 'AGCGCTAG',
            'CloudData': {
              'LibraryName': None,
              'DataAggregationGroup': '',
              'SampleId': 'TSPF-NA12878-10B-Rep1'
            },
            'IndexName': 'CCGCGGTT',
            'Name': 'TSPF-NA12878-10B-Rep1',
            'IndexSequence': 'CCGCGGTT',
            'SampleProject': 'bssh_aps2-sh-prod_3593591',
            'SampleID': 'TSPF-NA12878-10B-Rep1',
            'IndexSequence2': 'AGCGCTAG'
          },
          {
            'Index2Name': 'CCAACAGA',
            'CloudData': {
              'LibraryName': None,
              'DataAggregationGroup': '',
              'SampleId': 'TSPF-NA12878-10B-Rep2'
            },
            'IndexName': 'AGTTCAGG',
            'Name': 'TSPF-NA12878-10B-Rep2',
            'IndexSequence': 'AGTTCAGG',
            'SampleProject': 'bssh_aps2-sh-prod_3593591',
            'SampleID': 'TSPF-NA12878-10B-Rep2',
            'IndexSequence2': 'CCAACAGA'
          },
          {
            'Index2Name': 'ATATTCAC',
            'CloudData': {
              'LibraryName': None,
              'DataAggregationGroup': '',
              'SampleId': 'TSPF-NA12878-10B-Rep3'
            },
            'IndexName': 'TAATACAG',
            'Name': 'TSPF-NA12878-10B-Rep3',
            'IndexSequence': 'TAATACAG',
            'SampleProject': 'bssh_aps2-sh-prod_3593591',
            'SampleID': 'TSPF-NA12878-10B-Rep3',
            'IndexSequence2': 'ATATTCAC'
          }
        ]
      },
      'IsReAnalysis': True,
      'Properties': [],
      'Projects': {
        'OutputProject': {
          'Name': 'bssh_aps2-sh-prod_3593591'
        }
      }
    }

    :param fastq_list_pd: pandas dataframe of fastq list csv
    :param bssh_output_dict: dictionary of bssh output

    :return Returns the paths to the fastq files for each sample id and lane
    """

    fastq_list_pd["sample_prefix"] = fastq_list_pd.apply(
        lambda row: get_sample_id_path_prefix_from_bssh_datasets_dict(
                sample_id=row["RGSM"],
                lane=row["Lane"],
                datasets_dict=bssh_output_dict.get("Datasets")
        ),
        axis="columns"
    )

    # Update the fastqs to contain the full path
    fastq_list_pd["Read1FileURISrc"] = fastq_list_pd.apply(
        lambda row: convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            run_output_path / row["sample_prefix"] / row["Read1File"],
            DataType.FILE
        ),
        axis="columns"
    )

    fastq_list_pd["Read2FileURISrc"] = fastq_list_pd.apply(
        lambda row: convert_project_id_and_data_path_to_icav2_uri(
            project_id,
            run_output_path / row["sample_prefix"] / row["Read2File"],
            DataType.FILE
        ),
        axis="columns"
    )

    return fastq_list_pd

