from typing import List, Optional, Union

from pydantic import BaseModel, Field


class Company(BaseModel):
    """
    Represents a company with its associated details and ESG reports.

    This class models a company, including its stock symbol, name, sector, industry,
    location, and any associated ESG (Environmental, Social, and Governance) reports.

    :param symbol: The stock symbol of the company.
    :type symbol: str
    :param security: The name of the company.
    :type security: str
    :param gics_sector: The GICS sector of the company.
    :type gics_sector: str
    :param gics_industry: The GICS industry of the company.
    :type gics_industry: str
    :param country: The country where the company is headquartered.
    :type country: str
    :param region: The region where the company is headquartered.
    :type region: str
    :param esg_reports: A list of ESG reports associated with the company.
    :type esg_reports: List[ESGReport], optional

    Example:
        >>> company = Company(
        ...     symbol="AAPL",
        ...     security="Apple Inc.",
        ...     gics_sector="Information Technology",
        ...     gics_industry="Technology Hardware, Storage & Peripherals",
        ...     country="United States",
        ...     region="North America",
        ...     esg_reports=[]
        ... )
        >>> print(company.symbol)
        AAPL
    """

    symbol: Optional[str] = Field(None, description="The stock symbol of the company")
    security: str = Field(..., description="The name of the company")
    gics_sector: Optional[str] = Field(
        None, description="The GICS sector of the company"
    )
    gics_industry: Optional[str] = Field(
        None, description="The GICS industry of the company"
    )
    country: Optional[str] = Field(
        None, description="The country company is headquartered in"
    )
    region: Optional[str] = Field(
        None, description="The region the company is headquartered in"
    )
    esg_reports: List["ESGReport"] = Field(
        None, description="The ESG reports of the company"
    )


class ESGReport(BaseModel):
    """
    Represents an ESG (Environmental, Social, and Governance) report.

    This class models an ESG report, including its URL and the year it was published.

    :param url: The URL of the ESG report.
    :type url: Optional[str]
    :param year: The year the ESG report was published.
    :type year: Optional[str]

    Example:
        >>> report = ESGReport(
        ...     url="https://example.com/esg-report-2023.pdf",
        ...     year="2023"
        ... )
        >>> print(report.url)
        https://example.com/esg-report-2023.pdf
    """

    url: Optional[str] = Field(None, description="The URL of the ESG report")
    year: Optional[Union[str, int]] = Field(
        None, description="The year the ESG report was published"
    )


class SearchResult(BaseModel):
    """
    Represents a search result from a query.

    This class models a search result, including its title, metatag title, author, link, and snippet.

    :param title: The title of the search result.
    :type title: str
    :param metatag_title: The metatag title of the search result.
    :type metatag_title: Optional[str]
    :param author: The author of the page.
    :type author: Optional[str]
    :param link: The link to the search result.
    :type link: str
    :param snippet: The snippet of the search result.
    :type snippet: str

    Example:
        >>> result = SearchResult(
        ...     title="Example Search Result",
        ...     metatag_title="Example Meta Title",
        ...     author="John Doe",
        ...     link="https://example.com",
        ...     snippet="This is an example search result snippet."
        ... )
        >>> print(result.title)
        Example Search Result
    """

    title: str = Field(..., description="The title of the search result")
    metatag_title: Optional[str] = Field(
        None, description="The metatag title of the search result"
    )
    author: Optional[str] = Field(None, description="The author of the page")
    link: str = Field(..., description="The link to the search result")
    snippet: str = Field(..., description="The snippet of the search result")
