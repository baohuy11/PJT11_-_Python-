from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    test_cases = Column(Text)  # JSON文字列として保存
    expected_output = Column(Text)
    difficulty = Column(String, default="beginner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    submissions = relationship("Submission", back_populates="problem")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    student_name = Column(String, index=True)
    code = Column(Text)
    status = Column(String, default="pending")  # pending, evaluated
    test_results = Column(Text)  # JSON文字列として保存
    advice = Column(Text)
    cost = Column(Integer, default=0)  # LLM使用料（token数など）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    problem = relationship("Problem", back_populates="submissions")