"""Validated data structures returned by the language model."""

from pydantic import BaseModel, ConfigDict, Field


class ActionItem(BaseModel):
    """One transcript-grounded action item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(min_length=1, description="A concrete, verifiable action.")
    owner: str = Field(
        default="Unassigned",
        min_length=1,
        description="The supported owner, or 'Unassigned'.",
    )
    due_date: str = Field(
        default="Not specified",
        min_length=1,
        description="The supported due date, or 'Not specified'.",
    )
    evidence_excerpt: str = Field(
        min_length=1,
        description="A short verbatim excerpt from the transcript.",
    )
    speaker: str = Field(min_length=1, description="Speaker associated with the evidence.")
    timestamp: str = Field(
        min_length=1,
        description="Transcript timestamp, or 'Not specified' when unavailable.",
    )


class ActionReport(BaseModel):
    """The complete structured extraction for one transcript."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    actions: list[ActionItem] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

