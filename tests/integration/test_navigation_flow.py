"""
Integration tests for navigation flow.

Tests the complete end-to-end navigation process from input parsing
to browser launch, ensuring all components work together correctly.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.models.navigation import NavigationQuery, LocationEntity, RouteParameters, ProcessingResult
from src.models.navigation import QueryType, LocationType, TransportMode, ResultStatus
from src.utils.validation import NavigationValidator
from src.exceptions import NavigationToolError, BrowserNotAvailableError


class TestNavigationFlowIntegration:
    """Integration tests for the complete navigation workflow."""

    @pytest.fixture
    def sample_queries(self):
        """Sample navigation queries for testing."""
        return [
            "从北京到上海",
            "中关村到三里屯",
            "天安门到故宫",
            "清华大学到北京大学",
            "北京站到首都机场"
        ]

    @pytest.fixture
    def mock_browser_session(self):
        """Mock browser session for testing."""
        session = Mock()
        session.session_id = "test-session-123"
        session.browser_type = "chromium"
        session.headless = False
        session.launch_time_ms = 2000
        session.navigation_time_ms = 1500
        session.page_url = "https://uri.amap.com/navigation?from=北京&to=上海"
        session.is_active.return_value = True
        session.get_total_time_ms.return_value = 3500
        return session

    @pytest.fixture
    def mock_location_parser(self):
        """Mock location parser for testing."""
        def mock_parse(query_text):
            if "北京到上海" in query_text:
                return {
                    "origin": "北京",
                    "destination": "上海",
                    "query_type": QueryType.CITY_TO_CITY,
                    "confidence": 0.95
                }
            elif "中关村到三里屯" in query_text:
                return {
                    "origin": "中关村",
                    "destination": "三里屯",
                    "query_type": QueryType.DISTRICT_TO_DISTRICT,
                    "confidence": 0.88
                }
            else:
                return {
                    "origin": "未知起点",
                    "destination": "未知终点",
                    "query_type": QueryType.UNKNOWN,
                    "confidence": 0.5
                }
        return mock_parse

    @pytest.fixture
    def mock_url_constructor(self):
        """Mock URL constructor for testing."""
        def mock_construct_url(origin, destination, transport_mode="car"):
            base_url = "https://uri.amap.com/navigation"
            params = {
                "from": origin,
                "to": destination,
                "mode": transport_mode,
                "coordinate": "gaode",
                "callnative": "0"
            }
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base_url}?{query_string}"
        return mock_construct_url

    @patch('src.tools.browser_tools.PlaywrightBrowserManager')
    def test_complete_navigation_flow_success(self, mock_browser_manager, sample_queries):
        """Test successful complete navigation flow."""
        # Setup mocks
        mock_session = Mock()
        mock_session.session_id = "test-session"
        mock_session.launch_time_ms = 2000
        mock_session.page_url = "https://uri.amap.com/navigation?from=北京&to=上海"
        mock_session.is_active.return_value = True

        mock_browser_manager.return_value.launch_browser.return_value = mock_session
        mock_browser_manager.return_value.navigate_to_url.return_value = True

        # Simulate complete flow
        query_text = "从北京到上海"

        # 1. Validate input
        validator = NavigationValidator()
        validation_result = validator.validate_navigation_query(query_text)
        assert validation_result["valid"] is True
        assert validation_result["origin"] == "北京"
        assert validation_result["destination"] == "上海"

        # 2. Create navigation query
        nav_query = NavigationQuery(
            raw_input=query_text,
            origin=validation_result["origin"],
            destination=validation_result["destination"],
            query_type=validation_result["query_type"],
            confidence_score=validation_result["confidence"]
        )

        # 3. Create location entities
        origin_entity = LocationEntity(
            name=nav_query.origin,
            type=LocationType.CITY,
            confidence=0.95
        )
        destination_entity = LocationEntity(
            name=nav_query.destination,
            type=LocationType.CITY,
            confidence=0.95
        )

        # 4. Create route parameters
        route_params = RouteParameters(
            origin=origin_entity,
            destination=destination_entity,
            service_provider="gaode"
        )

        # 5. Get navigation URL
        navigation_url = route_params.get_navigation_url()
        assert "uri.amap.com" in navigation_url
        assert "北京" in navigation_url
        assert "上海" in navigation_url

        # 6. Mock browser operations
        browser_manager = mock_browser_manager.return_value
        session = browser_manager.launch_browser()
        success = browser_manager.navigate_to_url(session, navigation_url)

        assert session is not None
        assert success is True

    def test_validation_flow_various_queries(self, sample_queries):
        """Test validation flow with various query types."""
        validator = NavigationValidator()

        for query in sample_queries:
            validation_result = validator.validate_navigation_query(query)

            assert validation_result["valid"] is True
            assert "origin" in validation_result
            assert "destination" in validation_result
            assert "query_type" in validation_result
            assert "confidence" in validation_result

            # Basic validation of parsed components
            assert len(validation_result["origin"]) > 0
            assert len(validation_result["destination"]) > 0
            assert validation_result["origin"] != validation_result["destination"]

    def test_query_type_classification(self):
        """Test query type classification for different query patterns."""
        test_cases = [
            ("从北京到上海", QueryType.CITY_TO_CITY),
            ("中关村到三里屯", QueryType.DISTRICT_TO_DISTRICT),
            ("天安门到故宫", QueryType.LANDMARK_TO_LANDMARK),
            ("北京站到首都机场", QueryType.TRANSPORT_TO_TRANSPORT),
            ("清华大学到北京大学", QueryType.UNIVERSITY_TO_UNIVERSITY)
        ]

        validator = NavigationValidator()

        for query, expected_type in test_cases:
            validation_result = validator.validate_navigation_query(query)
            assert validation_result["query_type"] == expected_type

    def test_location_entity_creation_flow(self):
        """Test location entity creation from validated query."""
        # Simulate validation result
        validation_result = {
            "valid": True,
            "origin": "清华大学",
            "destination": "北京大学",
            "query_type": QueryType.UNIVERSITY_TO_UNIVERSITY,
            "confidence": 0.92
        }

        # Create location entities
        origin_entity = LocationEntity(
            name=validation_result["origin"],
            type=LocationType.UNIVERSITY,
            confidence=validation_result["confidence"],
            context="北京海淀区著名高校",
            alternatives=["清华", "Tsinghua University"],
            parent_region="北京市"
        )

        destination_entity = LocationEntity(
            name=validation_result["destination"],
            type=LocationType.UNIVERSITY,
            confidence=validation_result["confidence"],
            context="北京海淀区著名高校",
            alternatives=["北大", "Peking University"],
            parent_region="北京市"
        )

        # Validate entities
        assert origin_entity.name == "清华大学"
        assert origin_entity.type == LocationType.UNIVERSITY
        assert origin_entity.is_high_confidence() is True
        assert origin_entity.needs_disambiguation() is False

        assert destination_entity.name == "北京大学"
        assert destination_entity.type == LocationType.UNIVERSITY
        assert "北大" in destination_entity.alternatives

    def test_route_construction_flow(self, mock_url_constructor):
        """Test route parameter construction and URL generation."""
        origin_entity = LocationEntity(
            name="中关村",
            type=LocationType.DISTRICT,
            confidence=0.88
        )
        destination_entity = LocationEntity(
            name="三里屯",
            type=LocationType.DISTRICT,
            confidence=0.90
        )

        # Create route with different transport modes
        transport_modes = [
            TransportMode.DRIVING,
            TransportMode.WALKING,
            TransportMode.TRANSIT
        ]

        for mode in transport_modes:
            route_params = RouteParameters(
                origin=origin_entity,
                destination=destination_entity,
                transport_mode=mode,
                service_provider="gaode"
            )

            url = route_params.get_navigation_url()
            assert "uri.amap.com" in url
            assert "中关村" in url
            assert "三里屯" in url
            assert mode.value in url

    def test_error_handling_flow(self):
        """Test error handling throughout the navigation flow."""
        # Test invalid input
        invalid_queries = [
            "",
            "   ",
            "从到",  # Missing locations
            "A",  # Too short
            "从北京到北京",  # Same origin and destination
            "从" + "A" * 300 + "到" + "B" * 300  # Too long
        ]

        validator = NavigationValidator()

        for invalid_query in invalid_queries:
            with pytest.raises(Exception):  # Should raise some form of validation error
                validator.validate_navigation_query(invalid_query)

    def test_browser_unavailable_error_flow(self):
        """Test flow when browser is not available."""
        origin_entity = LocationEntity(name="北京", type=LocationType.CITY, confidence=0.95)
        destination_entity = LocationEntity(name="上海", type=LocationType.CITY, confidence=0.95)

        route_params = RouteParameters(
            origin=origin_entity,
            destination=destination_entity,
            service_provider="gaode"
        )

        # Simulate browser unavailability
        with patch('src.tools.browser_tools.ChromeBrowserManager') as mock_manager:
            mock_manager.side_effect = BrowserNotAvailableError("Chrome not found")

            with pytest.raises(BrowserNotAvailableError):
                manager = mock_manager()
                session = manager.launch_browser()

    def test_processing_result_creation_flow(self):
        """Test ProcessingResult creation from flow components."""
        # Create successful result
        nav_query = NavigationQuery(
            raw_input="从北京到上海",
            origin="北京",
            destination="上海",
            query_type=QueryType.CITY_TO_CITY,
            confidence_score=0.95
        )

        origin_entity = LocationEntity(name="北京", type=LocationType.CITY, confidence=0.95)
        destination_entity = LocationEntity(name="上海", type=LocationType.CITY, confidence=0.95)

        route_params = RouteParameters(
            origin=origin_entity,
            destination=destination_entity,
            service_provider="gaode"
        )

        browser_session = Mock()
        browser_session.session_id = "test-session"
        browser_session.browser_type = "chromium"
        browser_session.launch_time_ms = 2000
        browser_session.navigation_time_ms = 1500

        processing_result = ProcessingResult(
            status=ResultStatus.SUCCESS,
            success=True,
            message="Navigation completed successfully",
            query=nav_query,
            route_params=route_params,
            browser_session=browser_session,
            total_time_ms=8500,
            component_times={
                "parsing": 500,
                "url_construction": 100,
                "browser_launch": 2000,
                "navigation": 1500
            }
        )

        # Validate result
        assert processing_result.success is True
        assert processing_result.meets_performance_target() is True
        assert "成功" in processing_result.get_user_message()
        assert processing_result.total_time_ms == 8500

    def test_complex_scenario_integration(self):
        """Test integration with complex real-world scenario."""
        # Complex query: "清华大学到首都机场"
        query_text = "清华大学到首都机场"

        # 1. Validation
        validator = NavigationValidator()
        validation_result = validator.validate_navigation_query(query_text)
        assert validation_result["valid"] is True
        assert validation_result["origin"] == "清华大学"
        assert validation_result["destination"] == "首都机场"

        # 2. Create entities with realistic data
        origin_entity = LocationEntity(
            name=validation_result["origin"],
            type=LocationType.UNIVERSITY,
            confidence=validation_result["confidence"],
            coordinates={"latitude": 40.0042, "longitude": 116.3261},
            parent_region="北京市海淀区"
        )

        destination_entity = LocationEntity(
            name=validation_result["destination"],
            type=LocationType.TRANSPORT,
            confidence=validation_result["confidence"],
            coordinates={"latitude": 40.0799, "longitude": 116.6031},
            parent_region="北京市顺义区"
        )

        # 3. Create route with specific options
        route_params = RouteParameters(
            origin=origin_entity,
            destination=destination_entity,
            transport_mode=TransportMode.DRIVING,
            avoid_tolls=True,  # Avoid tolls for airport route
            service_provider="gaode"
        )

        # 4. Generate and validate URL
        navigation_url = route_params.get_navigation_url()
        assert "清华大学" in navigation_url
        assert "首都机场" in navigation_url
        assert "mode=car" in navigation_url
        assert "toll=0" in navigation_url  # Should avoid tolls

        # 5. Create complete navigation query
        nav_query = NavigationQuery(
            raw_input=query_text,
            origin=validation_result["origin"],
            destination=validation_result["destination"],
            query_type=QueryType.UNIVERSITY_TO_TRANSPORT,  # Mixed type
            confidence_score=validation_result["confidence"],
            parsing_method="hybrid_nlp",
            processing_time_ms=750
        )

        assert nav_query.is_valid() is True
        assert nav_query.query_type == QueryType.UNIVERSITY_TO_TRANSPORT

    def test_performance_target_validation(self):
        """Test that performance targets are enforced."""
        # Test various processing times
        test_cases = [
            (5000, True),   # Well under 10s target
            (10000, True),  # Exactly at 10s target
            (10001, False)  # Over 10s target
        ]

        for processing_time_ms, should_meet_target in test_cases:
            result = ProcessingResult(
                status=ResultStatus.SUCCESS,
                success=True,
                message="Test result",
                total_time_ms=processing_time_ms
            )

            assert result.meets_performance_target() == should_meet_target

            # Creating result with time over target should raise validation error
            if processing_time_ms > 10000:
                with pytest.raises(Exception):  # Pydantic validation error
                    ProcessingResult(
                        status=ResultStatus.SUCCESS,
                        success=True,
                        message="Test result",
                        total_time_ms=processing_time_ms  # This should trigger validation
                    )