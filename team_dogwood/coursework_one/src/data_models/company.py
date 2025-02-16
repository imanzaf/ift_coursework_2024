from typing import List

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
    url: str = Field(..., description="The URL of the ESG report")
    date: str = Field(..., description="The date the ESG report was published")
