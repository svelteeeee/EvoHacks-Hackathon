from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from backend.config import COUNTRIES, LANGUAGES

Theme = Literal["economy", "security", "human_cost", "diplomacy", "accountability", "innovation"]
THEMES = ["economy", "security", "human_cost", "diplomacy", "accountability", "innovation"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Article(StrictModel):
    id: str
    country: str
    outlet: str
    url: HttpUrl
    headline: str
    text: str
    language: str
    published: str
    coverage: Literal["full_text", "excerpt", "headline"]
    retrieval: str


class Claim(StrictModel):
    text: str
    quote: str


class LoadedWord(StrictModel):
    word: str
    explanation: str
    neutral: str


class ThemeScore(StrictModel):
    theme: Theme
    score: int = Field(ge=0, le=100)
    quote: str
    rationale: str


class Framing(StrictModel):
    translated_headline: str
    translated_text: str
    key_claims: list[Claim]
    loaded_words: list[LoadedWord]
    blamed: list[str]
    praised: list[str]
    tone: Literal["celebratory", "critical", "cautious", "alarmed", "matter_of_fact", "sympathetic"]
    themes: list[ThemeScore]
    omitted: list[str]
    confidence: float = Field(ge=0, le=1)


class OutletAnalysis(StrictModel):
    article: Article
    framing: Framing
    method: Literal["groq", "curated_demo"]


class ReferencedClaim(StrictModel):
    text: str
    source_ids: list[str] = Field(min_length=1)


class ClaimCluster(StrictModel):
    claim: str
    status: Literal["shared", "different_emphasis", "single_source", "disputed"]
    source_ids: list[str] = Field(min_length=1)
    note: str


class MissingVoice(StrictModel):
    perspective: str
    why_it_matters: str
    source_ids: list[str] = Field(min_length=1)


class Synthesis(StrictModel):
    summary: list[ReferencedClaim]
    simple_summary: list[ReferencedClaim]
    clusters: list[ClaimCluster]
    missing_voices: list[MissingVoice]
    caveat: str


class CountryResult(StrictModel):
    country: str
    outlets: list[OutletAnalysis]
    status: Literal["ready", "partial", "failed"]
    message: str


class Report(StrictModel):
    id: str
    query: str
    language: str
    mode: Literal["live", "demo", "cache"]
    created_at: str
    countries: list[CountryResult]
    synthesis: Synthesis
    notices: list[str]


class AnalysisRequest(StrictModel):
    query: str = Field(min_length=3, max_length=160)
    language: str = "en"
    countries: list[str] = Field(
        default_factory=lambda: list(COUNTRIES), min_length=1, max_length=6
    )
    demo: bool = False

    @field_validator("query")
    @classmethod
    def clean_query(cls, value: str) -> str:
        return " ".join(value.split())

    @model_validator(mode="after")
    def meaningful_query(self):
        if len(self.query) < 3:
            raise ValueError("Enter at least three non-space characters")
        return self

    @field_validator("countries")
    @classmethod
    def valid_countries(cls, value: list[str]) -> list[str]:
        if any(c not in COUNTRIES for c in value) or len(set(value)) != len(value):
            raise ValueError("Select unique supported countries")
        return value

    @field_validator("language")
    @classmethod
    def valid_language(cls, value: str) -> str:
        if value not in LANGUAGES:
            raise ValueError("Unsupported summary language")
        return value
