from pydantic import BaseModel


class QuestionAnswer(BaseModel):
    question: str
    answer: str

class QuestionLimit(BaseModel):
    limit: int = 5
    question: str

class QASearchResult(BaseModel):
    question: str | None
    answer: str | None
    score: float
    uuid: str
