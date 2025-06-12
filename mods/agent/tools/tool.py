"""
All tools available for the ai.
"""
from typing import Dict, List, Callable, Any, Optional, Union
import warnings
import re
import json
import os
from requests import Session
from bs4 import BeautifulSoup
from googlesearch import search
from duckduckgo_search import DDGS
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class ToolDefinition:
    """
    Encapsulates the definition of a tool, including its name, description, usage, parameters, examples, and example with parameters.
    """
    def __init__(
        self,
        tool_name: str,
        tool_function: Callable,
        tool_description: str,
        tool_usage: str,
        tool_parameters: Dict[str, str],
        tool_examples: List[str],
        tool_example_with_parameters: List[str]
    ):
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.tool_function = tool_function
        self.tool_usage = tool_usage
        self.tool_parameters = tool_parameters
        self.tool_examples = tool_examples
        self.tool_example_with_parameters = tool_example_with_parameters
    
    def for_prompt(self) -> str:
        """
        Returns a string representation of the tool definition for the prompt.
        """
        result = f"**{self.tool_name}**\n"
        result += f"-   **Description:** {self.tool_description}\n"
        result += f"-   **Usage:** `{self.tool_usage}`\n"
        
        if self.tool_parameters:
            result += "-   **Parameters:**\n"
            for param_name, param_description in self.tool_parameters.items():
                result += f"    -   `{param_name}`: {param_description}\n"
        
        if self.tool_examples:
            result += "-   **Examples:**\n"
            for example in self.tool_examples:
                result += f"    -   `{example}`\n"
        
        if self.tool_example_with_parameters:
            result += "-   **Example with Parameters:**\n"
            for example in self.tool_example_with_parameters:
                result += f"    -   `{example}`\n"
        
        return result

    def __str__(self) -> str:
        """
        Returns a string representation of the tool definition.
        """
        return self.for_prompt()

class ToolCall:
    """
    Represents a structured tool call with parameters.
    """
    def __init__(self, tool_name: str, primary_param: str, additional_params: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.primary_param = primary_param
        self.additional_params = additional_params or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tool": self.tool_name,
            "primary_param": self.primary_param,
            "params": self.additional_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCall':
        """Create ToolCall from dictionary."""
        return cls(
            tool_name=data.get("tool", ""),
            primary_param=data.get("primary_param", ""),
            additional_params=data.get("params", {})
        )
    
    def __str__(self) -> str:
        return f"ToolCall({self.tool_name}, {self.primary_param}, {self.additional_params})"

class ToolResult:
    """
    Represents the result of executing a tool.
    """
    def __init__(self, tool_call: ToolCall, result: Any, success: bool = True, error: Optional[str] = None):
        self.tool_call = tool_call
        self.result = result
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tool_call": self.tool_call.to_dict(),
            "result": self.result,
            "success": self.success,
            "error": self.error
        }

class ToolManager:
    """
    Manages the definitions of available tools and their execution.
    """
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def define_tool(
        self,
        tool_name: str,
        tool_function: Callable,
        tool_description: str,
        tool_usage: str,
        tool_parameters: Dict[str, str],
        tool_examples: List[str],
        tool_example_with_parameters: List[str]
    ) -> None:
        """
        Defines a tool and adds it to the tool manager.
        """
        tool = ToolDefinition(
            tool_name=tool_name,
            tool_function=tool_function,
            tool_description=tool_description,
            tool_usage=tool_usage,
            tool_parameters=tool_parameters,
            tool_examples=tool_examples,
            tool_example_with_parameters=tool_example_with_parameters
        )
        self.tools[tool_name] = tool

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        """
        Retrieves a tool definition by its name.
        """
        return self.tools.get(tool_name)

    def get_full_prompt(self) -> str:
        """
        Returns a full prompt with all tool definitions, numbered for clarity.
        """
        tool_prompts = [f"{i+1}. {tool.for_prompt()}" for i, tool in enumerate(self.tools.values())]
        return "\n\n".join(tool_prompts)
    
    def parse_tool_calls_json(self, content: str) -> List[ToolCall]:
        """
        Parse tool calls from JSON format in content.
        
        Expected format:
        <toolCalls>
        [
          {"tool": "websearch", "primary_param": "weather in NYC", "params": {"num_results": 5}},
          {"tool": "ddg_news", "primary_param": "current events", "params": {"num_results": 3}}
        ]
        </toolCalls>
        
        Args:
            content: String content containing JSON tool calls
            
        Returns:
            List of ToolCall objects
        """
        tool_calls = []
        
        pattern = r"<toolCalls>(.*?)</toolCalls>"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return tool_calls
        
        json_str = match.group(1).strip()
        
        try:
            calls_data = json.loads(json_str)
            if isinstance(calls_data, list):
                for call_data in calls_data:
                    if isinstance(call_data, dict):
                        tool_call = ToolCall.from_dict(call_data)
                        if tool_call.tool_name and self.get_tool(tool_call.tool_name):
                            tool_calls.append(tool_call)
        except json.JSONDecodeError as e:
            pass
        
        return tool_calls
    
    def parse_tool(self, message: str) -> tuple[Callable | None, str | None, dict[str, str] | None]:
        """
        Legacy method - parses the tool call and parameters from a message using old format.
        Kept for backwards compatibility.

        Args:
            message (str): The message containing the tool call.

        Returns:
            tuple: A tuple containing the tool's function, the primary parameter, and a dictionary of additional parameters.
                   Returns (None, None, None) if no valid tool call is found.
        """
        pattern = r"<(\w+)>([^<]+)</\1>"
        match = re.search(pattern, message)

        if not match:
            return None, None, None

        tool_name = match.group(1)
        parameter_string = match.group(2)
        parts = parameter_string.split(";")
        parameter = parts[0].strip()

        params = {}
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            try:
                params[key] = int(value)
            except ValueError:
                params[key] = value

        tool = self.get_tool(tool_name)
        if not tool:
            return None, None, None

        return tool.tool_function, parameter, params
    
    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a single tool call and return the result.
        
        Args:
            tool_call: The ToolCall object to execute
            
        Returns:
            ToolResult with the execution result
        """
        tool_def = self.get_tool(tool_call.tool_name)
        if not tool_def:
            tool_name_lower = tool_call.tool_name.lower()
            for registered_name in self.tools.keys():
                if registered_name.lower() == tool_name_lower:
                    tool_def = self.get_tool(registered_name)
                    tool_call.tool_name = registered_name
                    break
        
        if not tool_def:
            return ToolResult(
                tool_call=tool_call,
                result=None,
                success=False,
                error=f"Tool '{tool_call.tool_name}' not found"
            )
        
        try:
            result = tool_def.tool_function(tool_call.primary_param, **tool_call.additional_params)
            return ToolResult(
                tool_call=tool_call,
                result=result,
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_call=tool_call,
                result=None,
                success=False,
                error=f"Tool execution error: {str(e)}"
            )
    
    def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        Execute multiple tool calls and return all results.
        
        Args:
            tool_calls: List of ToolCall objects to execute
            
        Returns:
            List of ToolResult objects
        """
        results = []
        for tool_call in tool_calls:
            result = self.execute_tool_call(tool_call)
            results.append(result)
        return results
    
    def get_available_tools_for_prompt(self) -> str:
        """
        Get a formatted list of available tools for AI prompts.
        
        Returns:
            Formatted string describing all available tools
        """
        if not self.tools:
            return "No tools available."
        
        prompt = "## AVAILABLE TOOLS\n\n"
        for i, (tool_name, tool_def) in enumerate(self.tools.items(), 1):
            prompt += f"**{i}. {tool_name}**\n"
            prompt += f"   - **Purpose:** {tool_def.tool_description}\n"
            prompt += f"   - **Usage:** Use when {tool_def.tool_description.lower()}\n"
            
            if tool_def.tool_parameters:
                prompt += f"   - **Parameters:** {', '.join(tool_def.tool_parameters.keys())}\n"
            
            prompt += "\n"
        
        return prompt

#### TOOL MANAGER ####
tool_manager = ToolManager()

#### TOOLS ####
def google_search(query: str, num_results: int = 5, fetch: bool = False) -> str:
    """
    Perform a Google search and return the results.
    
    Args:
        query (str): The search query.
        num_results (int): The number of results to return.
        
    Returns:
        list[str]: A list of search results.
    """
    results = search(
        query,
        num_results=num_results,
        advanced=True,
        unique=True,
    )
    
    try:
        response = "## Google Search Results\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. {result.title.strip()}\n"
            response += f"Url: {result.url.strip()}\n"
            response += f"Body: {result.description.strip()}\n\n"
            if fetch and result.url:    
                response += f"Webpage Content: {fetch_webpage(result.url.strip(), 2000)}\n\n"
    except:
        return "ERROR_NO_RESULTS"
    return response
    
def duckduckgo_search(query: str, num_results: int = 5, fetch: bool = False) -> str:
    """
    Perform a DuckDuckGo search and return the results.
    
    Args:
        query (str): The search query.
        num_results (int): The number of results to return.
        
    Returns:
        list[str]: A list of search results.
    """
    results = DDGS().text(
        query,
        max_results=num_results,
    )
    
    try:
        response = "## DuckDuckGo Search Results\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. {result.get('title', 'No title').strip()}\n"
            response += f"Url: {result.get('href', 'No url').strip()}\n"
            response += f"Snippet: {result.get('body', 'No body').strip()}\n\n"
            if fetch and result.get('href'):
                response += f"Webpage Content: {fetch_webpage(result.get('href').strip(), 2000)}\n\n"
    except:
        return "ERROR_NO_RESULTS"
    return response

def ddg_news(query: str, num_results: int = 5, fetch: bool = False) -> str:
    """
    Perform a DuckDuckGo news search and return the results.
    
    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        list[str]: A list of search results.
    """
    results = DDGS().news(
        keywords=query,
        max_results=num_results,
    )

    try:
        response = "## DuckDuckGo News Search Results\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. {result.get('title', 'No title').strip()}\n"
            response += f"Url: {result.get('url', 'No url').strip()}\n"
            response += f"Snippet: {result.get('body', 'No body').strip()}\n"
            response += f"Source: {result.get('source', 'No source').strip()}\n"
            response += f"Date: {result.get('date', 'No date').strip()}\n\n"
            if fetch and result.get('url'):
                response += f"Webpage Content: {fetch_webpage(result.get('url').strip(), 2000)}\n\n"
    except:
        return "ERROR_NO_RESULTS"
    return response

def websearch(query: str, num_results: int = 5) -> str:
    """Perform a web search, defaults to DuckDuckGo if Google fails."""
    results = google_search(query, num_results)
    return results if results != "ERROR_NO_RESULTS" else duckduckgo_search(query, num_results)

def deep_search(query: str, num_results: int = 5) -> str:
    """
    Perform a deep search and return the results.
    Use both google and duckduckgo search and fetch the webpage content.
    
    Args:
        query (str): The search query.
        num_results (int): The number of results to return.
    """
    return google_search(query, num_results, True) + "\n\n" + duckduckgo_search(query, num_results, True)

def fetch_webpage(url: str, max_content: int = -1) -> str:
    """
    Fetch a webpage and return the results.
    
    Args:
        url (str): The url of the webpage to fetch.
        max_content (int): The maximum number of characters to return. If -1, return the entire webpage.
    """
    result = f"## Webpage Content\nUrl: {url}\n\n"
    with Session() as session:
        # Spoofing the user agent and adding browser like headers
        headers = {
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }
        response = session.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        result += soup.get_text(strip=True)
        if max_content != -1 and len(result) > max_content:
            result = result[:max_content] + "..."
    return result

def get_weather_info(location: str, detailed: bool = False) -> str:
    """
    Get weather information for a location using web search with enhanced parsing.

    Args:
        location (str): The location to get weather for.
        detailed (bool): Whether to get detailed weather information.

    Returns:
        str: Weather information for the location.
    """
    try:
        if detailed:
            query = f"detailed weather forecast for {location} today tomorrow"
            raw_results = google_search(query, 3, True)
        else:
            query = f"current weather in {location} today temperature conditions"
            raw_results = google_search(query, 2, True)

        weather_info = _parse_weather_from_search(raw_results, location)

        if weather_info:
            return weather_info
        else:
            return raw_results

    except Exception as e:
        return f"ERROR: Could not retrieve weather information for {location}. Error: {str(e)}"

def _parse_weather_from_search(search_results: str, location: str) -> str:
    """
    Parse weather information from Google search results.

    Args:
        search_results (str): Raw search results from Google
        location (str): The location being searched for

    Returns:
        str: Parsed weather information or None if parsing fails
    """
    import re

    try:
        text = search_results.lower()

        temp_patterns = [
            r'(\d+)°[cf]',
            r'(\d+)\s*degrees?',
            r'temperature[:\s]*(\d+)',
            r'(\d+)\s*°',
        ]

        temperatures = []
        for pattern in temp_patterns:
            matches = re.findall(pattern, text)
            temperatures.extend(matches)

        condition_patterns = [
            r'(sunny|cloudy|rainy|snowy|clear|overcast|partly cloudy|mostly sunny|thunderstorms?|drizzle|fog|windy)',
            r'(rain|snow|sun|cloud|storm|wind|mist|haze)',
        ]

        conditions = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, text)
            conditions.extend(matches)

        humidity_matches = re.findall(r'humidity[:\s]*(\d+)%?', text)

        wind_matches = re.findall(r'wind[:\s]*(\d+)\s*(?:mph|km/h|m/s)', text)

        if temperatures or conditions:
            weather_summary = f"Current weather in {location.title()}:\n"

            if temperatures:
                temp = max(set(temperatures), key=temperatures.count)
                weather_summary += f"🌡️ Temperature: {temp}°\n"

            if conditions:
                unique_conditions = list(set(conditions))
                weather_summary += f"☁️ Conditions: {', '.join(unique_conditions).title()}\n"

            if humidity_matches:
                humidity = humidity_matches[0]
                weather_summary += f"💧 Humidity: {humidity}%\n"

            if wind_matches:
                wind = wind_matches[0]
                weather_summary += f"💨 Wind: {wind} mph\n"

            return weather_summary.strip()

        return None

    except Exception as e:
        return None

def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time for a timezone.
    
    Args:
        timezone (str): The timezone to get time for.
        
    Returns:
        str: Current time information.
    """
    try:
        query = f"current time in {timezone} now"
        return google_search(query, 2, True)
    except:
        return f"ERROR: Could not retrieve time information for {timezone}"

def calculator(expression: str) -> str:
    """
    Perform basic mathematical calculations.
    
    Args:
        expression (str): The mathematical expression to evaluate.
        
    Returns:
        str: The result of the calculation.
    """
    try:
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in expression.replace(' ', '')):
            return "ERROR: Invalid characters in expression"
        
        expression = expression.replace('^', '**')
        
        result = eval(expression)
        return f"## Calculation Result\nExpression: {expression}\nResult: {result}"
    except Exception as e:
        return f"ERROR: Could not calculate '{expression}': {str(e)}"

def get_definition(word: str) -> str:
    """
    Get the definition of a word or term.

    Args:
        word (str): The word to define.

    Returns:
        str: Definition of the word.
    """
    try:
        query = f"definition meaning of {word}"
        return google_search(query, 3, True)
    except:
        return f"ERROR: Could not find definition for '{word}'"

def gif_search(query: str, num_results: int = 5, rating: str = "g") -> str:
    """
    Search for GIFs using the Giphy API.

    Args:
        query (str): The search query for GIFs.
        num_results (int): Number of GIFs to return (default: 5, max: 25).
        rating (str): Content rating filter (g, pg, pg-13, r). Default: g.

    Returns:
        str: Formatted list of GIF URLs and titles.
    """
    try:
        # Get API key from environment
        api_key = os.getenv("GIPHY_API_KEY")
        if not api_key:
            return "ERROR: GIPHY_API_KEY not found in environment variables. Please set up your Giphy API key."

        # Validate parameters
        num_results = min(max(1, num_results), 25)  # Limit between 1-25
        valid_ratings = ["g", "pg", "pg-13", "r"]
        if rating.lower() not in valid_ratings:
            rating = "g"

        # Giphy API endpoint
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": api_key,
            "q": query,
            "limit": num_results,
            "rating": rating.lower(),
            "lang": "en"
        }

        # Make API request
        with Session() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            }
            response = session.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("data"):
                return f"No GIFs found for query: '{query}'"

            # Format results
            result = f"## GIF Search Results for '{query}'\n"
            result += f"Found {len(data['data'])} GIF(s):\n\n"

            for i, gif in enumerate(data["data"], 1):
                title = gif.get("title", "Untitled GIF")
                gif_url = gif.get("images", {}).get("original", {}).get("url", "")

                # Fallback to other image formats if original is not available
                if not gif_url:
                    gif_url = gif.get("images", {}).get("fixed_height", {}).get("url", "")
                if not gif_url:
                    gif_url = gif.get("url", "")

                if gif_url:
                    result += f"{i}. **{title}**\n"
                    result += f"   URL: {gif_url}\n\n"
                else:
                    result += f"{i}. **{title}** - No URL available\n\n"

            return result

    except Exception as e:
        return f"ERROR: Failed to search GIFs - {str(e)}"

#### TOOL DEFINITIONS ####

# Web Search
tool_manager.define_tool(
    tool_name="websearch",
    tool_function=websearch,
    tool_description="Executes a web search query and retrieves relevant results. If Google fails, it defaults to DuckDuckGo.",
    tool_usage="<websearch>your search query</websearch>",
    tool_parameters={"num_results": "Number of results to return (default: 5)"},
    tool_examples=["<websearch>best restaurants in New York City</websearch>"],
    tool_example_with_parameters=["<websearch>best restaurants in New York City;num_results=10</websearch>"]
)

# DuckDuckGo News
tool_manager.define_tool(
    tool_name="ddg_news",
    tool_function=ddg_news,
    tool_description="Conducts a news search using DuckDuckGo and returns the latest news articles related to the query.",
    tool_usage="<ddg_news>your news query</ddg_news>",
    tool_parameters={"num_results": "Number of results to return (default: 5)"},
    tool_examples=["<ddg_news>stock market trends</ddg_news"],
    tool_example_with_parameters=["<ddg_news>stock market trends;num_results=10</ddg_news"]
)

# Deep Search
tool_manager.define_tool(
    tool_name="deep_search",
    tool_function=deep_search,
    tool_description="Performs an exhaustive search using both Google and DuckDuckGo, fetching webpage content for a comprehensive analysis. This tool gives you back much more information then the other tools but it isnt needed since most of the time you can get the information you need with the other tools.",
    tool_usage="<deep_search>your search query</deep_search>",
    tool_parameters={"num_results": "Number of results to return (default: 5)"},
    tool_examples=["<deep_search>climate change effects on coastal regions</deep_search>"],
    tool_example_with_parameters=["<deep_search>climate change effects on coastal regions;num_results=10</deep_search>"]
)

# Weather Information
tool_manager.define_tool(
    tool_name="get_weather_info",
    tool_function=get_weather_info,
    tool_description="Retrieves current weather information or detailed forecasts for a specific location using web search.",
    tool_usage="<get_weather_info>location name</get_weather_info>",
    tool_parameters={"detailed": "Boolean to get detailed forecast (default: False)"},
    tool_examples=["<get_weather_info>New York City</get_weather_info>", "<get_weather_info>London, UK</get_weather_info>"],
    tool_example_with_parameters=["<get_weather_info>Paris, France;detailed=true</get_weather_info>"]
)

# Current Time
tool_manager.define_tool(
    tool_name="get_current_time",
    tool_function=get_current_time,
    tool_description="Gets the current time for a specific timezone or location.",
    tool_usage="<get_current_time>timezone or location</get_current_time>",
    tool_parameters={},
    tool_examples=["<get_current_time>EST</get_current_time>", "<get_current_time>Tokyo</get_current_time>"],
    tool_example_with_parameters=["<get_current_time>Pacific Standard Time</get_current_time>"]
)

# Definition Lookup
tool_manager.define_tool(
    tool_name="get_definition",
    tool_function=get_definition,
    tool_description="Looks up the definition and meaning of words or terms.",
    tool_usage="<get_definition>word or term</get_definition>",
    tool_parameters={},
    tool_examples=["<get_definition>serendipity</get_definition>", "<get_definition>machine learning</get_definition>"],
    tool_example_with_parameters=["<get_definition>cryptocurrency</get_definition>"]
)

# GIF Search
tool_manager.define_tool(
    tool_name="gif_search",
    tool_function=gif_search,
    tool_description="Searches for animated GIFs using the Giphy API. Perfect for finding reaction GIFs, funny animations, or any visual content to enhance conversations.",
    tool_usage="<gif_search>search query</gif_search>",
    tool_parameters={
        "num_results": "Number of GIFs to return (1-25, default: 5)",
        "rating": "Content rating filter: 'g' (general), 'pg', 'pg-13', 'r' (default: g)"
    },
    tool_examples=[
        "<gif_search>funny cat</gif_search>",
        "<gif_search>celebration dance</gif_search>",
        "<gif_search>thumbs up</gif_search>"
    ],
    tool_example_with_parameters=[
        "<gif_search>excited reaction;num_results=3</gif_search>",
        "<gif_search>happy birthday;num_results=10;rating=pg</gif_search>"
    ]
)

def get_tools_prompt() -> str:
    """
    Crafts a detailed prompt for the agent, outlining available tools, usage instructions, and parameter specifications.
    This prompt is designed to guide the agent in effectively utilizing the tools for various tasks.
    """
    return f"""
    You are equipped with a suite of powerful tools to assist you in fulfilling user requests. To leverage these tools effectively, adhere to the following guidelines:

    **Tool Invocation Format:**
    To utilize a tool, enclose the tool's name and its corresponding parameters within angle brackets.  Parameters should be separated by semicolons.
    `<tool_name>parameter;key1=value1;key2=value2</tool_name>`

    **Available Tools & Parameters:**

    {tool_manager.get_full_prompt()}

    **Important Considerations:**
    -   Ensure that the tool name is correctly spelled and matches the options provided above.
    -   Provide a clear and concise parameter for each tool to ensure accurate and relevant results.
    -   Do not include any additional text or formatting within the tool invocation tags.
    """
