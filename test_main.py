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



def test_analytics_department_costs_empty():
    """Test 1: Vérifie la protection division par zéro quand aucun outil n'est actif."""
    response = client.get("/api/analytics/department-costs")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "No analytics data available - ensure tools data exists"
    assert data["summary"]["total_company_cost"] == 0.0
    assert len(data["data"]) == 0

def test_analytics_department_costs_happy_path():
    """Test 2: Vérifie les mathématiques et l'exclusion stricte des outils inactifs."""
    db = TestingSessionLocal()
    
    tools_data = [
        models.Tool(name="EngTool1", description="Test", vendor="V1", monthly_cost=100.0, owner_department="Engineering", category_id=1, status="active", active_users_count=10),
        models.Tool(name="EngTool2", description="Test", vendor="V2", monthly_cost=50.0, owner_department="Engineering", category_id=1, status="active", active_users_count=5),
        
        models.Tool(name="SalesTool1", description="Test", vendor="V3", monthly_cost=50.0, owner_department="Sales", category_id=1, status="active", active_users_count=5),
        
        models.Tool(name="OldSalesTool", description="Test", vendor="V4", monthly_cost=1000.0, owner_department="Sales", category_id=1, status="deprecated", active_users_count=100)
    ]
    
    db.add_all(tools_data)
    db.commit()
    db.close()

    response = client.get("/api/analytics/department-costs")
    assert response.status_code == 200
    
    result = response.json()
    
    assert result["summary"]["total_company_cost"] == 200.0
    assert result["summary"]["departments_count"] == 2
    assert result["summary"]["most_expensive_department"] == "Engineering"

    eng_stats = next(item for item in result["data"] if item["department"] == "Engineering")
    assert eng_stats["total_cost"] == 150.0
    assert eng_stats["tools_count"] == 2
    assert eng_stats["total_users"] == 15
    assert eng_stats["average_cost_per_tool"] == 75.0
    assert eng_stats["cost_percentage"] == 75.0

    sales_stats = next(item for item in result["data"] if item["department"] == "Sales")
    assert sales_stats["total_cost"] == 50.0
    assert sales_stats["tools_count"] == 1
    assert sales_stats["cost_percentage"] == 25.0

def test_analytics_department_costs_sorting():
    """Test 3: Vérifie que le tri dynamique fonctionne bien."""
    db = TestingSessionLocal()
    db.add(models.Tool(name="T1", description="D", vendor="V", monthly_cost=100.0, owner_department="Engineering", category_id=1, status="active", active_users_count=1))
    db.add(models.Tool(name="T2", description="D", vendor="V", monthly_cost=50.0, owner_department="Engineering", category_id=1, status="active", active_users_count=1))
    db.add(models.Tool(name="T3", description="D", vendor="V", monthly_cost=50.0, owner_department="Sales", category_id=1, status="active", active_users_count=1))
    db.commit()
    db.close()

    response = client.get("/api/analytics/department-costs?sort_by=tools_count&order=asc")
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert data[0]["department"] == "Sales"
    assert data[1]["department"] == "Engineering"

def test_analytics_expensive_tools_invalid_parameters():
    """Vérifie la gestion d'erreurs systémique sur plusieurs paramètres invalides."""
    response = client.get("/api/analytics/expensive-tools?limit=-10&min_cost=-10")
    assert response.status_code == 400
    
    data = response.json()
    assert data["error"] == "Invalid analytics parameter"
    assert "limit" in data["details"]
    assert "min_cost" in data["details"]

def test_analytics_expensive_tools_happy_path():
    """Vérifie le rating (excellent/low), le filtre min_cost et les économies identifiées."""
    db = TestingSessionLocal()
    
    db.add(models.Tool(name="GoodTool", description="D", vendor="V", monthly_cost=40.0, owner_department="Engineering", category_id=1, status="active", active_users_count=10)) 
    
    db.add(models.Tool(name="BadTool", description="D", vendor="V", monthly_cost=160.0, owner_department="Engineering", category_id=1, status="active", active_users_count=10))     
    db.add(models.Tool(name="ZeroUserTool", description="D", vendor="V", monthly_cost=15.0, owner_department="Engineering", category_id=1, status="active", active_users_count=0)) 
    
    db.commit()
    db.close()

    response = client.get("/api/analytics/expensive-tools?min_cost=20.0")
    assert response.status_code == 200
    result = response.json()
    
    assert result["analysis"]["total_tools_analyzed"] == 3
    assert result["analysis"]["avg_cost_per_user_company"] == 10.0
    
    assert result["analysis"]["potential_savings_identified"] == 175.0
    
    tools_data = result["data"]
    assert len(tools_data) == 2
    
    assert tools_data[0]["name"] == "BadTool"
    assert tools_data[0]["monthly_cost"] == 160.0
    assert tools_data[0]["efficiency_rating"] == "low"
    
    assert tools_data[1]["name"] == "GoodTool"
    assert tools_data[1]["efficiency_rating"] == "excellent"