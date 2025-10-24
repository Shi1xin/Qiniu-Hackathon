"""
Input validation utilities for CLI Navigation Tool.

Provides validation functions for navigation queries, locations, and other
user inputs with user-friendly error messages.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote, unquote

from src.models.navigation import NavigationQuery, LocationEntity, QueryType, LocationType
from src.exceptions import ValidationError, LocationParsingError


class NavigationValidator:
    """Validator for navigation-related inputs."""

    # Chinese location patterns
    CHINESE_LOCATION_PATTERN = re.compile(r'[\u4e00-\u9fff]+(?:[市|省|区|县|镇|乡|村|街道|路|大道|广场|站|机场|港口|大学|学院|公园|医院|商场|酒店|建筑|景点|古迹]*)?')

    # Navigation query patterns
    NAVIGATION_PATTERNS = [
        r'从(.+?)到(.+?)',  # 从A到B
        r'(.+?)到(.+?)',   # A到B (simplified)
        r'从(.+?)前往(.+?)', # 从A前往B
        r'(.+?)前往(.+?)',  # A前往B
        r'(.+?)去(.+?)',    # A去B
        r'(.+?)到(.+?)怎么走', # A到B怎么走
    ]

    # Location type indicators
    CITY_INDICATORS = ['市', '省', '首都', '直辖市']
    DISTRICT_INDICATORS = ['区', '县', '镇', '乡']
    LANDMARK_INDICATORS = ['广场', '公园', '医院', '学校', '大学', '学院', '博物馆', '景点', '古迹', '建筑', '商场', '酒店']
    TRANSPORT_INDICATORS = ['站', '机场', '港口', '码头', '车站', '地铁站', '公交站', '火车站', '汽车站']
    UNIVERSITY_INDICATORS = ['大学', '学院', '高校', '院校']

    @classmethod
    def validate_navigation_query(cls, input_text: str) -> Dict[str, Any]:
        """Validate and parse navigation query input."""
        if not input_text or not input_text.strip():
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query cannot be empty"
            )

        input_text = input_text.strip()

        # Length validation
        if len(input_text) < 3:
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query too short (minimum 3 characters)"
            )

        if len(input_text) > 200:
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query too long (maximum 200 characters)"
            )

        # Character validation
        if not cls._contains_chinese_characters(input_text):
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query must contain Chinese characters for location parsing"
            )

        # Parse navigation pattern
        parsed = cls._parse_navigation_pattern(input_text)
        if not parsed:
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query format not recognized. Use format: '从[起点]到[终点]'"
            )

        origin, destination = parsed

        # Validate individual locations
        cls._validate_location_text(origin, "origin")
        cls._validate_location_text(destination, "destination")

        # Check for common error patterns
        cls._check_common_errors(input_text, origin, destination)

        return {
            "valid": True,
            "origin": origin,
            "destination": destination,
            "query_type": cls._classify_query_type(origin, destination),
            "confidence": cls._calculate_confidence(input_text, origin, destination)
        }

    @classmethod
    def validate_location_entity(cls, location: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Validate a single location entity."""
        if not location or not location.strip():
            raise ValidationError(
                field_name="location",
                value=location,
                reason="Location cannot be empty"
            )

        location = location.strip()

        if len(location) < 1:
            raise ValidationError(
                field_name="location",
                value=location,
                reason="Location name too short"
            )

        if len(location) > 100:
            raise ValidationError(
                field_name="location",
                value=location,
                reason="Location name too long (maximum 100 characters)"
            )

        # Determine location type
        location_type = cls._classify_location_type(location)

        # Type-specific validation
        cls._validate_location_type_specific(location, location_type)

        return {
            "valid": True,
            "name": location,
            "type": location_type,
            "confidence": cls._calculate_location_confidence(location, location_type),
            "context": context
        }

    @classmethod
    def validate_browser_settings(cls, browser_type: str, headless: bool, window_size: str) -> Dict[str, Any]:
        """Validate browser configuration settings."""
        # Browser type validation
        if browser_type != "chromium":
            raise ValidationError(
                field_name="browser_type",
                value=browser_type,
                reason="Only Chrome/Chromium browser is supported"
            )

        # Window size validation
        try:
            width, height = map(int, window_size.split(','))
            if width < 800 or width > 1920:
                raise ValidationError(
                    field_name="window_size",
                    value=window_size,
                    reason="Window width must be between 800 and 1920"
                )
            if height < 600 or height > 1080:
                raise ValidationError(
                    field_name="window_size",
                    value=window_size,
                    reason="Window height must be between 600 and 1080"
                )
        except (ValueError, AttributeError):
            raise ValidationError(
                field_name="window_size",
                value=window_size,
                reason="Window size must be in format 'width,height' (e.g., '1280,800')"
            )

        return {
            "valid": True,
            "browser_type": browser_type,
            "headless": headless,
            "window_size": {"width": width, "height": height}
        }

    @classmethod
    def validate_timeout_settings(cls, timeout_ms: int) -> Dict[str, Any]:
        """Validate timeout configuration."""
        if timeout_ms < 1000:
            raise ValidationError(
                field_name="timeout_ms",
                value=str(timeout_ms),
                reason="Timeout must be at least 1 second (1000ms)"
            )

        if timeout_ms > 60000:
            raise ValidationError(
                field_name="timeout_ms",
                value=str(timeout_ms),
                reason="Timeout should not exceed 60 seconds (60000ms)"
            )

        return {
            "valid": True,
            "timeout_ms": timeout_ms
        }

    @classmethod
    def _contains_chinese_characters(cls, text: str) -> bool:
        """Check if text contains Chinese characters."""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    @classmethod
    def _parse_navigation_pattern(cls, input_text: str) -> Optional[Tuple[str, str]]:
        """Parse navigation pattern to extract origin and destination."""
        for pattern in cls.NAVIGATION_PATTERNS:
            match = re.search(pattern, input_text)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                if origin and destination and origin != destination:
                    return origin, destination
        return None

    @classmethod
    def _classify_query_type(cls, origin: str, destination: str) -> QueryType:
        """Classify the type of navigation query."""
        origin_type = cls._classify_location_type(origin)
        destination_type = cls._classify_location_type(destination)

        # Create classification rules
        if origin_type == LocationType.CITY and destination_type == LocationType.CITY:
            return QueryType.CITY_TO_CITY
        elif origin_type == LocationType.DISTRICT and destination_type == LocationType.DISTRICT:
            return QueryType.DISTRICT_TO_DISTRICT
        elif origin_type == LocationType.LANDMARK and destination_type == LocationType.LANDMARK:
            return QueryType.LANDMARK_TO_LANDMARK
        elif origin_type == LocationType.TRANSPORT and destination_type == LocationType.TRANSPORT:
            return QueryType.TRANSPORT_TO_TRANSPORT
        elif origin_type == LocationType.UNIVERSITY and destination_type == LocationType.UNIVERSITY:
            return QueryType.UNIVERSITY_TO_UNIVERSITY
        else:
            return QueryType.UNKNOWN

    @classmethod
    def _classify_location_type(cls, location: str) -> LocationType:
        """Classify location type based on indicators."""
        location_lower = location.lower()

        # Check for transport hubs
        if any(indicator in location for indicator in cls.TRANSPORT_INDICATORS):
            return LocationType.TRANSPORT

        # Check for universities
        if any(indicator in location for indicator in cls.UNIVERSITY_INDICATORS):
            return LocationType.UNIVERSITY

        # Check for landmarks
        if any(indicator in location for indicator in cls.LANDMARK_INDICATORS):
            return LocationType.LANDMARK

        # Check for districts
        if any(indicator in location for indicator in cls.DISTRICT_INDICATORS):
            return LocationType.DISTRICT

        # Check for cities
        if any(indicator in location for indicator in cls.CITY_INDICATORS):
            return LocationType.CITY

        # Heuristic classification based on name patterns
        if cls._looks_like_city_name(location):
            return LocationType.CITY
        elif cls._looks_like_district_name(location):
            return LocationType.DISTRICT
        elif cls._looks_like_landmark_name(location):
            return LocationType.LANDMARK

        return LocationType.UNKNOWN

    @classmethod
    def _looks_like_city_name(cls, location: str) -> bool:
        """Heuristic check for city names."""
        # Most Chinese city names are 2-4 characters and end with 市 or are well-known
        city_names = ['北京', '上海', '广州', '深圳', '天津', '重庆', '成都', '杭州', '南京', '武汉', '西安', '苏州', '青岛', '大连', '厦门']
        return location in city_names or (len(location) <= 4 and location.endswith('市'))

    @classmethod
    def _looks_like_district_name(cls, location: str) -> bool:
        """Heuristic check for district names."""
        # District names often end with 区 or are well-known districts
        return location.endswith('区') or len(location) <= 4

    @classmethod
    def _looks_like_landmark_name(cls, location: str) -> bool:
        """Heuristic check for landmark names."""
        # Landmarks often have descriptive names
        landmark_keywords = ['广场', '公园', '塔', '桥', '门', '寺', '宫', '楼', '堂', '馆', '中心', '大厦']
        return any(keyword in location for keyword in landmark_keywords)

    @classmethod
    def _validate_location_text(cls, location: str, field_name: str) -> None:
        """Validate individual location text."""
        if not location or not location.strip():
            raise ValidationError(
                field_name=field_name,
                value=location,
                reason="Location cannot be empty"
            )

        if len(location) > 50:
            raise ValidationError(
                field_name=field_name,
                value=location,
                reason="Location name too long (maximum 50 characters)"
            )

        if not cls._contains_chinese_characters(location):
            raise ValidationError(
                field_name=field_name,
                value=location,
                reason="Location name must contain Chinese characters"
            )

    @classmethod
    def _validate_location_type_specific(cls, location: str, location_type: LocationType) -> None:
        """Type-specific validation for locations."""
        if location_type == LocationType.UNKNOWN:
            # Unknown locations need more validation
            if len(location) < 2:
                raise ValidationError(
                    field_name="location",
                    value=location,
                    reason="Location name too short for reliable identification"
                )

    @classmethod
    def _calculate_confidence(cls, input_text: str, origin: str, destination: str) -> float:
        """Calculate confidence score for the parsed query."""
        base_confidence = 0.7

        # Increase confidence for clear patterns
        if input_text.startswith('从') and '到' in input_text:
            base_confidence += 0.1

        # Increase confidence for well-formatted locations
        if cls._looks_like_good_location(origin) and cls._looks_like_good_location(destination):
            base_confidence += 0.1

        # Increase confidence for common cities/locations
        if cls._is_common_location(origin) or cls._is_common_location(destination):
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    @classmethod
    def _calculate_location_confidence(cls, location: str, location_type: LocationType) -> float:
        """Calculate confidence score for individual location."""
        base_confidence = 0.6

        if location_type != LocationType.UNKNOWN:
            base_confidence += 0.2

        if cls._is_common_location(location):
            base_confidence += 0.2

        return min(base_confidence, 1.0)

    @classmethod
    def _looks_like_good_location(cls, location: str) -> bool:
        """Check if location looks well-formatted."""
        # Good locations have clear indicators or are known names
        return (
            cls._contains_chinese_characters(location) and
            2 <= len(location) <= 20 and
            not location.isdigit()
        )

    @classmethod
    def _is_common_location(cls, location: str) -> bool:
        """Check if location is a commonly known place."""
        common_locations = [
            # Major cities
            '北京', '上海', '广州', '深圳', '天津', '重庆', '成都', '杭州', '南京', '武汉',
            # Famous landmarks
            '天安门', '故宫', '长城', '天坛', '颐和园', '鸟巢', '水立方',
            # Transport hubs
            '北京站', '上海站', '广州站', '首都机场', '浦东机场', '白云机场',
            # Districts
            '海淀区', '朝阳区', '西城区', '东城区', '三里屯', '中关村', '国贸'
        ]
        return location in common_locations

    @classmethod
    def _check_common_errors(cls, input_text: str, origin: str, destination: str) -> None:
        """Check for common user errors."""
        # Same origin and destination
        if origin == destination:
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Origin and destination cannot be the same"
            )

        # Contains only navigation words, no locations
        if len(origin) < 2 or len(destination) < 2:
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Location names too short or unclear"
            )

        # Contains suspicious characters
        if re.search(r'[<>"\'\/\\]', input_text):
            raise ValidationError(
                field_name="query",
                value=input_text,
                reason="Query contains invalid characters"
            )


def validate_navigation_input(query: str) -> Dict[str, Any]:
    """Main validation function for navigation queries."""
    validator = NavigationValidator()
    return validator.validate_navigation_query(query)


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing potentially harmful characters."""
    if not text:
        return ""

    # Remove HTML/JavaScript tags and special characters
    sanitized = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'[<>"\'\/\\]', '', sanitized)  # Remove dangerous chars

    return sanitized.strip()


def validate_url_parameter(param: str) -> str:
    """Validate and encode URL parameter."""
    if not param:
        return ""

    # Sanitize and encode for URL
    sanitized = sanitize_input(param)
    return quote(sanitized, safe='')