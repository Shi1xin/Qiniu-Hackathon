"""
Performance tests for CLI Navigation Tool.

Tests that the 10-second performance target is met for various scenarios
and validates performance monitoring functionality.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from pathlib import Path

from src.utils.performance import (
    PerformanceMonitor, performance_timer, get_performance_monitor,
    timed_operation, check_performance_target
)
from src.models.navigation import NavigationQuery, ProcessingResult, ResultStatus
from src.exceptions import TimeoutError


class TestPerformanceMonitoring:
    """Test performance monitoring and timing functionality."""

    def test_performance_monitor_basic_functionality(self):
        """Test basic performance monitor functionality."""
        monitor = PerformanceMonitor()

        with monitor.timer("test_operation") as timer:
            time.sleep(0.1)  # Simulate 100ms operation

        # Check that metric was recorded
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.name == "test_operation"
        assert metric.duration_ms >= 90  # Should be at least 90ms
        assert metric.success is True
        assert metric.error is None

    def test_performance_monitor_with_timeout(self):
        """Test performance monitor with timeout enforcement."""
        monitor = PerformanceMonitor()

        # Test successful operation within timeout
        with monitor.timer("fast_operation", timeout_ms=200):
            time.sleep(0.05)  # 50ms, well under 200ms timeout

        metric = monitor.get_metric("fast_operation")
        assert metric.success is True
        assert metric.duration_ms < 200

        # Test operation that exceeds timeout
        with pytest.raises(TimeoutError):
            with monitor.timer("slow_operation", timeout_ms=50):
                time.sleep(0.1)  # 100ms, exceeds 50ms timeout

        # Should still record the failed metric
        metric = monitor.get_metric("slow_operation")
        assert metric.success is False
        assert "timeout" in metric.error.lower()

    def test_performance_monitor_memory_tracking(self):
        """Test memory tracking functionality."""
        monitor = PerformanceMonitor(enable_memory_tracking=True)

        with monitor.timer("memory_test") as timer:
            # Simulate some memory usage
            data = ['x'] * 1000000  # Allocate some memory
            del data  # Release memory

        metric = monitor.get_metric("memory_test")
        assert metric.memory_start_mb >= 0
        assert metric.memory_end_mb >= 0
        assert metric.memory_delta_mb == metric.memory_end_mb - metric.memory_start_mb

    def test_performance_monitor_statistics(self):
        """Test performance statistics calculation."""
        monitor = PerformanceMonitor()

        # Add multiple operations with different durations
        durations = [100, 200, 150, 300, 250]  # milliseconds
        for i, duration in enumerate(durations):
            with patch('time.time') as mock_time:
                # Mock time to simulate specific durations
                mock_time.side_effect = [0, duration / 1000.0, 0, duration / 1000.0]
                with monitor.timer(f"operation_{i}"):
                    pass

        # Test statistics
        assert monitor.get_total_time() > 0
        assert len(monitor.metrics) == len(durations)

        slow_ops = monitor.get_slow_operations(threshold_ms=200)
        assert len(slow_ops) == 2  # 300ms and 250ms operations

        avg_time = monitor.get_average_time("operation_0")
        assert avg_time == pytest.approx(100, rel=0.1)

    def test_performance_report_generation(self):
        """Test performance report generation."""
        monitor = PerformanceMonitor()

        # Add some sample metrics
        with monitor.timer("parsing", metadata={"input_length": 10}):
            time.sleep(0.01)

        with monitor.timer("url_construction"):
            time.sleep(0.005)

        with monitor.timer("browser_launch"):
            time.sleep(0.02)

        report = monitor.generate_report()

        # Validate report structure
        assert "summary" in report
        assert "operations" in report
        assert "all_metrics" in report

        summary = report["summary"]
        assert "total_execution_time_ms" in summary
        assert "meets_10s_target" in summary
        assert "total_operations" in summary
        assert summary["total_operations"] == 3

        operations = report["operations"]
        assert "parsing" in operations
        assert "url_construction" in operations
        assert "browser_launch" in operations

    @patch('src.utils.performance._performance_monitor')
    def test_global_performance_monitor_access(self, mock_global_monitor):
        """Test global performance monitor access."""
        mock_monitor = Mock()
        mock_global_monitor.return_value = mock_monitor

        # Test getting global monitor
        monitor = get_performance_monitor()
        assert monitor is not None

        # Test timed_operation decorator
        @timed_operation("decorated_function")
        def test_function():
            time.sleep(0.01)
            return "result"

        result = test_function()
        assert result == "result"

    def test_performance_target_validation(self):
        """Test performance target validation."""
        monitor = PerformanceMonitor()

        # Test within target
        with monitor.timer("fast_operation"):
            time.sleep(0.5)  # 500ms, well under 10s

        assert monitor.meets_performance_target() is True

        # Test exactly at target
        monitor.reset()
        with patch('time.time') as mock_time:
            # Mock time to simulate exactly 10 seconds
            mock_time.side_effect = [0, 10.0]
            with monitor.timer("target_operation"):
                pass

        assert monitor.meets_performance_target() is True

        # Test over target
        monitor.reset()
        with patch('time.time') as mock_time:
            # Mock time to simulate 10.1 seconds
            mock_time.side_effect = [0, 10.1]
            with monitor.timer("slow_operation"):
                pass

        assert monitor.meets_performance_target() is False


class TestNavigationPerformance:
    """Test performance of navigation-specific operations."""

    def test_input_validation_performance(self):
        """Test that input validation meets performance targets."""
        validator = Mock()  # We'll mock the actual validator
        validator.validate_navigation_query.return_value = {
            "valid": True,
            "origin": "北京",
            "destination": "上海",
            "query_type": "city_to_city",
            "confidence": 0.95
        }

        test_queries = [
            "从北京到上海",
            "中关村到三里屯",
            "天安门到故宫",
            "清华大学到北京大学",
            "北京站到首都机场"
        ]

        # Measure validation performance
        start_time = time.time()
        for query in test_queries:
            result = validator.validate_navigation_query(query)
            assert result["valid"] is True

        total_time_ms = int((time.time() - start_time) * 1000)

        # Validation should be very fast (< 100ms for 5 queries)
        assert total_time_ms < 100
        avg_time_per_query = total_time_ms / len(test_queries)
        assert avg_time_per_query < 20  # < 20ms per query

    def test_url_construction_performance(self):
        """Test that URL construction meets performance targets."""
        from src.models.navigation import LocationEntity, RouteParameters, LocationType

        origin_entity = LocationEntity(
            name="清华大学",
            type=LocationType.UNIVERSITY,
            confidence=0.92
        )
        destination_entity = LocationEntity(
            name="首都机场",
            type=LocationType.TRANSPORT,
            confidence=0.95
        )

        # Measure URL construction performance
        start_time = time.time()
        for i in range(100):  # Test 100 URL constructions
            route_params = RouteParameters(
                origin=origin_entity,
                destination=destination_entity,
                service_provider="gaode"
            )
            url = route_params.get_navigation_url()
            assert "uri.amap.com" in url

        total_time_ms = int((time.time() - start_time) * 1000)

        # URL construction should be very fast (< 500ms for 100 URLs)
        assert total_time_ms < 500
        avg_time_per_url = total_time_ms / 100
        assert avg_time_per_url < 5  # < 5ms per URL

    def test_model_creation_performance(self):
        """Test that model creation meets performance targets."""
        from src.models.navigation import NavigationQuery, LocationEntity

        # Test NavigationQuery creation
        start_time = time.time()
        for i in range(1000):  # Test 1000 query creations
            query = NavigationQuery(
                raw_input=f"从北京到上海{i}",
                origin="北京",
                destination="上海",
                confidence_score=0.95,
                processing_time_ms=500
            )
            assert query.is_valid() is True

        query_creation_time = int((time.time() - start_time) * 1000)

        # Should be very fast (< 1000ms for 1000 queries)
        assert query_creation_time < 1000
        avg_time_per_query = query_creation_time / 1000
        assert avg_time_per_query < 1  # < 1ms per query

        # Test LocationEntity creation
        start_time = time.time()
        for i in range(1000):
            entity = LocationEntity(
                name=f"测试地点{i}",
                type="city",
                confidence=0.9
            )
            assert entity.name == f"测试地点{i}"

        entity_creation_time = int((time.time() - start_time) * 1000)

        # Should be very fast (< 500ms for 1000 entities)
        assert entity_creation_time < 500
        avg_time_per_entity = entity_creation_time / 1000
        assert avg_time_per_entity < 0.5  # < 0.5ms per entity

    def test_cache_performance(self):
        """Test cache operation performance."""
        from src.cache.cache_manager import NavigationCache

        cache = NavigationCache()

        # Test cache write performance
        test_data = {"origin": "北京", "destination": "上海", "confidence": 0.95}
        start_time = time.time()
        for i in range(1000):
            cache.memory_cache.set(f"key_{i}", test_data)

        write_time_ms = int((time.time() - start_time) * 1000)
        assert write_time_ms < 1000  # < 1s for 1000 writes
        avg_write_time = write_time_ms / 1000
        assert avg_write_time < 1  # < 1ms per write

        # Test cache read performance
        start_time = time.time()
        for i in range(1000):
            result = cache.memory_cache.get(f"key_{i}")
            assert result is not None

        read_time_ms = int((time.time() - start_time) * 1000)
        assert read_time_ms < 500  # < 500ms for 1000 reads
        avg_read_time = read_time_ms / 1000
        assert avg_read_time < 0.5  # < 0.5ms per read

    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance."""
        from src.exceptions import ValidationError

        validator = Mock()

        # Test validation error performance
        error_count = 100
        validator.validate_navigation_query.side_effect = ValidationError(
            field_name="query",
            value="invalid",
            reason="test error"
        )

        start_time = time.time()
        for i in range(error_count):
            try:
                validator.validate_navigation_query("")  # Empty input should trigger error
            except ValidationError:
                pass  # Expected error

        error_handling_time = int((time.time() - start_time) * 1000)

        # Error handling should be fast (< 100ms for 100 errors)
        assert error_handling_time < 100
        avg_error_time = error_handling_time / error_count
        assert avg_error_time < 1  # < 1ms per error


class TestPerformanceUnderLoad:
    """Test performance under various load conditions."""

    def test_concurrent_operations_performance(self):
        """Test performance with concurrent operations."""
        monitor = PerformanceMonitor()

        def worker(worker_id, results):
            """Worker function for concurrent operations."""
            with monitor.timer(f"worker_{worker_id}") as timer:
                # Simulate some work
                time.sleep(0.1)
                results.append(worker_id)

        # Run multiple concurrent operations
        num_workers = 10
        results = []
        threads = []

        start_time = time.time()

        for i in range(num_workers):
            thread = threading.Thread(target=worker, args=(i, results))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time_ms = int((time.time() - start_time) * 1000)

        # With 10 concurrent 100ms operations, total time should be around 100-200ms
        assert total_time_ms < 300
        assert len(results) == num_workers
        assert len(monitor.metrics) == num_workers

    def test_memory_usage_under_load(self):
        """Test memory usage under high load."""
        monitor = PerformanceMonitor(enable_memory_tracking=True)

        initial_memory = monitor.get_memory_usage()

        # Create many objects to test memory usage
        large_objects = []
        for i in range(100):
            # Create objects with some data
            obj = {
                "id": i,
                "data": "x" * 10000,  # 10KB per object
                "nested": {
                    "level1": {"level2": {"level3": "data" * 100}}
                }
            }
            large_objects.append(obj)

        peak_memory = monitor.get_peak_memory()
        memory_increase = peak_memory - initial_memory

        # Memory usage should increase but stay reasonable (< 50MB for this test)
        assert memory_increase < 50  # Should be less than 50MB

        # Cleanup
        del large_objects

    def test_performance_target_stress_test(self):
        """Test performance target under stress conditions."""
        monitor = PerformanceMonitor()

        # Simulate the complete navigation flow many times
        num_iterations = 100

        start_time = time.time()
        for i in range(num_iterations):
            with monitor.timer("navigation_simulation"):
                # Simulate parsing (fast)
                time.sleep(0.001)

                # Simulate URL construction (fast)
                time.sleep(0.0005)

                # Simulate browser launch (slowest part, but simulated)
                time.sleep(0.01)

        total_time_ms = int((time.time() - start_time) * 1000)
        avg_time_per_iteration = total_time_ms / num_iterations

        # Each simulated iteration should be very fast (< 20ms average)
        assert avg_time_per_iteration < 20
        assert total_time_ms < 2000  # Total should be under 2 seconds

        # Check that we're still under the 10-second target
        assert monitor.meets_performance_target(10000) is True

        # Get slow operations
        slow_ops = monitor.get_slow_operations(threshold_ms=15)
        # Most operations should be fast
        assert len(slow_ops) < num_iterations * 0.1  # Less than 10% should be slow


class TestPerformanceRegressionPrevention:
    """Tests to prevent performance regressions."""

    def test_validation_performance_regression(self):
        """Test that validation performance doesn't regress."""
        from src.utils.validation import NavigationValidator

        validator = NavigationValidator()
        test_queries = [
            "从北京到上海",
            "中关村到三里屯",
            "天安门到故宫",
            "清华大学到北京大学"
        ]

        # Measure current performance
        start_time = time.time()
        for query in test_queries:
            result = validator.validate_navigation_query(query)
            assert result["valid"] is True

        current_time = int((time.time() - start_time) * 1000)

        # Set performance regression threshold (should be very fast)
        max_allowed_time_ms = 50  # 50ms for 4 queries = ~12ms per query
        assert current_time < max_allowed_time_ms, (
            f"Validation performance regression: {current_time}ms > {max_allowed_time_ms}ms"
        )

    def test_model_instantiation_regression(self):
        """Test that model instantiation doesn't regress."""
        test_iterations = 1000

        # Test NavigationQuery instantiation
        start_time = time.time()
        for i in range(test_iterations):
            query = NavigationQuery(
                raw_input=f"从北京到上海{i}",
                origin="北京",
                destination="上海",
                confidence_score=0.95
            )
            assert query.is_valid() is True

        query_time = int((time.time() - start_time) * 1000)
        max_query_time_ms = 500  # Should be < 0.5ms per query
        assert query_time < max_query_time_ms, (
            f"NavigationQuery performance regression: {query_time}ms > {max_query_time_ms}ms"
        )

        # Test LocationEntity instantiation
        start_time = time.time()
        for i in range(test_iterations):
            entity = LocationEntity(
                name=f"测试地点{i}",
                type="city",
                confidence=0.9
            )
            assert entity.name == f"测试地点{i}"

        entity_time = int((time.time() - start_time) * 1000)
        max_entity_time_ms = 300  # Should be < 0.3ms per entity
        assert entity_time < max_entity_time_ms, (
            f"LocationEntity performance regression: {entity_time}ms > {max_entity_time_ms}ms"
        )

    def test_url_construction_regression(self):
        """Test that URL construction performance doesn't regress."""
        from src.models.navigation import LocationEntity, RouteParameters

        origin = LocationEntity(name="北京", type="city", confidence=0.95)
        destination = LocationEntity(name="上海", type="city", confidence=0.95)

        test_iterations = 1000

        start_time = time.time()
        for i in range(test_iterations):
            route_params = RouteParameters(
                origin=origin,
                destination=destination,
                service_provider="gaode"
            )
            url = route_params.get_navigation_url()
            assert "uri.amap.com" in url

        construction_time = int((time.time() - start_time) * 1000)
        max_construction_time_ms = 1000  # Should be < 1ms per URL
        assert construction_time < max_construction_time_ms, (
            f"URL construction performance regression: {construction_time}ms > {max_construction_time_ms}ms"
        )