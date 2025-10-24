"""
Natural language parsing tools for Chinese navigation queries.

Provides Chinese NLP capabilities using a hybrid approach of
regex patterns, PaddleNLP, and LLM fallback for location parsing.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote

from src.models.navigation import NavigationQuery, LocationEntity, QueryType, LocationType
from src.utils.validation import NavigationValidator, validate_navigation_input
from src.exceptions import LocationParsingError, LLMError, handle_unexpected_error
from src.utils.config import get_config


class ChineseLocationParser:
    """Parser for Chinese navigation queries with hybrid NLP approach."""

    # Navigation pattern regexes
    NAVIGATION_PATTERNS = [
        r'从(.+?)到(.+?)',      # 从A到B
        r'(.+?)到(.+?)',        # A到B
        r'从(.+?)前往(.+?)',    # 从A前往B
        r'(.+?)前往(.+?)',      # A前往B
        r'(.+?)去(.+?)',         # A去B
        r'(.+?)到(.+?)怎么走',   # A到B怎么走
    ]

    # Location type indicators
    LOCATION_TYPE_INDICATORS = {
        'city': ['市', '省会', '首都', '直辖市', '省城'],
        'district': ['区', '县', '镇', '乡', '街道', '路', '大道'],
        'landmark': ['广场', '公园', '医院', '学校', '景点', '古迹', '建筑', '商场', '酒店', '塔', '桥', '门'],
        'transport': ['站', '机场', '港口', '码头', '车站', '地铁站', '公交站', '火车站', '汽车站', '客运站'],
        'university': ['大学', '学院', '高校', '院校', '师范', '理工', '科技']
    }

    # Common location suffixes for cleaning
    LOCATION_SUFFIXES = ['市', '省', '区', '县', '镇', '乡', '村', '站', '机场', '港', '广场', '公园', '大学', '学院']

    # Famous location database for improved recognition
    FAMOUS_LOCATIONS = {
        'city': [
            '北京', '上海', '广州', '深圳', '天津', '重庆', '成都', '杭州', '南京', '武汉', '西安',
            '苏州', '青岛', '大连', '厦门', '宁波', '无锡', '长沙', '郑州', '济南', '青岛'
        ],
        'district': [
            '海淀区', '朝阳区', '西城区', '东城区', '三里屯', '中关村', '国贸', '望京', '五道口',
            '陆家嘴', '静安寺', '徐家汇', '黄浦', '浦东', '浦西'
        ],
        'landmark': [
            '天安门', '故宫', '长城', '天坛', '颐和园', '鸟巢', '水立方', '东方明珠', '外滩',
            '豫园', '城隍庙', '人民广场', '中山公园'
        ],
        'transport': [
            '北京站', '上海站', '广州站', '首都机场', '浦东机场', '白云机场', '虹桥机场',
            '南苑机场', '西单站', '王府井站', '东直门站', '西直门站'
        ],
        'university': [
            '清华大学', '北京大学', '复旦大学', '上海交大', '人民大学', '北京师大', '同济大学',
            '南开大学', '天津大学', '中山大学', '华中科技', '西安交大'
        ]
    }

    def __init__(self, llm_client=None):
        """Initialize the Chinese location parser."""
        self.llm_client = llm_client
        self.config = get_config()

    def parse_navigation_query(self, query_text: str) -> NavigationQuery:
        """Parse navigation query and return NavigationQuery object."""
        try:
            # Input validation
            validated = validate_navigation_input(query_text)

            if not validated["valid"]:
                raise LocationParsingError(
                    input_text=query_text,
                    reason="Input validation failed",
                    details=validated
                )

            # Extract origin and destination
            origin, destination = self._extract_locations(query_text)

            if not origin or not destination:
                raise LocationParsingError(
                    input_text=query_text,
                    reason="Could not extract origin and destination"
                )

            # Classify query type
            query_type = self._classify_query_type(origin, destination)

            # Create location entities
            origin_entity = self._create_location_entity(origin, "origin")
            destination_entity = self._create_location_entity(destination, "destination")

            # Calculate confidence
            confidence = self._calculate_confidence(query_text, origin_entity, destination_entity)

            return NavigationQuery(
                raw_input=query_text,
                origin=origin_entity.name,
                destination=destination_entity.name,
                query_type=query_type,
                confidence_score=confidence,
                parsing_method=self._get_parsing_method(),
                processing_time_ms=0,  # Will be set by caller
                parse_errors=[],
                needs_clarification=origin_entity.needs_disambiguation() or destination_entity.needs_disambiguation()
            )

        except Exception as e:
            raise handle_unexpected_error(e, "parse_navigation_query")

    def _extract_locations(self, query_text: str) -> Tuple[str, str]:
        """Extract origin and destination from query text."""
        # Try each navigation pattern
        for pattern in self.NAVIGATION_PATTERNS:
            match = re.search(pattern, query_text)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()

                # Clean up location names
                origin = self._clean_location_name(origin)
                destination = self._clean_location_name(destination)

                # Validate that they're different
                if origin and destination and origin != destination:
                    return origin, destination

        return None, None

    def _clean_location_name(self, location: str) -> str:
        """Clean and normalize location name."""
        if not location:
            return location

        # Remove common navigation words
        location = re.sub(r'(从|到|前往|去|怎么走)', '', location)

        # Remove extra whitespace
        location = location.strip()

        # Remove redundant suffixes if location already implies them
        for suffix in self.LOCATION_SUFFIXES:
            if location.endswith(suffix) and len(location) > len(suffix) + 1:
                # Check if base name is a famous location
                base_name = location[:-len(suffix)]
                if self._is_famous_location(base_name):
                    location = base_name
                    break

        return location

    def _classify_query_type(self, origin: str, destination: str) -> QueryType:
        """Classify the type of navigation query."""
        origin_type = self._classify_location_type(origin)
        destination_type = self._classify_location_type(destination)

        # Create classification mapping
        type_mapping = {
            (LocationType.CITY, LocationType.CITY): QueryType.CITY_TO_CITY,
            (LocationType.DISTRICT, LocationType.DISTRICT): QueryType.DISTRICT_TO_DISTRICT,
            (LocationType.LANDMARK, LocationType.LANDMARK): QueryType.LANDMARK_TO_LANDMARK,
            (LocationType.TRANSPORT, LocationType.TRANSPORT): QueryType.TRANSPORT_TO_TRANSPORT,
            (LocationType.UNIVERSITY, LocationType.UNIVERSITY): QueryType.UNIVERSITY_TO_UNIVERSITY,
        }

        return type_mapping.get(
            (origin_type, destination_type),
            QueryType.UNKNOWN
        )

    def _classify_location_type(self, location: str) -> LocationType:
        """Classify location type based on indicators and patterns."""
        if not location:
            return LocationType.UNKNOWN

        location_lower = location.lower()

        # Check transport indicators first (most specific)
        for transport_indicator in self.LOCATION_TYPE_INDICATORS['transport']:
            if transport_indicator in location:
                return LocationType.TRANSPORT

        # Check university indicators
        for univ_indicator in self.LOCATION_TYPE_INDICATORS['university']:
            if univ_indicator in location:
                return LocationType.UNIVERSITY

        # Check landmark indicators
        for landmark_indicator in self.LOCATION_TYPE_INDICATORS['landmark']:
            if landmark_indicator in location:
                return LocationType.LANDMARK

        # Check district indicators
        for district_indicator in self.LOCATION_TYPE_INDICATORS['district']:
            if district_indicator in location:
                return LocationType.DISTRICT

        # Check city indicators
        for city_indicator in self.LOCATION_TYPE_INDICATORS['city']:
            if city_indicator in location:
                return LocationType.CITY

        # Check against famous locations database
        for loc_type, famous_list in self.FAMOUS_LOCATIONS.items():
            if location in famous_list:
                return getattr(LocationType, loc_type.upper())

        # Heuristic classification based on name patterns
        if len(location) <= 4 and not any(char.isdigit() for char in location):
            return LocationType.CITY  # Short names are likely cities
        elif '区' in location or '县' in location:
            return LocationType.DISTRICT
        elif any(indicator in location for indicator in ['广场', '公园', '寺', '塔']):
            return LocationType.LANDMARK
        else:
            return LocationType.UNKNOWN

    def _create_location_entity(self, location_name: str, context: str) -> LocationEntity:
        """Create a LocationEntity with classification and confidence."""
        # Classify location type
        location_type = self._classify_location_type(location_name)

        # Calculate confidence based on various factors
        confidence = self._calculate_location_confidence(location_name, location_type)

        # Generate alternatives if needed
        alternatives = self._generate_alternatives(location_name, location_type)

        # Determine parent region
        parent_region = self._determine_parent_region(location_name, location_type)

        return LocationEntity(
            name=location_name,
            type=location_type,
            confidence=confidence,
            context=f"{context} location in query",
            alternatives=alternatives,
            parent_region=parent_region,
            extraction_method=self._get_parsing_method()
        )

    def _calculate_confidence(self, query: str, origin_entity: LocationEntity, destination_entity: LocationEntity) -> float:
        """Calculate overall confidence score for the parsed query."""
        base_confidence = 0.5

        # Increase confidence for clear navigation patterns
        if '从' in query and '到' in query:
            base_confidence += 0.1

        # Increase confidence based on location entity confidence
        avg_entity_confidence = (origin_entity.confidence + destination_entity.confidence) / 2
        base_confidence += avg_entity_confidence * 0.3

        # Increase confidence for famous locations
        origin_famous = self._is_famous_location(origin_entity.name)
        dest_famous = self._is_famous_location(destination_entity.name)
        if origin_famous and dest_famous:
            base_confidence += 0.1
        elif origin_famous or dest_famous:
            base_confidence += 0.05

        # Adjust for query complexity
        if len(query.split('到')) == 2:  # Simple A到B pattern
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _calculate_location_confidence(self, location_name: str, location_type: LocationType) -> float:
        """Calculate confidence score for individual location."""
        base_confidence = 0.6

        # Higher confidence for known location types
        if location_type != LocationType.UNKNOWN:
            base_confidence += 0.2

        # Higher confidence for famous locations
        if self._is_famous_location(location_name):
            base_confidence += 0.2

        # Adjust based on location name characteristics
        if len(location_name) >= 2 and len(location_name) <= 6:
            base_confidence += 0.1  # Good length for Chinese locations

        # Decrease confidence for very long or very short names
        if len(location_name) == 1:
            base_confidence -= 0.2
        elif len(location_name) > 10:
            base_confidence -= 0.1

        return max(0.0, min(base_confidence, 1.0))

    def _generate_alternatives(self, location_name: str, location_type: LocationType) -> List[str]:
        """Generate alternative location names for disambiguation."""
        alternatives = []

        # Add variations with and without common suffixes
        for suffix in self.LOCATION_SUFFIXES:
            if location_name.endswith(suffix) and len(location_name) > len(suffix) + 1:
                base_name = location_name[:-len(suffix)]
                alternatives.append(base_name)
                break

        # Add location name with common suffixes
        if location_type == LocationType.CITY:
            if not location_name.endswith('市'):
                alternatives.append(f"{location_name}市")

        # Add famous location variations
        for loc_type, famous_list in self.FAMOUS_LOCATIONS.items():
            if location_name in famous_list:
                alternatives.extend([loc for loc in famous_list if location_name in loc])

        return list(set(alternatives))  # Remove duplicates

    def _determine_parent_region(self, location_name: str, location_type: LocationType) -> Optional[str]:
        """Determine parent administrative region for location."""
        # Known mappings for famous locations
        region_mappings = {
            # Cities and their provinces
            '北京': '北京市',
            '上海': '上海市',
            '天津': '天津市',
            '重庆': '重庆市',

            # District mappings
            '海淀区': '北京市',
            '朝阳区': '北京市',
            '浦东新区': '上海市',
            '静安区': '上海市',

            # University mappings
            '清华大学': '北京市海淀区',
            '北京大学': '北京市海淀区',
            '复旦大学': '上海市杨浦区',

            # Airport mappings
            '首都机场': '北京市',
            '浦东机场': '上海市',
            '虹桥机场': '上海市'
        }

        # Direct mapping
        if location_name in region_mappings:
            return region_mappings[location_name]

        # Pattern-based mapping
        if location_name.endswith('区') or location_name.endswith('县'):
            return '北京市'  # Default for districts

        if location_name.endswith('市'):
            return location_name  # City is its own region

        return None

    def _is_famous_location(self, location_name: str) -> bool:
        """Check if location is in famous locations database."""
        for famous_list in self.FAMOUS_LOCATIONS.values():
            if location_name in famous_list:
                return True
        return False

    def _get_parsing_method(self) -> str:
        """Get the parsing method used."""
        return "hybrid_regex_patterns"

    async def parse_with_llm_fallback(self, query_text: str) -> NavigationQuery:
        """Parse query using LLM when basic parsing fails."""
        if not self.llm_client or not self.config.has_llm_config():
            raise LLMError(
                provider=self.config.get_primary_llm_provider() or "none",
                reason="LLM client not available or not configured"
            )

        try:
            # Construct LLM prompt for location parsing
            prompt = self._construct_llm_prompt(query_text)

            # Call LLM API
            response = await self._call_llm_api(prompt)

            # Parse LLM response
            return self._parse_llm_response(response, query_text)

        except Exception as e:
            raise handle_unexpected_error(e, "llm_fallback_parsing")

    def _construct_llm_prompt(self, query_text: str) -> str:
        """Construct LLM prompt for location parsing."""
        return f"""
请分析以下中文导航查询，提取起点和终点位置：

查询：{query_text}

请以JSON格式返回结果，包含：
1. origin: 起点位置名称
2. destination: 终点位置名称
3. origin_type: 起点类型（city/district/landmark/transport/university）
4. destination_type: 终点类型
5. confidence: 解析置信度（0-1）
6. needs_clarification: 是否需要澄清（true/false）

注意事项：
- 只提取地理位置相关的实体
- 如果无法确定位置类型，使用"unknown"
- 置信度基于位置明确性和知名度
- 如果查询不完整或模糊，标记needs_clarification为true

示例输入：从清华大学到首都机场
示例输出：
{{
    "origin": "清华大学",
    "destination": "首都机场",
    "origin_type": "university",
    "destination_type": "transport",
    "confidence": 0.9,
    "needs_clarification": false
}}
"""

    async def _call_llm_api(self, prompt: str) -> str:
        """Call the configured LLM API."""
        try:
            if self.config.google_api_key:
                return await self._call_google_llm(prompt)
            elif self.config.openai_api_key:
                return await self._call_openai_llm(prompt)
            elif self.config.anthropic_api_key:
                return await self._call_anthropic_llm(prompt)
            else:
                raise LLMError(
                    provider="none",
                    reason="No LLM API key configured"
                )
        except Exception as e:
            raise LLMError(
                provider=self.config.get_primary_llm_provider() or "unknown",
                reason=f"LLM API call failed: {str(e)}"
            )

    async def _call_google_llm(self, prompt: str) -> str:
        """Call Google Gemini API."""
        # This would implement Google Gemini API call
        # For now, return a mock response
        return '{"origin": "mock", "destination": "mock", "confidence": 0.8}'

    async def _call_openai_llm(self, prompt: str) -> str:
        """Call OpenAI API."""
        # This would implement OpenAI API call
        return '{"origin": "mock", "destination": "mock", "confidence": 0.8}'

    async def _call_anthropic_llm(self, prompt: str) -> str:
        """Call Anthropic API."""
        # This would implement Anthropic API call
        return '{"origin": "mock", "destination": "mock", "confidence": 0.8}'

    def _parse_llm_response(self, response: str, original_query: str) -> NavigationQuery:
        """Parse LLM response into NavigationQuery."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response)
            if not json_match:
                raise LocationParsingError(
                    input_text=original_query,
                    reason="LLM response does not contain valid JSON"
                )

            parsed_data = json.loads(json_match.group(0))

            # Validate required fields
            required_fields = ['origin', 'destination']
            for field in required_fields:
                if field not in parsed_data:
                    raise LocationParsingError(
                        input_text=original_query,
                        reason=f"LLM response missing required field: {field}"
                    )

            origin = parsed_data.get('origin', '')
            destination = parsed_data.get('destination', '')
            confidence = parsed_data.get('confidence', 0.8)

            # Convert string types to enums
            origin_type_str = parsed_data.get('origin_type', 'unknown')
            destination_type_str = parsed_data.get('destination_type', 'unknown')

            # Create entities
            origin_entity = LocationEntity(
                name=origin,
                type=self._string_to_location_type(origin_type_str),
                confidence=confidence,
                extraction_method="llm_fallback"
            )

            destination_entity = LocationEntity(
                name=destination,
                type=self._string_to_location_type(destination_type_str),
                confidence=confidence,
                extraction_method="llm_fallback"
            )

            # Classify query type
            query_type = self._classify_query_type(origin, destination)

            return NavigationQuery(
                raw_input=original_query,
                origin=origin,
                destination=destination,
                query_type=query_type,
                confidence_score=confidence,
                parsing_method="llm_fallback",
                needs_clarification=parsed_data.get('needs_clarification', False)
            )

        except json.JSONDecodeError as e:
            raise LocationParsingError(
                input_text=original_query,
                reason=f"Failed to parse LLM JSON response: {str(e)}"
            )

    def _string_to_location_type(self, type_str: str) -> LocationType:
        """Convert string to LocationType enum."""
        type_mapping = {
            'city': LocationType.CITY,
            'district': LocationType.DISTRICT,
            'landmark': LocationType.LANDMARK,
            'transport': LocationType.TRANSPORT,
            'university': LocationType.UNIVERSITY,
            'unknown': LocationType.UNKNOWN
        }
        return type_mapping.get(type_str.lower(), LocationType.UNKNOWN)

    async def handle_ambiguous_locations(self, query: str, locations: List[str]) -> List[str]:
        """Handle ambiguous location suggestions."""
        # This would implement disambiguation logic with user confirmation
        # For now, return the locations as-is
        return locations


# Global parser instance
_parser_instance: Optional[ChineseLocationParser] = None


def get_location_parser() -> ChineseLocationParser:
    """Get global location parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ChineseLocationParser()
    return _parser_instance


def setup_location_parser(llm_client=None) -> ChineseLocationParser:
    """Setup location parser with LLM client."""
    global _parser_instance
    _parser_instance = ChineseLocationParser(llm_client)
    return _parser_instance


# Public API functions
async def parse_navigation_query(query_text: str, use_llm_fallback: bool = False) -> NavigationQuery:
    """Parse navigation query with optional LLM fallback."""
    parser = get_location_parser()

    try:
        # Try basic parsing first
        result = parser.parse_navigation_query(query_text)

        # If basic parsing fails and LLM fallback is enabled, try LLM
        if not result.origin or not result.destination and use_llm_fallback:
            result = await parser.parse_with_llm_fallback(query_text)

        return result

    except Exception as e:
        raise handle_unexpected_error(e, "parse_navigation_query")