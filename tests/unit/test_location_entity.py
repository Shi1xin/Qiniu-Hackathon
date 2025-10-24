"""
Unit tests for LocationEntity model.

Tests the LocationEntity data model including validation, confidence scoring,
and location type classification functionality.
"""

import pytest
from pydantic import ValidationError

from src.models.navigation import LocationEntity, LocationType
from src.exceptions import ValidationError as CustomValidationError


class TestLocationEntity:
    """Test cases for LocationEntity model."""

    def test_valid_location_entity_creation(self):
        """Test creating a valid LocationEntity."""
        location = LocationEntity(
            name="北京",
            type=LocationType.CITY,
            confidence=0.95,
            context="中国的首都",
            alternatives=["北京市", "Beijing"],
            parent_region="中国",
            extraction_method="llm",
            coordinates={"latitude": 39.9042, "longitude": 116.4074}
        )

        assert location.name == "北京"
        assert location.type == LocationType.CITY
        assert location.confidence == 0.95
        assert location.context == "中国的首都"
        assert location.alternatives == ["北京市", "Beijing"]
        assert location.parent_region == "中国"
        assert location.extraction_method == "llm"
        assert location.coordinates == {"latitude": 39.9042, "longitude": 116.4074}

    def test_minimal_valid_location(self):
        """Test creating location with minimal required fields."""
        location = LocationEntity(name="上海")

        assert location.name == "上海"
        assert location.type == LocationType.UNKNOWN
        assert location.confidence == 0.0
        assert location.context is None
        assert location.alternatives == []
        assert location.parent_region is None
        assert location.extraction_method == "unknown"
        assert location.coordinates is None

    def test_empty_name_validation(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LocationEntity(name="")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_only_name_validation(self):
        """Test that whitespace-only name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LocationEntity(name="   ")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_name_trimming(self):
        """Test that name is properly trimmed."""
        location = LocationEntity(name="  北京  ")
        assert location.name == "北京"

    def test_confidence_score_bounds(self):
        """Test confidence score validation bounds."""
        # Valid confidence scores
        loc1 = LocationEntity(name="北京", confidence=0.5)
        assert loc1.confidence == 0.5

        loc2 = LocationEntity(name="北京", confidence=1.0)
        assert loc2.confidence == 1.0

        # Invalid confidence scores
        with pytest.raises(ValidationError) as exc_info:
            LocationEntity(name="北京", confidence=0.4)  # Below minimum

        assert "too low" in str(exc_info.value).lower()

        with pytest.raises(ValidationError):
            LocationEntity(name="北京", confidence=1.1)  # Above maximum

    def test_location_type_enum_values(self):
        """Test all LocationType enum values."""
        location_types = [
            LocationType.CITY,
            LocationType.DISTRICT,
            LocationType.LANDMARK,
            LocationType.TRANSPORT,
            LocationType.UNIVERSITY,
            LocationType.ADDRESS,
            LocationType.UNKNOWN
        ]

        for loc_type in location_types:
            location = LocationEntity(name="测试地点", type=loc_type)
            assert location.type == loc_type
            assert isinstance(location.type.value, str)

    def test_is_high_confidence_method(self):
        """Test the is_high_confidence() method."""
        # High confidence (>= 0.8)
        high_conf = LocationEntity(name="北京", confidence=0.85)
        assert high_conf.is_high_confidence() is True

        high_conf_exact = LocationEntity(name="北京", confidence=0.8)
        assert high_conf_exact.is_high_confidence() is True

        # Low confidence (< 0.8)
        low_conf = LocationEntity(name="北京", confidence=0.79)
        assert low_conf.is_high_confidence() is False

        very_low_conf = LocationEntity(name="北京", confidence=0.5)
        assert very_low_conf.is_high_confidence() is False

    def test_needs_disambiguation_method(self):
        """Test the needs_disambiguation() method."""
        # High confidence, no alternatives - doesn't need disambiguation
        clear_location = LocationEntity(
            name="北京",
            confidence=0.9,
            alternatives=[]
        )
        assert clear_location.needs_disambiguation() is False

        # Low confidence - needs disambiguation
        low_conf_location = LocationEntity(
            name="人民广场",
            confidence=0.6,
            alternatives=[]
        )
        assert low_conf_location.needs_disambiguation() is True

        # Multiple alternatives - needs disambiguation
        ambiguous_location = LocationEntity(
            name="人民广场",
            confidence=0.85,
            alternatives=["人民广场(上海)", "人民广场(北京)", "人民广场(广州)"]
        )
        assert ambiguous_location.needs_disambiguation() is True

        # Edge case: exactly 0.7 confidence with no alternatives
        edge_confidence = LocationEntity(
            name="测试地点",
            confidence=0.7,
            alternatives=[]
        )
        assert edge_confidence.needs_disambiguation() is True

    def test_coordinates_validation(self):
        """Test coordinates field validation."""
        # Valid coordinates
        valid_coords = {
            "latitude": 39.9042,
            "longitude": 116.4074
        }
        location = LocationEntity(name="北京", coordinates=valid_coords)
        assert location.coordinates == valid_coords

        # None coordinates should be allowed
        location_no_coords = LocationEntity(name="北京")
        assert location_no_coords.coordinates is None

        # Empty dict should be allowed
        location_empty_coords = LocationEntity(name="北京", coordinates={})
        assert location_empty_coords.coordinates == {}

    def test_alternatives_list_handling(self):
        """Test alternatives list functionality."""
        # With alternatives
        location_with_alts = LocationEntity(
            name="人民广场",
            alternatives=["人民广场(上海)", "人民广场(北京)"]
        )
        assert len(location_with_alts.alternatives) == 2
        assert "人民广场(上海)" in location_with_alts.alternatives

        # Default alternatives should be empty list
        location_default = LocationEntity(name="北京")
        assert location_default.alternatives == []

    def test_location_type_string_conversion(self):
        """Test that LocationType accepts string values."""
        location = LocationEntity(
            name="北京",
            type="city"  # String instead of enum
        )

        assert location.type == LocationType.CITY

    def test_invalid_location_type_string(self):
        """Test that invalid location type raises error."""
        with pytest.raises(ValueError):
            LocationEntity(
                name="北京",
                type="invalid_type"
            )

    def test_comprehensive_location_creation(self):
        """Test creating a comprehensive location entity."""
        location = LocationEntity(
            name="清华大学",
            type=LocationType.UNIVERSITY,
            confidence=0.92,
            context="中国著名高等学府",
            alternatives=["清华", "Tsinghua University"],
            parent_region="北京市",
            extraction_method="hybrid_nlp",
            coordinates={"latitude": 40.0042, "longitude": 116.3261}
        )

        assert location.name == "清华大学"
        assert location.type == LocationType.UNIVERSITY
        assert location.is_high_confidence() is True
        assert location.needs_disambiguation() is False
        assert location.parent_region == "北京市"
        assert "Tsinghua" in location.alternatives[1]

    def test_transport_hubs(self):
        """Test transport hub location types."""
        transport_locations = [
            ("北京站", LocationType.TRANSPORT),
            ("首都机场", LocationType.TRANSPORT),
            ("上海港", LocationType.TRANSPORT)
        ]

        for name, expected_type in transport_locations:
            location = LocationEntity(name=name, type=expected_type)
            assert location.name == name
            assert location.type == expected_type

    def test_landmarks(self):
        """Test landmark location types."""
        landmarks = [
            ("天安门", LocationType.LANDMARK),
            ("故宫", LocationType.LANDMARK),
            ("长城", LocationType.LANDMARK)
        ]

        for name, expected_type in landmarks:
            location = LocationEntity(name=name, type=expected_type)
            assert location.name == name
            assert location.type == expected_type

    def test_universities(self):
        """Test university location types."""
        universities = [
            ("清华大学", LocationType.UNIVERSITY),
            ("北京大学", LocationType.UNIVERSITY),
            ("复旦大学", LocationType.UNIVERSITY)
        ]

        for name, expected_type in universities:
            location = LocationEntity(name=name, type=expected_type)
            assert location.name == name
            assert location.type == expected_type

    def test_districts(self):
        """Test district location types."""
        districts = [
            ("海淀区", LocationType.DISTRICT),
            ("朝阳区", LocationType.DISTRICT),
            ("浦东新区", LocationType.DISTRICT)
        ]

        for name, expected_type in districts:
            location = LocationEntity(name=name, type=expected_type)
            assert location.name == name
            assert location.type == expected_type


class TestLocationEntityEdgeCases:
    """Test edge cases and error conditions for LocationEntity."""

    def test_unicode_location_names(self):
        """Test location names with Unicode characters."""
        unicode_names = [
            "🏛️天安门广场",
            "北京大学🎓",
            "上海🌃外滩",
            "北京🏯故宫"
        ]

        for name in unicode_names:
            location = LocationEntity(name=name)
            assert location.name == name

    def test_very_long_location_names(self):
        """Test handling of very long location names."""
        long_name = "北京市海淀区清华园街道" + "大学" * 20
        location = LocationEntity(name=long_name)
        assert len(location.name) > 100  # Should allow long names

    def test_coordinates_with_various_formats(self):
        """Test coordinates in different formats."""
        # Float coordinates
        location1 = LocationEntity(
            name="北京",
            coordinates={"latitude": 39.9042, "longitude": 116.4074}
        )
        assert isinstance(location1.coordinates["latitude"], float)

        # String coordinates (should be allowed)
        location2 = LocationEntity(
            name="北京",
            coordinates={"latitude": "39.9042", "longitude": "116.4074"}
        )
        assert location2.coordinates["latitude"] == "39.9042"

        # Integer coordinates
        location3 = LocationEntity(
            name="北京",
            coordinates={"lat": 40, "lng": 116}
        )
        assert location3.coordinates["lat"] == 40

    def test_alternatives_with_unicode(self):
        """Test alternatives with Unicode and mixed languages."""
        location = LocationEntity(
            name="清华大学",
            alternatives=["清华大学", "清华", "Tsinghua University", "🎓清华"]
        )
        assert len(location.alternatives) == 4
        assert "🎓清华" in location.alternatives

    def test_context_field_various_content(self):
        """Test context field with different types of content."""
        contexts = [
            "中国的首都",
            "著名的旅游景点",
            "繁忙的交通枢纽",
            "世界一流的高等学府",
            "北京市中心区域"
        ]

        for context in contexts:
            location = LocationEntity(name="测试地点", context=context)
            assert location.context == context

    def test_parent_region_hierarchies(self):
        """Test parent region field with different hierarchical levels."""
        region_tests = [
            ("天安门", "北京市"),
            ("海淀区", "北京市"),
            ("北京", "中国"),
            ("清华大学", "北京市海淀区"),
            ("外滩", "上海市黄浦区")
        ]

        for name, region in region_tests:
            location = LocationEntity(name=name, parent_region=region)
            assert location.parent_region == region

    def test_extraction_method_values(self):
        """Test different extraction method values."""
        extraction_methods = [
            "regex",
            "paddle_nlp",
            "llm",
            "hybrid_nlp",
            "manual",
            "unknown"
        ]

        for method in extraction_methods:
            location = LocationEntity(name="测试地点", extraction_method=method)
            assert location.extraction_method == method