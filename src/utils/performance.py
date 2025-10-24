"""
Performance monitoring and profiling utilities for CLI Navigation Tool.

Provides timing, memory usage tracking, and performance analysis capabilities
to ensure the 10-second performance target is met.
"""

import time
import tracemalloc
import threading
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import Path

from src.exceptions import TimeoutError


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    name: str
    duration_ms: int
    timestamp: datetime
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def memory_delta_mb(self) -> float:
        """Memory change during the operation."""
        return self.memory_end_mb - self.memory_start_mb

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "memory_start_mb": self.memory_start_mb,
            "memory_end_mb": self.memory_end_mb,
            "memory_peak_mb": self.memory_peak_mb,
            "memory_delta_mb": self.memory_delta_mb,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


class PerformanceMonitor:
    """Performance monitoring system for tracking operation metrics."""

    def __init__(self, enable_memory_tracking: bool = True, enable_profiling: bool = False):
        """Initialize performance monitor."""
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_profiling = enable_profiling
        self.metrics: List[PerformanceMetric] = []
        self.active_timers: Dict[str, float] = {}
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())

        # Memory tracking
        if self.enable_memory_tracking:
            tracemalloc.start()

    @contextmanager
    def timer(self, operation_name: str, timeout_ms: Optional[int] = None, **metadata):
        """Context manager for timing operations with optional timeout."""
        start_time = time.time()
        timer_thread = None
        timeout_occurred = threading.Event()

        # Start memory tracking
        memory_start = self._get_memory_usage() if self.enable_memory_tracking else 0
        memory_peak = memory_start

        # Start timeout timer if specified
        if timeout_ms:
            def timeout_check():
                time.sleep(timeout_ms / 1000.0)
                if not timeout_occurred.is_set():
                    timeout_occurred.set()

            timer_thread = threading.Thread(target=timeout_check, daemon=True)
            timer_thread.start()

        try:
            yield self
            success = True
            error = None

        except Exception as e:
            success = False
            error = str(e)
            raise

        finally:
            # Stop timeout timer
            if timer_thread:
                timeout_occurred.set()

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get final memory usage
            memory_end = self._get_memory_usage() if self.enable_memory_tracking else 0
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                memory_peak = peak / (1024 * 1024)  # Convert to MB

            # Check for timeout
            if timeout_ms and duration_ms > timeout_ms:
                raise TimeoutError(
                    operation=operation_name,
                    timeout_seconds=timeout_ms / 1000.0,
                    details={"actual_duration_ms": duration_ms}
                )

            # Record metric
            metric = PerformanceMetric(
                name=operation_name,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                memory_start_mb=memory_start,
                memory_end_mb=memory_end,
                memory_peak_mb=memory_peak,
                success=success,
                error=error,
                metadata=metadata
            )

            self.metrics.append(metric)

    def add_metric(self, metric: PerformanceMetric):
        """Add a manually created metric."""
        self.metrics.append(metric)

    def get_metric(self, operation_name: str) -> Optional[PerformanceMetric]:
        """Get the most recent metric for an operation."""
        for metric in reversed(self.metrics):
            if metric.name == operation_name:
                return metric
        return None

    def get_metrics_by_name(self, operation_name: str) -> List[PerformanceMetric]:
        """Get all metrics for a specific operation."""
        return [m for m in self.metrics if m.name == operation_name]

    def get_average_time(self, operation_name: str) -> Optional[float]:
        """Get average duration for an operation."""
        metrics = self.get_metrics_by_name(operation_name)
        if not metrics:
            return None
        return sum(m.duration_ms for m in metrics) / len(metrics)

    def get_total_time(self) -> int:
        """Get total time since monitor was created."""
        return int((time.time() - self.start_time) * 1000)

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self._get_memory_usage()

    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB."""
        try:
            return self.process.memory_info().rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB since monitoring started."""
        if not self.enable_memory_tracking or not tracemalloc.is_tracing():
            return 0.0

        try:
            current, peak = tracemalloc.get_traced_memory()
            return peak / (1024 * 1024)
        except (tracemalloc.TracingMemoryError, psutil.NoSuchProcess):
            return 0.0

    def meets_performance_target(self, target_ms: int = 10000) -> bool:
        """Check if total execution time meets performance target."""
        total_time = self.get_total_time()
        return total_time <= target_ms

    def get_slow_operations(self, threshold_ms: int = 1000) -> List[PerformanceMetric]:
        """Get operations that took longer than threshold."""
        return [m for m in self.metrics if m.duration_ms > threshold_ms]

    def get_failed_operations(self) -> List[PerformanceMetric]:
        """Get operations that failed."""
        return [m for m in self.metrics if not m.success]

    def get_memory_intensive_operations(self, threshold_mb: float = 50.0) -> List[PerformanceMetric]:
        """Get operations with high memory usage."""
        return [m for m in self.metrics if m.memory_peak_mb > threshold_mb]

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.metrics:
            return {"message": "No performance data available"}

        # Calculate statistics
        total_time = self.get_total_time()
        successful_operations = [m for m in self.metrics if m.success]
        failed_operations = self.get_failed_operations()

        # Operation breakdown
        operation_stats = {}
        for metric in self.metrics:
            if metric.name not in operation_stats:
                operation_stats[metric.name] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "successful": 0,
                    "failed": 0,
                    "avg_duration_ms": 0,
                    "min_duration_ms": float('inf'),
                    "max_duration_ms": 0,
                    "memory_peak_mb": 0
                }

            stats = operation_stats[metric.name]
            stats["count"] += 1
            stats["total_duration_ms"] += metric.duration_ms
            stats["successful"] += 1 if metric.success else 0
            stats["failed"] += 1 if not metric.success else 0
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
            stats["min_duration_ms"] = min(stats["min_duration_ms"], metric.duration_ms)
            stats["max_duration_ms"] = max(stats["max_duration_ms"], metric.duration_ms)
            stats["memory_peak_mb"] = max(stats["memory_peak_mb"], metric.memory_peak_mb)

        return {
            "summary": {
                "total_execution_time_ms": total_time,
                "meets_10s_target": self.meets_performance_target(),
                "total_operations": len(self.metrics),
                "successful_operations": len(successful_operations),
                "failed_operations": len(failed_operations),
                "current_memory_mb": self.get_memory_usage(),
                "peak_memory_mb": self.get_peak_memory()
            },
            "operations": operation_stats,
            "slow_operations": [m.to_dict() for m in self.get_slow_operations()],
            "failed_operations": [m.to_dict() for m in failed_operations],
            "memory_intensive_operations": [m.to_dict() for m in self.get_memory_intensive_operations()],
            "all_metrics": [m.to_dict() for m in self.metrics]
        }

    def save_report(self, output_path: Path) -> None:
        """Save performance report to file."""
        import json
        report = self.generate_report()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """Reset all metrics and timers."""
        self.metrics.clear()
        self.active_timers.clear()
        self.start_time = time.time()

        if self.enable_memory_tracking and tracemalloc.is_tracing():
            tracemalloc.stop()
            tracemalloc.start()

    def stop_memory_tracking(self) -> None:
        """Stop memory tracing to free resources."""
        if self.enable_memory_tracking and tracemalloc.is_tracing():
            tracemalloc.stop()


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def setup_performance_monitoring(
    enable_memory_tracking: bool = True,
    enable_profiling: bool = False
) -> PerformanceMonitor:
    """Setup and configure the global performance monitor."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(
        enable_memory_tracking=enable_memory_tracking,
        enable_profiling=enable_profiling
    )
    return _performance_monitor


def reset_performance_monitoring() -> None:
    """Reset the global performance monitor."""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.reset()


@contextmanager
def performance_timer(operation_name: str, timeout_ms: Optional[int] = None, **metadata):
    """Convenience function to access global performance monitor."""
    monitor = get_performance_monitor()
    with monitor.timer(operation_name, timeout_ms, **metadata) as timer:
        yield timer


def check_performance_target(target_ms: int = 10000) -> bool:
    """Check if current execution meets performance target."""
    monitor = get_performance_monitor()
    return monitor.meets_performance_target(target_ms)


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary from global monitor."""
    monitor = get_performance_monitor()
    return monitor.generate_report()


def save_performance_report(output_path: str) -> None:
    """Save performance report to specified path."""
    monitor = get_performance_monitor()
    monitor.save_report(Path(output_path))


# Decorator for automatic performance timing
def timed_operation(
    operation_name: Optional[str] = None,
    timeout_ms: Optional[int] = None,
    **metadata
):
    """Decorator to automatically time function execution."""
    def decorator(func: Callable):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            with performance_timer(operation_name, timeout_ms, **metadata):
                return func(*args, **kwargs)

        return wrapper
    return decorator