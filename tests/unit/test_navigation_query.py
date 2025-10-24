"""
Unit tests for NavigationQuery model.

Tests the NavigationQuery data model including validation, parsing,
and serialization functionality.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.navigation import NavigationQuery, QueryType
from src.exceptions import ValidationError as CustomValidationError


class TestNavigationQuery:
    """Test cases for NavigationQuery model."""

    def test_valid_navigation_query_creation(self):
        """Test creating a valid NavigationQuery."""
        query = NavigationQuery(
            raw_input="从北京到上海",
            origin="北京",
            destination="上海",
            query_type=QueryType.CITY_TO_CITY,
            confidence_score=0.95,
            parsing_method="hybrid_nlp",
            processing_time_ms=500
        )

        assert query.raw_input == "从北京到上海"
        assert query.origin == "北京"
        assert query.destination == "上海"
        assert query.query_type == QueryType.CITY_TO_CITY
        assert query.confidence_score == 0.95
        assert query.parsing_method == "hybrid_nlp"
        assert query.processing_time_ms == 500

    def test_minimal_valid_query(self):
        """Test creating query with minimal required fields."""
        query = NavigationQuery(raw_input="从北京到上海")

        assert query.raw_input == "从北京到上海"
        assert query.query_type == QueryType.UNKNOWN
        assert query.confidence_score == 0.0
        assert query.parsing_method == "unknown"
        assert query.processing_time_ms == 0

    def test_empty_raw_input_validation(self):
        """Test that empty raw_input raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            NavigationQuery(raw_input="")

        assert "too short" in str(exc_info.value).lower()

    def test_whitespace_only_input_validation(self):
        """Test that whitespace-only input raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            NavigationQuery(raw_input="   ")

        assert "too short" in str(exc_info.value).lower()

    def test_input_too_long_validation(self):
        """Test that input exceeding max length raises validation error."""
        long_input = "从" + "a" * 300 + "到" + "b" * 300  # Way over 200 chars

        with pytest.raises(ValidationError) as exc_info:
            NavigationQuery(raw_input=long_input)

        assert "too long" in str(exc_info.value).lower()

    def test_input_at_length_limits(self):
        """Test inputs at minimum and maximum length limits."""
        # Minimum valid length (3 characters)
        min_query = NavigationQuery(raw_input="A到B")
        assert min_query.raw_input == "A到B"

        # Maximum valid length (200 characters)
        max_input = "从" + "京" * 98 + "到" + "海" * 98  # Exactly 200 chars
        max_query = NavigationQuery(raw_input=max_input)
        assert max_query.raw_input == max_input

    def test_location_validation_empty_string(self):
        """Test that empty location strings are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NavigationQuery(
                raw_input="从A到B",
                origin="",
                destination="B"
            )

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_location_validation_whitespace_only(self):
        """Test that whitespace-only locations are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NavigationQuery(
                raw_input="从A到B",
                origin="   ",
                destination="B"
            )

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_confidence_score_validation(self):
        """Test confidence score bounds validation."""
        # Valid confidence scores
        query1 = NavigationQuery(
            raw_input="从北京到上海",
            confidence_score=0.0
        )
        assert query1.confidence_score == 0.0

        query2 = NavigationQuery(
            raw_input="从北京到上海",
            confidence_score=1.0
        )
        assert query2.confidence_score == 1.0

        # Invalid confidence scores
        with pytest.raises(ValidationError):
            NavigationQuery(
                raw_input="从北京到上海",
                confidence_score=-0.1
            )

        with pytest.raises(ValidationError):
            NavigationQuery(
                raw_input="从北京到上海",
                confidence_score=1.1
            )

    def test_processing_time_validation(self):
        """Test processing time validation."""
        # Valid processing times
        query1 = NavigationQuery(
            raw_input="从北京到上海",
            processing_time_ms=0
        )
        assert query1.processing_time_ms == 0

        query2 = NavigationQuery(
            raw_input="从北京到上海",
            processing_time_ms=10000
        )
        assert query2.processing_time_ms == 10000

        # Invalid processing time (negative)
        with pytest.raises(ValidationError):
            NavigationQuery(
                raw_input="从北京到上海",
                processing_time_ms=-1
            )

    def test_is_valid_method(self):
        """Test the is_valid() method."""
        # Valid query (has both origin and destination)
        valid_query = NavigationQuery(
            raw_input="从北京到上海",
            origin="北京",
            destination="上海"
        )
        assert valid_query.is_valid() is True

        # Invalid query (missing origin)
        no_origin = NavigationQuery(
            raw_input="从北京到上海",
            origin=None,
            destination="上海"
        )
        assert no_origin.is_valid() is False

        # Invalid query (missing destination)
        no_destination = NavigationQuery(
            raw_input="从北京到上海",
            origin="北京",
            destination=None
        )
        assert no_destination.is_valid() is False

        # Invalid query (both missing)
        both_missing = NavigationQuery(
            raw_input="从北京到上海",
            origin=None,
            destination=None
        )
        assert both_missing.is_valid() is False

    def test_to_dict_method(self):
        """Test the to_dict() serialization method."""
        query = NavigationQuery(
            raw_input="从北京到上海",
            origin="北京",
            destination="上海",
            query_type=QueryType.CITY_TO_CITY,
            confidence_score=0.95,
            parsing_method="hybrid_nlp",
            processing_time_ms=500,
            parse_errors=["error1", "error2"],
            needs_clarification=True
        )

        result = query.to_dict()

        expected = {
            "raw_input": "从北京到上海",
            "origin": "北京",
            "destination": "上海",
            "query_type": "city_to_city",
            "confidence_score": 0.95,
            "parsing_method": "hybrid_nlp",
            "processing_time_ms": 500,
            "parse_errors": ["error1", "error2"],
            "needs_clarification": True
        }

        assert result == expected

    def test_query_type_enum(self):
        """Test all QueryType enum values."""
        query_types = [
            QueryType.CITY_TO_CITY,
            QueryType.DISTRICT_TO_DISTRICT,
            QueryType.LANDMARK_TO_LANDMARK,
            QueryType.TRANSPORT_TO_TRANSPORT,
            QueryType.UNIVERSITY_TO_UNIVERSITY,
            QueryType.UNKNOWN
        ]

        for query_type in query_types:
            query = NavigationQuery(
                raw_input="从A到B",
                query_type=query_type
            )
            assert query.query_type == query_type
            assert isinstance(query.query_type.value, str)

    def test_default_values(self):
        """Test that default values are correctly applied."""
        query = NavigationQuery(raw_input="从北京到上海")

        assert query.origin is None
        assert query.destination is None
        assert query.query_type == QueryType.UNKNOWN
        assert query.confidence_score == 0.0
        assert query.parsing_method == "unknown"
        assert query.processing_time_ms == 0
        assert query.parse_errors == []  # Should be empty list, not None
        assert query.needs_clarification is False

    def test_location_trimming(self):
        """Test that location fields are properly trimmed."""
        query = NavigationQuery(
            raw_input="从北京到上海",
            origin="  北京  ",
            destination="  上海  "
        )

        assert query.origin == "北京"
        assert query.destination == "上海"

    def test_raw_input_trimming(self):
        """Test that raw_input is properly trimmed."""
        query = NavigationQuery(raw_input="  从北京到上海  ")

        assert query.raw_input == "从北京到上海"

    def test_parse_errors_handling(self):
        """Test parse errors list functionality."""
        # With parse errors
        query_with_errors = NavigationQuery(
            raw_input="从A到B",
            parse_errors=["error1", "error2", "error3"]
        )
        assert query_with_errors.parse_errors == ["error1", "error2", "error3"]

        # Default parse errors should be empty list
        query_default = NavigationQuery(raw_input="从A到B")
        assert query_default.parse_errors == []

    def test_comprehensive_query_creation(self):
        """Test creating a comprehensive query with all fields."""
        query = NavigationQuery(
            raw_input="从清华大学到北京大学",
            origin="清华大学",
            destination="北京大学",
            query_type=QueryType.UNIVERSITY_TO_UNIVERSITY,
            confidence_score=0.88,
            parsing_method="hybrid_nlp_with_llm",
            processing_time_ms=750,
            parse_errors=[],
            needs_clarification=False
        )

        assert query.is_valid() is True
        assert query.query_type == QueryType.UNIVERSITY_TO_UNIVERSITY
        assert query.confidence_score > 0.8
        assert query.needs_clarification is False
        assert len(query.parse_errors) == 0


class TestNavigationQueryEdgeCases:
    """Test edge cases and error conditions for NavigationQuery."""

    def test_unicode_handling(self):
        """Test proper handling of Unicode characters."""
        query = NavigationQuery(
            raw_input="从北京🏛️到上海🌃",
            origin="北京🏛️",
            destination="上海🌃"
        )

        assert "🏛️" in query.origin
        assert "🌃" in query.destination

    def test_special_characters_in_raw_input(self):
        """Test handling of special characters in raw input."""
        special_chars = "从北京到上海!@#$%^&*()"
        query = NavigationQuery(raw_input=special_chars)
        assert query.raw_input == special_chars

    def test_very_long_location_names(self):
        """Test handling of very long location names."""
        long_origin = "北京市" + "区" * 50
        long_destination = "上海市" + "路" * 50

        query = NavigationQuery(
            raw_input="从A到B",
            origin=long_origin,
            destination=long_destination
        )

        assert query.origin == long_origin
        assert query.destination == long_destination

    def test_query_type_string_values(self):
        """Test that QueryType enum works with string values."""
        query = NavigationQuery(
            raw_input="从A到B",
            query_type="city_to_city"  # String instead of enum
        )

        # Should automatically convert to enum
        assert query.query_type == QueryType.CITY_TO_CITY

    def test_invalid_query_type_string(self):
        """Test that invalid query type raises error."""
        with pytest.raises(ValueError):
            NavigationQuery(
                raw_input="从A到B",
                query_type="invalid_type"
            )