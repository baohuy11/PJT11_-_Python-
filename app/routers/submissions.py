from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
from app.database.database import get_db
from app.models import models, schemas
from app.services.code_evaluator import CodeEvaluator
from app.services.gemini_service import GeminiAdviceService

router = APIRouter(prefix="/submissions", tags=["submissions"])

@router.post("/", response_model=schemas.Submission)
def create_submission(
    submission: schemas.SubmissionCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    コードを提出
    """
    # 問題が存在するかチェック
    problem = db.query(models.Problem).filter(models.Problem.id == submission.problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # 提出を作成
    db_submission = models.Submission(**submission.dict())
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # バックグラウンドでコード評価を実行
    background_tasks.add_task(evaluate_submission, db_submission.id, db)
    
    return db_submission

@router.get("/{submission_id}", response_model=schemas.Submission)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """
    提出を取得
    """
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

@router.get("/{submission_id}/advice", response_model=schemas.AdviceResponse)
def get_advice(submission_id: int, db: Session = Depends(get_db)):
    """
    アドバイスを取得
    """
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission.status != "evaluated":
        raise HTTPException(status_code=400, detail="Submission not yet evaluated")
    
    try:
        test_results = json.loads(submission.test_results) if submission.test_results else {}
        advice_data = json.loads(submission.advice) if submission.advice else {}
        
        return schemas.AdviceResponse(
            advice=advice_data.get("advice", "アドバイスがありません"),
            test_results=test_results,
            cost=submission.cost,
            suggestions=advice_data.get("suggestions", [])
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse advice data")

@router.get("/", response_model=List[schemas.Submission])
def get_submissions(
    skip: int = 0, 
    limit: int = 100, 
    problem_id: int = None, 
    db: Session = Depends(get_db)
):
    """
    提出一覧を取得
    """
    query = db.query(models.Submission)
    if problem_id:
        query = query.filter(models.Submission.problem_id == problem_id)
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions

def evaluate_submission(submission_id: int, db: Session):
    """
    バックグラウンドタスクとして実行される評価処理
    """
    try:
        # 提出との問題を取得
        submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        problem = db.query(models.Problem).filter(models.Problem.id == submission.problem_id).first()
        
        if not submission or not problem:
            return
        
        # コード評価サービスの初期化
        evaluator = CodeEvaluator()
        gemini_service = GeminiAdviceService()
        
        # 安全性チェック
        is_safe, safety_warnings = evaluator.check_code_safety(submission.code)
        if not is_safe:
            submission.status = "error"
            submission.advice = json.dumps({
                "advice": "コードに安全上の問題があります。",
                "suggestions": safety_warnings,
                "hints": []
            })
            db.commit()
            return
        
        # コード評価の実行
        test_results, all_passed = evaluator.evaluate_code(submission.code, problem.test_cases)
        
        # チート検出
        cheat_result = gemini_service.detect_cheating(submission.code, problem.description)
        
        # アドバイス生成
        advice_data = gemini_service.generate_advice(
            submission.code, 
            problem.description, 
            test_results
        )
        
        # チート検出結果をアドバイスに追加
        if cheat_result.get("is_cheating", False) and cheat_result.get("confidence", 0) > 0.7:
            advice_data["advice"] = "提出されたコードには不適切な内容が含まれている可能性があります。問題を理解し、自分で解法を考えてみましょう。"
            advice_data["suggestions"] = cheat_result.get("recommendations", [])
        
        # 結果をデータベースに保存
        submission.status = "evaluated"
        submission.test_results = json.dumps(test_results)
        submission.advice = json.dumps(advice_data)
        submission.cost = advice_data.get("token_count", 0)
        
        db.commit()
        
    except Exception as e:
        # エラーハンドリング
        submission.status = "error"
        submission.advice = json.dumps({
            "advice": f"評価中にエラーが発生しました: {str(e)}",
            "suggestions": [],
            "hints": []
        })
        db.commit()