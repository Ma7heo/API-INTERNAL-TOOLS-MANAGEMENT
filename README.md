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
- **Justification des choix techniques**: FastAPI a été sélectionné pour ses performances et sa génération automatique de la documentation OpenAPI (Swagger). SQLAlchemy (ORM) est utilisé pour sa robustesse et sa capacité à déléguer les calculs d'agrégation (moyennes, comptages) directement au moteur PostgreSQL, optimisant ainsi l'utilisation de la mémoire.
- **Structure du projet**:
  - `main.py` : Controllers (Points d'entrée HTTP et définition des routes).
  - `services.py` : Logique métier et requêtes d'accès aux données (Séparation des responsabilités).
  - `models.py` : Modèles ORM reflétant l'architecture de la base de données.
  - `schemas.py` : Modèles Pydantic pour la validation stricte des inputs/outputs.
  - `database.py` : Configuration de la base de données et gestion du pool de connexions.


## Moteur d'Analytics (Stratégie Hybride)
Pour les endpoints d'analytique financière (Part 2), une approche hybride a été adoptée pour équilibrer les performances de la base de données et la flexibilité de la logique métier :
- **Push to DB (SQLAlchemy) :** Le filtrage (`status = 'active'`), le regroupement (`GROUP BY`), les jointures (`JOIN categories`) et les agrégations brutes (`SUM`, `COUNT`) sont délégués au moteur PostgreSQL pour minimiser la charge mémoire du serveur Python.
- **Pull to App (Python) :** Les règles métiers complexes (ex: distribution en pourcentages, attribution des *Efficiency Ratings* avec seuils stricts, concaténation de listes uniques de départements) sont traitées en mémoire par Python sur un jeu de données déjà réduit.

## Gestion des Erreurs et Robustesse
- **Validation Stricte :** Implémentation de validations manuelles pour forcer des réponses `HTTP 400` au format JSON exact exigé par les spécifications métiers (ex: `limit` ou `max_users` négatifs), bypassant la validation `422 Unprocessable Entity` par défaut de FastAPI.
- **Fallbacks (Empty States) :** Anticipation des divisions par zéro. Si la base de données ne contient aucun outil actif, les endpoints d'analytics renvoient un `HTTP 200 OK` avec une structure de données vide et un message d'information, évitant un crash de l'API.
- **Programmation Défensive :** Interception sécurisée des types de données (ex: extraction des valeurs brutes des `Enum` SQLAlchemy pour éviter les conflits de sérialisation Pydantic).

## ⚠️ Spécifications Métier : Le cas du `monthly_cost`
Lors du développement, une contradiction dans les règles métier (Business Logic) a été identifiée entre les spécifications de la Part 1 et de la Part 2 concernant le champ `monthly_cost` :
- **Part 1 (Endpoint `/api/tools/{id}`)** : L'exemple de réponse JSON attendu implique que `monthly_cost` est un coût unitaire par utilisateur (ex: `monthly_cost: 5.50` * `active_users_count: 9` = `total_monthly_cost: 49.50`).
- **Part 2 (Analytics)** : Les formules de calcul exigées (ex: `avg_cost_per_user_company = Somme(monthly_cost) / Somme(active_users)`) impliquent mathématiquement que `monthly_cost` représente le coût forfaitaire global de l'outil par mois.

**Résolution adoptée :** Pour respecter les contrats d'interface stricts (JSON) attendus par les tests automatisés de chaque partie, les endpoints de la Part 1 et de la Part 2 ont été isolés dans leur traitement mathématique. Le moteur d'Analytics traite `monthly_cost` comme le coût total (conformément aux formules de la Part 2) pour garantir la pertinence des indicateurs d'efficacité financière. 
*Recommandation V2 :* Normaliser la base de données en ajoutant un champ `pricing_model` (`flat_rate` vs `per_seat`) pour uniformiser les calculs sur l'ensemble de l'API.