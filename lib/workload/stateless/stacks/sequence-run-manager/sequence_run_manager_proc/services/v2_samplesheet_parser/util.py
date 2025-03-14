import re

# https://regex101.com/r/AneCvL/1
# Matches any number of headers, separated by commas
# Matches [Header], [Header, Header2], [Test_Section_1]
HEADER_REGEX_MATCH = re.compile(
    r"\[([a-zA-Z0-9_]+)](?:,*)?"
)

def pascal_case_to_snake_case(s: str) -> str:
    """
    Convert string from PascalCase to snake_case with special cases handling.
    
    Examples:
        TrimUMI -> trim_umi
        Sample_ID -> sample_id
        Cloud_Workflow -> cloud_workflow
        Index_ID -> index_id
        I7_Index_ID -> i7_index_id
        I5_Index_ID -> i5_index_id
        Sample_Type -> sample_type
        Sample_Description -> sample_description
        BCLConvert_Settings -> bclconvert_settings
        TSO500L_Settings -> tso500l_settings
        TSO500_Settings -> tso500_settings
        Read1Cycles -> read_1_cycles
    """
    # Special case replacements
    replacements = {
        'UMI': 'Umi',
        'ID': 'Id',
        'BCLConvert': 'Bclconvert',
        'TSO500L': 'Tso500l',
        'TSO500': 'Tso500'
    }
    
    # Apply initial replacements
    result = s
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Remove underscores and convert to snake_case
    result = ''.join(result.split('_'))
    result = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in result]).lstrip('_')
    
    # Handle numeric cases (processed after converting to snake case)
    number_replacements = [
        ('read1_', 'read_1_'),
        ('read2_', 'read_2_'),
        ('index1_', 'index_1_'),
        ('index2_', 'index_2_'),
        ('_index1', '_index_1'),
        ('_index2', '_index_2'),
        ('_read1', '_read_1'),
        ('_read2', '_read_2')
    ]
    
    for old, new in number_replacements:
        result = result.replace(old, new)
        
    return result

