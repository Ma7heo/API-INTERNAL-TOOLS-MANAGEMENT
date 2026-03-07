import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
import models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    test_category = models.Category(name="Communication", description="Outils de test")
    db.add(test_category)
    db.commit()
    db.close()
    
    yield 
    
    models.Base.metadata.drop_all(bind=engine)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200

def test_list_tools_empty():
    response = client.get("/api/tools")
    assert response.status_code == 200
    assert response.json()["total"] == 0

# --- TESTS DE CRÉATION (POST) ---

def test_create_tool_success():
    """Vérifie qu'on peut créer un outil complet."""
    payload = {
        "name": "SuperTestTool",
        "description": "Un outil de test génial",
        "vendor": "TechCorp",
        "website_url": "https://test.com",
        "monthly_cost": 49.99,
        "owner_department": "Engineering",
        "category_id": 1,
        "status": "active"
    }
    response = client.post("/api/tools", json=payload)
    assert response.status_code == 201

def test_create_tool_missing_field():
    """Vérifie que Pydantic bloque s'il manque un champ obligatoire (ex: vendor)."""
    payload = {
        "name": "IncompleteTool",
        "description": "Il manque le vendor",
        "monthly_cost": 10.0,
        "owner_department": "Engineering",
        "category_id": 1,
        "status": "active"
    }
    response = client.post("/api/tools", json=payload)
    assert response.status_code == 422 

def test_create_tool_invalid_url_and_negative_price():
    """Vérifie que Pydantic bloque les prix négatifs et les fausses URLs."""
    payload = {
        "name": "BadTool",
        "description": "Test",
        "vendor": "BadVendor",
        "website_url": "ceci-nest-pas-une-url", 
        "monthly_cost": -50.0,
        "owner_department": "Engineering",
        "category_id": 1,
        "status": "active"
    }
    response = client.post("/api/tools", json=payload)
    assert response.status_code == 422

def test_create_tool_duplicate_name():
    """Vérifie la règle métier : Impossible d'avoir deux outils avec le même nom."""
    payload = {
        "name": "UniqueTool",
        "description": "Test",
        "vendor": "Vendor",
        "monthly_cost": 10.0,
        "owner_department": "Engineering", # <-- CORRECTION ICI
        "category_id": 1,
        "status": "active"
    }
    client.post("/api/tools", json=payload)
    response = client.post("/api/tools", json=payload)
    assert response.status_code == 400
    assert "Tool name already exists" in response.json()["detail"]

def test_create_tool_bad_category():
    """Vérifie la règle métier : Impossible d'utiliser une catégorie qui n'existe pas."""
    payload = {
        "name": "NoCategoryTool",
        "description": "Test",
        "vendor": "Vendor",
        "monthly_cost": 10.0,
        "owner_department": "Engineering", # <-- CORRECTION ICI
        "category_id": 999, 
        "status": "active"
    }
    response = client.post("/api/tools", json=payload)
    assert response.status_code == 400

# --- TESTS DE LECTURE (GET) ---

def test_get_tool_not_found():
    """Vérifie l'erreur 404 pour un outil inexistant."""
    response = client.get("/api/tools/999")
    assert response.status_code == 404

# --- TESTS DE MISE À JOUR (PUT) ---

def test_update_tool_partial():
    """Vérifie qu'on peut mettre à jour JUSTE le prix et le statut (Partial Update)."""
    payload = {
        "name": "UpdateMe", "description": "Test", "vendor": "Vendor",
        "monthly_cost": 10.0, "owner_department": "Engineering", "category_id": 1, "status": "active" # <-- CORRECTION ICI
    }
    create_resp = client.post("/api/tools", json=payload)
    tool_id = create_resp.json()["id"]

    update_payload = {"monthly_cost": 99.99, "status": "deprecated"}
    response = client.put(f"/api/tools/{tool_id}", json=update_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert float(data["monthly_cost"]) == 99.99
    assert data["status"] == "deprecated"
    assert data["name"] == "UpdateMe"

def test_update_tool_not_found():
    """Vérifie qu'on ne peut pas mettre à jour un outil fantôme."""
    response = client.put("/api/tools/999", json={"monthly_cost": 50.0})
    assert response.status_code == 404