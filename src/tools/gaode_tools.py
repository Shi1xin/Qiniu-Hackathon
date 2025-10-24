"""
Gaode Maps URL construction and integration tools.

Provides Gaode Maps specific URL building, parameter handling,
and fallback service integration for Chinese navigation queries.
"""

import re
from typing import Dict, Optional, Any, List, Tuple
from urllib.parse import quote, urlencode, unquote

from src.models.navigation import LocationEntity, RouteParameters, TransportMode
from src.models.results import ProcessingResult, create_success_result, create_error_result
from src.exceptions import NavigationError, handle_unexpected_error
from src.utils.validation import validate_url_parameter
from src.utils.config import get_config
from src.utils.logging import get_logger


class GaodeMapsTools:
    """Tools for Gaode Maps integration and URL construction."""

    # Gaode Maps API endpoints and patterns
    GAODE_NAVIGATION_BASE = "https://uri.amap.com/navigation"
    GAODE_SEARCH_BASE = "https://restapi.amap.com/v3/place/text"
    GAODE_GEOCODING_BASE = "https://restapi.amap.com/v3/geocode/geo"

    # Transport mode mappings for Gaode
    GAODE_TRANSPORT_MODES = {
        TransportMode.DRIVING: "car",
        TransportMode.WALKING: "walk",
        TransportMode.TRANSIT: "bus",
        TransportMode.RIDING: "ride",
        TransportMode.TRUCK: "truck"
    }

    # Fallback map services
    FALLBACK_SERVICES = {
        "baidu": {
            "navigation_base": "https://map.baidu.com/direction",
            "transport_modes": {
                "car": "driving",
                "walk": "walking",
                "bus": "transit"
            }
        },
        "tencent": {
            "navigation_base": "https://map.qq.com/dir",
            "transport_modes": {
                "car": "driving",
                "walk": "walking",
                "bus": "bus"
            }
        }
    }

    def __init__(self):
        """Initialize Gaode Maps tools."""
        self.config = get_config()
        self.logger = get_logger()

    def construct_navigation_url(
        self,
        origin: LocationEntity,
        destination: LocationEntity,
        transport_mode: TransportMode = TransportMode.DRIVING,
        avoid_tolls: bool = False,
        avoid_highways: bool = False,
        service_provider: str = "gaode"
    ) -> Dict[str, Any]:
        """Construct navigation URL for specified locations."""
        try:
            # Validate inputs
            if not origin or not destination:
                raise NavigationError(
                    operation="construct_navigation_url",
                    reason="Both origin and destination must be provided"
                )

            # Get service base URL
            if service_provider == "gaode":
                url = self._construct_gaode_url(
                    origin, destination, transport_mode, avoid_tolls, avoid_highways
                )
            elif service_provider in self.FALLBACK_SERVICES:
                url = self._construct_fallback_url(
                    origin, destination, transport_mode, service_provider
                )
            else:
                raise NavigationError(
                    operation="construct_navigation_url",
                    reason=f"Unsupported service provider: {service_provider}"
                )

            return {
                "success": True,
                "url": url,
                "service_provider": service_provider,
                "transport_mode": transport_mode.value,
                "origin_name": origin.name,
                "destination_name": destination.name
            }

        except Exception as e:
            error = handle_unexpected_error(e, "construct_navigation_url")
            self.logger.log_error(error, "gaode_url_construction")

            return {
                "success": False,
                "error": error.message,
                "error_type": "url_construction_error"
            }

    def _construct_gaode_url(
        self,
        origin: LocationEntity,
        destination: LocationEntity,
        transport_mode: TransportMode,
        avoid_tolls: bool,
        avoid_highways: bool
    ) -> str:
        """Construct Gaode Maps navigation URL."""
        # Prepare URL parameters
        params = {
            # Core navigation parameters
            'from': self._encode_location(origin.name),
            'to': self._encode_location(destination.name),
            'mode': self.GAODE_TRANSPORT_MODES.get(transport_mode, 'car'),
            'coordinate': 'gaode',
            'callnative': '0',  # Don't auto-launch Gaode app
            'src': 'pc',  # Source platform
            'output': 'html'  # Output format
        }

        # Add route preferences
        if avoid_tolls:
            params['toll'] = '0'  # Avoid toll roads
        if avoid_highways:
            params['highway'] = '0'  # Avoid highways

        # Add location context if available
        if origin.parent_region:
            params['from_ename'] = self._encode_location(origin.parent_region)
        if destination.parent_region:
            params['to_ename'] = self._encode_location(destination.parent_region)

        # Add coordinates if available
        if origin.coordinates and 'latitude' in origin.coordinates and 'longitude' in origin.coordinates:
            params['from_lng'] = str(origin.coordinates['longitude'])
            params['from_lat'] = str(origin.coordinates['latitude'])

        if destination.coordinates and 'latitude' in destination.coordinates and 'longitude' in destination.coordinates:
            params['to_lng'] = str(destination.coordinates['longitude'])
            params['to_lat'] = str(destination.coordinates['latitude'])

        # Build complete URL
        return f"{self.GAODE_NAVIGATION_BASE}?{urlencode(params)}"

    def _construct_fallback_url(
        self,
        origin: LocationEntity,
        destination: LocationEntity,
        transport_mode: TransportMode,
        service_provider: str
    ) -> str:
        """Construct fallback service navigation URL."""
        if service_provider not in self.FALLBACK_SERVICES:
            raise NavigationError(
                operation="construct_fallback_url",
                reason=f"Unsupported fallback service: {service_provider}"
            )

        service_config = self.FALLBACK_SERVICES[service_provider]
        base_url = service_config["navigation_base"]

        # Map transport modes
        fallback_mode = service_config["transport_modes"].get(
            transport_mode.value, "driving"
        )

        # Prepare parameters
        params = {
            'origin': self._encode_location(origin.name),
            'destination': self._encode_location(destination.name),
            'mode': fallback_mode,
            'output': 'html'
        }

        return f"{base_url}?{urlencode(params)}"

    def _encode_location(self, location: str) -> str:
        """Prepare location name for URL parameter."""
        # Validate and sanitize location parameter
        from src.utils.validation import sanitize_input
        clean_location = sanitize_input(location)
        return clean_location

    def search_location(
        self,
        query: str,
        city: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search for locations using Gaode Maps API."""
        try:
            # Prepare search parameters
            params = {
                'keywords': query,
                'city': city or '',
                'citylimit': True,
                'datatype': 'poi',  # Points of interest
                'output': 'json',
                'key': self.config.get_primary_llm_provider(),  # Use API key if available
                'offset': 0,
                'page': 1,
                'limit': limit
            }

            # For demo purposes, return mock data
            # In real implementation, this would make HTTP request to Gaode API
            mock_results = self._get_mock_search_results(query, city, limit)

            return {
                "success": True,
                "query": query,
                "results": mock_results,
                "count": len(mock_results)
            }

        except Exception as e:
            error = handle_unexpected_error(e, "search_location")
            self.logger.log_error(error, "gaode_search")

            return {
                "success": False,
                "error": error.message,
                "error_type": "search_error"
            }

    def _get_mock_search_results(self, query: str, city: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Get mock search results for demonstration."""
        # In real implementation, this would be replaced with actual API calls
        mock_results = []

        # Generate some realistic mock results based on query
        if "天安门" in query:
            mock_results = [
                {
                    "name": "天安门广场",
                    "address": "北京市东城区天安门广场",
                    "location": {"lat": 39.9042, "lng": 116.3976},
                    "type": "landmark",
                    "confidence": 0.95
                }
            ]
        elif "清华" in query:
            mock_results = [
                {
                    "name": "清华大学",
                    "address": "北京市海淀区清华园1号",
                    "location": {"lat": 40.0042, "lng": 116.3261},
                    "type": "university",
                    "confidence": 0.98
                }
            ]
        elif "北京" in query and "站" in query:
            mock_results = [
                {
                    "name": "北京站",
                    "address": "北京市东城区毛家湾胡同甲13号",
                    "location": {"lat": 39.9013, "lng": 116.4272},
                    "type": "transport",
                    "confidence": 0.92
                }
            ]
        else:
            # Generic location result
            mock_results = [
                {
                    "name": f"{query}（模拟结果）",
                    "address": f"北京市某区{query}",
                    "location": {"lat": 39.9042, "lng": 116.4074},
                    "type": "landmark",
                    "confidence": 0.8
                }
            ]

        return mock_results[:limit]

    def geocode_location(
        self,
        address: str,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert address to coordinates using Gaode Maps API."""
        try:
            # Prepare geocoding parameters
            params = {
                'address': address,
                'city': city or '',
                'output': 'json'
            }

            # For demo purposes, return mock data
            # In real implementation, this would make HTTP request to Gaode API
            mock_coordinates = self._get_mock_coordinates(address, city)

            return {
                "success": True,
                "address": address,
                "coordinates": mock_coordinates
            }

        except Exception as e:
            error = handle_unexpected_error(e, "geocode_location")
            self.logger.log_error(error, "gaode_geocode")

            return {
                "success": False,
                "error": error.message,
                "error_type": "geocode_error"
            }

    def _get_mock_coordinates(self, address: str, city: Optional[str]) -> Dict[str, float]:
        """Get mock coordinates for demonstration."""
        # Common Beijing area coordinates
        coordinates_map = {
            "天安门": {"lat": 39.9042, "lng": 116.3976},
            "故宫": {"lat": 39.9163, "lng": 116.3972},
            "清华大学": {"lat": 40.0042, "lng": 116.3261},
            "北京大学": {"lat": 39.9869, "lng": 116.3059},
            "中关村": {"lat": 39.9847, "lng": 116.3054},
            "三里屯": {"lat": 39.9368, "lng": 116.4472},
            "首都机场": {"lat": 40.0799, "lng": 116.6031},
            "北京站": {"lat": 39.9013, "lng": 116.4272},
            "上海站": {"lat": 31.2515, "lng": 121.4590}
        }

        # Try to find coordinates by address
        for key, coords in coordinates_map.items():
            if key in address:
                return coords

        # Default to central Beijing if no match
        return {"lat": 39.9042, "lng": 116.3976}

    def get_service_status(self, service_provider: str = "gaode") -> Dict[str, Any]:
        """Get status of map service availability."""
        try:
            # In real implementation, this would ping the service
            status_info = {
                "gaode": {"available": True, "response_time_ms": 150},
                "baidu": {"available": True, "response_time_ms": 200},
                "tencent": {"available": True, "response_time_ms": 250}
            }

            if service_provider in status_info:
                return {
                    "success": True,
                    "service": service_provider,
                    "available": status_info[service_provider]["available"],
                    "response_time_ms": status_info[service_provider]["response_time_ms"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Service {service_provider} not supported"
                }

        except Exception as e:
            error = handle_unexpected_error(e, "get_service_status")
            self.logger.log_error(error, "service_status_check")

            return {
                "success": False,
                "error": error.message,
                "error_type": "service_check_error"
            }

    def construct_search_url(
        self,
        query: str,
        city: Optional[str] = None,
        service_provider: str = "gaode"
    ) -> str:
        """Construct search URL for the specified service."""
        try:
            # URL-encode search query
            encoded_query = quote(query, safe='')

            if service_provider == "gaode":
                # For demo, return mock search URL
                return f"https://www.amap.com/search?query={encoded_query}&city={quote(city or '', safe='')}"
            elif service_provider == "baidu":
                return f"https://map.baidu.com/s?wd={encoded_query}&pn=0"
            elif service_provider == "tencent":
                return f"https://map.qq.com/search?keyword={encoded_query}"
            else:
                raise NavigationError(
                    operation="construct_search_url",
                    reason=f"Unsupported service: {service_provider}"
                )

        except Exception as e:
            raise NavigationError(
                operation="construct_search_url",
                reason=f"Failed to construct search URL: {str(e)}"
            )

    def validate_url_structure(self, url: str) -> Dict[str, Any]:
        """Validate Gaode Maps URL structure."""
        try:
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(url)

            # Basic validation
            if not parsed_url.scheme or not parsed_url.netloc:
                return {
                    "valid": False,
                    "error": "Invalid URL structure"
                }

            # Check Gaode-specific structure
            if "amap.com" not in parsed_url.netloc:
                return {
                    "valid": False,
                    "error": "URL does not appear to be for Gaode Maps"
                }

            # Parse and validate query parameters
            query_params = parse_qs(parsed_url.query)

            required_params = ['from', 'to']
            for param in required_params:
                if param not in query_params:
                    return {
                        "valid": False,
                        "error": f"Missing required parameter: {param}"
                    }

            # Validate transport mode
            valid_modes = ['car', 'walk', 'bus', 'ride', 'truck']
            mode = query_params.get('mode', ['car'])[0]
            if mode not in valid_modes:
                return {
                    "valid": False,
                    "error": f"Invalid transport mode: {mode}"
                }

            return {
                "valid": True,
                "service": "gaode",
                "parameters": query_params
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"URL validation failed: {str(e)}"
            }

    def format_location_suggestion(self, location: LocationEntity) -> str:
        """Format location for user suggestions."""
        if location.type:
            return f"{location.name}（{location.type.value}）"
        return location.name

    def get_location_context(self, location: LocationEntity) -> str:
        """Get human-readable context for location."""
        context_parts = []
        if location.parent_region:
            context_parts.append(f"位于{location.parent_region}")
        if location.alternatives:
            context_parts.append(f"可能是: {', '.join(location.alternatives[:3])}")
        if location.confidence < 0.8:
            context_parts.append("置信度较低")

        return " | ".join(context_parts) if context_parts else "位置信息"


# Global Gaode tools instance
_gaode_tools_instance: Optional[GaodeMapsTools] = None


def get_gaode_tools() -> GaodeMapsTools:
    """Get global Gaode Maps tools instance."""
    global _gaode_tools_instance
    if _gaode_tools_instance is None:
        _gaode_tools_instance = GaodeMapsTools()
    return _gaode_tools_instance


# High-level API functions
def construct_navigation_url(
    origin_name: str,
    destination_name: str,
    transport_mode: str = "car",
    avoid_tolls: bool = False,
    avoid_highways: bool = False
) -> str:
    """High-level function to construct Gaode navigation URL."""
    tools = get_gaode_tools()

    # Create basic location entities
    from src.models.navigation import LocationEntity, TransportMode

    origin = LocationEntity(name=origin_name, confidence=0.8)
    destination = LocationEntity(name=destination_name, confidence=0.8)

    # Map transport mode string
    try:
        mode = TransportMode(transport_mode)
    except ValueError:
        mode = TransportMode.DRIVING

    # Construct URL
    result = tools.construct_navigation_url(
        origin=origin,
        destination=destination,
        transport_mode=mode,
        avoid_tolls=avoid_tolls,
        avoid_highways=avoid_highways
    )

    return result.get("url", "")


def validate_gaode_url(url: str) -> Dict[str, Any]:
    """Validate a Gaode Maps URL."""
    tools = get_gaode_tools()
    return tools.validate_url_structure(url)


def search_locations(query: str, city: Optional[str] = None) -> Dict[str, Any]:
    """Search for locations using Gaode Maps."""
    tools = get_gaode_tools()
    return tools.search_location(query, city)