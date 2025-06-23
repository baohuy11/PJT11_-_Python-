from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProblemBase(BaseModel):
    title: str
    description: str
    test_cases: str
    expected_output: str
    difficulty: Optional[str] = "beginner"

class ProblemCreate(ProblemBase):
    pass

class Problem(ProblemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SubmissionBase(BaseModel):
    problem_id: int
    student_name: str
    code: str

class SubmissionCreate(SubmissionBase):
    pass

class Submission(SubmissionBase):
    id: int
    status: str
    test_results: Optional[str] = None
    advice: Optional[str] = None
    cost: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdviceResponse(BaseModel):
    advice: str
    test_results: Dict[str, Any]
    cost: int
    suggestions: List[str]