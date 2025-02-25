from typing import List, Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    symbol: str = Field(..., description="The stock symbol of the company")
    security: str = Field(..., description="The name of the company")
    gics_sector: str = Field(..., description="The GICS sector of the company")
    gics_industry: str = Field(..., description="The GICS industry of the company")
    country: str = Field(..., description="The country company is headquartered in")
    region: str = Field(..., description="The region the company is headquartered in")
    esg_reports: List["ESGReport"] = Field(
        None, description="The ESG reports of the company"
    )


class ESGReport(BaseModel):
    url: Optional[str] = Field(None, description="The URL of the ESG report")
    year: Optional[str] = Field(
        None, description="The year the ESG report was published"
    )


class SearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result")
    metatag_title: Optional[str] = Field(
        None, description="The metatag title of the search result"
    )
    author: Optional[str] = Field(None, description="The author of the page")
    link: str = Field(..., description="The link to the search result")
    snippet: str = Field(..., description="The snippet of the search result")
