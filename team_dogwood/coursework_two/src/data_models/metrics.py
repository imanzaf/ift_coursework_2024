"""
Store ESG metrics data models.
"""

from pydantic import BaseModel, Field


class ScopeMetrics(BaseModel):
    """
    Class for representing Scope 1, 2, and 3 emissions metrics.
    """

    scope_1: float = Field(
        ...,
        description="Scope 1 emissions in metric tons of CO2 equivalent.",
    )
    scope_2: float = Field(
        ...,
        description="Scope 2 emissions in metric tons of CO2 equivalent.",
    )
    scope_3: float = Field(
        ...,
        description="Scope 3 emissions in metric tons of CO2 equivalent.",
    )


class WaterMetrics(BaseModel):
    """
    Class for representing water usage metrics.
    """

    total_water_usage: float = Field(
        ...,
        description="Total water usage in cubic meters.",
    )
    water_usage_intensity: float = Field(
        ...,
        description="Water usage intensity in cubic meters per unit of production.",
    )