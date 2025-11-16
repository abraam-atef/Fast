from fastapi import FastAPI ,Depends ,HTTPException
from sqlalchemy import Column, JSON , String , Integer , create_engine
from sqlalchemy.orm import Session , sessionmaker ,declarative_base
from pydantic import BaseModel
from sqladmin import Admin, ModelView
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Medical Termonology")

# ================== Cors Header ===============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== Sql Conect ================
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


# =================== Project Model ===============

class Question(Base):
    __tablename__= "question"

    id = Column(Integer,primary_key=True,index=True)
    title = Column(String)
    question = Column(String)
    answers = Column(JSON,default=[])

Base.metadata.create_all(bind=engine)
# ================= SQL Admin ==========================

admin = Admin(app, engine)
class ProductAdmin(ModelView, model=Question):
    column_list = [
        Question.id,
        Question.title,
        Question.question,
        Question.answers,
    ]

admin.add_view(ProductAdmin)

# ===================== Schema =========================

class QuesionBase(BaseModel):
    id:int
    title:str
    question:str
    answers:list
    class config:
        orm_mode = True


# ====================== End Pointes ======================
@app.get("/",response_model=list[QuesionBase])
def GetData(db:Session=Depends(get_db)):
    return db.query(Question).all()

@app.post("/",response_model=QuesionBase)
def create(Q:QuesionBase,db:Session=Depends(get_db)):
    newq = Question(**Q.dict())
    db.add(newq)
    db.commit()
    db.refresh(newq)
    return newq

@app.get("/ques/{qid}", response_model=QuesionBase)
def GetOne(qid:int,db:Session=Depends(get_db)):
    quis = db.query(Question).filter(Question.id == qid).first()
    if not quis:
        return HTTPException(status_code=404,detail="not found")
    return quis

@app.delete("/ques/{qid}",response_model=QuesionBase)
def Del(quid:int,db:Session=Depends(get_db)):
    q = db.query(Question).filter(Question.id == quid).first()
    if not q:
        return HTTPException(status_code=404,detail="not found")
    db.delete(q)
    db.commit()
    return {"msg":"delete succesfully"}

@app.put("/quid/{id}",response_model=QuesionBase)
def Update(id:int,updated_data,db:Session=Depends(get_db)):
    q = db.query(Question).filter(Question.id == id).first()
    if not q:
        return HTTPException(status_code=404,detail="not found")
    for key, value in updated_data.dict().items():
        setattr(q, key, value)
        db.commit()
        db.refresh(q)
        return q