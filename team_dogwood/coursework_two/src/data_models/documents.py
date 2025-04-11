"""
Store ESG report data models.
"""

from pydantic import BaseModel, Field

from typing import List, Optional

from llama_index.core import Document


class ESGReport(BaseModel):
    """
    Class for representing an ESG report.
    """
    
    pages: List[Document] = Field(
        ...,
        description="List of extracted pages in the ESG report.",
    )
