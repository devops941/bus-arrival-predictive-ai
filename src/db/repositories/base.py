"""
Base Repository with Role and Owner Scoping.
Provides standardized CRUD operations and ensures role-based data filtering.
"""

from typing import Dict, Any, List, Optional
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database
from src.db.mongo import get_database


class BaseRepository:
    def __init__(self, collection_name: str, db: Optional[Database] = None):
        self.db = db if db is not None else get_database()
        self.collection: Collection = self.db[collection_name]
        self.collection_name = collection_name

    def filter_by_role_and_owner(
        self,
        base_query: Optional[Dict[str, Any]] = None,
        user_role: Optional[str] = None,
        user_id: Optional[str] = None,
        enforce_owner: bool = False
    ) -> Dict[str, Any]:
        """
        Enforce role-based and ownership scoping on queries.
        - Admin has unrestricted global visibility.
        - Non-admin with enforce_owner=True is scoped to records created_by user_id or public records.
        """
        query = dict(base_query or {})
        if user_role == "admin":
            return query

        if enforce_owner and user_id:
            # Match records created by user or records without owner
            query["$or"] = [
                {"created_by": user_id},
                {"created_by": None},
                {"created_by": {"$exists": False}},
            ]
        return query

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching query."""
        doc = self.collection.find_one(query)
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            doc["_id"] = str(doc["_id"])
        return doc

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Find a single document by its ObjectId or string ID."""
        try:
            oid = ObjectId(doc_id)
            query = {"$or": [{"_id": oid}, {"id": doc_id}]}
        except Exception:
            query = {"id": doc_id}
        return self.find_one(query)

    def find_many(
        self,
        query: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents matching query with pagination and sorting."""
        q = query or {}
        cursor = self.collection.find(q).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = []
        for d in cursor:
            if "_id" in d:
                d["id"] = str(d["_id"])
                d["_id"] = str(d["_id"])
            docs.append(d)
        return docs

    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching query."""
        return self.collection.count_documents(query or {})

    def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a document and return its string ID."""
        res = self.collection.insert_one(document)
        return str(res.inserted_id)

    def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by its ID."""
        try:
            oid = ObjectId(doc_id)
            query = {"$or": [{"_id": oid}, {"id": doc_id}]}
        except Exception:
            query = {"id": doc_id}
        res = self.collection.update_one(query, {"$set": updates})
        return res.modified_count > 0 or res.matched_count > 0

    def delete_by_id(self, doc_id: str) -> bool:
        """Delete a document by its ID."""
        try:
            oid = ObjectId(doc_id)
            query = {"$or": [{"_id": oid}, {"id": doc_id}]}
        except Exception:
            query = {"id": doc_id}
        res = self.collection.delete_one(query)
        return res.deleted_count > 0

    def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching query."""
        res = self.collection.delete_many(query)
        return res.deleted_count
