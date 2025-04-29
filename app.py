from datetime import timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
import models, schemas
from sqlalchemy.orm import joinedload 
from database import engine, get_db
from auth import authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ChatAPP API", description="API for Chat App", version="4.0")

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Routes
@app.post("/users", response_model=schemas.UserResponse, tags=["Users"])
def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_data = schemas.UserCreate(name=name, email=email, password=password)
    try:
        return create_user(db, user_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    
@app.post("/create/{message}", response_model=schemas.MessageResponse, tags=["Messages"])
def create_message(
    content: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_message = models.Message(
        content=content,
        user_id=current_user.id,
        user=current_user
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@app.get("/get/{message}", response_model=List[schemas.MessageResponse], tags=["Messages"])
def get_messages(
    current_user: models.User = Depends(get_current_user),  # Add this line
    db: Session = Depends(get_db)
):
    messages = db.query(models.Message)\
              .options(joinedload(models.Message.user))\
              .order_by(models.Message.created_at.desc())\
              .all()
    return messages

# Add these new endpoints after the existing ones

@app.put("/update/{message_id}", response_model=schemas.MessageResponse, tags=["Messages"])
def update_message(
    message_id: int,
    content: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the message and verify ownership
    db_message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.user_id == current_user.id
    ).first()

    if not db_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or unauthorized"
        )

    # Update the message content
    db_message.content = content
    db.commit()
    db.refresh(db_message)
    return db_message

@app.delete("/delete/{message_id}", tags=["Messages"])
def delete_message(
    message_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the message and verify ownership
    db_message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.user_id == current_user.id
    ).first()

    if not db_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or unauthorized"
        )

    # Delete the message
    db.delete(db_message)
    db.commit()
    return {"detail": "Message deleted successfully"}

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
