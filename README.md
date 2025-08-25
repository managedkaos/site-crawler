# Site Crawler

A Python-based web crawler that recursively visits pages on a website and generates comprehensive reports.

## Features

- Recursive crawling with configurable depth limits
- HTTP status code tracking and error reporting
- Domain-restricted crawling (stays within the same domain)
- Configurable delays between requests
- Comprehensive reporting with detailed statistics
- Command-line interface with various options

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py https://example.com
```

### Advanced Usage

```bash
# Crawl with custom depth and delay
python main.py https://example.com --max-depth 5 --delay 0.5

# Save report to file
python main.py https://example.com --output report.md
```

### Command Line Options

- `url`: The base URL to start crawling from (required)
- `--max-depth`: Maximum depth to crawl (default: 3)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--output`: Output file for the report (default: print to console)

## Example Output

The crawler generates a markdown report including:

- Crawl statistics (total pages, duration, etc.)
- HTTP status code summary
- Detailed error report
- All visited pages organized by depth

## Examples

For detailed explanations of the following examples and the commands used to generate them, see [EXAMPLES.md](examples/EXAMPLES.md).

- **[Simple Site Report](examples/example_com-report.md)** - Basic crawling of a single-page site
- **[Error Reporting Example](examples/google_com-report.md)** - Multi-depth crawling with error detection
- **[Interrupted Crawl Example](examples/github_com-report.md)** - Large site handling with partial results
