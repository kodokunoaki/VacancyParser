from pydantic import BaseModel, Field


class Vacancy(BaseModel):
    title: str
    company: str
    url: str
    description: str = "—"
    key_skills: list[str] = Field(default_factory=list)

    @property
    def key_skills_text(self) -> str:
        return ", ".join(self.key_skills) if self.key_skills else "—"
