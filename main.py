from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, JSON, String, Integer, create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from pydantic import BaseModel
from sqladmin import Admin, ModelView
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Medical Terminology")

# ========================== CORS ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================= Database =========================
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====================== Model =============================
class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    question = Column(String)
    answers = Column(JSON, default=list)


Base.metadata.create_all(bind=engine)


# ====================== SQL Admin =========================
admin = Admin(app, engine)


class QuestionAdmin(ModelView, model=Question):
    column_list = [
        Question.id,
        Question.title,
        Question.question,
        Question.answers,
    ]


admin.add_view(QuestionAdmin)


# ===================== Schemas ============================
class QuestionBase(BaseModel):
    id: int
    title: str
    question: str
    answers: list

    class Config:
        orm_mode = True


class CreateQuestion(BaseModel):
    title: str
    question: str
    answers: list


# ===================== Endpoints ==========================

# Get All
@app.get("/", response_model=list[QuestionBase])
def get_all(db: Session = Depends(get_db)):
    return db.query(Question).all()


# Create
@app.post("/", response_model=QuestionBase)
def create(q: CreateQuestion, db: Session = Depends(get_db)):
    new_q = Question(**q.dict())
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q


# Get One
@app.get("/ques/{qid}", response_model=QuestionBase)
def get_one(qid: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(status_code=404, detail="not found")
    return q


# Delete
@app.delete("/ques/{qid}")
def delete(qid: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(status_code=404, detail="not found")

    db.delete(q)
    db.commit()
    return {"msg": "delete successfully"}


# Update
@app.put("/ques/{qid}", response_model=QuestionBase)
def update(qid: int, updated: CreateQuestion, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(status_code=404, detail="not found")

    for key, value in updated.dict().items():
        setattr(q, key, value)

    db.commit()
    db.refresh(q)
    return q

import uvicorn, os

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
