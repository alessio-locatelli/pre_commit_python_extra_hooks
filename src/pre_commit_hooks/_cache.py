"""File content hash caching for pre-commit hooks.

This module implements a content-hash-based cache similar to mypy's approach,
with mtime optimization for performance. Caches are stored in .cache/pre_commit_hooks/
and invalidated when file content changes.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

__all__ = ["CacheManager"]


class CacheManager:
    """Content-hash-based file cache with mtime optimization.

    Uses SHA-1 content hashing for cache keys with mtime fast-path optimization.
    Cache is stored in .cache/pre_commit_hooks/ directory in JSON format.

    Example:
        >>> cache = CacheManager(hook_name="forbid-vars")
        >>> result = cache.get_cached_result(Path("foo.py"), "forbid-vars")
        >>> if result is None:
        ...     # Run expensive check
        ...     violations = check_file("foo.py")
        ...     cache.set_cached_result(
        ...         Path("foo.py"), "forbid-vars", {"violations": violations}
        ...     )
    """

    CACHE_VERSION = "1.0.0"
    DEFAULT_CACHE_DIR = Path(".cache/pre_commit_hooks")

    def __init__(
        self,
        cache_dir: Path | None = None,
        hook_name: str = "",
        cache_version: str | None = None,
    ) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Cache directory (default: .cache/pre_commit_hooks/)
            hook_name: Name of hook for logging/debugging
            cache_version: Cache format version (default: 1.0.0)
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.hook_name = hook_name
        self.cache_version = cache_version or self.CACHE_VERSION
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory with CACHEDIR.TAG marker."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create CACHEDIR.TAG to mark this as a cache directory
        # See: https://bford.info/cachedir/
        tag_file = self.cache_dir / "CACHEDIR.TAG"
        if not tag_file.exists():
            tag_file.write_text(
                "Signature: 8a477f597d28d172789f06886806bc55\n"
                "# This directory is a cache directory for pre_commit_hooks.\n"
                "# It is safe to delete this directory to clear the cache.\n"
            )

    def get_cached_result(
        self, filepath: Path, hook_name: str
    ) -> dict[str, Any] | None:
        """Get cached result for a file if valid.

        Uses mtime fast-path: if mtime unchanged, skip expensive hash computation.
        If mtime changed, verify with content hash.

        Args:
            filepath: Path to Python file
            hook_name: Hook identifier (e.g., "forbid-vars")

        Returns:
            Cached result dict or None if cache invalid/missing
        """
        try:
            # Get file stats
            stat = filepath.stat()
            cache_file = self._get_cache_path(filepath)

            if not cache_file.exists():
                return None

            # Load cache metadata
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            # Version check
            if cache_data.get("version") != self.cache_version:
                return None

            # Fast path: mtime + size check (no hashing needed)
            if (
                cache_data.get("mtime") == stat.st_mtime_ns
                and cache_data.get("size") == stat.st_size
            ):
                # mtime unchanged, cache is valid!
                return cache_data.get("hook_results", {}).get(hook_name)

            # Slow path: mtime changed, verify with content hash
            file_hash = self.compute_file_hash(filepath)
            if cache_data.get("file_hash") == file_hash:
                # Content unchanged, update mtime in cache
                cache_data["mtime"] = stat.st_mtime_ns
                cache_data["size"] = stat.st_size
                self._write_cache(cache_file, cache_data)
                return cache_data.get("hook_results", {}).get(hook_name)

            # Content changed, cache invalid
            return None

        except (OSError, json.JSONDecodeError, KeyError):
            # Treat any error as cache miss
            return None

    def set_cached_result(
        self, filepath: Path, hook_name: str, result: dict[str, Any]
    ) -> None:
        """Store result in cache.

        Args:
            filepath: Path to Python file
            hook_name: Hook identifier (e.g., "forbid-vars")
            result: Result dict to cache (e.g., {"violations": [...]})
        """
        try:
            stat = filepath.stat()
            file_hash = self.compute_file_hash(filepath)
            cache_file = self._get_cache_path(filepath)

            # Load existing cache or create new
            if cache_file.exists():
                with open(cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                cache_data = {"version": self.cache_version, "hook_results": {}}

            # Update cache
            cache_data["file_hash"] = file_hash
            cache_data["mtime"] = stat.st_mtime_ns
            cache_data["size"] = stat.st_size
            cache_data["hook_results"][hook_name] = result
            cache_data["hook_results"][hook_name]["checked_at"] = int(time.time())

            # Atomic write
            self._write_cache(cache_file, cache_data)

        except (OSError, json.JSONDecodeError):
            # Don't crash on cache write failure - just skip caching
            pass

    def _get_cache_path(self, filepath: Path) -> Path:
        """Get cache file path for a source file.

        Uses two-level directory structure for better filesystem performance:
        .cache/pre_commit_hooks/ab/abc123...def.json

        Args:
            filepath: Source file path

        Returns:
            Cache file path
        """
        # Hash the filepath (not content) to get stable cache location
        file_hash = hashlib.sha1(str(filepath.resolve()).encode()).hexdigest()
        prefix = file_hash[:2]
        cache_subdir = self.cache_dir / prefix
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{file_hash}.json"

    @staticmethod
    def compute_file_hash(filepath: Path) -> str:
        """Compute SHA-1 hash of file content.

        Args:
            filepath: Path to file

        Returns:
            SHA-1 hex digest
        """
        sha1 = hashlib.sha1()
        with open(filepath, "rb") as f:
            # Read in 64KB chunks for large files
            for chunk in iter(lambda: f.read(65536), b""):
                sha1.update(chunk)
        return sha1.hexdigest()

    def _write_cache(self, cache_file: Path, data: dict[str, Any]) -> None:
        """Atomically write cache file.

        Uses temp file + rename for atomic write on POSIX systems.

        Args:
            cache_file: Cache file path
            data: Cache data to write
        """
        temp_file = cache_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(cache_file)  # Atomic on POSIX
        finally:
            # Clean up temp file if it still exists
            if temp_file.exists():  # pragma: no cover
                temp_file.unlink()

    def clear_cache(self, older_than_days: int = 30) -> None:
        """Clear old cache entries.

        Args:
            older_than_days: Delete cache files older than this many days
        """
        cutoff = time.time() - (older_than_days * 86400)
        for cache_file in self.cache_dir.rglob("*.json"):  # pragma: no cover
            try:
                if cache_file.stat().st_mtime < cutoff:
                    cache_file.unlink()
            except OSError:
                pass
