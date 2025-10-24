"""
Cache management for CLI Navigation Tool.

Provides memory and file-based caching for location parsing results,
browser sessions, and frequently accessed data to improve performance.
"""

import json
import time
import hashlib
from typing import Any, Dict, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict

from src.models.navigation import LocationEntity, NavigationQuery, RouteParameters
from src.exceptions import CacheError


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""
    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        """Initialize last_accessed timestamp."""
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)

    @property
    def age_seconds(self) -> int:
        """Get age of cache entry in seconds."""
        return int((datetime.now() - self.timestamp).total_seconds())

    def access(self) -> Any:
        """Access the cache entry and update metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl_seconds=data["ttl_seconds"],
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )


class MemoryCache:
    """In-memory cache with LRU eviction and size limits."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """Initialize memory cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order = []

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired:
            self._remove_entry(key)
            return None

        # Update access order for LRU
        self._update_access_order(key)
        return entry.access()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        # Evict if necessary
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        ttl = ttl_seconds or self.default_ttl
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=datetime.now(),
            ttl_seconds=ttl
        )

        self._cache[key] = entry
        self._update_access_order(key)

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if key in self._cache:
            self._remove_entry(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()
        self._access_order.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            self._remove_entry(key)

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._cache:
            return {"size": 0, "entries": []}

        entries = [
            {
                "key": key,
                "age_seconds": entry.age_seconds,
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None
            }
            for key, entry in self._cache.items()
        ]

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "entries": entries
        }

    def _remove_entry(self, key: str) -> None:
        """Remove entry and update access order."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

    def _update_access_order(self, key: str) -> None:
        """Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]


class FileCache:
    """File-based persistent cache with JSON storage."""

    def __init__(
        self,
        cache_dir: Union[str, Path],
        default_ttl: int = 3600,
        max_size_mb: int = 100
    ):
        """Initialize file cache."""
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.max_size_mb = max_size_mb
        self.cache_file = self.cache_dir / "cache.json"

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self._cache: Dict[str, CacheEntry] = {}
        self._load_cache()

    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired:
            self.delete(key)
            self._save_cache()
            return None

        entry.access()
        self._save_cache()
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in file cache."""
        # Check size limit
        if self._get_cache_size_mb() > self.max_size_mb:
            self._cleanup_old_entries()

        ttl = ttl_seconds or self.default_ttl
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=datetime.now(),
            ttl_seconds=ttl
        )

        self._cache[key] = entry
        self._save_cache()

    def delete(self, key: str) -> bool:
        """Delete entry from file cache."""
        if key in self._cache:
            del self._cache[key]
            self._save_cache()
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from file cache."""
        self._cache.clear()
        self._save_cache()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._save_cache()

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "file_size_mb": self._get_cache_size_mb(),
            "max_size_mb": self.max_size_mb,
            "cache_file": str(self.cache_file)
        }

    def _load_cache(self) -> None:
        """Load cache from file."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for key, entry_data in data.items():
                try:
                    entry = CacheEntry.from_dict(entry_data)
                    if not entry.is_expired:
                        self._cache[key] = entry
                except (KeyError, ValueError):
                    # Skip invalid entries
                    continue

        except (json.JSONDecodeError, IOError) as e:
            raise CacheError(
                operation="load_cache",
                reason=f"Failed to load cache file: {str(e)}"
            )

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            cache_data = {
                key: entry.to_dict()
                for key, entry in self._cache.items()
                if not entry.is_expired
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

        except IOError as e:
            raise CacheError(
                operation="save_cache",
                reason=f"Failed to save cache file: {str(e)}"
            )

    def _get_cache_size_mb(self) -> float:
        """Get current cache size in MB."""
        if not self.cache_file.exists():
            return 0.0

        return self.cache_file.stat().st_size / (1024 * 1024)

    def _cleanup_old_entries(self) -> None:
        """Remove old entries to free space."""
        # Sort by last accessed time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed or datetime.min
        )

        # Remove oldest entries until under size limit
        while (self._get_cache_size_mb() > self.max_size_mb * 0.8 and
               len(self._cache) > 10):
            key, _ = sorted_entries.pop(0)
            del self._cache[key]


class NavigationCache:
    """High-level cache interface for navigation data."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize navigation cache with configuration."""
        self.config = config or {}

        # Memory cache for frequently accessed data
        self.memory_cache = MemoryCache(
            max_size=self.config.get("memory_max_size", 1000),
            default_ttl=self.config.get("memory_ttl", 3600)
        )

        # File cache for persistent storage
        cache_dir = self.config.get("cache_dir", "/tmp/nav_cli_cache")
        self.file_cache = FileCache(
            cache_dir=cache_dir,
            default_ttl=self.config.get("file_ttl", 86400),  # 24 hours
            max_size_mb=self.config.get("max_size_mb", 100)
        )

    def cache_location_parsing(
        self,
        query: str,
        origin: LocationEntity,
        destination: LocationEntity,
        confidence: float,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Cache location parsing results."""
        key = f"location_parse:{self._hash_string(query)}"
        value = {
            "origin": origin.to_dict() if hasattr(origin, 'to_dict') else origin,
            "destination": destination.to_dict() if hasattr(destination, 'to_dict') else destination,
            "confidence": confidence,
            "query": query
        }

        # Cache in memory for fast access
        self.memory_cache.set(key, value, ttl_seconds or 3600)

        # Cache in file for persistence
        self.file_cache.set(key, value, ttl_seconds or 86400)

    def get_cached_location_parsing(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached location parsing results."""
        key = f"location_parse:{self._hash_string(query)}"

        # Try memory cache first
        result = self.memory_cache.get(key)
        if result is not None:
            return result

        # Try file cache
        result = self.file_cache.get(key)
        if result is not None:
            # Store in memory for faster future access
            self.memory_cache.set(key, result)
            return result

        return None

    def cache_route_parameters(
        self,
        origin_name: str,
        destination_name: str,
        route_params: RouteParameters,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Cache route parameters."""
        key = f"route_params:{self._hash_string(f'{origin_name}->{destination_name}')}"
        value = route_params.to_dict() if hasattr(route_params, 'to_dict') else route_params

        self.memory_cache.set(key, value, ttl_seconds or 3600)
        self.file_cache.set(key, value, ttl_seconds or 86400)

    def get_cached_route_parameters(
        self,
        origin_name: str,
        destination_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached route parameters."""
        key = f"route_params:{self._hash_string(f'{origin_name}->{destination_name}')}"

        result = self.memory_cache.get(key)
        if result is not None:
            return result

        result = self.file_cache.get(key)
        if result is not None:
            self.memory_cache.set(key, result)
            return result

        return None

    def cleanup(self) -> Dict[str, int]:
        """Cleanup expired entries in both caches."""
        memory_cleaned = self.memory_cache.cleanup_expired()
        file_cleaned = self.file_cache.cleanup_expired()

        return {
            "memory_entries_removed": memory_cleaned,
            "file_entries_removed": file_cleaned
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self.memory_cache.clear()
        self.file_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "file_cache": self.file_cache.get_stats()
        }

    @staticmethod
    def _hash_string(text: str) -> str:
        """Generate hash for cache key."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]


# Global cache instance
_cache_instance: Optional[NavigationCache] = None


def get_cache() -> NavigationCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = NavigationCache()
    return _cache_instance


def setup_cache(config: Dict[str, Any]) -> NavigationCache:
    """Setup cache with custom configuration."""
    global _cache_instance
    _cache_instance = NavigationCache(config)
    return _cache_instance