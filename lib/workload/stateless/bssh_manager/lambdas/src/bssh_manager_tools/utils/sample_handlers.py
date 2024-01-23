#!/usr/bin/env python3

"""

"""
from typing import Dict

import pandas as pd
from pathlib import Path


def get_sample_id_path_prefix_from_bssh_datasets_dict(sample_id, datasets_dict) -> Path:
    """
    From the DataSets dict, collect the sample_id as a key and then retunr the path attribute
    :param sample_id:
    :param datasets_dict:
    :return:
    """
    return Path(datasets_dict.get(sample_id).get('path'))


def get_fastq_list_paths_from_bssh_output_and_fastq_list_csv(fastq_list_pd: pd.DataFrame, bssh_output_dict: Dict) -> Dict:
    """
    Takes the SampleSheet.Samples key for bssh output dict and convert into a pandas DataFrame,
    :param fastq_list_pd: pandas dataframe of fastq list csv
    :param bssh_output_dict: dictionary of bssh output
    """
    fastq_list_paths_dict = {}
    samplesheet_df = pd.DataFrame(bssh_output_dict['SampleSheet']['Samples'])
    for sample_id in samplesheet_df["Sample_ID"].unique().tolist():
        sample_path_prefix = get_sample_id_path_prefix_from_bssh_datasets_dict(
            sample_id=sample_id,
            datasets_dict=bssh_output_dict.get("Datasets")
        )
        sample_fastq_list_df = fastq_list_pd.query(f"RGSM == '{sample_id}'")
        fastq_list_paths_dict[sample_id] = (
            list(
                sample_fastq_list_df["Read1File"].apply(
                    lambda read_1_file_iter: sample_path_prefix / read_1_file_iter
                )
            ) +
            list(
                sample_fastq_list_df["Read2File"].apply(
                    lambda read_2_file_iter: sample_path_prefix / read_2_file_iter
                )
            )
        )

    return fastq_list_paths_dict

