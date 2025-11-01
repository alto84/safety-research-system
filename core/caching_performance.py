"""Caching and performance monitoring system."""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import time
from collections import defaultdict


logger = logging.getLogger(__name__)


class MemoryCache:
    """
    In-memory cache with TTL support.

    Serves as fallback when Redis is not available.
    """

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize memory cache.

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            return None

        entry = self.cache[key]
        expires_at = entry.get("expires_at")

        # Check expiration
        if expires_at and datetime.utcnow() > expires_at:
            del self.cache[key]
            return None

        return entry.get("value")

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(
            1 for entry in self.cache.values()
            if entry.get("expires_at") and datetime.utcnow() > entry["expires_at"]
        )

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
        }


class RedisCache:
    """
    Redis-based caching layer.

    Falls back to MemoryCache if Redis is not available.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        enable_fallback: bool = True
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            enable_fallback: Enable fallback to memory cache
        """
        self.default_ttl = default_ttl
        self.enable_fallback = enable_fallback
        self.redis_client = None
        self.fallback_cache = MemoryCache(default_ttl) if enable_fallback else None

        # Try to connect to Redis
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                if not enable_fallback:
                    raise
                logger.info("Using in-memory cache fallback")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Fallback to memory cache
        if self.fallback_cache:
            return self.fallback_cache.get(key)

        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        ttl = ttl if ttl is not None else self.default_ttl

        # Try Redis first
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # Fallback to memory cache
        if self.fallback_cache:
            self.fallback_cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        success = False

        # Try Redis first
        if self.redis_client:
            try:
                success = self.redis_client.delete(key) > 0
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Fallback to memory cache
        if self.fallback_cache:
            return self.fallback_cache.delete(key) or success

        return success

    def clear(self) -> None:
        """Clear all cache entries."""
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        # Fallback to memory cache
        if self.fallback_cache:
            self.fallback_cache.clear()


class ResultCache:
    """
    Result caching for expensive operations (especially LLM calls).
    """

    def __init__(self, cache_backend: Optional[Any] = None):
        """
        Initialize result cache.

        Args:
            cache_backend: Cache backend (RedisCache or MemoryCache)
        """
        self.cache = cache_backend or MemoryCache()
        self.hit_count = 0
        self.miss_count = 0

    def generate_key(
        self,
        operation: str,
        **kwargs
    ) -> str:
        """
        Generate cache key from operation and parameters.

        Args:
            operation: Operation name
            **kwargs: Operation parameters

        Returns:
            Cache key
        """
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_data = f"{operation}:{json.dumps(sorted_kwargs, sort_keys=True)}"

        # Hash for consistent key length
        return f"result:{hashlib.sha256(key_data.encode()).hexdigest()}"

    def get_cached_result(
        self,
        operation: str,
        **kwargs
    ) -> Optional[Any]:
        """
        Get cached result for operation.

        Args:
            operation: Operation name
            **kwargs: Operation parameters

        Returns:
            Cached result or None
        """
        key = self.generate_key(operation, **kwargs)
        result = self.cache.get(key)

        if result is not None:
            self.hit_count += 1
            logger.info(f"Cache hit for {operation}")
        else:
            self.miss_count += 1
            logger.debug(f"Cache miss for {operation}")

        return result

    def cache_result(
        self,
        result: Any,
        operation: str,
        ttl: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Cache operation result.

        Args:
            result: Result to cache
            operation: Operation name
            ttl: Time-to-live in seconds
            **kwargs: Operation parameters
        """
        key = self.generate_key(operation, **kwargs)
        self.cache.set(key, result, ttl)
        logger.debug(f"Cached result for {operation}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (
            self.hit_count / total_requests if total_requests > 0 else 0
        )

        return {
            "total_requests": total_requests,
            "cache_hits": self.hit_count,
            "cache_misses": self.miss_count,
            "hit_rate": hit_rate,
        }


def memoize(ttl: int = 3600, cache_backend: Optional[Any] = None):
    """
    Decorator for memoizing expensive function calls.

    Args:
        ttl: Time-to-live for cached results in seconds
        cache_backend: Cache backend to use

    Returns:
        Decorated function
    """
    result_cache = ResultCache(cache_backend)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = result_cache.generate_key(
                operation=func.__name__,
                args=args,
                kwargs=kwargs
            )

            # Try to get cached result
            cached = result_cache.cache.get(cache_key)
            if cached is not None:
                result_cache.hit_count += 1
                logger.info(f"Memoized result for {func.__name__}")
                return cached

            # Execute function
            result_cache.miss_count += 1
            result = func(*args, **kwargs)

            # Cache result
            result_cache.cache.set(cache_key, result, ttl)

            return result

        # Attach cache stats to function
        wrapper.cache_stats = result_cache.get_stats

        return wrapper

    return decorator


class PerformanceMonitor:
    """
    Performance monitoring system for tracking operation metrics.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)

    def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Record operation performance.

        Args:
            operation: Operation name
            duration: Operation duration in seconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        self.metrics[operation].append(duration)
        self.operation_counts[operation] += 1

        if not success:
            self.error_counts[operation] += 1

        logger.debug(
            f"Performance: {operation} completed in {duration:.3f}s "
            f"(success: {success})"
        )

    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics.

        Args:
            operation: Specific operation name (None for all)

        Returns:
            Performance metrics dictionary
        """
        if operation:
            return self._get_operation_metrics(operation)

        # Return metrics for all operations
        return {
            op: self._get_operation_metrics(op)
            for op in self.metrics.keys()
        }

    def _get_operation_metrics(self, operation: str) -> Dict[str, Any]:
        """Get metrics for specific operation."""
        durations = self.metrics.get(operation, [])

        if not durations:
            return {
                "operation": operation,
                "count": 0,
                "error_count": 0,
            }

        return {
            "operation": operation,
            "count": self.operation_counts[operation],
            "error_count": self.error_counts[operation],
            "error_rate": (
                self.error_counts[operation] / self.operation_counts[operation]
                if self.operation_counts[operation] > 0 else 0
            ),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
        }

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate performance report.

        Returns:
            Performance report
        """
        all_metrics = self.get_metrics()

        # Overall statistics
        total_operations = sum(self.operation_counts.values())
        total_errors = sum(self.error_counts.values())
        total_duration = sum(
            sum(durations) for durations in self.metrics.values()
        )

        # Slowest operations
        slowest_ops = sorted(
            all_metrics.items(),
            key=lambda x: x[1].get("avg_duration", 0),
            reverse=True
        )[:5]

        # Most frequent operations
        frequent_ops = sorted(
            self.operation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "overall": {
                "total_operations": total_operations,
                "total_errors": total_errors,
                "error_rate": total_errors / total_operations if total_operations > 0 else 0,
                "total_duration": total_duration,
            },
            "slowest_operations": [
                {"operation": op, **metrics}
                for op, metrics in slowest_ops
            ],
            "most_frequent_operations": [
                {"operation": op, "count": count}
                for op, count in frequent_ops
            ],
            "detailed_metrics": all_metrics,
        }


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator for monitoring function performance.

    Args:
        operation_name: Optional operation name (defaults to function name)

    Returns:
        Decorated function
    """
    # Shared performance monitor
    if not hasattr(monitor_performance, 'monitor'):
        monitor_performance.monitor = PerformanceMonitor()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            success = True
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = e
                raise
            finally:
                duration = time.time() - start_time
                monitor_performance.monitor.record_operation(
                    op_name,
                    duration,
                    success,
                    metadata={"error": str(error) if error else None}
                )

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    # Example: Using memoization
    @memoize(ttl=600)
    def expensive_calculation(x: int, y: int) -> int:
        time.sleep(1)  # Simulate expensive operation
        return x + y

    # First call - cache miss
    result1 = expensive_calculation(5, 3)
    print(f"Result: {result1}")

    # Second call - cache hit
    result2 = expensive_calculation(5, 3)
    print(f"Cached result: {result2}")

    # Example: Performance monitoring
    @monitor_performance()
    def process_task(task_id: int) -> str:
        time.sleep(0.5)
        return f"Task {task_id} completed"

    for i in range(5):
        process_task(i)

    # Generate performance report
    report = monitor_performance.monitor.generate_report()
    print("\nPerformance Report:")
    print(json.dumps(report, indent=2))
