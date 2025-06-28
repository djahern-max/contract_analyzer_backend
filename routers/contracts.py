# routers/contracts.py
import os
import shutil
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.project import Project
from models.contract import Contract
from routers.auth import get_current_active_user
from services.contract_analyzer import ContractAnalyzer
import uuid
from datetime import datetime

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Pydantic models
class ContractDetailResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_url: str
    is_processed: str
    created_at: str
    updated_at: str
    contract_data: dict = {}

    class Config:
        from_attributes = True


class ContractAnalysisResponse(BaseModel):
    contract_id: int
    analysis: dict
    success: bool
    message: str


# Helper functions
def save_uploaded_file(upload_file: UploadFile, project_id: int) -> str:
    """Save uploaded file and return the file path"""
    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Create project subdirectory
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(exist_ok=True)

    file_path = project_dir / unique_filename

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


async def analyze_contract_background(contract_id: int, file_path: str, db_url: str):
    """Background task to analyze contract"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create new DB session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        # Get contract
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return

        # Update status to processing
        contract.is_processed = "processing"
        db.commit()

        # Analyze with local file
        analyzer = ContractAnalyzer()
        result = await analyzer.analyze_contract_from_local_file(file_path)

        if result["success"]:
            # Update contract with analysis results
            contract.contract_data = result["analysis"]
            contract.is_processed = "completed"
            contract.processed_at = datetime.utcnow()
        else:
            # Handle analysis failure
            contract.contract_data = {"error": result["error"]}
            contract.is_processed = "failed"

        db.commit()

    except Exception as e:
        # Handle any errors
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if contract:
            contract.is_processed = "failed"
            contract.contract_data = {"error": str(e)}
            db.commit()

    finally:
        db.close()


# Routes
@router.post("/upload/{project_id}", response_model=ContractDetailResponse)
async def upload_contract(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a contract file to a project"""

    # Verify project exists and belongs to user
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not supported. Allowed types: {', '.join(allowed_extensions)}",
        )

    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    if file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 50MB.",
        )

    try:
        # Save file
        file_path = save_uploaded_file(file, project_id)

        # Create contract record
        contract = Contract(
            project_id=project_id,
            file_name=file.filename,
            file_url=file_path,  # Local file path
            contract_data={},
            is_processed="pending",
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        # Start background analysis
        from database.database import DATABASE_URL

        background_tasks.add_task(
            analyze_contract_background, contract.id, file_path, DATABASE_URL
        )

        return ContractDetailResponse(
            id=contract.id,
            project_id=contract.project_id,
            file_name=contract.file_name,
            file_url=contract.file_url,
            is_processed=contract.is_processed,
            created_at=contract.created_at.isoformat(),
            updated_at=contract.updated_at.isoformat(),
            contract_data=contract.contract_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get contract details and analysis"""

    # Get contract and verify ownership through project
    contract = (
        db.query(Contract)
        .join(Project)
        .filter(Contract.id == contract_id, Project.user_id == current_user.id)
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    return ContractDetailResponse(
        id=contract.id,
        project_id=contract.project_id,
        file_name=contract.file_name,
        file_url=contract.file_url,
        is_processed=contract.is_processed,
        created_at=contract.created_at.isoformat(),
        updated_at=contract.updated_at.isoformat(),
        contract_data=contract.contract_data,
    )


@router.post("/{contract_id}/reanalyze", response_model=dict)
async def reanalyze_contract(
    contract_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Re-analyze an existing contract"""

    # Get contract and verify ownership
    contract = (
        db.query(Contract)
        .join(Project)
        .filter(Contract.id == contract_id, Project.user_id == current_user.id)
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    # Check if file still exists
    if not Path(contract.file_url).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Original file no longer available",
        )

    # Start background analysis
    from database.database import DATABASE_URL

    background_tasks.add_task(
        analyze_contract_background, contract.id, contract.file_url, DATABASE_URL
    )

    # Update status
    contract.is_processed = "pending"
    db.commit()

    return {"message": "Contract analysis started", "contract_id": contract_id}


@router.post("/{contract_id}/question")
async def ask_question_about_contract(
    contract_id: int,
    question: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question about an analyzed contract"""

    # Get contract and verify ownership
    contract = (
        db.query(Contract)
        .join(Project)
        .filter(Contract.id == contract_id, Project.user_id == current_user.id)
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    if contract.is_processed != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must be analyzed before asking questions",
        )

    # Answer question using contract analysis
    analyzer = ContractAnalyzer()
    answer = await analyzer.answer_question(contract.contract_data, question)

    return {"question": question, "answer": answer, "contract_id": contract_id}


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a contract and its file"""

    # Get contract and verify ownership
    contract = (
        db.query(Contract)
        .join(Project)
        .filter(Contract.id == contract_id, Project.user_id == current_user.id)
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    # Delete file if it exists
    try:
        file_path = Path(contract.file_url)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Warning: Could not delete file {contract.file_url}: {e}")

    # Delete database record
    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully"}
