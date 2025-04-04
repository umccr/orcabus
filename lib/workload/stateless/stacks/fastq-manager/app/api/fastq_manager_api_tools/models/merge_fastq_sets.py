from pydantic import BaseModel
from typing import List

class MergePatch(BaseModel):
    fastq_set_ids: List[str]
 
