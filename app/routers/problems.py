from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models import models, schemas

router = APIRouter(prefix="/problems", tags=["problems"])

@router.post("/", response_model=schemas.Problem)
def create_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    """
    問題を作成（管理者用）
    """
    db_problem = models.Problem(**problem.dict())
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem

@router.get("/", response_model=List[schemas.Problem])
def get_problems(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    問題一覧を取得
    """
    problems = db.query(models.Problem).offset(skip).limit(limit).all()
    return problems

@router.get("/{problem_id}", response_model=schemas.Problem)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    """
    特定の問題を取得
    """
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.put("/{problem_id}", response_model=schemas.Problem)
def update_problem(problem_id: int, problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    """
    問題を更新（管理者用）
    """
    db_problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if db_problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    for key, value in problem.dict().items():
        setattr(db_problem, key, value)
    
    db.commit()
    db.refresh(db_problem)
    return db_problem

@router.delete("/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    """
    問題を削除（管理者用）
    """
    db_problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if db_problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    db.delete(db_problem)
    db.commit()
    return {"message": "Problem deleted successfully"}