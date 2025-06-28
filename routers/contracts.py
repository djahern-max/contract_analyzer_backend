# routers/contracts.py - Updated to use schemas
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

from database import get_db
from models.user import User
from models.project import Project
from models.contract import Contract
from routers.auth import get_current_active_user
from services.contract_analyzer import ContractAnalyzer

# Import schemas from the new schemas package
from schemas.contract import (
    ContractDetailResponse,
    ContractAnalysisResponse,
    ContractSummaryResponse,
    ContractQuestionRequest,
    ContractQuestionResponse,
    ContractSearchParams,
    ContractStatusUpdate,
)
from schemas.base import SuccessResponse

import uuid
from datetime import datetime

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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
        # Handle any other errors
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if contract:
            contract.contract_data = {"error": str(e)}
            contract.is_processed = "failed"
            db.commit()

    finally:
        db.close()


@router.post("/upload/{project_id}", response_model=ContractDetailResponse)
async def upload_contract(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a contract file for analysis"""

    # Verify project ownership
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
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}",
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
            updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
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
        processed_at=(
            contract.processed_at.isoformat() if contract.processed_at else None
        ),
        created_at=contract.created_at.isoformat(),
        updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
        contract_data=contract.contract_data,
    )


@router.post("/{contract_id}/reanalyze", response_model=SuccessResponse)
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

    return SuccessResponse(
        message="Contract analysis started", data={"contract_id": contract_id}
    )


@router.post("/{contract_id}/question", response_model=ContractQuestionResponse)
async def ask_question_about_contract(
    contract_id: int,
    question_data: ContractQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question about a specific contract"""

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
            detail="Contract must be fully processed before asking questions",
        )

    try:
        # Use the contract analyzer to answer the question
        analyzer = ContractAnalyzer()
        result = await analyzer.answer_question(
            contract.contract_data,
            question_data.question,
            context=question_data.context,
        )

        return ContractQuestionResponse(
            contract_id=contract_id,
            question=question_data.question,
            answer=result.get("answer", "Unable to generate answer"),
            confidence=result.get("confidence"),
            sources=result.get("sources", []),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}",
        )


@router.get("/project/{project_id}", response_model=List[ContractSummaryResponse])
async def get_project_contracts(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all contracts for a specific project"""

    # Verify project ownership
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get contracts
    contracts = db.query(Contract).filter(Contract.project_id == project_id).all()

    return [
        ContractSummaryResponse(
            id=contract.id,
            project_id=contract.project_id,
            file_name=contract.file_name,
            is_processed=contract.is_processed,
            created_at=contract.created_at.isoformat(),
            file_size=None,  # Could add file size calculation here
            file_type=Path(contract.file_name).suffix.lower(),
        )
        for contract in contracts
    ]


@router.put("/{contract_id}/status", response_model=ContractDetailResponse)
async def update_contract_status(
    contract_id: int,
    status_update: ContractStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update contract processing status (admin use)"""

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

    # Update status
    contract.is_processed = status_update.is_processed

    if status_update.contract_data is not None:
        contract.contract_data = status_update.contract_data

    if status_update.is_processed == "completed":
        contract.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(contract)

    return ContractDetailResponse(
        id=contract.id,
        project_id=contract.project_id,
        file_name=contract.file_name,
        file_url=contract.file_url,
        is_processed=contract.is_processed,
        processed_at=(
            contract.processed_at.isoformat() if contract.processed_at else None
        ),
        created_at=contract.created_at.isoformat(),
        updated_at=contract.updated_at.isoformat() if contract.updated_at else None,
        contract_data=contract.contract_data,
    )


@router.delete("/{contract_id}", response_model=SuccessResponse)
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a contract and its associated file"""

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

    # Delete physical file if it exists
    file_path = Path(contract.file_url)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            # Log the error but don't fail the deletion
            print(f"Warning: Could not delete file {file_path}: {e}")

    # Delete from database
    db.delete(contract)
    db.commit()

    return SuccessResponse(
        message="Contract deleted successfully", data={"contract_id": contract_id}
    )
