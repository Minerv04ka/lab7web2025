import pytest
from fastapi.testclient import TestClient
from app.main import app, database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI TestClient
client = TestClient(app)

# Fixture to reset the database before each test
@pytest.fixture
async def clean_db():
    """Fixture to clean the database before each test."""
    query = "DELETE FROM books"
    await database.execute(query)
    yield

# Fixture for sample book data
@pytest.fixture
def book_data():
    """Fixture to provide sample book data."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "price": 9.99
    }

@pytest.mark.asyncio
async def test_create_book(clean_db, book_data):
    """Test creating a new book."""
    response = client.post("/books", json=book_data)
    assert response.status_code == 200
    assert response.json()["title"] == book_data["title"]
    assert response.json()["author"] == book_data["author"]
    assert response.json()["price"] == book_data["price"]
    assert "id" in response.json()
    return response.json()["id"]

@pytest.mark.asyncio
async def test_get_books(clean_db, book_data):
    """Test retrieving the list of books."""
    # Create a book first
    client.post("/books", json=book_data)
    response = client.get("/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == book_data["title"]

@pytest.mark.asyncio
async def test_get_book_by_id(clean_db, book_data):
    """Test retrieving a book by ID."""
    book_id = client.post("/books", json=book_data).json()["id"]
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["id"] == book_id
    assert response.json()["title"] == book_data["title"]

@pytest.mark.asyncio
async def test_get_book_not_found(clean_db):
    """Test retrieving a non-existent book."""
    response = client.get("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_update_book(clean_db, book_data):
    """Test updating an existing book."""
    book_id = client.post("/books", json=book_data).json()["id"]
    updated_data = {
        "title": "Updated Book",
        "author": "Updated Author",
        "price": 12.99
    }
    response = client.put(f"/books/{book_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["id"] == book_id
    assert response.json()["title"] == updated_data["title"]
    assert response.json()["author"] == updated_data["author"]
    assert response.json()["price"] == updated_data["price"]

@pytest.mark.asyncio
async def test_update_book_not_found(clean_db):
    """Test updating a non-existent book."""
    updated_data = {
        "title": "Updated Book",
        "author": "Updated Author",
        "price": 12.99
    }
    response = client.put("/books/999", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_delete_book(clean_db, book_data):
    """Test deleting a book."""
    book_id = client.post("/books", json=book_data).json()["id"]
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted successfully"
    # Verify the book is deleted
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_delete_book_not_found(clean_db):
    """Test deleting a non-existent book."""
    response = client.delete("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"