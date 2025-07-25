from pydantic import BaseModel


class QuestionAnswerSchema(BaseModel):
    answer: str
    question: str

class QASchemaWithForceSave(QuestionAnswerSchema):
    force_save: bool = False

class QADetailsSchema(QuestionAnswerSchema):
    details: str