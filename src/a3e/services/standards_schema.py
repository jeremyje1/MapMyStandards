"""Pydantic models for standards corpus validation."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class IndicatorList(BaseModel):
    __root__: List[str]  # For potential future expansion


class Clause(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    indicators: Optional[List[str]] = Field(default=None)


class Standard(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    clauses: Optional[List[Clause]] = Field(default=None)
    version: Optional[str] = None
    effective_date: Optional[str] = None


class Corpus(BaseModel):
    accreditor: str
    version: Optional[str] = None
    effective_date: Optional[str] = None
    standards: List[Standard]
