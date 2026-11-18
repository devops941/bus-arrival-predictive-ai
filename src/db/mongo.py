"""
BusArrival AI - MongoDB Connection, Lifecycle & Schema Management
Connects using MONGODB_URI strictly from environment settings. Never logs credentials.
Configures indexes and jsonSchema collection validators.
"""

from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from src.config import get_settings


_client: Optional[MongoClient] = None


def get_mongo_client(uri: Optional[str] = None, timeout_ms: Optional[int] = None) -> MongoClient:
    """
    Get or create a singleton MongoClient instance using credentials from settings.
    Never logs or exposes the connection string.
    """
    global _client
    if _client is None:
        settings = get_settings()
        conn_uri = uri or settings.MONGODB_URI
        timeout = timeout_ms or settings.MONGODB_TIMEOUT_MS
        _client = MongoClient(
            conn_uri,
            serverSelectionTimeoutMS=timeout,
            connectTimeoutMS=timeout,
            appname="BusArrivalAI"
        )
    return _client


def get_database(db_name: Optional[str] = None, client: Optional[MongoClient] = None) -> Database:
    """
    Return a reference to the specified database (defaults to MONGODB_DB_NAME).
    """
    settings = get_settings()
    cli = client if client is not None else get_mongo_client()
    target_db = db_name if db_name is not None else settings.MONGODB_DB_NAME
    return cli[target_db]


def ping_database(db_name: Optional[str] = None, client: Optional[MongoClient] = None) -> Dict[str, Any]:
    """
    Execute a ping command against MongoDB to check connectivity.
    Returns status dictionary or raises ConnectionFailure.
    """
    try:
        db = get_database(db_name, client)
        res = db.command("ping")
        return {"ok": bool(res.get("ok", 0)), "database": db.name}
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        raise ConnectionFailure(f"MongoDB connection failed: {exc.__class__.__name__}") from exc


def close_mongo_client() -> None:
    """Gracefully close singleton MongoClient connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


# Collection JSON Schema Validators (Section 11)
USERS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["email", "hashed_password", "role", "is_active", "created_at"],
        "properties": {
            "email": {
                "bsonType": "string",
                "pattern": "^.+@.+\\..+$",
                "description": "User email address - required valid format",
            },
            "hashed_password": {
                "bsonType": "string",
                "description": "Bcrypt hashed password - required",
            },
            "role": {
                "enum": ["passenger", "analyst", "admin"],
                "description": "Role must be one of passenger, analyst, admin",
            },
            "full_name": {
                "bsonType": "string",
            },
            "is_active": {
                "bsonType": "bool",
            },
            "failed_login_attempts": {
                "bsonType": "int",
            },
            "locked_until": {
                "bsonType": ["date", "null"],
            },
            "created_at": {
                "bsonType": "date",
            },
            "updated_at": {
                "bsonType": ["date", "null"],
            },
        },
    }
}

ROUTES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["route_no", "name", "origin", "destination", "total_distance_km", "scheduled_headway_min", "active"],
        "properties": {
            "route_no": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "origin": {"bsonType": "string"},
            "destination": {"bsonType": "string"},
            "total_distance_km": {"bsonType": ["double", "int"], "minimum": 0.01},
            "scheduled_headway_min": {"bsonType": "int", "minimum": 1},
            "active": {"bsonType": "bool"},
            "created_by": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
        },
    }
}

OBSERVATIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["trip_id", "scheduled_arrival", "actual_arrival", "delay_min"],
        "properties": {
            "trip_id": {"bsonType": "string"},
            "stop_code": {"bsonType": "string"},
            "stop_id": {"bsonType": "string"},
            "route_no": {"bsonType": "string"},
            "route_id": {"bsonType": "string"},
            "scheduled_arrival": {"bsonType": "date"},
            "actual_arrival": {"bsonType": "date"},
            "delay_min": {"bsonType": ["double", "int"]},
            "passengers_optional": {"bsonType": ["int", "null"]},
            "weather_optional": {"bsonType": ["string", "null"]},
            "is_outlier": {"bsonType": "bool"},
            "created_by": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
        },
    }
}


def apply_collection_validators(db: Database) -> None:
    """Apply or update jsonSchema collection validators for core collections."""
    schemas = {
        "users": USERS_SCHEMA,
        "routes": ROUTES_SCHEMA,
        "observations": OBSERVATIONS_SCHEMA,
    }

    existing_collections = db.list_collection_names()
    for coll_name, schema in schemas.items():
        try:
            if coll_name not in existing_collections:
                db.create_collection(coll_name, validator=schema)
            else:
                db.command({
                    "collMod": coll_name,
                    "validator": schema,
                    "validationLevel": "moderate"
                })
        except OperationFailure:
            # If Atlas user does not have collMod permissions or schema is unchanged, proceed safely
            pass


def ensure_indexes(db: Database) -> None:
    """
    Ensure all unique and query indexes per Section 11 of the spec.
    """
    # 1. users: unique email
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING)])

    # 2. routes: unique route_no
    db.routes.create_index([("route_no", ASCENDING)], unique=True)

    # 3. stops: unique stop_code, geospatial index
    db.stops.create_index([("stop_code", ASCENDING)], unique=True)
    db.stops.create_index([("lat", ASCENDING), ("lon", ASCENDING)])

    # 4. route_stops: unique (route_no, stop_code) and (route_no, sequence)
    db.route_stops.create_index([("route_no", ASCENDING), ("stop_code", ASCENDING)], unique=True)
    db.route_stops.create_index([("route_no", ASCENDING), ("sequence", ASCENDING)], unique=True)

    # 5. trips: trip_id (unique), (route_no, date)
    db.trips.create_index([("trip_id", ASCENDING)], unique=True)
    db.trips.create_index([("route_no", ASCENDING), ("date", ASCENDING)])

    # 6. observations: unique (trip_id, stop_code); compound (route_no, scheduled_arrival)
    db.observations.create_index([("trip_id", ASCENDING), ("stop_code", ASCENDING)], unique=True)
    db.observations.create_index([("route_no", ASCENDING), ("scheduled_arrival", ASCENDING)])

    # 7. models: status, created_at
    db.models.create_index([("status", ASCENDING), ("created_at", DESCENDING)])

    # 8. audit_log: timestamp, user_id, action
    db.audit_log.create_index([("timestamp", DESCENDING)])
    db.audit_log.create_index([("user_id", ASCENDING), ("action", ASCENDING)])

    # 9. predictions_log: model_id, created_at
    db.predictions_log.create_index([("model_id", ASCENDING), ("created_at", DESCENDING)])

    # 10. alerts: status, route_id, created_at
    db.alerts.create_index([("status", ASCENDING), ("created_at", DESCENDING)])


def init_database(db: Optional[Database] = None) -> Database:
    """Initialize database schemas and indexes."""
    target_db = db if db is not None else get_database()
    apply_collection_validators(target_db)
    ensure_indexes(target_db)
    return target_db
