"""
Model Registry Repository for MongoDB.
Manages candidate, active, and archived ML models and training metadata.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class ModelRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("models", db)

    def get_by_model_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"$or": [{"model_id": model_id}, {"id": model_id}]})

    def get_active_model(self) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active production model."""
        return self.find_one({"status": "active"})

    def activate_model(self, model_id: str) -> bool:
        """
        Set target model as active production model.
        Archives previous active model.
        """
        target = self.get_by_model_id(model_id)
        if not target:
            return False

        now = datetime.now(timezone.utc)
        # Archive any currently active models
        self.collection.update_many(
            {"status": "active"},
            {"$set": {"status": "archived", "archived_at": now}}
        )

        # Set target model to active
        res = self.collection.update_one(
            {"$or": [{"model_id": model_id}, {"id": model_id}]},
            {"$set": {"status": "active", "activated_at": now}}
        )
        return res.modified_count > 0 or res.matched_count > 0

    def rollback_model(self) -> Optional[Dict[str, Any]]:
        """
        Roll back to the most recently archived model.
        """
        archived_models = self.find_many(
            {"status": "archived"},
            limit=1,
            sort=[("archived_at", -1), ("created_at", -1)]
        )
        if not archived_models:
            return None

        prev_model = archived_models[0]
        self.activate_model(prev_model["model_id"])
        return self.get_active_model()
