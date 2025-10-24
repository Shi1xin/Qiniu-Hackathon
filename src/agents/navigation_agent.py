"""
LangChain Agent for navigation decision making.

Implements the Agent-Driven Architecture with high-level tools and
autonomous decision-making capabilities for location parsing and browser automation.
"""

import asyncio
from typing import Dict, List, Any, Optional
from langchain.agents import Agent, AgentExecutor, Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import AgentAction, AgentFinish

from src.tools.parsing_tools import parse_navigation_query
from src.tools.browser_tools import launch_browser_with_route, handle_ambiguous_locations
from src.tools.gaode_tools import construct_navigation_url
from src.models.navigation import NavigationQuery, ProcessingResult, ResultStatus
from src.exceptions import NavigationToolError, handle_unexpected_error
from src.utils.config import get_config
from src.utils.logging import get_logger
from src.utils.performance import performance_timer


class NavigationAgent:
    """LangChain-based Agent for navigation tasks."""

    def __init__(self, tools: List[Tool] = None, verbose: bool = False):
        """Initialize the navigation agent."""
        self.config = get_config()
        self.logger = get_logger()
        self.verbose = verbose or self.config.verbose_agent

        # Create tools for the agent
        self.tools = tools or self._create_agent_tools()

        # Create memory for conversation context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Create the agent with system prompt
        self.agent = self._create_agent()

        # Create agent executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            max_iterations=3,  # Limit iterations for performance
            early_stopping_method="generate"  # Allow early stopping
        )

    def _create_agent_tools(self) -> List[Tool]:
        """Create the list of tools available to the agent."""
        return [
            Tool(
                name="parse_navigation_query",
                description="Parse a Chinese navigation query to extract origin and destination locations",
                func=self._tool_parse_navigation_query
            ),
            Tool(
                name="construct_navigation_url",
                description="Construct a Gaode Maps navigation URL from origin and destination",
                func=self._tool_construct_navigation_url
            ),
            Tool(
                name="launch_browser_with_route",
                description="Launch a browser window and navigate to the specified URL",
                func=self._tool_launch_browser_with_route
            ),
            Tool(
                name="handle_ambiguous_locations",
                description="Handle ambiguous locations by asking for user clarification or providing alternatives",
                func=self._tool_handle_ambiguous_locations
            )
        ]

    def _create_agent(self) -> Agent:
        """Create the LangChain agent with appropriate system prompt."""
        system_prompt = """
你是一个智能导航助手，专门帮助用户处理中文导航查询。

你的任务是：
1. 解析用户的中文导航查询，提取起点和终点
2. 如果位置不明确，提供澄清选项或替代方案
3. 构建高德地图导航URL
4. 启动浏览器显示导航路线

工作原则：
- 优先使用确定性高的位置信息
- 对于模糊的地点，主动提供选项而不是等待用户澄清
- 确保在10秒内完成所有操作
- 如果Chrome浏览器不可用，提供清晰的错误信息和解决建议

可用工具：
1. parse_navigation_query: 解析中文导航查询
2. construct_navigation_url: 构建高德地图URL
3. launch_browser_with_route: 启动浏览器导航
4. handle_ambiguous_locations: 处理模糊位置

请根据用户输入智能选择合适的工具组合来完成导航任务。
"""

        # Get LLM based on configuration
        llm = self._get_llm()

        return Agent.from_llm_and_tools(
            llm=llm,
            tools=self.tools,
            system_prompt=system_prompt,
            verbose=self.verbose
        )

    def _get_llm(self):
        """Get LLM based on configuration."""
        provider = self.config.get_primary_llm_provider()

        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.config.google_api_key,
                temperature=0.1
            )
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=self.config.openai_api_key,
                temperature=0.1
            )
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-3-haiku-20240307",
                anthropic_api_key=self.config.anthropic_api_key,
                temperature=0.1
            )
        else:
            # Fallback to a basic rule-based approach if no LLM is configured
            return None

    def _tool_parse_navigation_query(self, query: str) -> Dict[str, Any]:
        """Tool wrapper for parsing navigation query."""
        try:
            with performance_timer("parse_navigation_query"):
                nav_query = asyncio.run(parse_navigation_query(query))

            return {
                "success": True,
                "query": nav_query,
                "message": f"Successfully parsed query: {nav_query.origin} -> {nav_query.destination}",
                "confidence": nav_query.confidence_score
            }

        except Exception as e:
            error = handle_unexpected_error(e, "agent_parse_query")
            self.logger.log_error(error, "parsing_query_tool")
            return {
                "success": False,
                "error": error.message,
                "message": f"Failed to parse navigation query: {query}"
            }

    def _tool_construct_navigation_url(self, origin: str, destination: str, transport_mode: str = "car") -> Dict[str, Any]:
        """Tool wrapper for constructing navigation URL."""
        try:
            with performance_timer("construct_navigation_url"):
                from src.models.navigation import LocationEntity, TransportMode, RouteParameters

                # Create location entities
                origin_entity = LocationEntity(
                    name=origin,
                    type="city",  # Default type
                    confidence=0.8
                )
                destination_entity = LocationEntity(
                    name=destination,
                    type="city",  # Default type
                    confidence=0.8
                )

                # Create route parameters
                route_params = RouteParameters(
                    origin=origin_entity,
                    destination=destination_entity,
                    transport_mode=TransportMode(transport_mode),
                    service_provider="gaode"
                )

                # Get URL
                url = route_params.get_navigation_url()

            return {
                "success": True,
                "url": url,
                "message": f"Constructed navigation URL: {url}",
                "origin": origin,
                "destination": destination
            }

        except Exception as e:
            error = handle_unexpected_error(e, "agent_construct_url")
            self.logger.log_error(error, "construct_url_tool")
            return {
                "success": False,
                "error": error.message,
                "message": f"Failed to construct navigation URL: {origin} -> {destination}"
            }

    def _tool_launch_browser_with_route(self, url: str, browser_type: str = "chromium") -> Dict[str, Any]:
        """Tool wrapper for launching browser."""
        try:
            with performance_timer("launch_browser_with_route"):
                result = asyncio.run(launch_browser_with_route(url, browser_type))

            return {
                "success": result.get("success", False),
                "session_id": result.get("session_id"),
                "browser_type": browser_type,
                "message": f"Launched {browser_type} browser with URL: {url}",
                "launch_time_ms": result.get("launch_time_ms", 0)
            }

        except Exception as e:
            error = handle_unexpected_error(e, "agent_launch_browser")
            self.logger.log_error(error, "launch_browser_tool")
            return {
                "success": False,
                "error": error.message,
                "message": f"Failed to launch {browser_type} browser with URL: {url}"
            }

    def _tool_handle_ambiguous_locations(self, location_name: str, alternatives: List[str] = None) -> Dict[str, Any]:
        """Tool wrapper for handling ambiguous locations."""
        try:
            with performance_timer("handle_ambiguous_locations"):
                result = asyncio.run(handle_ambiguous_locations(location_name, alternatives or []))

            return {
                "success": result.get("success", False),
                "clarification_needed": result.get("clarification_needed", False),
                "resolved_location": result.get("resolved_location"),
                "alternatives": result.get("alternatives", alternatives),
                "message": f"Handled ambiguous location: {location_name}"
            }

        except Exception as e:
            error = handle_unexpected_error(e, "agent_handle_ambiguous")
            self.logger.log_error(error, "handle_ambiguous_locations_tool")
            return {
                "success": False,
                "error": error.message,
                "message": f"Failed to handle ambiguous location: {location_name}"
            }

    async def process_navigation_request(self, query: str) -> ProcessingResult:
        """Process a complete navigation request using the agent."""
        start_time = self.logger._get_timestamp_ms()

        try:
            self.logger.info(f"Processing navigation request: {query}")

            # Use agent to process the query
            result = await self.executor.arun(query)

            # Extract results from agent execution
            success = self._extract_agent_result(result)

            # Create processing result
            total_time_ms = self.logger._get_timestamp_ms() - start_time

            if success:
                processing_result = ProcessingResult(
                    status=ResultStatus.SUCCESS,
                    success=True,
                    message="Navigation completed successfully",
                    total_time_ms=total_time_ms,
                    component_times=success.get("component_times", {}),
                    suggestions=success.get("suggestions", [])
                )
            else:
                processing_result = ProcessingResult(
                    status=ResultStatus.BROWSER_ERROR,
                    success=False,
                    message=success.get("error_message", "Navigation failed"),
                    total_time_ms=total_time_ms,
                    error_type=success.get("error_type", "unknown"),
                    error_details=success.get("error_details", {}),
                    suggestions=success.get("suggestions", [
                        "Check your internet connection",
                        "Ensure Chrome/Chromium is installed",
                        "Try again with different locations"
                    ])
                )

            return processing_result

        except Exception as e:
            error = handle_unexpected_error(e, "agent_process_navigation")
            self.logger.log_error(error, "agent_execution")

            total_time_ms = self.logger._get_timestamp_ms() - start_time
            return ProcessingResult(
                status=ResultStatus.SYSTEM_ERROR,
                success=False,
                message=f"System error during navigation: {error.message}",
                total_time_ms=total_time_ms,
                error_type="system_error",
                error_details=error.details,
                suggestions=[
                    "Try again with a simpler query",
                    "Check system requirements",
                    "Contact support if the problem persists"
                ]
            )

    def _extract_agent_result(self, agent_result: Any) -> Dict[str, Any]:
        """Extract relevant information from agent execution result."""
        # Handle AgentFinish
        if isinstance(agent_result, AgentFinish):
            try:
                import json
                result_data = json.loads(agent_result.return_values["output"])
                return {
                    "success": True,
                    "url": result_data.get("url"),
                    "session_id": result_data.get("session_id"),
                    "component_times": result_data.get("component_times", {}),
                    "suggestions": result_data.get("suggestions", [])
                }
            except (json.JSONDecodeError, KeyError):
                return {
                    "success": False,
                    "error_message": "Agent result format invalid",
                    "error_type": "parse_error"
                }

        # Handle error cases
        if hasattr(agent_result, 'tool_calls'):
            failed_calls = [call for call in agent_result.tool_calls if not call.success]
            if failed_calls:
                error = failed_calls[0].error
                return {
                    "success": False,
                    "error_message": str(error),
                    "error_type": "tool_execution_error",
                    "error_details": {"failed_tool": failed_calls[0].tool}
                }

        # Default success case
        return {
            "success": True,
            "message": "Agent completed successfully"
        }

    async def handle_complex_query(self, query: str) -> ProcessingResult:
        """Handle complex navigation queries that may require multiple steps."""
        try:
            # First attempt basic parsing
            basic_result = await parse_navigation_query(query, use_llm_fallback=True)

            # If basic parsing fails or has low confidence, use full agent
            if (not basic_result.origin or not basic_result.destination or
                    basic_result.confidence_score < 0.7 or basic_result.needs_clarification):

                self.logger.info("Basic parsing insufficient, using agent for complex query")
                return await self.process_navigation_request(query)

            # Basic parsing succeeded, proceed with direct processing
            return await self._process_with_basic_parsing(basic_result, query)

        except Exception as e:
            error = handle_unexpected_error(e, "handle_complex_query")
            self.logger.log_error(error, "complex_query_handling")

            return ProcessingResult(
                status=ResultStatus.PARSE_ERROR,
                success=False,
                message=f"Failed to process complex query: {error.message}",
                error_type="parse_error",
                error_details=error.details,
                suggestions=[
                    "Try a simpler query format",
                    "Use more specific location names",
                    "Check for typos in location names"
                ]
            )

    async def _process_with_basic_parsing(self, nav_query: NavigationQuery, original_query: str) -> ProcessingResult:
        """Process navigation using already parsed query."""
        start_time = self.logger._get_timestamp_ms()

        try:
            # Construct navigation URL
            from src.models.navigation import LocationEntity, RouteParameters

            origin_entity = LocationEntity(
                name=nav_query.origin,
                type="city",  # Will be refined by URL construction
                confidence=nav_query.confidence_score
            )
            destination_entity = LocationEntity(
                name=nav_query.destination,
                type="city",
                confidence=nav_query.confidence_score
            )

            route_params = RouteParameters(
                origin=origin_entity,
                destination=destination_entity,
                service_provider="gaode"
            )

            # Get navigation URL
            with performance_timer("url_construction"):
                navigation_url = route_params.get_navigation_url()

            # Launch browser
            with performance_timer("browser_launch"):
                browser_result = await launch_browser_with_route(navigation_url)

            # Create success result
            total_time_ms = self.logger._get_timestamp_ms() - start_time

            if browser_result.get("success"):
                return ProcessingResult(
                    status=ResultStatus.SUCCESS,
                    success=True,
                    message=f"Successfully navigated from {nav_query.origin} to {nav_query.destination}",
                    query=nav_query,
                    route_params=route_params,
                    total_time_ms=total_time_ms,
                    component_times={
                        "parsing": nav_query.processing_time_ms or 500,
                        "url_construction": 100,
                        "browser_launch": browser_result.get("launch_time_ms", 0)
                    }
                )
            else:
                return ProcessingResult(
                    status=ResultStatus.BROWSER_ERROR,
                    success=False,
                    message=browser_result.get("error", "Browser launch failed"),
                    query=nav_query,
                    route_params=route_params,
                    total_time_ms=total_time_ms,
                    error_type="browser_error",
                    error_details=browser_result.get("error_details", {}),
                    suggestions=[
                        "Check Chrome/Chromium installation",
                        "Ensure browser permissions",
                        "Try running with admin privileges"
                    ]
                )

        except Exception as e:
            error = handle_unexpected_error(e, "_process_with_basic_parsing")
            self.logger.log_error(error, "basic_parsing_processing")

            total_time_ms = self.logger._get_timestamp_ms() - start_time
            return ProcessingResult(
                status=ResultStatus.SYSTEM_ERROR,
                success=False,
                message=f"Processing failed: {error.message}",
                total_time_ms=total_time_ms,
                error_type="system_error",
                error_details=error.details,
                suggestions=[
                    "Try again with different locations",
                    "Check system requirements",
                    "Contact support if the problem persists"
                ]
            )


# Global agent instance
_agent_instance: Optional[NavigationAgent] = None


def get_navigation_agent(verbose: bool = False) -> NavigationAgent:
    """Get the global navigation agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = NavigationAgent(verbose=verbose)
    return _agent_instance


def setup_navigation_agent(tools: List[Tool] = None, verbose: bool = False) -> NavigationAgent:
    """Setup navigation agent with custom tools and settings."""
    global _agent_instance
    _agent_instance = NavigationAgent(tools=tools, verbose=verbose)
    return _agent_instance


# High-level API functions
async def process_navigation_query(query: str, use_agent: bool = True) -> ProcessingResult:
    """Process navigation query using either agent or direct parsing."""
    agent = get_navigation_agent()

    if use_agent:
        return await agent.handle_complex_query(query)
    else:
        # Direct parsing path
        try:
            nav_query = await parse_navigation_query(query)
            return await agent._process_with_basic_parsing(nav_query, query)
        except Exception as e:
            error = handle_unexpected_error(e, "process_navigation_query")
            return ProcessingResult(
                status=ResultStatus.PARSE_ERROR,
                success=False,
                message=error.message,
                error_type="parse_error",
                error_details=error.details,
                suggestions=[
                    "Check query format: '从A到B'",
                    "Use more specific location names",
                    "Avoid special characters"
                ]
            )