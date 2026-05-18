"""User profile — captured during `warmapply init`, used by every command after.

Profile lives at ~/.warmapply/profile.yaml. Resume is copied to
~/.warmapply/resume.md. We extract most fields from the resume itself
(name, email, LinkedIn, location) and ask the user for the parts no
resume contains: what they actually want.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

import yaml
from platformdirs import user_data_dir


def applybrief_dir() -> Path:
    p = Path(user_data_dir("applybrief", appauthor=False))
    p.mkdir(parents=True, exist_ok=True)
    return p


def profile_path() -> Path:
    return applybrief_dir() / "profile.yaml"


def resume_path() -> Path:
    return applybrief_dir() / "resume.md"


def briefs_dir() -> Path:
    d = applybrief_dir() / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def discoveries_dir() -> Path:
    d = applybrief_dir() / "discoveries"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Profile:
    # Extracted from resume (do not ask the user)
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    location: str = ""  # current city/region from resume
    current_title: str = ""
    years_experience: int = 0

    # User's own words — captured during init, kept verbatim for the LLM
    narrative: str = ""               # "what kind of work are you looking for?"
    must_haves: str = ""              # "what do you absolutely need?"
    deal_breakers: str = ""           # "what do you not want?"
    other_context: str = ""           # "anything else I should know?"

    # Parsed from the narrative + resume (for search + filtering)
    target_roles: list[str] = field(default_factory=list)
    target_seniority: str = ""        # IC / senior / lead / manager / director / vp
    remote: str = "remote"            # remote | hybrid | onsite | any
    locations: list[str] = field(default_factory=list)
    comp_floor: int = 0
    industries_focus: list[str] = field(default_factory=list)
    industries_avoid: list[str] = field(default_factory=list)
    clearance: str = ""               # "" | secret | top-secret | ts-sci | public-trust
    special_circumstances: str = ""   # short summary the LLM uses everywhere

    # LLM provider
    llm_model: str = "anthropic/claude-haiku-4-5"

    version: int = 2

    @classmethod
    def load(cls) -> Profile | None:
        p = profile_path()
        if not p.exists():
            return None
        data = yaml.safe_load(p.read_text()) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self) -> Path:
        p = profile_path()
        p.write_text(yaml.safe_dump(asdict(self), sort_keys=False))
        return p

    def resume_text(self) -> str:
        r = resume_path()
        if not r.exists():
            return ""
        return r.read_text()

    def context_block(self) -> str:
        """Compact block the LLM can use in any prompt to know who this person is and what they want."""
        lines = ["# Candidate"]
        if self.name:
            lines.append(f"- name: {self.name}")
        if self.current_title:
            lines.append(f"- current title: {self.current_title}")
        if self.location:
            lines.append(f"- location: {self.location}")
        if self.years_experience:
            lines.append(f"- years experience: {self.years_experience}")
        lines.append("")
        lines.append("# What they're looking for (their words)")
        if self.narrative:
            lines.append(self.narrative)
        if self.must_haves:
            lines.append(f"\n**Must-haves:** {self.must_haves}")
        if self.deal_breakers:
            lines.append(f"\n**Won't accept:** {self.deal_breakers}")
        if self.other_context:
            lines.append(f"\n**Other context:** {self.other_context}")
        lines.append("")
        lines.append("# Structured (parsed)")
        if self.target_roles:
            lines.append(f"- target roles: {', '.join(self.target_roles)}")
        if self.target_seniority:
            lines.append(f"- target seniority: {self.target_seniority}")
        lines.append(f"- work mode: {self.remote}")
        if self.locations:
            lines.append(f"- locations: {', '.join(self.locations)}")
        if self.comp_floor:
            lines.append(f"- comp floor: ${self.comp_floor:,}")
        if self.industries_focus:
            lines.append(f"- industries (focus): {', '.join(self.industries_focus)}")
        if self.industries_avoid:
            lines.append(f"- industries (avoid): {', '.join(self.industries_avoid)}")
        if self.clearance:
            lines.append(f"- clearance: {self.clearance}")
        if self.special_circumstances:
            lines.append(f"- notes: {self.special_circumstances}")
        return "\n".join(lines)
