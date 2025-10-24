# Quick Start Guide: CLI Navigation Tool

**Purpose**: Get the CLI Navigation Tool running in under 10 minutes
**Target**: Developers working on the implementation
**Prerequisites**: Python 3.11+, Git, Chrome/Chromium browser

## Installation & Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd Qiniu-Hackathon

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
# Install browser binaries
playwright install chromium

# Verify installation
playwright install --dry-run
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required .env variables:**
```bash
# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here  # For Gemini 2.0 Flash
# OR
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Performance settings
NAV_TOOL_DEFAULT_BROWSER=chromium
NAV_TOOL_HEADLESS_MODE=false
NAV_TOOL_TIMEOUT_MS=10000
```

## Basic Usage

### 1. Simple Navigation Query

```bash
# Basic usage
python -m nav_cli "从北京到上海"

# With specific browser (Chrome/Chromium only per clarification)
python -m nav_cli "中关村到三里屯" --browser chromium

# Headless mode (for automation)
python -m nav_cli "天安门到故宫" --headless
```

### 2. Expected Output

```bash
$ python -m nav_cli "从北京到上海"
✅ 正在解析位置信息...
✅ 构建导航URL...
✅ 启动Chrome浏览器...
✅ 路线规划成功！耗时 8500ms

浏览器已打开，显示北京到上海的导航路线。
按 Enter 键关闭浏览器...
```

### 3. Help and Options

```bash
# Show help
python -m nav_cli --help

# Available options
python -m nav_cli "从A到B" \
  --browser chromium \
  --headless \
  --timeout 10000 \
  --service gaode
```

## Development Workflow

### 1. Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/test_parsing.py
pytest tests/integration/test_browser.py
pytest tests/contract/test_api.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### 2. Development Mode

```bash
# Install in development mode
pip install -e .

# Run with debug output
python -m nav_cli "从北京到上海" --debug

# Check performance
python -m nav_cli "从北京到上海" --profile
```

### 3. Code Quality

```bash
# Format code
black src/
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Architecture Overview

### High-Level Flow

```mermaid
graph LR
    A[User Input] --> B[CLI Parser]
    B --> C[LangChain Agent]
    C --> D[Location Parser Tool]
    C --> E[URL Constructor Tool]
    C --> F[Browser Automation Tool]
    F --> G[Navigation Display]
```

### Key Components

1. **CLI Interface** (`src/cli/`)
   - Typer-based command-line interface
   - Input validation and error handling
   - Progress reporting to user

2. **Agent System** (`src/agents/`)
   - LangChain Agent orchestration
   - Tool selection and execution
   - Error recovery and retry logic (single retry per clarification)

3. **Location Parser** (`src/tools/parsing_tools.py`)
   - Hybrid NLP: PaddleNLP + LLM fallback
   - Context-based disambiguation (per clarification)
   - Confidence scoring and validation

4. **Browser Automation** (`src/tools/browser_tools.py`)
   - Playwright-based Chrome/Chromium control (per clarification)
   - Cross-platform compatibility
   - Error handling for browser unavailability

5. **URL Construction** (`src/tools/gaode_tools.py`)
   - Gaode Maps URL building with Chinese encoding
   - Fallback URL generation
   - Parameter validation

## Testing Your Changes

### 1. Unit Testing

```python
# Test location parsing
pytest tests/unit/test_parsing_tools.py -v

# Test URL construction
pytest tests/unit/test_gaode_tools.py -v

# Test browser automation
pytest tests/unit/test_browser_tools.py -v
```

### 2. Integration Testing

```bash
# Test end-to-end flow
pytest tests/integration/test_agent_flow.py -v

# Test performance requirements (<10s per clarification)
pytest tests/integration/test_performance.py -v
```

### 3. Manual Testing

```bash
# Test common query patterns
python -m nav_cli "从北京到上海"          # City to city
python -m nav_cli "中关村到三里屯"        # District to district
python -m nav_cli "天安门到故宫"          # Landmark to landmark
python -m nav_cli "北京站到首都机场"       # Transport to transport

# Test error handling
python -m nav_cli ""                      # Empty input
python -m nav_cli "无效输入"               # Invalid input
python -m nav_cli "从火星到木星"           # Impossible locations
```

## Performance Monitoring

### 1. Performance Targets (Updated per Clarifications)

- **Total Response Time**: <10 seconds (per clarification)
- **Agent Processing**: <3 seconds
- **Browser Launch**: <3 seconds
- **Cache Hit Rate**: >60% for common queries

### 2. Performance Profiling

```bash
# Enable performance profiling
python -m nav_cli "从北京到上海" --profile

# View performance report
cat /tmp/nav_cli_profile.json | python -m json.tool
```

### 3. Benchmarking

```bash
# Run performance benchmarks
python -m nav_cli.benchmark --queries benchmark_queries.txt

# Sample benchmark queries
echo "从北京到上海
中关村到三里屯
天安门到故宫
北京站到首都机场
清华大学到北京大学" > benchmark_queries.txt
```

## Troubleshooting

### Common Issues

#### 1. Chrome/Chromium Not Available (Per Clarification)

```bash
# Symptoms: "Chrome/Chromium not found" error
# Solutions:
# Install Chrome/Chromium
# macOS: brew install --cask chromium
# Ubuntu: sudo apt-get install chromium-browser
# Windows: Download and install Chrome

# Check browser availability
python -c "from src.tools.browser_tools import ChromeBrowserManager; print(ChromeBrowserManager().check_chrome_availability())"
```

#### 2. Browser Launch Fails

```bash
# Symptoms: "Browser launch timed out" error
# Solutions:
playwright install chromium  # Reinstall browsers
python -m nav_cli --help    # Check system requirements

# Check browser permissions (macOS)
xattr -rd com.apple.quarantine $(which chromium)
```

#### 3. LLM API Errors

```bash
# Symptoms: "API key invalid" or "Rate limit exceeded"
# Solutions:
# Check .env file
cat .env | grep API_KEY

# Test API connection
python -c "from src.agents.navigation_agent import test_llm_connection; test_llm_connection()"
```

#### 4. Chinese Text Parsing Issues

```bash
# Symptoms: "Cannot parse location information"
# Solutions:
# Test with known good queries
python -m nav_cli "从北京到上海"

# Check NLP dependencies
pip list | grep -E "(paddle|jieba)"
```

### Debug Mode

```bash
# Enable debug output
python -m nav_cli "从北京到上海" --debug

# Check logs
tail -f /tmp/nav_cli.log

# Verbose agent execution
DEBUG=1 python -m nav_cli "从北京到上海"
```

## Distribution and Deployment

### 1. Building Standalone Executable (Per Clarification)

```bash
# Build executable
pyinstaller --onefile --name nav-tool src/cli/main.py

# Test executable
./dist/nav-tool "从北京到上海"
```

### 2. Cross-Platform Builds

```bash
# Build for all platforms
pyinstaller build.spec --clean

# Output in dist/
# - nav-tool.exe (Windows)
# - nav-tool (macOS/Linux)
```

## Contributing

### 1. Code Style

- Use Black for code formatting
- Follow PEP 8 guidelines
- Type hints required for all public functions
- Docstrings for all modules and functions

### 2. Testing Requirements

- All new features must include unit tests
- Integration tests for end-to-end flows
- Performance tests for critical paths
- Maintain >90% test coverage

### 3. Submitting Changes

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
pytest
black .
isort .

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

## Next Steps

1. **Explore the codebase**: Start with `src/cli/main.py` and `src/agents/navigation_agent.py`
2. **Run the examples**: Try different query formats and options
3. **Run the test suite**: Ensure all tests pass in your environment
4. **Make a small change**: Add a new query pattern or error message
5. **Read the full specification**: See `spec.md` for complete requirements

## Resources

- [Feature Specification](spec.md) - Complete requirements and user stories
- [Data Model](data-model.md) - Entity definitions and relationships
- [API Contracts](contracts/api-contract.yaml) - Internal API documentation
- [Research Findings](research.md) - Technical research and decisions
- [Implementation Plan](plan.md) - Detailed technical architecture

## Getting Help

- Check the troubleshooting section above
- Review existing GitHub issues
- Check the debug logs in `/tmp/nav_cli.log`
- Run `python -m nav_cli --help` for available options
- Contact the development team for specific issues

## Key Clarifications Applied

1. **Performance Target**: 10 seconds total execution time (updated from 3 seconds)
2. **Browser Support**: Chrome/Chromium only with explicit error for other browsers
3. **Error Handling**: Single retry with exponential backoff for network issues
4. **Location Disambiguation**: Context-based resolution with user confirmation
5. **Distribution**: Standalone executable with embedded dependencies
6. **Architecture**: Agent-Driven Architecture with high-level tools and structured observations