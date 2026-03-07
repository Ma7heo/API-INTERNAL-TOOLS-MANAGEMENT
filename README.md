# Internal Tools API

API RESTful pour la gestion centralisée du catalogue d'outils SaaS de TechCorp Solutions.

## Technologies
- Langage: Python 3.12
- Framework: FastAPI
- Base de données: PostgreSQL
- Port API: 8000 (configurable)

## Quick Start

1. `./scripts/start-postgres.sh` (ou `docker compose up -d`)
2. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. `uvicorn main:app --reload`
4. API disponible sur http://localhost:8000
5. Documentation: http://localhost:8000/api/docs

## Configuration
- Variables d'environnement: voir `.env.example`
- Configuration DB: Les identifiants de connexion sont chargés dynamiquement via SQLAlchemy dans le fichier `database.py` depuis les variables d'environnement pour garantir la sécurité.

## Tests  
`pytest` - Tests unitaires + intégration

## Architecture
- **Justification des choix techniques**: FastAPI a été sélectionné pour ses performances exceptionnelles et sa génération automatique de la documentation OpenAPI (Swagger). SQLAlchemy (ORM) est utilisé pour sa robustesse et sa capacité à déléguer les calculs d'agrégation (moyennes, comptages) directement au moteur PostgreSQL, optimisant ainsi l'utilisation de la mémoire.
- **Structure du projet**:
  - `main.py` : Controllers (Points d'entrée HTTP et définition des routes).
  - `services.py` : Logique métier et requêtes d'accès aux données (Séparation des responsabilités).
  - `models.py` : Modèles ORM reflétant l'architecture de la base de données.
  - `schemas.py` : Modèles Pydantic pour la validation stricte des inputs/outputs.
  - `database.py` : Configuration de la base de données et gestion du pool de connexions.