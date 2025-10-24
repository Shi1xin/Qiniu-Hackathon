"""
Unit tests for RouteParameters model.

Tests the RouteParameters data model including URL construction,
transport mode validation, and Gaode Maps integration.
"""

import pytest
from urllib.parse import urlparse, parse_qs
from pydantic import ValidationError

from src.models.navigation import (
    RouteParameters, LocationEntity, LocationType, TransportMode
)
from src.exceptions import ValidationError as CustomValidationError


class TestRouteParameters:
    """Test cases for RouteParameters model."""

    def test_valid_route_parameters_creation(self):
        """Test creating valid RouteParameters with location entities."""
        origin = LocationEntity(
            name="北京",
            type=LocationType.CITY,
            confidence=0.95
        )
        destination = LocationEntity(
            name="上海",
            type=LocationType.CITY,
            confidence=0.95
        )

        route = RouteParameters(
            origin=origin,
            destination=destination,
            transport_mode=TransportMode.DRIVING,
            avoid_tolls=False,
            avoid_highways=False,
            service_provider="gaode"
        )

        assert route.origin == origin
        assert route.destination == destination
        assert route.transport_mode == TransportMode.DRIVING
        assert route.avoid_tolls is False
        assert route.avoid_highways is False
        assert route.service_provider == "gaode"
        assert route.construction_time_ms == 0

    def test_minimal_route_parameters(self):
        """Test creating route parameters with minimal required fields."""
        origin = LocationEntity(name="北京", confidence=0.8)
        destination = LocationEntity(name="上海", confidence=0.8)

        route = RouteParameters(origin=origin, destination=destination)

        assert route.origin == origin
        assert route.destination == destination
        assert route.transport_mode == TransportMode.DRIVING  # Default
        assert route.avoid_tolls is False  # Default
        assert route.avoid_highways is False  # Default
        assert route.service_provider == "gaode"  # Default

    def test_transport_modes(self):
        """Test all transport mode options."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        transport_modes = [
            TransportMode.DRIVING,
            TransportMode.WALKING,
            TransportMode.TRANSIT,
            TransportMode.RIDING,
            TransportMode.TRUCK
        ]

        for mode in transport_modes:
            route = RouteParameters(
                origin=origin,
                destination=destination,
                transport_mode=mode
            )
            assert route.transport_mode == mode

    def test_transport_mode_string_conversion(self):
        """Test that transport mode accepts string values."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            transport_mode="walk"  # String instead of enum
        )

        assert route.transport_mode == TransportMode.WALKING

    def test_invalid_service_provider(self):
        """Test that invalid service provider raises validation error."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        with pytest.raises(ValidationError) as exc_info:
            RouteParameters(
                origin=origin,
                destination=destination,
                service_provider="invalid_provider"
            )

        assert "service provider" in str(exc_info.value).lower()

    def test_valid_service_providers(self):
        """Test all valid service provider options."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        providers = ["gaode", "baidu", "tencent"]

        for provider in providers:
            route = RouteParameters(
                origin=origin,
                destination=destination,
                service_provider=provider
            )
            assert route.service_provider == provider

    def test_route_preferences(self):
        """Test route preference settings."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        # Avoid tolls
        route1 = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=True,
            avoid_highways=False
        )
        assert route1.avoid_tolls is True
        assert route1.avoid_highways is False

        # Avoid highways
        route2 = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=False,
            avoid_highways=True
        )
        assert route2.avoid_tolls is False
        assert route2.avoid_highways is True

        # Avoid both
        route3 = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=True,
            avoid_highways=True
        )
        assert route3.avoid_tolls is True
        assert route3.avoid_highways is True

    def test_construction_time_validation(self):
        """Test construction time validation."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        # Valid construction times
        route1 = RouteParameters(origin=origin, destination=destination, construction_time_ms=0)
        assert route1.construction_time_ms == 0

        route2 = RouteParameters(origin=origin, destination=destination, construction_time_ms=1000)
        assert route2.construction_time_ms == 1000

        # Invalid construction time (negative)
        with pytest.raises(ValidationError):
            RouteParameters(
                origin=origin,
                destination=destination,
                construction_time_ms=-1
            )

    def test_get_navigation_url_gaode_basic(self):
        """Test basic Gaode Maps URL construction."""
        origin = LocationEntity(name="北京", type=LocationType.CITY)
        destination = LocationEntity(name="上海", type=LocationType.CITY)

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()
        parsed_url = urlparse(url)

        assert parsed_url.netloc == "uri.amap.com"
        assert parsed_url.path == "/navigation"

        query_params = parse_qs(parsed_url.query)
        assert query_params["from"][0] == "北京"
        assert query_params["to"][0] == "上海"
        assert query_params["mode"][0] == "car"
        assert query_params["coordinate"][0] == "gaode"
        assert query_params["callnative"][0] == "0"

    def test_get_navigation_url_gaode_with_encoding(self):
        """Test Gaode Maps URL construction with special characters."""
        origin = LocationEntity(name="北京天安门")
        destination = LocationEntity(name="上海外滩")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Check that Chinese characters are properly URL encoded
        from urllib.parse import unquote
        assert unquote(query_params["from"][0]) == "北京天安门"
        assert unquote(query_params["to"][0]) == "上海外滩"

    def test_get_navigation_url_different_transport_modes(self):
        """Test URL construction for different transport modes."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        transport_test_cases = [
            (TransportMode.DRIVING, "car"),
            (TransportMode.WALKING, "walk"),
            (TransportMode.TRANSIT, "bus"),
            (TransportMode.RIDING, "ride"),
            (TransportMode.TRUCK, "truck")
        ]

        for mode, expected_mode in transport_test_cases:
            route = RouteParameters(
                origin=origin,
                destination=destination,
                transport_mode=mode,
                service_provider="gaode"
            )

            url = route.get_navigation_url()
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            assert query_params["mode"][0] == expected_mode

    def test_get_navigation_url_with_avoid_options(self):
        """Test URL construction with route avoidance options."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        # Avoid tolls
        route_avoid_tolls = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=True,
            avoid_highways=False,
            service_provider="gaode"
        )

        url = route_avoid_tolls.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        assert query_params["toll"][0] == "0"

        # Avoid highways
        route_avoid_highways = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=False,
            avoid_highways=True,
            service_provider="gaode"
        )

        url = route_avoid_highways.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        assert query_params["highway"][0] == "0"

        # Avoid both
        route_avoid_both = RouteParameters(
            origin=origin,
            destination=destination,
            avoid_tolls=True,
            avoid_highways=True,
            service_provider="gaode"
        )

        url = route_avoid_both.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        assert query_params["toll"][0] == "0"
        assert query_params["highway"][0] == "0"

    def test_get_navigation_url_with_encoded_components(self):
        """Test URL construction with pre-encoded components."""
        origin = LocationEntity(name="北京天安门")
        destination = LocationEntity(name="上海外滩")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            encoded_origin="Beijing%20Tiananmen",
            encoded_destination="Shanghai%20Bund",
            service_provider="gaode"
        )

        url = route.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Should use encoded components if provided
        assert query_params["from"][0] == "Beijing%20Tiananmen"
        assert query_params["to"][0] == "Shanghai%20Bund"

    def test_get_navigation_url_unsupported_provider(self):
        """Test that unsupported provider raises error."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="unsupported"
        )

        with pytest.raises(ValueError) as exc_info:
            route.get_navigation_url()

        assert "not implemented" in str(exc_info.value).lower()

    def test_construct_gaode_url_method(self):
        """Test the internal _construct_gaode_url method."""
        origin = LocationEntity(name="清华大学")
        destination = LocationEntity(name="北京大学")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        # Call the internal method directly
        url = route._construct_gaode_url()

        assert url.startswith("https://uri.amap.com/navigation?")
        assert "from=" in url
        assert "to=" in url
        assert "mode=car" in url
        assert "coordinate=gaode" in url

    def test_url_structure_validation(self):
        """Test that generated URLs have proper structure."""
        origin = LocationEntity(name="北京")
        destination = LocationEntity(name="上海")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()

        # Basic URL structure validation
        assert url.startswith("https://")
        assert "uri.amap.com" in url
        assert "/navigation" in url
        assert "from=" in url
        assert "to=" in url

        # Should be a valid URL
        parsed_url = urlparse(url)
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc == "uri.amap.com"
        assert parsed_url.path == "/navigation"

    def test_complex_route_scenario(self):
        """Test a complex real-world route scenario."""
        origin = LocationEntity(
            name="清华大学",
            type=LocationType.UNIVERSITY,
            confidence=0.92,
            coordinates={"latitude": 40.0042, "longitude": 116.3261}
        )
        destination = LocationEntity(
            name="首都机场",
            type=LocationType.TRANSPORT,
            confidence=0.95,
            coordinates={"latitude": 40.0799, "longitude": 116.6031}
        )

        route = RouteParameters(
            origin=origin,
            destination=destination,
            transport_mode=TransportMode.DRIVING,
            avoid_tolls=True,
            avoid_highways=False,
            service_provider="gaode",
            construction_time_ms=150
        )

        url = route.get_navigation_url()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Validate all components are present
        assert query_params["from"][0] == "清华大学"
        assert query_params["to"][0] == "首都机场"
        assert query_params["mode"][0] == "car"
        assert query_params["toll"][0] == "0"  # Avoid tolls
        assert "highway" not in query_params  # Not avoiding highways

        assert route.construction_time_ms == 150
        assert route.origin.name == "清华大学"
        assert route.destination.name == "首都机场"


class TestRouteParametersEdgeCases:
    """Test edge cases and error conditions for RouteParameters."""

    def test_unicode_location_names_in_url(self):
        """Test URL construction with Unicode location names."""
        origin = LocationEntity(name="🏛️天安门广场")
        destination = LocationEntity(name="🎓清华大学")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()

        # URL should contain the Unicode names (properly encoded)
        assert "from=" in url
        assert "to=" in url
        assert len(url) > len("https://uri.amap.com/navigation")

    def test_very_long_location_names_in_url(self):
        """Test URL construction with very long location names."""
        long_origin = "北京市海淀区清华园街道清华大学" + "大学" * 10
        long_destination = "上海市浦东新区陆家嘴金融贸易区" + "中心" * 10

        origin = LocationEntity(name=long_origin)
        destination = LocationEntity(name=long_destination)

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()
        parsed_url = urlparse(url)

        # URL should be valid even with long names
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc == "uri.amap.com"

    def test_special_characters_in_location_names(self):
        """Test URL construction with special characters in names."""
        origin = LocationEntity(name="北京站(主站)")
        destination = LocationEntity(name="上海虹桥机场T2")

        route = RouteParameters(
            origin=origin,
            destination=destination,
            service_provider="gaode"
        )

        url = route.get_navigation_url()

        # Should be a valid URL with proper encoding
        parsed_url = urlparse(url)
        assert parsed_url.scheme == "https"
        assert "from=" in url
        assert "to=" in url