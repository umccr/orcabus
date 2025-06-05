#!/usr/bin/env python

"""
Build a cttsov2 samplesheet (in JSON format)

Given an instrument run id, and a list of bclconvert data rows, generate a samplesheet for a tso500l library
"""

# Imports
from copy import deepcopy
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Globals
HEADER = {
    "file_format_version": 2,
    "run_name": None,  # Replaced by instrument run id
    "instrument_type": "NovaSeq"
}

READS = {
    "read_1_cycles": 151,
    "read_2_cycles": 151,
    "index_1_cycles": 10,
    "index_2_cycles": 10
}

V1_BCLCONVERT_SETTINGS = {
    "adapter_behavior": "trim",
    "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
    "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
    "minimum_trimmed_read_length": 35,
    "mask_short_reads": 35,
    "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
}

V2_BCLCONVERT_SETTINGS = {
    "adapter_behavior": "trim",
    "adapter_read_1": "CTGTCTCTTATACACATCT",
    "adapter_read_2": "CTGTCTCTTATACACATCT",
    "minimum_trimmed_read_length": 35,
    "mask_short_reads": 35,
    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
}

V1_TSO500L_SETTINGS = {
    "adapter_behavior": "trim",
    "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
    "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
    "minimum_trimmed_read_length": 35,
    "mask_short_reads": 35,
    "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
}

V2_TSO500L_SETTINGS = {
    "adapter_read_1": "CTGTCTCTTATACACATCT",
    "adapter_read_2": "CTGTCTCTTATACACATCT",
    "minimum_trimmed_read_length": 35,
    "mask_short_reads": 35,
    "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
}

TSO500L_SAMPLE_TYPE = "DNA"

V1_CTTSO_VALID_INDEXES = [
    {"index_id": "UP01", "index": "TCCGGAGA", "index2": "CCTATCCT", "index2_rev": "AGGATAGG"},
    {"index_id": "UP02", "index": "CTGAAGCT", "index2": "GGCTCTGA", "index2_rev": "TCAGAGCC"},
    {"index_id": "UP03", "index": "CGTAGCTC", "index2": "TTCGGATG", "index2_rev": "CATCCGAA"},
    {"index_id": "UP04", "index": "GAATTCGT", "index2": "ACTCATAA", "index2_rev": "TTATGAGT"},
    {"index_id": "UP05", "index": "AGCGATAG", "index2": "TTATTCGT", "index2_rev": "ACGAATAA"},
    {"index_id": "UP06", "index": "GCGATTAA", "index2": "AGCAGATC", "index2_rev": "GATCTGCT"},
    {"index_id": "UP07", "index": "ATTCAGAA", "index2": "TATAGCCT", "index2_rev": "AGGCTATA"},
    {"index_id": "UP08", "index": "GAATAATC", "index2": "ATAGAGGC", "index2_rev": "GCCTCTAT"},
    {"index_id": "UP09", "index": "TTAATCAG", "index2": "AGGCGAAG", "index2_rev": "CTTCGCCT"},
    {"index_id": "UP10", "index": "CGCTCATT", "index2": "TAATCTTA", "index2_rev": "TAAGATTA"},
    {"index_id": "UP11", "index": "TCCGCGAA", "index2": "TACTTACT", "index2_rev": "AGTAAGTA"},
    {"index_id": "UP12", "index": "ATTACTCG", "index2": "AGGAAGTC", "index2_rev": "GACTTCCT"},
    {"index_id": "UP13", "index": "ACTGCTTA", "index2": "GCGCCTCT", "index2_rev": "AGAGGCGC"},
    {"index_id": "UP14", "index": "ATGCGGCT", "index2": "CGCGGCTA", "index2_rev": "TAGCCGCG"},
    {"index_id": "UP15", "index": "GCCTCTCT", "index2": "CCTACGAA", "index2_rev": "TTCGTAGG"},
    {"index_id": "UP16", "index": "GCCGTAGG", "index2": "GCGGAGCG", "index2_rev": "CGCTCCGC"},
]

V2_CTTSO_VALID_INDEXES = [
    {"index_id": "UDP0001", "index": "GAACTGAGCG", "index_rev": "ATAGACCGTT", "index2": "TCGTGGAGCG", "index2_rev": "CGCTCCACGA"},
    {"index_id": "UDP0002", "index": "AGGTCAGATA", "index_rev": "ACCGGCTCAG", "index2": "CTACAAGATA", "index2_rev": "TATCTTGTAG"},
    {"index_id": "UDP0003V3", "index": "CGACATCCGA", "index_rev": "CACTCGCACT", "index2": "TACGTTCATT", "index2_rev": "AATGAACGTA"},
    {"index_id": "UDP0004", "index": "ATTCCATAAG", "index_rev": "GTTATATGGC", "index2": "TGCCTGGTGG", "index2_rev": "CCACCAGGCA"},
    {"index_id": "UDP0005V3", "index": "CACAATAGGA", "index_rev": "CTAGCGTCGA", "index2": "TCCATCCGAG", "index2_rev": "CTCGGATGGA"},
    {"index_id": "UDP0006", "index": "AACATCGCGC", "index_rev": "GCTCTCGTTG", "index2": "GTCCACTTGT", "index2_rev": "ACAAGTGGAC"},
    {"index_id": "UDP0007", "index": "CTAGTGCTCT", "index_rev": "CTCGACTCCT", "index2": "TGGAACAGTA", "index2_rev": "TACTGTTCCA"},
    {"index_id": "UDP0008", "index": "GATCAAGGCA", "index_rev": "GACTTAGAAG", "index2": "CCTTGTTAAT", "index2_rev": "ATTAACAAGG"},
    {"index_id": "UDP0009", "index": "GACTGAGTAG", "index_rev": "CCGGACCACA", "index2": "GTTGATAGTG", "index2_rev": "CACTATCAAC"},
    {"index_id": "UDP0010", "index": "AGTCAGACGA", "index_rev": "GGAATTGTTC", "index2": "ACCAGCGACA", "index2_rev": "TGTCGCTGGT"},
    {"index_id": "UDP0011", "index": "CCGTATGTTC", "index_rev": "TAATCGGTAC", "index2": "CATACACTGT", "index2_rev": "ACAGTGTATG"},
    {"index_id": "UDP0012", "index": "GAGTCATAGG", "index_rev": "AGAAGCCAAT", "index2": "GTGTGGCGCT", "index2_rev": "AGCGCCACAC"},
    {"index_id": "UDP0013", "index": "CTTGCCATTA", "index_rev": "CCTTACTATG", "index2": "ATCACGAAGG", "index2_rev": "CCTTCGTGAT"},
    {"index_id": "UDP0014", "index": "GAAGCGGCAC", "index_rev": "CTCGTTATCA", "index2": "CGGCTCTACT", "index2_rev": "AGTAGAGCCG"},
    {"index_id": "UDP0015", "index": "TCCATTGCCG", "index_rev": "TCGCCGGTTA", "index2": "GAATGCACGA", "index2_rev": "TCGTGCATTC"},
    {"index_id": "UDP0016", "index": "CGGTTACGGC", "index_rev": "GATATAACAG", "index2": "AAGACTATAG", "index2_rev": "CTATAGTCTT"},
    {"index_id": "UDP0017", "index": "GAGAATGGTT", "index_rev": "CGAGGCGGTA", "index2": "TCGGCAGCAA", "index2_rev": "TTGCTGCCGA"},
    {"index_id": "UDP0018", "index": "AGAGGCAACC", "index_rev": "TCTACCGCTG", "index2": "CTAATGATGG", "index2_rev": "CCATCATTAG"},
    {"index_id": "UDP0019", "index": "CCATCATTAG", "index_rev": "TTATCTTGCA", "index2": "GGTTGCCTCT", "index2_rev": "AGAGGCAACC"},
    {"index_id": "UDP0020", "index": "GATAGGCCGA", "index_rev": "TAGTCACAAC", "index2": "CGCACATGGC", "index2_rev": "GCCATGTGCG"},
    {"index_id": "UDP0021", "index": "ATGGTTGACT", "index_rev": "TTGAGAGGAT", "index2": "GGCCTGTCCT", "index2_rev": "AGGACAGGCC"},
    {"index_id": "UDP0022", "index": "TATTGCGCTC", "index_rev": "AGGTTGCAGG", "index2": "CTGTGTTAGG", "index2_rev": "CCTAACACAG"},
    {"index_id": "UDP0023", "index": "ACGCCTTGTT", "index_rev": "AATATGAAGC", "index2": "TAAGGAACGT", "index2_rev": "ACGTTCCTTA"},
    {"index_id": "UDP0024", "index": "TTCTACATAC", "index_rev": "AATAGAGCAA", "index2": "CTAACTGTAA", "index2_rev": "TTACAGTTAG"},
    {"index_id": "UDP0025", "index": "AACCATAGAA", "index_rev": "GCCTCGGATA", "index2": "GGCGAGATGG", "index2_rev": "CCATCTCGCC"},
    {"index_id": "UDP0026", "index": "GGTTGCGAGG", "index_rev": "ATTCCGCTAT", "index2": "AATAGAGCAA", "index2_rev": "TTGCTCTATT"},
    {"index_id": "UDP0027", "index": "TAAGCATCCA", "index_rev": "CTATACGCGG", "index2": "TCAATCCATT", "index2_rev": "AATGGATTGA"},
    {"index_id": "UDP0028", "index": "ACCACGACAT", "index_rev": "TAAGGAACGT", "index2": "TCGTATGCGG", "index2_rev": "CCGCATACGA"},
    {"index_id": "UDP0029", "index": "GCCGCACTCT", "index_rev": "AATTGCTGCG", "index2": "TCCGACCTCG", "index2_rev": "CGAGGTCGGA"},
    {"index_id": "UDP0030", "index": "CCACCAGGCA", "index_rev": "GGCCATCATA", "index2": "CTTATGGAAT", "index2_rev": "ATTCCATAAG"},
    {"index_id": "UDP0031", "index": "GTGACACGCA", "index_rev": "CAGGCGCCAT", "index2": "GCTTACGGAC", "index2_rev": "GTCCGTAAGC"},
    {"index_id": "UDP0032", "index": "ACAGTGTATG", "index_rev": "GTCCACTTGT", "index2": "GAACATACGG", "index2_rev": "CCGTATGTTC"},
    {"index_id": "UDP0033", "index": "TGATTATACG", "index_rev": "GTAGAGTCAG", "index2": "GTCGATTACA", "index2_rev": "TGTAATCGAC"},
    {"index_id": "UDP0034", "index": "CAGCCGCGTA", "index_rev": "CGCTGCAGAG", "index2": "ACTAGCCGTG", "index2_rev": "CACGGCTAGT"},
    {"index_id": "UDP0035", "index": "GGTAACTCGC", "index_rev": "ACCTTATGAA", "index2": "AAGTTGGTGA", "index2_rev": "TCACCAACTT"},
    {"index_id": "UDP0036", "index": "ACCGGCCGTA", "index_rev": "GTTCCGCAGG", "index2": "TGGCAATATT", "index2_rev": "AATATTGCCA"},
    {"index_id": "UDP0037", "index": "TGTAATCGAC", "index_rev": "CCACCTGTGT", "index2": "GATCACCGCG", "index2_rev": "CGCGGTGATC"},
    {"index_id": "UDP0038", "index": "GTGCAGACAG", "index_rev": "GGTGTACAAG", "index2": "TACCATCCGT", "index2_rev": "ACGGATGGTA"},
    {"index_id": "UDP0039", "index": "CAATCGGCTG", "index_rev": "ACGTCAATAC", "index2": "GCTGTAGGAA", "index2_rev": "TTCCTACAGC"},
    {"index_id": "UDP0040", "index": "TATGTAGTCA", "index_rev": "AAGTACTCCA", "index2": "CGCACTAATG", "index2_rev": "CATTAGTGCG"},
    {"index_id": "UDP0041", "index": "ACTCGGCAAT", "index_rev": "CTCGTGCGTT", "index2": "GACAACTGAA", "index2_rev": "TTCAGTTGTC"},
    {"index_id": "UDP0042", "index": "GTCTAATGGC", "index_rev": "TATTCCTCAG", "index2": "AGTGGTCAGG", "index2_rev": "CCTGACCACT"},
    {"index_id": "UDP0043", "index": "CCATCTCGCC", "index_rev": "AAGCTTATGC", "index2": "TTCTATGGTT", "index2_rev": "AACCATAGAA"},
    {"index_id": "UDP0044", "index": "CTGCGAGCCA", "index_rev": "TTACAATTCC", "index2": "AATCCGGCCA", "index2_rev": "TGGCCGGATT"},
    {"index_id": "UDP0045", "index": "CGTTATTCTA", "index_rev": "TAATGGATCT", "index2": "CCATAAGGTT", "index2_rev": "AACCTTATGG"},
    {"index_id": "UDP0046V3", "index": "GCAACATGGA", "index_rev": "TAATCTCGTC", "index2": "CTTGTCTTAA", "index2_rev": "TTAAGACAAG"},
    {"index_id": "UDP0047", "index": "GTCCTGGATA", "index_rev": "ATATGAGACG", "index2": "CGGTGGCGAA", "index2_rev": "TTCGCCACCG"},
    {"index_id": "UDP0048", "index": "CAGTGGCACT", "index_rev": "CTTAACCACT", "index2": "TAACAATAGG", "index2_rev": "CCTATTGTTA"},
    {"index_id": "UDP0049", "index": "AGTGTTGCAC", "index_rev": "CAAGTTCATA", "index2": "CTGGTACACG", "index2_rev": "CGTGTACCAG"},
    {"index_id": "UDP0050", "index": "GACACCATGT", "index_rev": "TCGTGGTTGA", "index2": "TCAACGTGTA", "index2_rev": "TACACGTTGA"},
    {"index_id": "UDP0051", "index": "CCTGTCTGTC", "index_rev": "ATGAGAACCA", "index2": "ACTGTTGTGA", "index2_rev": "TCACAACAGT"},
    {"index_id": "UDP0052", "index": "TGATGTAAGA", "index_rev": "TCCATAATCC", "index2": "GTGCGTCCTT", "index2_rev": "AAGGACGCAC"},
    {"index_id": "UDP0053V3", "index": "TAGTTCGGTA", "index_rev": "CAGTATCAAT", "index2": "CCATGTGTAG", "index2_rev": "CTACACATGG"},
    {"index_id": "UDP0054V3", "index": "CTATTACTAC", "index_rev": "AGAACCGCGG", "index2": "GAGTCTCTCC", "index2_rev": "GGAGAGACTC"},
    {"index_id": "UDP0055V3", "index": "TAGCATAACC", "index_rev": "GTTGTACTCA", "index2": "GCTATGCGCA", "index2_rev": "TGCGCATAGC"},
    {"index_id": "UDP0056V3", "index": "ACTCTATTGT", "index_rev": "GGACGTCTTG", "index2": "ATCGCATATG", "index2_rev": "CATATGCGAT"},
    {"index_id": "UDP0057", "index": "TCTATCCTAA", "index_rev": "ACTGAATAGA", "index2": "CGTCGACTGG", "index2_rev": "CCAGTCGACG"},
    {"index_id": "UDP0058", "index": "CTCGCTTCGG", "index_rev": "GTGGTTGAAG", "index2": "TACTAGTCAA", "index2_rev": "TTGACTAGTA"},
    {"index_id": "UDP0059", "index": "CTGTTGGTCC", "index_rev": "TGAACGCAAC", "index2": "ATAGACCGTT", "index2_rev": "AACGGTCTAT"},
    {"index_id": "UDP0060", "index": "TTACCTGGAA", "index_rev": "TACTTGGTTG", "index2": "ACAGTTCCAG", "index2_rev": "CTGGAACTGT"},
    {"index_id": "UDP0061", "index": "TGGCTAATCA", "index_rev": "CATGGTTCGT", "index2": "AGGCATGTAG", "index2_rev": "CTACATGCCT"},
    {"index_id": "UDP0062", "index": "AACACTGTTA", "index_rev": "GCTGCCGGAT", "index2": "GCAAGTCTCA", "index2_rev": "TGAGACTTGC"},
    {"index_id": "UDP0063", "index": "ATTGCGCGGT", "index_rev": "TGAATTCATC", "index2": "TTGGCTCCGC", "index2_rev": "GCGGAGCCAA"},
    {"index_id": "UDP0064", "index": "TGGCGCGAAC", "index_rev": "GCAGGCTGGA", "index2": "AACTGATACT", "index2_rev": "AGTATCAGTT"},
    {"index_id": "UDP0065", "index": "TAATGTGTCT", "index_rev": "CGCCATACCT", "index2": "GTAAGGCATA", "index2_rev": "TATGCCTTAC"},
    {"index_id": "UDP0066", "index": "ATACCAACGC", "index_rev": "GCGCAGAGTA", "index2": "AATTGCTGCG", "index2_rev": "CGCAGCAATT"},
    {"index_id": "UDP0067", "index": "AGGATGTGCT", "index_rev": "ATTACTCACC", "index2": "TTACAATTCC", "index2_rev": "GGAATTGTAA"},
    {"index_id": "UDP0068", "index": "CACGGAACAA", "index_rev": "AGCATTAACT", "index2": "AACCTAGCAC", "index2_rev": "GTGCTAGGTT"},
    {"index_id": "UDP0069V3", "index": "CCAAGGCCTT", "index_rev": "AGGCCAGACA", "index2": "TCGAAGTACT", "index2_rev": "AGTACTTCGA"},
    {"index_id": "UDP0070V3", "index": "TTACTCCACA", "index_rev": "TTGGCCAGGT", "index2": "GACACCGATG", "index2_rev": "CATCGGTGTC"},
    {"index_id": "UDP0071V3", "index": "AGTAGAAGTG", "index_rev": "GAAGGTACAC", "index2": "CTAGCGTCGA", "index2_rev": "TCGACGCTAG"},
    {"index_id": "UDP0072V3", "index": "TACGAGTCCA", "index_rev": "ATCCTTGTCG", "index2": "TAGCGAAGCA", "index2_rev": "TGCTTCGCTA"},
    {"index_id": "UDP0073V3", "index": "TCTCATGATA", "index_rev": "GCAGCAACGA", "index2": "AACACGTGGA", "index2_rev": "TCCACGTGTT"},
    {"index_id": "UDP0074V3", "index": "CGAGGCCAAG", "index_rev": "AGGTGCGTAA", "index2": "GTGTTACCGG", "index2_rev": "CCGGTAACAC"},
    {"index_id": "UDP0075V3", "index": "TTCACGAGAC", "index_rev": "TGCGTCCAGG", "index2": "AGATTGTTAC", "index2_rev": "GTAACAATCT"},
    {"index_id": "UDP0076V3", "index": "GCGTGGATGG", "index_rev": "CAAGGCTATC", "index2": "TTGACCAATG", "index2_rev": "CATTGGTCAA"},
    {"index_id": "UDP0077", "index": "TCTGGTATCC", "index_rev": "AGCGCGGTGA", "index2": "CGTTGCTTAC", "index2_rev": "GTAAGCAACG"},
    {"index_id": "UDP0078", "index": "CATTAGTGCG", "index_rev": "ACACAGCGCT", "index2": "TGACTACATA", "index2_rev": "TATGTAGTCA"},
    {"index_id": "UDP0079", "index": "ACGGTCAGGA", "index_rev": "GTGTGATATC", "index2": "CGGCCTCGTT", "index2_rev": "AACGAGGCCG"},
    {"index_id": "UDP0080", "index": "GGCAAGCCAG", "index_rev": "ACGGAATGCG", "index2": "CAAGCATCCG", "index2_rev": "CGGATGCTTG"},
    {"index_id": "UDP0081", "index": "TGTCGCTGGT", "index_rev": "TGAAGTAAGT", "index2": "TCGTCTGACT", "index2_rev": "AGTCAGACGA"},
    {"index_id": "UDP0082", "index": "ACCGTTACAA", "index_rev": "CACGTTAGGC", "index2": "CTCATAGCGA", "index2_rev": "TCGCTATGAG"},
    {"index_id": "UDP0083", "index": "TATGCCTTAC", "index_rev": "TCGACTTAAG", "index2": "AGACACATTA", "index2_rev": "TAATGTGTCT"},
    {"index_id": "UDP0084V3", "index": "ACTGGATCTA", "index_rev": "GTGGCTGGTT", "index2": "TCGCCGCTAG", "index2_rev": "CTAGCGGCGA"},
    {"index_id": "UDP0085", "index": "TGGTACCTAA", "index_rev": "TGTGTAAGCT", "index2": "CATGAGTACT", "index2_rev": "AGTACTCATG"},
    {"index_id": "UDP0086", "index": "TTGGAATTCC", "index_rev": "TTCCTCCTTA", "index2": "ACGTCAATAC", "index2_rev": "GTATTGACGT"},
    {"index_id": "UDP0087", "index": "CCTCTACATG", "index_rev": "ACTAATTCAG", "index2": "GATACCTCCT", "index2_rev": "AGGAGGTATC"},
    {"index_id": "UDP0088", "index": "GGAGCGTGTA", "index_rev": "GACATCAGCT", "index2": "ATCCGTAAGT", "index2_rev": "ACTTACGGAT"},
    {"index_id": "UDP0089", "index": "GTCCGTAAGC", "index_rev": "CGGCGTAAGA", "index2": "CGTGTATCTT", "index2_rev": "AAGATACACG"},
    {"index_id": "UDP0090", "index": "ACTTCAAGCG", "index_rev": "GGTGCGTTCG", "index2": "GAACCATGAA", "index2_rev": "TTCATGGTTC"},
    {"index_id": "UDP0091", "index": "TCAGAAGGCG", "index_rev": "ATCGTCGCTC", "index2": "GGCCATCATA", "index2_rev": "TATGATGGCC"},
    {"index_id": "UDP0092", "index": "GCGTTGGTAT", "index_rev": "GACTGGTTGC", "index2": "ACATACTTCC", "index2_rev": "GGAAGTATGT"},
    {"index_id": "UDP0093", "index": "ACATATCCAG", "index_rev": "TCACTCATGT", "index2": "TATGTGCAAT", "index2_rev": "ATTGCACATA"},
    {"index_id": "UDP0094", "index": "TCATAGATTG", "index_rev": "GTTGCAGTTG", "index2": "GATTAAGGTG", "index2_rev": "CACCTTAATC"},
    {"index_id": "UDP0095", "index": "GTATTCCACC", "index_rev": "CCACCTTACA", "index2": "ATGTAGACAA", "index2_rev": "TTGTCTACAT"},
    {"index_id": "UDP0096", "index": "CCTCCGTCCA", "index_rev": "TTGAGCCTAA", "index2": "CACATCGGTG", "index2_rev": "CACCGATGTG"},
    {"index_id": "UDP0097", "index": "TGCCGGTCAG", "index_rev": "CCGGAATCAT", "index2": "CCTGATACAA", "index2_rev": "TTGTATCAGG"},
    {"index_id": "UDP0098", "index": "CACTCAATTC", "index_rev": "ACCAGTCATT", "index2": "TTAAGTTGTG", "index2_rev": "CACAACTTAA"},
    {"index_id": "UDP0099", "index": "TCTCACACGC", "index_rev": "CAAGGTGACG", "index2": "CGGACAGTGA", "index2_rev": "TCACTGTCCG"},
    {"index_id": "UDP0100", "index": "TCAATGGAGA", "index_rev": "GCAACAGGTG", "index2": "GCACTACAAC", "index2_rev": "GTTGTAGTGC"},
    {"index_id": "UDP0101", "index": "ATATGCATGT", "index_rev": "ACAAGGATTG", "index2": "TGGTGCCTGG", "index2_rev": "CCAGGCACCA"},
    {"index_id": "UDP0102V3", "index": "CTAGCTTCAA", "index_rev": "GAAGCTAGCT", "index2": "TGTGTAAGCT", "index2_rev": "AGCTTACACA"},
    {"index_id": "UDP0103", "index": "TCCGTTATGT", "index_rev": "CGGCAAGCTC", "index2": "TTGTAGTGTA", "index2_rev": "TACACTACAA"},
    {"index_id": "UDP0104", "index": "GGTCTATTAA", "index_rev": "ACTAGCCGTG", "index2": "CCACGACACG", "index2_rev": "CGTGTCGTGG"},
    {"index_id": "UDP0105", "index": "CAGCAATCGT", "index_rev": "TTGGATTCAA", "index2": "TGTGATGTAT", "index2_rev": "ATACATCACA"},
    {"index_id": "UDP0106", "index": "TTCTGTAGAA", "index_rev": "GCCAGATCCA", "index2": "GAGCGCAATA", "index2_rev": "TATTGCGCTC"},
    {"index_id": "UDP0107", "index": "GAACGCAATA", "index_rev": "AAGCAGATAT", "index2": "ATCTTACTGT", "index2_rev": "ACAGTAAGAT"},
    {"index_id": "UDP0108", "index": "AGTACTCATG", "index_rev": "CACCTCTTGG", "index2": "ATGTCGTGGT", "index2_rev": "ACCACGACAT"},
    {"index_id": "UDP0109", "index": "GGTAGAATTA", "index_rev": "ACTAGAACTT", "index2": "GTAGCCATCA", "index2_rev": "TGATGGCTAC"},
    {"index_id": "UDP0110", "index": "TAATTAGCGT", "index_rev": "TGCCTACGAG", "index2": "TGGTTAAGAA", "index2_rev": "TTCTTAACCA"},
    {"index_id": "UDP0111", "index": "ATTAACAAGG", "index_rev": "GCGGAGTTAC", "index2": "TGTTGTTCGT", "index2_rev": "ACGAACAACA"},
    {"index_id": "UDP0112", "index": "TGATGGCTAC", "index_rev": "ATGCCGACCG", "index2": "CCAACAACAT", "index2_rev": "ATGTTGTTGG"},
    {"index_id": "UDP0113", "index": "GAATTACAAG", "index_rev": "TAGGTCGTTG", "index2": "ACCGGCTCAG", "index2_rev": "CTGAGCCGGT"},
    {"index_id": "UDP0114", "index": "TAGAATTGGA", "index_rev": "TACTAACACA", "index2": "GTTAATCTGA", "index2_rev": "TCAGATTAAC"},
    {"index_id": "UDP0115", "index": "AGGCAGCTCT", "index_rev": "GGAGATTAGT", "index2": "CGGCTAACGT", "index2_rev": "ACGTTAGCCG"},
    {"index_id": "UDP0116", "index": "ATCGGCGAAG", "index_rev": "TGTACCGAAT", "index2": "TCCAAGAATT", "index2_rev": "AATTCTTGGA"},
    {"index_id": "UDP0117", "index": "CCGTGACCGA", "index_rev": "CCTTAGTGCC", "index2": "CCGAACGTTG", "index2_rev": "CAACGTTCGG"},
    {"index_id": "UDP0118", "index": "ATACTTGTTC", "index_rev": "AGCGTGAATG", "index2": "TAACCGCCGA", "index2_rev": "TCGGCGGTTA"},
    {"index_id": "UDP0119", "index": "TCCGCCAATT", "index_rev": "GTGCTATTAA", "index2": "CTCCGTGCTG", "index2_rev": "CAGCACGGAG"},
    {"index_id": "UDP0120", "index": "AGGACAGGCC", "index_rev": "ACTTCCTAGC", "index2": "CATTCCAGCT", "index2_rev": "AGCTGGAATG"},
    {"index_id": "UDP0121", "index": "AGAGAACCTA", "index_rev": "TGCACGAGAA", "index2": "GGTTATGCTA", "index2_rev": "TAGCATAACC"},
    {"index_id": "UDP0122", "index": "GATATTGTGT", "index_rev": "AAGAGAGGTG", "index2": "ACCACACGGT", "index2_rev": "ACCGTGTGGT"},
    {"index_id": "UDP0123", "index": "CGTACAGGAA", "index_rev": "CTTGTCTTAA", "index2": "TAGGTTCTCT", "index2_rev": "AGAGAACCTA"},
    {"index_id": "UDP0124", "index": "CTGCGTTACC", "index_rev": "CATACTTGAA", "index2": "TATGGCTCGA", "index2_rev": "TCGAGCCATA"},
    {"index_id": "UDP0125", "index": "AGGCCGTGGA", "index_rev": "GTGCTAGGTG", "index2": "CTCGTGCGTT", "index2_rev": "AACGCACGAG"},
    {"index_id": "UDP0126", "index": "AGGAGGTATC", "index_rev": "AACATACCTA", "index2": "CCAGTTGGCA", "index2_rev": "TGCCAACTGG"},
    {"index_id": "UDP0127", "index": "GCTGACGTTG", "index_rev": "TGTGATGTAT", "index2": "TGTTCGCATT", "index2_rev": "AATGCGAACA"},
    {"index_id": "UDP0128", "index": "CTAATAACCG", "index_rev": "AACGGAGCGG", "index2": "AACCGCATCG", "index2_rev": "CGATGCGGTT"},
    {"index_id": "UDP0129", "index": "TCTAGGCGCG", "index_rev": "GAGTCTCTCC", "index2": "CGAAGGTTAA", "index2_rev": "TTAACCTTCG"},
    {"index_id": "UDP0130", "index": "ATAGCCAAGA", "index_rev": "GGACCTCAAT", "index2": "AGTGCCACTG", "index2_rev": "CAGTGGCACT"},
    {"index_id": "UDP0131", "index": "TTCGGTGTGA", "index_rev": "CAAGCCACTA", "index2": "GAACAAGTAT", "index2_rev": "ATACTTGTTC"},
    {"index_id": "UDP0132", "index": "ATGTAACGTT", "index_rev": "GAAGCGGACC", "index2": "ACGATTGCTG", "index2_rev": "CAGCAATCGT"},
    {"index_id": "UDP0133", "index": "AACGAGGCCG", "index_rev": "AGTGAGTGAA", "index2": "ATACCTGGAT", "index2_rev": "ATCCAGGTAT"},
    {"index_id": "UDP0134", "index": "TGGTGTTATG", "index_rev": "GATAACCTGG", "index2": "TCCAATTCTA", "index2_rev": "TAGAATTGGA"},
    {"index_id": "UDP0135", "index": "TGGCCTCTGT", "index_rev": "TCTAGTCTTC", "index2": "TGAGACAGCG", "index2_rev": "CGCTGTCTCA"},
    {"index_id": "UDP0136", "index": "CCAGGCACCA", "index_rev": "TCCTTCATAG", "index2": "ACGCTAATTA", "index2_rev": "TAATTAGCGT"},
    {"index_id": "UDP0137", "index": "CCGGTTCCTA", "index_rev": "ATTCATTGCA", "index2": "TATATTCGAG", "index2_rev": "CTCGAATATA"},
    {"index_id": "UDP0138", "index": "GGCCAATATT", "index_rev": "CGTGTATCTT", "index2": "CGGTCCGATA", "index2_rev": "TATCGGACCG"},
    {"index_id": "UDP0139", "index": "GAATACCTAT", "index_rev": "GAATGCACGA", "index2": "ACAATAGAGT", "index2_rev": "ACTCTATTGT"},
    {"index_id": "UDP0140", "index": "TACGTGAAGG", "index_rev": "TGGCAATATT", "index2": "CGGTTATTAG", "index2_rev": "CTAATAACCG"},
    {"index_id": "UDP0141", "index": "CTTATTGGCC", "index_rev": "ATGTGCGAGC", "index2": "GATAACAAGT", "index2_rev": "ACTTGTTATC"},
    {"index_id": "UDP0142", "index": "ACAACTACTG", "index_rev": "GTCTTCTAAT", "index2": "AGTTATCACA", "index2_rev": "TGTGATAACT"},
    {"index_id": "UDP0143", "index": "GTTGGATGAA", "index_rev": "GCTACTATCT", "index2": "TTCCAGGTAA", "index2_rev": "TTACCTGGAA"},
    {"index_id": "UDP0144", "index": "AATCCAATTG", "index_rev": "TCCTCTTCTC", "index2": "CATGTAGAGG", "index2_rev": "CCTCTACATG"},
    {"index_id": "UDP0145V3", "index": "GTGCTAGGTT", "index_rev": "TGTAGACTTG", "index2": "TGAATATTGC", "index2_rev": "GCAATATTCA"},
    {"index_id": "UDP0146V3", "index": "ACAGCGACCA", "index_rev": "AGTACCTATA", "index2": "CAGGAGCTCT", "index2_rev": "AGAGCTCCTG"},
    {"index_id": "UDP0147V3", "index": "TCCACACAGA", "index_rev": "GATGCCAAGG", "index2": "TTGTCGGATG", "index2_rev": "CATCCGACAA"},
    {"index_id": "UDP0148V3", "index": "AAGTGTTAGG", "index_rev": "CATTCCAGCT", "index2": "GCTAGTTCCG", "index2_rev": "CGGAACTAGC"},
    {"index_id": "UDP0149", "index": "GATTCTGAAT", "index_rev": "AGTGGTCAGG", "index2": "AGCGGTGGAC", "index2_rev": "GTCCACCGCT"},
    {"index_id": "UDP0150", "index": "TAGAGAATAC", "index_rev": "GGCGAATTCT", "index2": "TATAGATTCG", "index2_rev": "CGAATCTATA"},
    {"index_id": "UDP0151", "index": "TTGTATCAGG", "index_rev": "CAGAGTGATA", "index2": "ACAGAGGCCA", "index2_rev": "TGGCCTCTGT"},
    {"index_id": "UDP0152", "index": "CACAGCGGTC", "index_rev": "CACTTAATCT", "index2": "ATTCCTATTG", "index2_rev": "CAATAGGAAT"},
    {"index_id": "UDP0153", "index": "CCACGCTGAA", "index_rev": "TGTACTTGTT", "index2": "TATTCCTCAG", "index2_rev": "CTGAGGAATA"},
    {"index_id": "UDP0154", "index": "GTTCGGAGTT", "index_rev": "ACTTGTCCAC", "index2": "CGCCTTCTGA", "index2_rev": "TCAGAAGGCG"},
    {"index_id": "UDP0155V3", "index": "ATGTCGTATT", "index_rev": "TCACAGATCG", "index2": "TTCTTGCTGG", "index2_rev": "CCAGCAAGAA"},
    {"index_id": "UDP0156", "index": "GCAATATTCA", "index_rev": "TCCTAGGAAG", "index2": "GGCGCCAATT", "index2_rev": "AATTGGCGCC"},
    {"index_id": "UDP0157", "index": "CTAGATTGCG", "index_rev": "CCGCTTAGCT", "index2": "AGATATGGCG", "index2_rev": "CGCCATATCT"},
    {"index_id": "UDP0158", "index": "CGATGCGGTT", "index_rev": "AATAGGCCTC", "index2": "CCTGCTTGGT", "index2_rev": "ACCAAGCAGG"},
    {"index_id": "UDP0159", "index": "TCCGGACTAG", "index_rev": "GTATCATTGG", "index2": "GACGAACAAT", "index2_rev": "ATTGTTCGTC"},
    {"index_id": "UDP0160", "index": "GTGACGGAGC", "index_rev": "AGCTGTTATA", "index2": "TGGCGGTCCA", "index2_rev": "TGGACCGCCA"},
    {"index_id": "UDP0161", "index": "AATTCCATCT", "index_rev": "GAGACATAAT", "index2": "CTTCAGTTAC", "index2_rev": "GTAACTGAAG"},
    {"index_id": "UDP0162", "index": "TTAACGGTGT", "index_rev": "AGGATAAGTT", "index2": "TCCTGACCGT", "index2_rev": "ACGGTCAGGA"},
    {"index_id": "UDP0163", "index": "ACTTGTTATC", "index_rev": "GCTCGCCTAC", "index2": "CGCGCCTAGA", "index2_rev": "TCTAGGCGCG"},
    {"index_id": "UDP0164", "index": "CGTGTACCAG", "index_rev": "TAGTAGATGA", "index2": "AGGATAAGTT", "index2_rev": "AACTTATCCT"},
    {"index_id": "UDP0165", "index": "TTAACCTTCG", "index_rev": "GAAGCTCCTC", "index2": "AGGCCAGACA", "index2_rev": "TGTCTGGCCT"},
    {"index_id": "UDP0166", "index": "CATATGCGAT", "index_rev": "CCTAGACACT", "index2": "CCTTGAACGG", "index2_rev": "CCGTTCAAGG"},
    {"index_id": "UDP0167", "index": "AGCCTATGAT", "index_rev": "TCTCGGTTAG", "index2": "CACCACCTAC", "index2_rev": "GTAGGTGGTG"},
    {"index_id": "UDP0168", "index": "TATGACAATC", "index_rev": "GCCGACAAGA", "index2": "TTGCTTGTAT", "index2_rev": "ATACAAGCAA"},
    {"index_id": "UDP0169", "index": "ATGTTGTTGG", "index_rev": "ATACTGTGTG", "index2": "CAATCTATGA", "index2_rev": "TCATAGATTG"},
    {"index_id": "UDP0170", "index": "GCACCACCAA", "index_rev": "CATGGTCTAA", "index2": "TGGTACTGAT", "index2_rev": "ATCAGTACCA"},
    {"index_id": "UDP0171", "index": "AGGCGTTCGC", "index_rev": "CTAATTCGCT", "index2": "TTCATCCAAC", "index2_rev": "GTTGGATGAA"},
    {"index_id": "UDP0172", "index": "CCTCCGGTTG", "index_rev": "CAATGGCGCC", "index2": "CATAACACCA", "index2_rev": "TGGTGTTATG"},
    {"index_id": "UDP0173", "index": "GTCCACCGCT", "index_rev": "AACGGTATGA", "index2": "TCCTATTAGC", "index2_rev": "GCTAATAGGA"},
    {"index_id": "UDP0174", "index": "ATTGTTCGTC", "index_rev": "TATACCATGG", "index2": "TCTCTAGATT", "index2_rev": "AATCTAGAGA"},
    {"index_id": "UDP0175", "index": "GGACCAGTGG", "index_rev": "AGATTGTTAC", "index2": "CGCGAGCCTA", "index2_rev": "TAGGCTCGCG"},
    {"index_id": "UDP0176", "index": "CCTTCTAACA", "index_rev": "TGTTCTATAC", "index2": "GATAAGCTCT", "index2_rev": "AGAGCTTATC"},
    {"index_id": "UDP0177", "index": "CTCGAATATA", "index_rev": "ACGAGACTGA", "index2": "GAGATGTCGA", "index2_rev": "TCGACATCTC"},
    {"index_id": "UDP0178", "index": "GATCGTCGCG", "index_rev": "CAAGATGCTT", "index2": "CTGGATATGT", "index2_rev": "ACATATCCAG"},
    {"index_id": "UDP0179V3", "index": "CCGACCTGTC", "index_rev": "GGTATTGAGA", "index2": "TGCTCATAAC", "index2_rev": "GTTATGAGCA"},
    {"index_id": "UDP0180", "index": "CGCTGTCTCA", "index_rev": "CCAGATTCGG", "index2": "ATTACTCACC", "index2_rev": "GGTGAGTAAT"},
    {"index_id": "UDP0181", "index": "AATGCGAACA", "index_rev": "ATTAATACGC", "index2": "AATTGGCGGA", "index2_rev": "TCCGCCAATT"},
    {"index_id": "UDP0182", "index": "AATTCTTGGA", "index_rev": "CCGAACGTTG", "index2": "TTGTCAACTT", "index2_rev": "AAGTTGACAA"},
    {"index_id": "UDP0183", "index": "TTCCTACAGC", "index_rev": "TGCTGGACAT", "index2": "GGCGAATTCT", "index2_rev": "AGAATTCGCC"},
    {"index_id": "UDP0184", "index": "ATCCAGGTAT", "index_rev": "GATCTCTGGA", "index2": "CAACGTCAGC", "index2_rev": "GCTGACGTTG"},
    {"index_id": "UDP0185", "index": "ACGGTCCAAC", "index_rev": "GGCACGCCAT", "index2": "TCTTACATCA", "index2_rev": "TGATGTAAGA"},
    {"index_id": "UDP0186", "index": "GTAACTTGGT", "index_rev": "AGTGGATAAT", "index2": "CGCCATACCT", "index2_rev": "AGGTATGGCG"},
    {"index_id": "UDP0187", "index": "AGCGCCACAC", "index_rev": "TGGTCTAGTG", "index2": "CTAATGTCTT", "index2_rev": "AAGACATTAG"},
    {"index_id": "UDP0188", "index": "TGCTACTGCC", "index_rev": "TAGCCGAGAG", "index2": "CAACCGGAGG", "index2_rev": "CCTCCGGTTG"},
    {"index_id": "UDP0189", "index": "CAACACCGCA", "index_rev": "GAACCATGAA", "index2": "GGCAGTAGCA", "index2_rev": "TGCTACTGCC"},
    {"index_id": "UDP0190", "index": "CACCTTAATC", "index_rev": "AGACTCTCTT", "index2": "TTAGGATAGA", "index2_rev": "TCTATCCTAA"},
    {"index_id": "UDP0191", "index": "TTGAATGTTG", "index_rev": "TCCGCGTTCA", "index2": "CGCAATCTAG", "index2_rev": "CTAGATTGCG"},
    {"index_id": "UDP0192", "index": "CCGGTAACAC", "index_rev": "GTCTCCTTCC", "index2": "GAGTTGTACT", "index2_rev": "AGTACAACTC"},
    {"index_id": "UDP0193V3", "index": "ATCGTTACGG", "index_rev": "ACTCTTCCTT", "index2": "GCTCCGGAAG", "index2_rev": "CTTCCGGAGC"},
    {"index_id": "UDP0194V3", "index": "TCCTACGTCA", "index_rev": "TGGTTAAGAA", "index2": "TACTTAAGTG", "index2_rev": "CACTTAAGTA"},
    {"index_id": "UDP0195V3", "index": "GTTATATCGC", "index_rev": "TAAGACCTAT", "index2": "AAGACAAGGA", "index2_rev": "TCCTTGTCTT"},
    {"index_id": "UDP0196V3", "index": "GTTGGCCATC", "index_rev": "TGCTAACTAT", "index2": "TGACATTCGT", "index2_rev": "ACGAATGTCA"},
    {"index_id": "UDP0197", "index": "TCCTGGTTGT", "index_rev": "ATTAGTGGAG", "index2": "CTGACCGGCA", "index2_rev": "TGCCGGTCAG"},
    {"index_id": "UDP0198", "index": "TAATTCTGCT", "index_rev": "GTCACCACAG", "index2": "TCTCATCAAT", "index2_rev": "ATTGATGAGA"},
    {"index_id": "UDP0199", "index": "CGCACGACTG", "index_rev": "AAGTCTTGTA", "index2": "GGACCAACAG", "index2_rev": "CTGTTGGTCC"},
    {"index_id": "UDP0200", "index": "GAGGTTAGAC", "index_rev": "GTAATTACTG", "index2": "AATGTATTGC", "index2_rev": "GCAATACATT"},
    {"index_id": "UDP0201", "index": "AACCGAGTTC", "index_rev": "ACGGCCGTCA", "index2": "GATCTCTGGA", "index2_rev": "TCCAGAGATC"},
    {"index_id": "UDP0202", "index": "TGTGATAACT", "index_rev": "CAGATACCAC", "index2": "CAGGCGCCAT", "index2_rev": "ATGGCGCCTG"},
    {"index_id": "UDP0203", "index": "AGTATGCTAC", "index_rev": "AGTTAAGAGC", "index2": "TTAATAGACC", "index2_rev": "GGTCTATTAA"},
    {"index_id": "UDP0204", "index": "GTAACTGAAG", "index_rev": "TAGCGCTAGT", "index2": "GGAGTCGCGA", "index2_rev": "TCGCGACTCC"},
    {"index_id": "UDP0205", "index": "TCCTCGGACT", "index_rev": "TTGAGGCTGC", "index2": "AACGCCAGAG", "index2_rev": "CTCTGGCGTT"},
    {"index_id": "UDP0206", "index": "CTGGAACTGT", "index_rev": "AGATATGGCG", "index2": "CGTAATTAAC", "index2_rev": "GTTAATTACG"},
    {"index_id": "UDP0207", "index": "GAATATGCGG", "index_rev": "GCTTCCACTA", "index2": "ACGAGACTGA", "index2_rev": "TCAGTCTCGT"},
    {"index_id": "UDP0208", "index": "GATCGGATAA", "index_rev": "ACTTCCATAA", "index2": "GTATCGGCCG", "index2_rev": "CGGCCGATAC"},
    {"index_id": "UDP0209", "index": "GCTAGACTAT", "index_rev": "GAGCCAGGTT", "index2": "AATACGACAT", "index2_rev": "ATGTCGTATT"},
    {"index_id": "UDP0210", "index": "AGCTACTATA", "index_rev": "GCGTGATCGA", "index2": "GTTATATGGC", "index2_rev": "GCCATATAAC"},
    {"index_id": "UDP0211", "index": "CCACCGGAGT", "index_rev": "TGCGCTCTAG", "index2": "GCCTGCCATG", "index2_rev": "CATGGCAGGC"},
    {"index_id": "UDP0212", "index": "CTTACCGCAC", "index_rev": "GCGTACTTAG", "index2": "TAAGACCTAT", "index2_rev": "ATAGGTCTTA"},
    {"index_id": "UDP0213", "index": "TTAGGATATC", "index_rev": "CTAACTGTAA", "index2": "TATACCATGG", "index2_rev": "CCATGGTATA"},
    {"index_id": "UDP0214", "index": "TTATACGCGA", "index_rev": "TACGTAGATG", "index2": "GCCGTCTGTT", "index2_rev": "AACAGACGGC"},
    {"index_id": "UDP0215", "index": "CGCTTAGAAT", "index_rev": "GTTGATAGTG", "index2": "CAGAGTGATA", "index2_rev": "TATCACTCTG"},
    {"index_id": "UDP0216", "index": "CCGAAGCGCT", "index_rev": "AGCGCTTCGG", "index2": "TGCTAACTAT", "index2_rev": "ATAGTTAGCA"},
    {"index_id": "UDP0217", "index": "CACTATCAAC", "index_rev": "ATTCTAAGCG", "index2": "TCAGTTAATG", "index2_rev": "CATTAACTGA"},
    {"index_id": "UDP0218V3", "index": "CATCTACGTA", "index_rev": "TCGCGTATAA", "index2": "TGTAATTGAG", "index2_rev": "CTCAATTACA"},
    {"index_id": "UDP0219", "index": "TTACAGTTAG", "index_rev": "GATATCCTAA", "index2": "ACATGCATAT", "index2_rev": "ATATGCATGT"},
    {"index_id": "UDP0220", "index": "CTAAGTACGC", "index_rev": "GTGCGGTAAG", "index2": "AACATACCTA", "index2_rev": "TAGGTATGTT"},
    {"index_id": "UDP0221V3", "index": "CTAGAGCGCA", "index_rev": "ACTCCGGTGG", "index2": "GCTTCTAGCA", "index2_rev": "TGCTAGAAGC"},
    {"index_id": "UDP0222V3", "index": "TCGATCACGC", "index_rev": "TATAGTAGCT", "index2": "CATAGAGCCT", "index2_rev": "AGGCTCTATG"},
    {"index_id": "UDP0223V3", "index": "AACCTGGCTC", "index_rev": "ATAGTCTAGC", "index2": "TGAGTATGTT", "index2_rev": "AACATACTCA"},
    {"index_id": "UDP0224V3", "index": "TTATGGAAGT", "index_rev": "TTATCCGATC", "index2": "GACAATAACA", "index2_rev": "TGTTATTGTC"},
    {"index_id": "UDP0225", "index": "TAGTGGAAGC", "index_rev": "CCGCATATTC", "index2": "AGTACCTATA", "index2_rev": "TATAGGTACT"},
    {"index_id": "UDP0226", "index": "CGCCATATCT", "index_rev": "ACAGTTCCAG", "index2": "GACCGGAGAT", "index2_rev": "ATCTCCGGTC"},
    {"index_id": "UDP0227V3", "index": "GCAGCCTCAA", "index_rev": "AGTCCGAGGA", "index2": "TAAGTGCTAG", "index2_rev": "CTAGCACTTA"},
    {"index_id": "UDP0228", "index": "ACTAGCGCTA", "index_rev": "CTTCAGTTAC", "index2": "TTACTTCCTC", "index2_rev": "GAGGAAGTAA"},
    {"index_id": "UDP0229", "index": "GCTCTTAACT", "index_rev": "GTAGCATACT", "index2": "CACGTCCACC", "index2_rev": "GGTGGACGTG"},
    {"index_id": "UDP0230", "index": "GTGGTATCTG", "index_rev": "AGTTATCACA", "index2": "GCTACTATCT", "index2_rev": "AGATAGTAGC"},
    {"index_id": "UDP0231", "index": "TGACGGCCGT", "index_rev": "GAACTCGGTT", "index2": "AGTCAACCAT", "index2_rev": "ATGGTTGACT"},
    {"index_id": "UDP0232", "index": "CAGTAATTAC", "index_rev": "GTCTAACCTC", "index2": "CGAGGCGGTA", "index2_rev": "TACCGCCTCG"},
    {"index_id": "UDP0233", "index": "TACAAGACTT", "index_rev": "CAGTCGTGCG", "index2": "CAGGTGTTCA", "index2_rev": "TGAACACCTG"},
    {"index_id": "UDP0234", "index": "CTGTGGTGAC", "index_rev": "AGCAGAATTA", "index2": "GACAGACAGG", "index2_rev": "CCTGTCTGTC"},
    {"index_id": "UDP0235", "index": "CTCCACTAAT", "index_rev": "ACAACCAGGA", "index2": "TGTACTTGTT", "index2_rev": "AACAAGTACA"},
    {"index_id": "UDP0236", "index": "ATAGTTAGCA", "index_rev": "GATGGCCAAC", "index2": "CTCTAAGTAG", "index2_rev": "CTACTTAGAG"},
    {"index_id": "UDP0237", "index": "ATAGGTCTTA", "index_rev": "GCGATATAAC", "index2": "GTCACCACAG", "index2_rev": "CTGTGGTGAC"},
    {"index_id": "UDP0238", "index": "TTCTTAACCA", "index_rev": "TGACGTAGGA", "index2": "TCTACATACC", "index2_rev": "GGTATGTAGA"},
    {"index_id": "UDP0239", "index": "AAGGAAGAGT", "index_rev": "CCGTAACGAT", "index2": "CACGTTAGGC", "index2_rev": "GCCTAACGTG"},
    {"index_id": "UDP0240", "index": "GGAAGGAGAC", "index_rev": "GTGTTACCGG", "index2": "TGGTGAGTCT", "index2_rev": "AGACTCACCA"},
    {"index_id": "UDP0241", "index": "TGAACGCGGA", "index_rev": "CAACATTCAA", "index2": "CTTCGAAGGA", "index2_rev": "TCCTTCGAAG"},
    {"index_id": "UDP0242V3", "index": "AAGAGAGTCT", "index_rev": "GATTAAGGTG", "index2": "TACGAATCTT", "index2_rev": "AAGATTCGTA"},
    {"index_id": "UDP0243", "index": "TTCATGGTTC", "index_rev": "TGCGGTGTTG", "index2": "GACATTGTCA", "index2_rev": "TGACAATGTC"},
    {"index_id": "UDP0244V3", "index": "CTCTCGGCTA", "index_rev": "GGCAGTAGCA", "index2": "TACCAGATCT", "index2_rev": "AGATCTGGTA"},
    {"index_id": "UDP0245", "index": "CACTAGACCA", "index_rev": "GTGTGGCGCT", "index2": "ACTGCCTTAT", "index2_rev": "ATAAGGCAGT"},
    {"index_id": "UDP0246", "index": "ATTATCCACT", "index_rev": "ACCAAGTTAC", "index2": "TACGCACGTA", "index2_rev": "TACGTGCGTA"},
    {"index_id": "UDP0247", "index": "ATGGCGTGCC", "index_rev": "GTTGGACCGT", "index2": "CGCTTGAAGT", "index2_rev": "ACTTCAAGCG"},
    {"index_id": "UDP0248", "index": "TCCAGAGATC", "index_rev": "ATACCTGGAT", "index2": "CTGCACTTCA", "index2_rev": "TGAAGTGCAG"},
    {"index_id": "UDP0249", "index": "ATGTCCAGCA", "index_rev": "GCTGTAGGAA", "index2": "CAGCGGACAA", "index2_rev": "TTGTCCGCTG"},
    {"index_id": "UDP0250", "index": "CAACGTTCGG", "index_rev": "TCCAAGAATT", "index2": "GGATCCGCAT", "index2_rev": "ATGCGGATCC"},
    {"index_id": "UDP0251", "index": "GCGTATTAAT", "index_rev": "TGTTCGCATT", "index2": "TGCGGTGTTG", "index2_rev": "CAACACCGCA"},
    {"index_id": "UDP0252V2", "index": "CCGAATCTGG", "index_rev": "TGAGACAGCG", "index2": "ATGAATCAAG", "index2_rev": "CTTGATTCAT"},
    {"index_id": "UDP0253", "index": "TCTCAATACC", "index_rev": "GACAGGTCGG", "index2": "GACGTTCGCG", "index2_rev": "CGCGAACGTC"},
    {"index_id": "UDP0254", "index": "AAGCATCTTG", "index_rev": "CGCGACGATC", "index2": "CATTCAACAA", "index2_rev": "TTGTTGAATG"},
    {"index_id": "UDP0255", "index": "TCAGTCTCGT", "index_rev": "TATATTCGAG", "index2": "CACGGATTAT", "index2_rev": "ATAATCCGTG"},
    {"index_id": "UDP0256V3", "index": "GTATAGAACA", "index_rev": "TGTTAGAAGG", "index2": "TGTCACAGGA", "index2_rev": "TCCTGTGACA"},
    {"index_id": "UDP0257", "index": "GTAACAATCT", "index_rev": "CCACTGGTCC", "index2": "CTCTGTATAC", "index2_rev": "GTATACAGAG"},
    {"index_id": "UDP0258V2", "index": "CCATGGTATA", "index_rev": "GACGAACAAT", "index2": "TCTCGCGGAG", "index2_rev": "CTCCGCGAGA"},
    {"index_id": "UDP0259", "index": "TCATACCGTT", "index_rev": "AGCGGTGGAC", "index2": "GGTAACGCAG", "index2_rev": "CTGCGTTACC"},
    {"index_id": "UDP0260", "index": "GGCGCCATTG", "index_rev": "CAACCGGAGG", "index2": "ACCGCGCAAT", "index2_rev": "ATTGCGCGGT"},
    {"index_id": "UDP0261", "index": "AGCGAATTAG", "index_rev": "GCGAACGCCT", "index2": "AGCCGGAACA", "index2_rev": "TGTTCCGGCT"},
    {"index_id": "UDP0262", "index": "TTAGACCATG", "index_rev": "TTGGTGGTGC", "index2": "TCCTAGGAAG", "index2_rev": "CTTCCTAGGA"},
    {"index_id": "UDP0263", "index": "CACACAGTAT", "index_rev": "CCAACAACAT", "index2": "TTGAGCCTAA", "index2_rev": "TTAGGCTCAA"},
    {"index_id": "UDP0264", "index": "TCTTGTCGGC", "index_rev": "GATTGTCATA", "index2": "CCACCTGTGT", "index2_rev": "ACACAGGTGG"},
    {"index_id": "UDP0265V3", "index": "CTAACCGAGA", "index_rev": "ATCATAGGCT", "index2": "TCGATGCGCG", "index2_rev": "CGCGCATCGA"},
    {"index_id": "UDP0266V3", "index": "AGTGTCTAGG", "index_rev": "ATCGCATATG", "index2": "CCTAGAAGCA", "index2_rev": "TGCTTCTAGG"},
    {"index_id": "UDP0267V3", "index": "GAGGAGCTTC", "index_rev": "CGAAGGTTAA", "index2": "GACGTATACA", "index2_rev": "TGTATACGTC"},
    {"index_id": "UDP0268V3", "index": "TCATCTACTA", "index_rev": "CTGGTACACG", "index2": "TAGGCGACTT", "index2_rev": "AAGTCGCCTA"},
    {"index_id": "UDP0269", "index": "GTAGGCGAGC", "index_rev": "GATAACAAGT", "index2": "TAGGAGCGCA", "index2_rev": "TGCGCTCCTA"},
    {"index_id": "UDP0270", "index": "AACTTATCCT", "index_rev": "ACACCGTTAA", "index2": "GTACTGGCGT", "index2_rev": "ACGCCAGTAC"},
    {"index_id": "UDP0271", "index": "ATTATGTCTC", "index_rev": "AGATGGAATT", "index2": "AGTTAAGAGC", "index2_rev": "GCTCTTAACT"},
    {"index_id": "UDP0272", "index": "TATAACAGCT", "index_rev": "GCTCCGTCAC", "index2": "TCGCGTATAA", "index2_rev": "TTATACGCGA"},
    {"index_id": "UDP0273", "index": "CCAATGATAC", "index_rev": "CTAGTCCGGA", "index2": "GAGTGTGCCG", "index2_rev": "CGGCACACTC"},
    {"index_id": "UDP0274", "index": "GAGGCCTATT", "index_rev": "AACCGCATCG", "index2": "CTAGTCCGGA", "index2_rev": "TCCGGACTAG"},
    {"index_id": "UDP0275", "index": "AGCTAAGCGG", "index_rev": "CGCAATCTAG", "index2": "ATTAATACGC", "index2_rev": "GCGTATTAAT"},
    {"index_id": "UDP0276", "index": "CTTCCTAGGA", "index_rev": "TGAATATTGC", "index2": "CCTAGAGTAT", "index2_rev": "ATACTCTAGG"},
    {"index_id": "UDP0277", "index": "CGATCTGTGA", "index_rev": "AATACGACAT", "index2": "TAGGAAGACT", "index2_rev": "AGTCTTCCTA"},
    {"index_id": "UDP0278", "index": "GTGGACAAGT", "index_rev": "AACTCCGAAC", "index2": "CCGTGGCCTT", "index2_rev": "AAGGCCACGG"},
    {"index_id": "UDP0279", "index": "AACAAGTACA", "index_rev": "TTCAGCGTGG", "index2": "GGATATATCC", "index2_rev": "GGATATATCC"},
    {"index_id": "UDP0280", "index": "AGATTAAGTG", "index_rev": "GACCGCTGTG", "index2": "CACCTCTTGG", "index2_rev": "CCAAGAGGTG"},
    {"index_id": "UDP0281", "index": "TATCACTCTG", "index_rev": "CCTGATACAA", "index2": "AACGTTACAT", "index2_rev": "ATGTAACGTT"},
    {"index_id": "UDP0282", "index": "AGAATTCGCC", "index_rev": "GTATTCTCTA", "index2": "CGGCAAGCTC", "index2_rev": "GAGCTTGCCG"},
    {"index_id": "UDP0283", "index": "CCTGACCACT", "index_rev": "ATTCAGAATC", "index2": "TCTTGGCTAT", "index2_rev": "ATAGCCAAGA"},
    {"index_id": "UDP0284", "index": "AGCTGGAATG", "index_rev": "CCTAACACTT", "index2": "ACGGAATGCG", "index2_rev": "CGCATTCCGT"},
    {"index_id": "UDP0285V3", "index": "CCTTGGCATC", "index_rev": "TCTGTGTGGA", "index2": "GACCGATTCG", "index2_rev": "CGAATCGGTC"},
    {"index_id": "UDP0286V3", "index": "TATAGGTACT", "index_rev": "TGGTCGCTGT", "index2": "TAGGTGAGAT", "index2_rev": "ATCTCACCTA"},
    {"index_id": "UDP0287V3", "index": "CAAGTCTACA", "index_rev": "AACCTAGCAC", "index2": "CACGTACGTG", "index2_rev": "CACGTACGTG"},
    {"index_id": "UDP0288V3", "index": "GAGAAGAGGA", "index_rev": "CAATTGGATT", "index2": "TTGACCTAAC", "index2_rev": "GTTAGGTCAA"},
    {"index_id": "UDP0289V2", "index": "AGATAGTAGC", "index_rev": "TTCATCCAAC", "index2": "GGCACGCCAT", "index2_rev": "ATGGCGTGCC"},
    {"index_id": "UDP0290V2", "index": "ATTAGAAGAC", "index_rev": "CAGTAGTTGT", "index2": "GCAGGCTGGA", "index2_rev": "TCCAGCCTGC"},
    {"index_id": "UDP0291V2", "index": "GCTCGCACAT", "index_rev": "GGCCAATAAG", "index2": "ATGGCTTAAT", "index2_rev": "ATTAAGCCAT"},
    {"index_id": "UDP0292", "index": "AATATTGCCA", "index_rev": "CCTTCACGTA", "index2": "CGGTGACACC", "index2_rev": "GGTGTCACCG"},
    {"index_id": "UDP0293", "index": "TCGTGCATTC", "index_rev": "ATAGGTATTC", "index2": "GCGTTGGTAT", "index2_rev": "ATACCAACGC"},
    {"index_id": "UDP0294", "index": "AAGATACACG", "index_rev": "AATATTGGCC", "index2": "TGTGCTAACA", "index2_rev": "TGTTAGCACA"},
    {"index_id": "UDP0295", "index": "TGCAATGAAT", "index_rev": "TAGGAACCGG", "index2": "CCAGAAGTAA", "index2_rev": "TTACTTCTGG"},
    {"index_id": "UDP0296", "index": "CTATGAAGGA", "index_rev": "TGGTGCCTGG", "index2": "CTTATACCTG", "index2_rev": "CAGGTATAAG"},
    {"index_id": "UDP0297", "index": "GAAGACTAGA", "index_rev": "ACAGAGGCCA", "index2": "ACTAGAACTT", "index2_rev": "AAGTTCTAGT"},
    {"index_id": "UDP0298V3", "index": "CCAGGTTATC", "index_rev": "CATAACACCA", "index2": "GAATGCAGTT", "index2_rev": "AACTGCATTC"},
    {"index_id": "UDP0299", "index": "TTCACTCACT", "index_rev": "CGGCCTCGTT", "index2": "TATCATGAGA", "index2_rev": "TCTCATGATA"},
    {"index_id": "UDP0300", "index": "GGTCCGCTTC", "index_rev": "AACGTTACAT", "index2": "CTCACACAAG", "index2_rev": "CTTGTGTGAG"},
    {"index_id": "UDP0301V2", "index": "TAGTGGCTTG", "index_rev": "TCACACCGAA", "index2": "AGTTACTTGG", "index2_rev": "CCAAGTAACT"},
    {"index_id": "UDP0302", "index": "ATTGAGGTCC", "index_rev": "TCTTGGCTAT", "index2": "CGGATTATAT", "index2_rev": "ATATAATCCG"},
    {"index_id": "UDP0303", "index": "GGAGAGACTC", "index_rev": "CGCGCCTAGA", "index2": "TTGAAGCAGA", "index2_rev": "TCTGCTTCAA"},
    {"index_id": "UDP0304", "index": "CCGCTCCGTT", "index_rev": "CGGTTATTAG", "index2": "TACGGCGAAG", "index2_rev": "CTTCGCCGTA"},
    {"index_id": "UDP0305", "index": "ATACATCACA", "index_rev": "CAACGTCAGC", "index2": "TCTCCATTGA", "index2_rev": "TCAATGGAGA"},
    {"index_id": "UDP0306", "index": "TAGGTATGTT", "index_rev": "GATACCTCCT", "index2": "CGAGACCAAG", "index2_rev": "CTTGGTCTCG"},
    {"index_id": "UDP0307", "index": "CACCTAGCAC", "index_rev": "TCCACGGCCT", "index2": "TGCTGGACAT", "index2_rev": "ATGTCCAGCA"},
    {"index_id": "UDP0308", "index": "TTCAAGTATG", "index_rev": "GGTAACGCAG", "index2": "GATGGTATCG", "index2_rev": "CGATACCATC"},
    {"index_id": "UDP0309", "index": "TTAAGACAAG", "index_rev": "TTCCTGTACG", "index2": "GGCTTAATTG", "index2_rev": "CAATTAAGCC"},
    {"index_id": "UDP0310", "index": "CACCTCTCTT", "index_rev": "ACACAATATC", "index2": "CTCGACTCCT", "index2_rev": "AGGAGTCGAG"},
    {"index_id": "UDP0311", "index": "TTCTCGTGCA", "index_rev": "TAGGTTCTCT", "index2": "ATACACAGAG", "index2_rev": "CTCTGTGTAT"},
    {"index_id": "UDP0312", "index": "GCTAGGAAGT", "index_rev": "GGCCTGTCCT", "index2": "TCTCGGACGA", "index2_rev": "TCGTCCGAGA"},
    {"index_id": "UDP0313", "index": "TTAATAGCAC", "index_rev": "AATTGGCGGA", "index2": "ACCACGTCTG", "index2_rev": "CAGACGTGGT"},
    {"index_id": "UDP0314", "index": "CATTCACGCT", "index_rev": "GAACAAGTAT", "index2": "GTTGTACTCA", "index2_rev": "TGAGTACAAC"},
    {"index_id": "UDP0315", "index": "GGCACTAAGG", "index_rev": "TCGGTCACGG", "index2": "TCAGGTCAAC", "index2_rev": "GTTGACCTGA"},
    {"index_id": "UDP0316", "index": "ATTCGGTACA", "index_rev": "CTTCGCCGAT", "index2": "AGTCCGAGGA", "index2_rev": "TCCTCGGACT"},
    {"index_id": "UDP0317", "index": "ACTAATCTCC", "index_rev": "AGAGCTGCCT", "index2": "CACTTAATCT", "index2_rev": "AGATTAAGTG"},
    {"index_id": "UDP0318", "index": "TGTGTTAGTA", "index_rev": "TCCAATTCTA", "index2": "TACTCTGTTA", "index2_rev": "TAACAGAGTA"},
    {"index_id": "UDP0319", "index": "CAACGACCTA", "index_rev": "CTTGTAATTC", "index2": "GCGACTCGAT", "index2_rev": "ATCGAGTCGC"},
    {"index_id": "UDP0320", "index": "CGGTCGGCAT", "index_rev": "GTAGCCATCA", "index2": "CTAGGCAAGG", "index2_rev": "CCTTGCCTAG"},
    {"index_id": "UDP0321V3", "index": "GTAACTCCGC", "index_rev": "CCTTGTTAAT", "index2": "AATAGAACGG", "index2_rev": "CCGTTCTATT"},
    {"index_id": "UDP0322", "index": "CTCGTAGGCA", "index_rev": "ACGCTAATTA", "index2": "TCATCCTCTT", "index2_rev": "AAGAGGATGA"},
    {"index_id": "UDP0323", "index": "AAGTTCTAGT", "index_rev": "TAATTCTACC", "index2": "GGTAAGATAA", "index2_rev": "TTATCTTACC"},
    {"index_id": "UDP0324", "index": "CCAAGAGGTG", "index_rev": "CATGAGTACT", "index2": "AACGAGCCAG", "index2_rev": "CTGGCTCGTT"},
    {"index_id": "UDP0325", "index": "ATATCTGCTT", "index_rev": "TATTGCGTTC", "index2": "TAGACAATCT", "index2_rev": "AGATTGTCTA"},
    {"index_id": "UDP0326", "index": "TGGATCTGGC", "index_rev": "TTCTACAGAA", "index2": "CAATGCTGAA", "index2_rev": "TTCAGCATTG"},
    {"index_id": "UDP0327", "index": "TTGAATCCAA", "index_rev": "ACGATTGCTG", "index2": "GTCACGGTGT", "index2_rev": "ACACCGTGAC"},
    {"index_id": "UDP0328", "index": "CACGGCTAGT", "index_rev": "TTAATAGACC", "index2": "GGTGTACAAG", "index2_rev": "CTTGTACACC"},
    {"index_id": "UDP0329", "index": "GAGCTTGCCG", "index_rev": "ACATAACGGA", "index2": "AGGTTGCAGG", "index2_rev": "CCTGCAACCT"},
    {"index_id": "UDP0330", "index": "AGCTAGCTTC", "index_rev": "TTGAAGCTAG", "index2": "TAATACGGAG", "index2_rev": "CTCCGTATTA"},
    {"index_id": "UDP0331", "index": "CAATCCTTGT", "index_rev": "ACATGCATAT", "index2": "CGAAGACGCA", "index2_rev": "TGCGTCTTCG"},
    {"index_id": "UDP0332", "index": "CACCTGTTGC", "index_rev": "TCTCCATTGA", "index2": "ATTGACACAT", "index2_rev": "ATGTGTCAAT"},
    {"index_id": "UDP0333", "index": "CGTCACCTTG", "index_rev": "GCGTGTGAGA", "index2": "CAGCCGATTG", "index2_rev": "CAATCGGCTG"},
    {"index_id": "UDP0334", "index": "AATGACTGGT", "index_rev": "GAATTGAGTG", "index2": "TCTCACGCGT", "index2_rev": "ACGCGTGAGA"},
    {"index_id": "UDP0335", "index": "ATGATTCCGG", "index_rev": "CTGACCGGCA", "index2": "CTCTGACGTG", "index2_rev": "CACGTCAGAG"},
    {"index_id": "UDP0336", "index": "TTAGGCTCAA", "index_rev": "TGGACGGAGG", "index2": "TCGAATGGAA", "index2_rev": "TTCCATTCGA"},
    {"index_id": "UDP0337", "index": "TGTAAGGTGG", "index_rev": "GGTGGAATAC", "index2": "AAGGCCTTGG", "index2_rev": "CCAAGGCCTT"},
    {"index_id": "UDP0338", "index": "CAACTGCAAC", "index_rev": "CAATCTATGA", "index2": "TGAACGCAAC", "index2_rev": "GTTGCGTTCA"},
    {"index_id": "UDP0339", "index": "ACATGAGTGA", "index_rev": "CTGGATATGT", "index2": "CCGCTTAGCT", "index2_rev": "AGCTAAGCGG"},
    {"index_id": "UDP0340", "index": "GCAACCAGTC", "index_rev": "ATACCAACGC", "index2": "CACCGAGGAA", "index2_rev": "TTCCTCGGTG"},
    {"index_id": "UDP0341", "index": "GAGCGACGAT", "index_rev": "CGCCTTCTGA", "index2": "CGTATAATCA", "index2_rev": "TGATTATACG"},
    {"index_id": "UDP0342", "index": "CGAACGCACC", "index_rev": "CGCTTGAAGT", "index2": "ATGACAGAAC", "index2_rev": "GTTCTGTCAT"},
    {"index_id": "UDP0343", "index": "TCTTACGCCG", "index_rev": "GCTTACGGAC", "index2": "ATTCATTGCA", "index2_rev": "TGCAATGAAT"},
    {"index_id": "UDP0344", "index": "AGCTGATGTC", "index_rev": "TACACGCTCC", "index2": "TCATGTCCTG", "index2_rev": "CAGGACATGA"},
    {"index_id": "UDP0345", "index": "CTGAATTAGT", "index_rev": "CATGTAGAGG", "index2": "AATTCGATCG", "index2_rev": "CGATCGAATT"},
    {"index_id": "UDP0346", "index": "TAAGGAGGAA", "index_rev": "GGAATTCCAA", "index2": "TTCCGACATT", "index2_rev": "AATGTCGGAA"},
    {"index_id": "UDP0347", "index": "AGCTTACACA", "index_rev": "TTAGGTACCA", "index2": "TGGCACGACC", "index2_rev": "GGTCGTGCCA"},
    {"index_id": "UDP0348", "index": "AACCAGCCAC", "index_rev": "TAGATCCAGT", "index2": "GCCACAGCAC", "index2_rev": "GTGCTGTGGC"},
    {"index_id": "UDP0349", "index": "CTTAAGTCGA", "index_rev": "GTAAGGCATA", "index2": "CAGTAGTTGT", "index2_rev": "ACAACTACTG"},
    {"index_id": "UDP0350", "index": "GCCTAACGTG", "index_rev": "TTGTAACGGT", "index2": "AGCTCTCAAG", "index2_rev": "CTTGAGAGCT"},
    {"index_id": "UDP0351", "index": "ACTTACTTCA", "index_rev": "ACCAGCGACA", "index2": "TCTGGAATTA", "index2_rev": "TAATTCCAGA"},
    {"index_id": "UDP0352", "index": "CGCATTCCGT", "index_rev": "CTGGCTTGCC", "index2": "ATTAGTGGAG", "index2_rev": "CTCCACTAAT"},
    {"index_id": "UDP0353", "index": "GATATCACAC", "index_rev": "TCCTGACCGT", "index2": "GACTATATGT", "index2_rev": "ACATATAGTC"},
    {"index_id": "UDP0354", "index": "AGCGCTGTGT", "index_rev": "CGCACTAATG", "index2": "CGTTCGGAAC", "index2_rev": "GTTCCGAACG"},
    {"index_id": "UDP0355", "index": "TCACCGCGCT", "index_rev": "GGATACCAGA", "index2": "TCGATACTAG", "index2_rev": "CTAGTATCGA"},
    {"index_id": "UDP0356", "index": "GATAGCCTTG", "index_rev": "CCATCCACGC", "index2": "TACCACAATG", "index2_rev": "CATTGTGGTA"},
    {"index_id": "UDP0357", "index": "CCTGGACGCA", "index_rev": "GTCTCGTGAA", "index2": "TGGTATACCA", "index2_rev": "TGGTATACCA"},
    {"index_id": "UDP0358", "index": "TTACGCACCT", "index_rev": "CTTGGCCTCG", "index2": "GCTCTCGTTG", "index2_rev": "CAACGAGAGC"},
    {"index_id": "UDP0359", "index": "TCGTTGCTGC", "index_rev": "TATCATGAGA", "index2": "GTCTCGTGAA", "index2_rev": "TTCACGAGAC"},
    {"index_id": "UDP0360", "index": "CGACAAGGAT", "index_rev": "TGGACTCGTA", "index2": "AAGGCCACCT", "index2_rev": "AGGTGGCCTT"},
    {"index_id": "UDP0361", "index": "GTGTACCTTC", "index_rev": "CACTTCTACT", "index2": "CTGTGAGCTA", "index2_rev": "TAGCTCACAG"},
    {"index_id": "UDP0362", "index": "ACCTGGCCAA", "index_rev": "TGTGGAGTAA", "index2": "TCACAGATCG", "index2_rev": "CGATCTGTGA"},
    {"index_id": "UDP0363", "index": "TGTCTGGCCT", "index_rev": "AAGGCCTTGG", "index2": "AGAAGCCAAT", "index2_rev": "ATTGGCTTCT"},
    {"index_id": "UDP0364", "index": "AGTTAATGCT", "index_rev": "TTGTTCCGTG", "index2": "ACTGCAGCCG", "index2_rev": "CGGCTGCAGT"},
    {"index_id": "UDP0365", "index": "GGTGAGTAAT", "index_rev": "AGCACATCCT", "index2": "AACATCTAGT", "index2_rev": "ACTAGATGTT"},
    {"index_id": "UDP0366", "index": "TACTCTGCGC", "index_rev": "GCGTTGGTAT", "index2": "CCTTACTATG", "index2_rev": "CATAGTAAGG"},
    {"index_id": "UDP0367", "index": "AGGTATGGCG", "index_rev": "AGACACATTA", "index2": "GTGGCGAGAC", "index2_rev": "GTCTCGCCAC"},
    {"index_id": "UDP0368", "index": "TCCAGCCTGC", "index_rev": "GTTCGCGCCA", "index2": "GCCAGATCCA", "index2_rev": "TGGATCTGGC"},
    {"index_id": "UDP0369V3", "index": "GATGAATTCA", "index_rev": "ACCGCGCAAT", "index2": "TGCTGTGATT", "index2_rev": "AATCACAGCA"},
    {"index_id": "UDP0370V3", "index": "ATCCGGCAGC", "index_rev": "TAACAGTGTT", "index2": "GATCGAATAA", "index2_rev": "TTATTCGATC"},
    {"index_id": "UDP0371V3", "index": "ACGAACCATG", "index_rev": "TGATTAGCCA", "index2": "ACTGAATTAC", "index2_rev": "GTAATTCAGT"},
    {"index_id": "UDP0372V3", "index": "CAACCAAGTA", "index_rev": "TTCCAGGTAA", "index2": "CCATCCACGC", "index2_rev": "GCGTGGATGG"},
    {"index_id": "UDP0373", "index": "GTTGCGTTCA", "index_rev": "GGACCAACAG", "index2": "GTTGCAGTTG", "index2_rev": "CAACTGCAAC"},
    {"index_id": "UDP0374", "index": "CTTCAACCAC", "index_rev": "CCGAAGCGAG", "index2": "TTATGCGCCT", "index2_rev": "AGGCGCATAA"},
    {"index_id": "UDP0375", "index": "TCTATTCAGT", "index_rev": "TTAGGATAGA", "index2": "TCTCAGTACA", "index2_rev": "TGTACTGAGA"},
    {"index_id": "UDP0376", "index": "CAAGACGTCC", "index_rev": "ACAATAGAGT", "index2": "AGTATACGGA", "index2_rev": "TCCGTATACT"},
    {"index_id": "UDP0377", "index": "TGAGTACAAC", "index_rev": "GGTTATGCTA", "index2": "ACGCTTGGAC", "index2_rev": "GTCCAAGCGT"},
    {"index_id": "UDP0378", "index": "CCGCGGTTCT", "index_rev": "GTAGTAATAG", "index2": "GGAGTAGATT", "index2_rev": "AATCTACTCC"},
    {"index_id": "UDP0379", "index": "ATTGATACTG", "index_rev": "TACCGAACTA", "index2": "TACACGCTCC", "index2_rev": "GGAGCGTGTA"},
    {"index_id": "UDP0380", "index": "GGATTATGGA", "index_rev": "TCTTACATCA", "index2": "TCCGATAGAG", "index2_rev": "CTCTATCGGA"},
    {"index_id": "UDP0381", "index": "TGGTTCTCAT", "index_rev": "GACAGACAGG", "index2": "CTCAAGGCCG", "index2_rev": "CGGCCTTGAG"},
    {"index_id": "UDP0382", "index": "TCAACCACGA", "index_rev": "ACATGGTGTC", "index2": "CAAGTTCATA", "index2_rev": "TATGAACTTG"},
    {"index_id": "UDP0383", "index": "TATGAACTTG", "index_rev": "GTGCAACACT", "index2": "AATCCTTAGG", "index2_rev": "CCTAAGGATT"},
    {"index_id": "UDP0384", "index": "AGTGGTTAAG", "index_rev": "AGTGCCACTG", "index2": "GGTGGAATAC", "index2_rev": "GTATTCCACC"},
    {"index_id": "UDP0003", "index": "CGTCTCATAT", "index_rev": "TATCCAGGAC", "index2": "TATAGTAGCT", "index2_rev": "AGCTACTATA"},
    {"index_id": "UDP0005", "index": "GACGAGATTA", "index_rev": "TCCATGTTGC", "index2": "ACATTATCCT", "index2_rev": "AGGATAATGT"},
    {"index_id": "UDP0046", "index": "AGATCCATTA", "index_rev": "TAGAATAACG", "index2": "ATCTCTACCA", "index2_rev": "TGGTAGAGAT"},
    {"index_id": "UDP0053", "index": "GGAATTGTAA", "index_rev": "TGGCTCGCAG", "index2": "AGCACATCCT", "index2_rev": "AGGATGTGCT"},
    {"index_id": "UDP0054", "index": "GCATAAGCTT", "index_rev": "GGCGAGATGG", "index2": "TTCCGTCGCA", "index2_rev": "TGCGACGGAA"},
    {"index_id": "UDP0055", "index": "CTGAGGAATA", "index_rev": "GCCATTAGAC", "index2": "CTTAACCACT", "index2_rev": "AGTGGTTAAG"},
    {"index_id": "UDP0056", "index": "AACGCACGAG", "index_rev": "ATTGCCGAGT", "index2": "GCCTCGGATA", "index2_rev": "TATCCGAGGC"},
    {"index_id": "UDP0069", "index": "TGGAGTACTT", "index_rev": "TGACTACATA", "index2": "TCTGTGTGGA", "index2_rev": "TCCACACAGA"},
    {"index_id": "UDP0070", "index": "GTATTGACGT", "index_rev": "CAGCCGATTG", "index2": "GGAATTCCAA", "index2_rev": "TTGGAATTCC"},
    {"index_id": "UDP0071", "index": "CTTGTACACC", "index_rev": "CTGTCTGCAC", "index2": "AAGCGCGCTT", "index2_rev": "AAGCGCGCTT"},
    {"index_id": "UDP0072", "index": "ACACAGGTGG", "index_rev": "GTCGATTACA", "index2": "TGAGCGTTGT", "index2_rev": "ACAACGCTCA"},
    {"index_id": "UDP0073", "index": "CCTGCGGAAC", "index_rev": "TACGGCCGGT", "index2": "ATCATAGGCT", "index2_rev": "AGCCTATGAT"},
    {"index_id": "UDP0074", "index": "TTCATAAGGT", "index_rev": "GCGAGTTACC", "index2": "TGTTAGAAGG", "index2_rev": "CCTTCTAACA"},
    {"index_id": "UDP0075", "index": "CTCTGCAGCG", "index_rev": "TACGCGGCTG", "index2": "GATGGATGTA", "index2_rev": "TACATCCATC"},
    {"index_id": "UDP0076", "index": "CTGACTCTAC", "index_rev": "CGTATAATCA", "index2": "ACGGCCGTCA", "index2_rev": "TGACGGCCGT"},
    {"index_id": "UDP0084", "index": "ACAAGTGGAC", "index_rev": "CATACACTGT", "index2": "GCGCGATGTT", "index2_rev": "AACATCGCGC"},
    {"index_id": "UDP0102", "index": "ATGGCGCCTG", "index_rev": "TGCGTGTCAC", "index2": "TCCACGGCCT", "index2_rev": "AGGCCGTGGA"},
    {"index_id": "UDP0145", "index": "TATGATGGCC", "index_rev": "TGCCTGGTGG", "index2": "GATTGTCATA", "index2_rev": "TATGACAATC"},
    {"index_id": "UDP0146", "index": "CGCAGCAATT", "index_rev": "AGAGTGCGGC", "index2": "ATTCCGCTAT", "index2_rev": "ATAGCGGAAT"},
    {"index_id": "UDP0147", "index": "ACGTTCCTTA", "index_rev": "ATGTCGTGGT", "index2": "GACCGCTGTG", "index2_rev": "CACAGCGGTC"},
    {"index_id": "UDP0148", "index": "CCGCGTATAG", "index_rev": "TGGATGCTTA", "index2": "TAGGAACCGG", "index2_rev": "CCGGTTCCTA"},
    {"index_id": "UDP0155", "index": "ATAGCGGAAT", "index_rev": "CCTCGCAACC", "index2": "GCGCAGAGTA", "index2_rev": "TACTCTGCGC"},
    {"index_id": "UDP0179", "index": "TATCCGAGGC", "index_rev": "TTCTATGGTT", "index2": "GGCCAATAAG", "index2_rev": "CTTATTGGCC"},
    {"index_id": "UDP0218", "index": "TTGCTCTATT", "index_rev": "GTATGTAGAA", "index2": "GTGACCTTGA", "index2_rev": "TCAAGGTCAC"},
    {"index_id": "UDP0227", "index": "GCTTCATATT", "index_rev": "AACAAGGCGT", "index2": "CGTTCAGCCT", "index2_rev": "AGGCTGAACG"},
    {"index_id": "UDP0242", "index": "CCTGCAACCT", "index_rev": "GAGCGCAATA", "index2": "GTAGAGTCAG", "index2_rev": "CTGACTCTAC"},
    {"index_id": "UDP0244", "index": "ATCCTCTCAA", "index_rev": "AGTCAACCAT", "index2": "TCCGCAAGGC", "index2_rev": "GCCTTGCGGA"},
    {"index_id": "UDP0252", "index": "GTTGTGACTA", "index_rev": "TCGGCCTATC", "index2": "ACATAACGGA", "index2_rev": "TCCGTTATGT"},
    {"index_id": "UDP0256", "index": "TGCAAGATAA", "index_rev": "CTAATGATGG", "index2": "TTGAGGACGG", "index2_rev": "CCGTCCTCAA"},
    {"index_id": "UDP0258", "index": "CAGCGGTAGA", "index_rev": "GGTTGCCTCT", "index2": "GCAACAGGTG", "index2_rev": "CACCTGTTGC"},
    {"index_id": "UDP0265", "index": "TACCGCCTCG", "index_rev": "AACCATTCTC", "index2": "CCTCGCAACC", "index2_rev": "GGTTGCGAGG"},
    {"index_id": "UDP0266", "index": "CTGTTATATC", "index_rev": "GCCGTAACCG", "index2": "GTATAGCTGT", "index2_rev": "ACAGCTATAC"},
    {"index_id": "UDP0267", "index": "TAACCGGCGA", "index_rev": "CGGCAATGGA", "index2": "GCTACATTAG", "index2_rev": "CTAATGTAGC"},
    {"index_id": "UDP0285", "index": "TGATAACGAG", "index_rev": "GTGCCGCTTC", "index2": "GTTCCGCAGG", "index2_rev": "CCTGCGGAAC"},
    {"index_id": "UDP0286", "index": "CATAGTAAGG", "index_rev": "TAATGGCAAG", "index2": "ACCAAGTTAC", "index2_rev": "GTAACTTGGT"},
    {"index_id": "UDP0287", "index": "ATTGGCTTCT", "index_rev": "CCTATGACTC", "index2": "TGGCTCGCAG", "index2_rev": "CTGCGAGCCA"},
    {"index_id": "UDP0288", "index": "GTACCGATTA", "index_rev": "GAACATACGG", "index2": "AACTAACGTT", "index2_rev": "AACGTTAGTT"},
    {"index_id": "UDP0289", "index": "GAACAATTCC", "index_rev": "TCGTCTGACT", "index2": "TAGAGTTGGA", "index2_rev": "TCCAACTCTA"},
    {"index_id": "UDP0290", "index": "TGTGGTCCGG", "index_rev": "CTACTCAGTC", "index2": "AGAGCACTAG", "index2_rev": "CTAGTGCTCT"},
    {"index_id": "UDP0291", "index": "CTTCTAAGTC", "index_rev": "TGCCTTGATC", "index2": "ACTCTACAGG", "index2_rev": "CCTGTAGAGT"},
    {"index_id": "UDP0298", "index": "AGGAGTCGAG", "index_rev": "AGAGCACTAG", "index2": "TTAGGCTTAC", "index2_rev": "GTAAGCCTAA"},
    {"index_id": "UDP0301", "index": "CAACGAGAGC", "index_rev": "GCGCGATGTT", "index2": "GAATTGAGTG", "index2_rev": "CACTCAATTC"},
    {"index_id": "UDP0321", "index": "TCGACGCTAG", "index_rev": "TCCTATTGTG", "index2": "CCTCTTCGAA", "index2_rev": "TTCGAAGAGG"},
    {"index_id": "UDP0369", "index": "GCCATATAAC", "index_rev": "CTTATGGAAT", "index2": "ACACAATATC", "index2_rev": "GATATTGTGT"},
    {"index_id": "UDP0370", "index": "AGTGCGAGTG", "index_rev": "TCGGATGTCG", "index2": "TGGAGGTAAT", "index2_rev": "ATTACCTCCA"},
    {"index_id": "UDP0371", "index": "CTGAGCCGGT", "index_rev": "TATCTGACCT", "index2": "CCTTCACGTA", "index2_rev": "TACGTGAAGG"},
    {"index_id": "UDP0372", "index": "AACGGTCTAT", "index_rev": "CGCTCAGTTC", "index2": "CTATACGCGG", "index2_rev": "CCGCGTATAG"},
]


def get_cttso_index_id_from_index(index_str: str, index_type: str) -> str:
    """
    Base function for get_cttso_i7_index_id_from_index and get_cttso_i5_index_id_from_index2
    """
    if len(index_str) == 10:
        try:
            return next(
                filter(
                    lambda index_dict: index_dict.get(index_type) == index_str,
                    V2_CTTSO_VALID_INDEXES
                )
            ).get("index_id")
        except StopIteration:
            logger.error(f"Could not get index id for {index_type} - {index_str}")
            raise ValueError
    elif len(index_str) == 8:
        try:
            return next(
                filter(
                    lambda index_dict: index_dict.get(index_type) == index_str,
                    V1_CTTSO_VALID_INDEXES
                )
            ).get("index_id")
        except StopIteration:
            logger.error(f"Could not get index id for {index_type} - {index_str}")
            raise ValueError


def get_cttso_i7_index_id_from_index(i7_index_str: str) -> str:
    return get_cttso_index_id_from_index(i7_index_str, "index")


def get_cttso_i5_index_id_from_index(i5_index_str: str, is_forward_index_orientation: Optional[bool] = None) -> str:
    if is_forward_index_orientation is not None:
        if is_forward_index_orientation:
            return get_cttso_index_id_from_index(i5_index_str, "index2")
        else:
            return get_cttso_index_id_from_index(i5_index_str, "index2_rev")
    else:
        og_log_level = logger.level
        logger.setLevel(logging.CRITICAL)
        try:
            index_id = get_cttso_index_id_from_index(i5_index_str, "index2")
        except ValueError:
            logger.setLevel(og_log_level)
            index_id = get_cttso_index_id_from_index(i5_index_str, "index2_rev")
        logger.setLevel(og_log_level)

        return index_id


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """

    # Get the instrument run id
    instrument_run_id = event.get("instrument_run_id")

    # Get the bclconvert data rows
    bclconvert_data_rows = event.get("bclconvert_data_rows")

    # Set the header
    header = deepcopy(HEADER)
    header["run_name"] = instrument_run_id

    # Set the reads
    reads = deepcopy(READS)

    # Set the bclconvert settings
    if len(bclconvert_data_rows[0].get("index")) == 8:
        bclconvert_settings = deepcopy(V1_BCLCONVERT_SETTINGS)
    else:
        bclconvert_settings = deepcopy(V2_BCLCONVERT_SETTINGS)

    # Set the bclconvert data
    # Take only the sample id, index, index2 and lane
    bclconvert_data = list(
        map(
            lambda bclconvert_data_row_iter: {
                "sample_id": bclconvert_data_row_iter.get("sample_id"),
                "index": bclconvert_data_row_iter.get("index"),
                "index2": bclconvert_data_row_iter.get("index2"),
                "lane": bclconvert_data_row_iter.get("lane")
            },
            bclconvert_data_rows
        )
    )

    # Set the tso500 settings
    if len(bclconvert_data_rows[0].get("index")) == 8:
        tso500l_settings = deepcopy(V1_TSO500L_SETTINGS)
    else:
        tso500l_settings = deepcopy(V2_TSO500L_SETTINGS)

    # Set the tso500l data
    tso500l_data = [
        {
            "sample_id": bclconvert_data_rows[0].get("sample_id"),
            "sample_type": TSO500L_SAMPLE_TYPE,
            "index": bclconvert_data_rows[0].get("index"),
            "index2": bclconvert_data_rows[0].get("index2"),
            "i7_index_id": get_cttso_i7_index_id_from_index(bclconvert_data_rows[0].get("index")),
            "i5_index_id": get_cttso_i5_index_id_from_index(bclconvert_data_rows[0].get("index2")),
        }
    ]

    # If any of the index ids end with V3, we might need to a bit of a 'switcheroo' to
    # convince the dragen tso500 pipeline we can pass the samplesheet validation step
    for tso500l_data_row in tso500l_data:
        if tso500l_data_row["i7_index_id"].endswith("V3"):
            # Update the tso500 row i7 index id and index
            tso500l_data_row["i7_index_id"] = tso500l_data_row["i7_index_id"].replace("V3", "")
            tso500l_data_row["index"] = next(filter(
                lambda index_dict: index_dict.get("index_id") == tso500l_data_row["i7_index_id"],
                V2_CTTSO_VALID_INDEXES
            )).get("index")
            # We will also need to update the bclconvert data row index
            for bclconvert_data_row in bclconvert_data:
                if bclconvert_data_row["sample_id"] == tso500l_data_row["sample_id"]:
                    bclconvert_data_row["index"] = tso500l_data_row["index"]

        if tso500l_data_row["i5_index_id"].endswith("V3"):
            # Update the tso500 row i5 index id and index2
            tso500l_data_row["i5_index_id"] = tso500l_data_row["i5_index_id"].replace("V3", "")
            tso500l_data_row["index2"] = next(filter(
                lambda index_dict: index_dict.get("index_id") == tso500l_data_row["i5_index_id"],
                V2_CTTSO_VALID_INDEXES
            )).get("index2")
            # We will also need to update the bclconvert data row index
            for bclconvert_data_row in bclconvert_data:
                if bclconvert_data_row["sample_id"] == tso500l_data_row["sample_id"]:
                    bclconvert_data_row["index2"] = tso500l_data_row["index2"]

    return {
        "samplesheet": {
            "header": header,
            "reads": reads,
            "bclconvert_settings": bclconvert_settings,
            "bclconvert_data": bclconvert_data,
            "tso500l_settings": tso500l_settings,
            "tso500l_data": tso500l_data
        }
    }

# ## V2 SampleSheet
# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "bclconvert_data_rows": [
#                         {
#                             "sample_id": "L2500613",
#                             "index": "CGACATCCGA",
#                             "index2": "AATGAACGTA",
#                             "lane": 4
#                         }
#                     ],
#                     "instrument_run_id": "250523_A01052_0263_AHFHHTDSXF"
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "samplesheet": {
#     #         "header": {
#     #             "file_format_version": 2,
#     #             "run_name": "250523_A01052_0263_AHFHHTDSXF",
#     #             "instrument_type": "NovaSeq"
#     #         },
#     #         "reads": {
#     #             "read_1_cycles": 151,
#     #             "read_2_cycles": 151,
#     #             "index_1_cycles": 10,
#     #             "index_2_cycles": 10
#     #         },
#     #         "bclconvert_settings": {
#     #             "adapter_behavior": "trim",
#     #             "adapter_read_1": "CTGTCTCTTATACACATCT",
#     #             "adapter_read_2": "CTGTCTCTTATACACATCT",
#     #             "minimum_trimmed_read_length": 35,
#     #             "mask_short_reads": 35,
#     #             "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #         },
#     #         "bclconvert_data": [
#     #             {
#     #                 "sample_id": "L2500613",
#     #                 "index": "CGTCTCATAT",
#     #                 "index2": "TATAGTAGCT",
#     #                 "lane": 4
#     #             }
#     #         ],
#     #         "tso500l_settings": {
#     #             "adapter_read_1": "CTGTCTCTTATACACATCT",
#     #             "adapter_read_2": "CTGTCTCTTATACACATCT",
#     #             "minimum_trimmed_read_length": 35,
#     #             "mask_short_reads": 35,
#     #             "override_cycles": "U7N1Y143;I10;I10;U7N1Y143"
#     #         },
#     #         "tso500l_data": [
#     #             {
#     #                 "sample_id": "L2500613",
#     #                 "sample_type": "DNA",
#     #                 "index": "CGTCTCATAT",
#     #                 "index2": "TATAGTAGCT",
#     #                 "i7_index_id": "UDP0003",
#     #                 "i5_index_id": "UDP0003"
#     #             }
#     #         ]
#     #     }
#     # }


# V1 SampleSheet
# if __name__ == "__main__":
#     import json
#     print(
#         json.dumps(
#             handler(
#                 {
#                     "instrument_run_id": "240424_A01052_0193_BH7JMMDRX5",
#                     "bclconvert_data_rows": [
#                       {
#                         "sample_id": "L2401146",
#                         "lane": 4,
#                         "index": "ATGCGGCT",
#                         "index2": "TAGCCGCG"
#                       }
#                     ]
#                 },
#                 None
#             ),
#             indent=4
#         )
#     )
#
#     # {
#     #     "samplesheet": {
#     #         "header": {
#     #             "file_format_version": 2,
#     #             "run_name": "240424_A01052_0193_BH7JMMDRX5",
#     #             "instrument_type": "NovaSeq"
#     #         },
#     #         "reads": {
#     #             "read_1_cycles": 151,
#     #             "read_2_cycles": 151,
#     #             "index_1_cycles": 10,
#     #             "index_2_cycles": 10
#     #         },
#     #         "bclconvert_settings": {
#     #             "adapter_behavior": "trim",
#     #             "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
#     #             "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
#     #             "minimum_trimmed_read_length": 35,
#     #             "mask_short_reads": 35,
#     #             "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#     #         },
#     #         "bclconvert_data": [
#     #             {
#     #                 "sample_id": "L2401146",
#     #                 "index": "ATGCGGCT",
#     #                 "index2": "TAGCCGCG",
#     #                 "lane": 4
#     #             }
#     #         ],
#     #         "tso500l_settings": {
#     #             "adapter_behavior": "trim",
#     #             "adapter_read_1": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
#     #             "adapter_read_2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
#     #             "minimum_trimmed_read_length": 35,
#     #             "mask_short_reads": 35,
#     #             "override_cycles": "U7N1Y143;I8N2;I8N2;U7N1Y143"
#     #         },
#     #         "tso500l_data": [
#     #             {
#     #                 "sample_id": "L2401146",
#     #                 "sample_type": "DNA",
#     #                 "lane": 4,
#     #                 "index": "ATGCGGCT",
#     #                 "index2": "TAGCCGCG",
#     #                 "i7_index_id": "UP14",
#     #                 "i5_index_id": "UP14"
#     #             }
#     #         ]
#     #     }
#     # }
