import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Import your modules
from app.security import verify_password, get_password_hash, create_access_token, verify_token
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.database import get_db

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    print(f"DEBUG: Attempting to register user: {user.email}")
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            print(f"DEBUG: User {user.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user.password)
        print(f"DEBUG: Password hashed successfully")
        
        # Create new user
        new_user = User(
            email=user.email,
            hashed_password=hashed_password,
            is_active=True
        )
        print(f"DEBUG: User object created: {new_user.email}")
        
        # Save to database
        db.add(new_user)
        print("DEBUG: User added to session")
        
        db.commit()
        print("DEBUG: Transaction committed")
        
        db.refresh(new_user)
        print(f"DEBUG: User refreshed - ID: {new_user.id}")
        
        # Verify user was saved
        saved_user = db.query(User).filter(User.email == user.email).first()
        if saved_user:
            print(f"DEBUG: Verification successful - User {saved_user.id} found in database")
        else:
            print("ERROR: User not found after commit!")
            raise HTTPException(status_code=500, detail="Failed to save user")
        
        return UserResponse(id=new_user.id, email=new_user.email)
        
    except HTTPException:
        print("DEBUG: HTTPException occurred, rolling back")
        db.rollback()
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login and get access token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}