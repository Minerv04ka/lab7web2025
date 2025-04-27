from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
import databases
import logging
import time

# Configure logging
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Library API", description="API для управління книгами", version="1.0.0")

DATABASE_URL = "sqlite:///./library.db"
database = databases.Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class BookDB(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    price = Column(Float)

# Pydantic models for validation
class BookBase(BaseModel):
    title: str
    author: str
    price: float

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency for database session
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )
    return response

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await database.connect()
    logger.info("Application started and database connected")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Application shutdown and database disconnected")

# CRUD operations
@app.get("/books", response_model=List[Book])
async def get_books():
    logger.info("GET /books - Fetching all books")
    query = "SELECT * FROM books"
    return await database.fetch_all(query)

@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: int):
    logger.info(f"GET /books/{book_id}")
    query = "SELECT * FROM books WHERE id = :id"
    book = await database.fetch_one(query, {"id": book_id})
    if book is None:
        logger.warning(f"Book with id {book_id} not found")
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.post("/books", response_model=Book)
async def create_book(book: BookCreate):
    logger.info(f"POST /books - Creating book: {book.title}")
    query = "INSERT INTO books (title, author, price) VALUES (:title, :author, :price) RETURNING *"
    values = {"title": book.title, "author": book.author, "price": book.price}
    created_book = await database.fetch_one(query, values)
    return created_book

@app.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, book: BookCreate):
    logger.info(f"PUT /books/{book_id} - Updating book: {book.title}")
    query = "UPDATE books SET title = :title, author = :author, price = :price WHERE id = :id RETURNING *"
    values = {"id": book_id, "title": book.title, "author": book.author, "price": book.price}
    updated_book = await database.fetch_one(query, values)
    if updated_book is None:
        logger.warning(f"Book with id {book_id} not found")
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    logger.info(f"DELETE /books/{book_id}")
    query = "DELETE FROM books WHERE id = :id RETURNING *"
    deleted_book = await database.fetch_one(query, {"id": book_id})
    if deleted_book is None:
        logger.warning(f"Book with id {book_id} not found")
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}