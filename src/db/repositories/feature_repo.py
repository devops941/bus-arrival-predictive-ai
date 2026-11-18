"""
Feature Cache Repository for MongoDB.
Stores and invalidates pre-computed feature vectors by data_version.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class FeatureCacheRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("features_cache", db)

    def get_latest_cache(self) -> Optional[Dict[str, Any]]:
        """Retrieve the latest cached feature dataset metadata."""
        docs = self.find_many({}, skip=0, limit=1, sort=[("data_version", -1), ("created_at", -1)])
        return docs[0] if docs else None

    def cache_features_metadata(
        self,
        data_version: int,
        feature_count: int,
        feature_names: List[str],
        sample_preview: List[Dict[str, Any]],
    ) -> str:
        """Store feature build metadata and preview rows."""
        doc = {
            "data_version": data_version,
            "feature_count": feature_count,
            "feature_names": feature_names,
            "sample_preview": sample_preview,
            "created_at": datetime.now(timezone.utc),
        }
        return self.insert_one(doc)
