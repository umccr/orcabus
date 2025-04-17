#!/usr/bin/env python3

"""
Given the sequali stats json data, summarise into a qc coverage report

From

{
  "meta": {
    "sequali_version": "0.12.0",
    "report_generated": "2025-03-11 01:47:16+0000",
    "filename": "r1.fastq",
    "filesize": 14571253,
    "filename_read2": "r2.fastq",
    "filesize_read2": 14582369
  },
  "summary": {
    "mean_length": 257.56632,
    "minimum_length": 111,
    "maximum_length": 261,
    "total_reads": 25000,
    "q20_reads": 20262,
    "total_bases": 6439158,
    "q20_bases": 5946256,
    "total_gc_bases": 1362393,
    "total_n_bases": 2087,
    "read_pair_info": "Read 1"
  },
  "summary_read2": {
    "mean_length": 257.78864,
    "minimum_length": 111,
    "maximum_length": 261,
    "total_reads": 25000,
    "q20_reads": 15420,
    "total_bases": 6444716,
    "q20_bases": 5774140,
    "total_gc_bases": 1360600,
    "total_n_bases": 23133,
    "read_pair_info": "Read 2"
  },
  "insert_size_metrics": {
    [
        0,
        1,
        2,
        3
    ]
  }

{
  "insertSizeEstimate": 0,
  "rawWgsCoverageEstimate": 0,
  "r1Q20Fraction": 0,
  "r2Q20Fraction": 0,
  "r1GcFraction": 0,
  "r2GcFraction": 0
}
"""

# Imports
import json
import sys
from os import environ
from typing import List, Optional, Dict, Union

# Globals
HG38_N_BASES = 3099734149  #  https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000001405.26


# Handling functions
def get_inputs_from_stdin():
    return json.load(sys.stdin)


def write_output_to_stdout(data):
    print(json.dumps(data, indent=2))


def get_insert_size_estimate(insert_sizes: List[int]) -> int:
    """
    Given a list of counts, return the cell index with the median count
    :param insert_sizes:
    :return:
    """

    # Check if insert_sizes is empty
    if not insert_sizes or not isinstance(insert_sizes, List):
        return 0

    total_insert_size_count = sum(insert_sizes)
    index_count = 0
    for i, insert_size_count in enumerate(insert_sizes):
        if i == 0:
            continue
        index_count += insert_size_count
        if index_count >= total_insert_size_count / 2:
            # Read length is represented by the index
            return i
    return len(insert_sizes) - 1


def get_raw_coverage_estimate(mean_length: float) -> float:
    # Check if the environment variable is set
    if environ.get('READ_COUNT', None) is None:
        return 0

    # Get the read count
    read_count = int(environ['READ_COUNT'])

    # Get the coverage estimate by multipying the read count by the mean length
    return round(read_count * mean_length / HG38_N_BASES, 2)


def get_duplication_fraction(estimated_duplication_fractions_dict: Dict[str, float]) -> float:
    """
    {
        "1": 0.57464,
        "2": 0.21584,
        "3": 0.09792,
        "4": 0.05024,
        "5": 0.0244,
        "6-10": 0.02944,
        "11-20": 0.00752,
        "21-30": 0.0,
        "31-50": 0.0,
        "51-100": 0.0,
        "101-500": 0.0,
        "501-1000": 0.0,
        "1001-5000": 0.0,
        "5001-10000": 0.0,
        "10001-50000": 0.0,
        "> 50000": 0.0
    }
    :param estimated_duplication_fractions_dict:
    :return:
    """

    return round(1 - estimated_duplication_fractions_dict["1"], 2)


def get_q20_fraction(summary_dict: Dict[str, Union[float, int, str]]) -> float:
    """
    {
        "mean_length": 257.56632,
        "minimum_length": 111,
        "maximum_length": 261,
        "total_reads": 25000,
        "q20_reads": 20262,
        "total_bases": 6439158,
        "q20_bases": 5946256,
        "total_gc_bases": 1362393,
        "total_n_bases": 2087,
        "read_pair_info": "Read 1"
    }
    :param summary_dict:
    :return:
    """
    return round(summary_dict["q20_bases"] / summary_dict["total_bases"], 2)


def get_gc_fraction(summary_dict: Dict[str, Union[float, int, str]]) -> float:
    """
    {
        "mean_length": 257.56632,
        "minimum_length": 111,
        "maximum_length": 261,
        "total_reads": 25000,
        "q20_reads": 20262,
        "total_bases": 6439158,
        "q20_bases": 5946256,
        "total_gc_bases": 1362393,
        "total_n_bases": 2087,
        "read_pair_info": "Read 1"
    }
    :param summary_dict:
    :return:
    """
    return round(summary_dict["total_gc_bases"] / summary_dict["total_bases"], 2)


def main():
    # Get data from standard input
    data = get_inputs_from_stdin()

    mean_length = data['summary']['mean_length']
    if 'summary_read2' in data.keys():
        mean_length += data['summary_read2']['mean_length']

    output_dict = {
        "insertSizeEstimate": get_insert_size_estimate(data['insert_size_metrics']['insert_sizes']),
        "rawWgsCoverageEstimate": get_raw_coverage_estimate(mean_length),
        "r1Q20Fraction": get_q20_fraction(data['summary']),
        "r2Q20Fraction": get_q20_fraction(data['summary_read2']) if 'summary_read2' in data.keys() else None,
        "r1GcFraction": get_gc_fraction(data['summary']),
        "r2GcFraction": get_gc_fraction(data['summary_read2']) if 'summary_read2' in data.keys() else None,
        "duplicationFractionEstimate": get_duplication_fraction(data['duplication_fractions']['estimated_duplication_fractions'])
    }

    # Write output to standard output
    write_output_to_stdout(output_dict)


if __name__ == "__main__":
    main()