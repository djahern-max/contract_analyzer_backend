# routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.project import Project
from models.contract import Contract
from routers.auth import get_current_active_user

router = APIRouter()


# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    description: str = None


class ProjectUpdate(BaseModel):
    name: str = None
    description: str = None


class ContractResponse(BaseModel):
    id: int
    file_name: str
    is_processed: str
    created_at: str

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str = None
    created_at: str
    contract_count: int = 0
    contracts: List[ContractResponse] = []

    class Config:
        from_attributes = True


# Project CRUD endpoints
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new project"""
    project = Project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        contract_count=0,
        contracts=[],
    )


@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()

    project_responses = []
    for project in projects:
        contracts = db.query(Contract).filter(Contract.project_id == project.id).all()
        contract_responses = [
            ContractResponse(
                id=contract.id,
                file_name=contract.file_name,
                is_processed=contract.is_processed,
                created_at=contract.created_at.isoformat(),
            )
            for contract in contracts
        ]

        project_responses.append(
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at.isoformat(),
                contract_count=len(contracts),
                contracts=contract_responses,
            )
        )

    return project_responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific project with its contracts"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    contracts = db.query(Contract).filter(Contract.project_id == project.id).all()
    contract_responses = [
        ContractResponse(
            id=contract.id,
            file_name=contract.file_name,
            is_processed=contract.is_processed,
            created_at=contract.created_at.isoformat(),
        )
        for contract in contracts
    ]

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        contract_count=len(contracts),
        contracts=contract_responses,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a project"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description

    db.commit()
    db.refresh(project)

    contracts = db.query(Contract).filter(Contract.project_id == project.id).all()
    contract_responses = [
        ContractResponse(
            id=contract.id,
            file_name=contract.file_name,
            is_processed=contract.is_processed,
            created_at=contract.created_at.isoformat(),
        )
        for contract in contracts
    ]

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        contract_count=len(contracts),
        contracts=contract_responses,
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a project and all its contracts"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}
