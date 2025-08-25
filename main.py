#!/usr/bin/env python3
"""
Site Crawler Script

This script crawls a website starting from the root URL and recursively visits all linked pages.
It provides a comprehensive report of pages visited and any HTTP errors encountered.

Usage:
    python main.py <base_url>

Example:
    python main.py https://example.com
"""

import argparse
import logging
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SiteCrawler:
    def __init__(self, base_url: str, max_depth: int = 3, delay: float = 1.0):
        """
        Initialize the crawler.

        Args:
            base_url: The starting URL for the crawl
            max_depth: Maximum depth to crawl (default: 3)
            delay: Delay between requests in seconds (default: 1.0)
        """
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.delay = delay

        # Crawl state
        self.visited_urls: Set[str] = set()
        self.url_status: Dict[str, int] = {}
        self.url_depth: Dict[str, int] = {}
        self.error_urls: Dict[int, List[str]] = defaultdict(list)

        # Statistics
        self.total_requests = 0
        self.start_time = time.time()

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MMX-Site-Crawler/1.0"})

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled."""
        parsed = urlparse(url)

        # Only crawl same domain
        if parsed.netloc != self.domain:
            return False

        # Skip non-HTTP/HTTPS protocols
        if parsed.scheme not in ["http", "https"]:
            return False

        # Skip common non-content file types
        skip_extensions = {
            ".pdf",
            ".zip",
            ".exe",
            ".dmg",
            ".pkg",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".ico",
            ".css",
            ".js",
            ".xml",
        }
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip common non-content paths
        skip_paths = ["/api/", "/admin/", "/wp-admin/", "/cgi-bin/", "/mail/"]
        if any(skip_path in parsed.path.lower() for skip_path in skip_paths):
            return False

        return True

    def extract_links(self, html_content: str, current_url: str) -> Set[str]:
        """Extract links from HTML content."""
        import re

        links = set()

        # Simple regex to find href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(href_pattern, html_content)

        for match in matches:
            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, match)

            # Clean up URL (remove fragments, query params for crawling)
            parsed = urlparse(absolute_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            if self.is_valid_url(clean_url):
                links.add(clean_url)

        return links

    def crawl_page(self, url: str, depth: int = 0) -> None:
        """Crawl a single page and extract links."""
        if depth > self.max_depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        self.url_depth[url] = depth

        try:
            logger.info(f"Crawling {url} (depth {depth})")

            # Make request
            response = self.session.get(url, timeout=30, allow_redirects=True)
            self.total_requests += 1

            # Record status
            status_code = response.status_code
            self.url_status[url] = status_code

            # Track errors
            if status_code >= 400:
                self.error_urls[status_code].append(url)
                logger.warning(f"HTTP {status_code} for {url}")

            # Extract links for further crawling
            if status_code == 200 and depth < self.max_depth:
                try:
                    links = self.extract_links(response.text, url)
                    for link in links:
                        if link not in self.visited_urls:
                            # Add delay between requests
                            time.sleep(self.delay)
                            self.crawl_page(link, depth + 1)
                except Exception as e:
                    logger.error(f"Error extracting links from {url}: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            self.url_status[url] = 0  # Mark as failed
            self.error_urls[0].append(url)

        except Exception as e:
            logger.error(f"Unexpected error crawling {url}: {e}")
            self.url_status[url] = 0  # Mark as failed
            self.error_urls[0].append(url)

    def crawl(self) -> None:
        """Start the crawling process."""
        logger.info(f"Starting crawl of {self.base_url}")
        logger.info(f"Max depth: {self.max_depth}, Delay: {self.delay}s")

        self.crawl_page(self.base_url, 0)

        logger.info("Crawling completed!")

    def generate_report(self, is_partial: bool = False) -> str:
        """Generate a comprehensive crawl report."""
        end_time = time.time()
        duration = end_time - self.start_time

        # Count status codes
        status_counts = Counter(self.url_status.values())

        # Generate report
        report = []
        report.append(f"# Site Crawler Report: {self.base_url}\n")
        if is_partial:
            report.append("⚠️ **PARTIAL REPORT** - Crawling was interrupted\n")

        # Create properly aligned table
        metrics = [
            ("Base URL", self.base_url),
            ("Domain", self.domain),
            (
                "Start Time",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            ),
            ("Duration", f"{duration:.2f} seconds"),
            ("Total Requests", str(self.total_requests)),
            ("Total Pages Visited", str(len(self.visited_urls))),
            (
                "Max Depth Reached",
                str(max(self.url_depth.values()) if self.url_depth else 0),
            ),
        ]

        # Find the maximum width for the metric column
        max_metric_width = max(len(metric) for metric, _ in metrics)

        # Create the table header
        report.append(f"| {'Metric':<{max_metric_width}} | Value |")
        report.append(f"|{'-' * max_metric_width}-|--------|")

        # Add each metric row
        for metric, value in metrics:
            report.append(f"| {metric:<{max_metric_width}} | {value} |")

        report.append("")

        # Status code summary
        report.append("## HTTP STATUS CODE SUMMARY\n")
        report.append("| Status Code | Description | Count |")
        report.append("|-------------|-------------|-------|")
        for status_code in sorted(status_counts.keys()):
            count = status_counts[status_code]
            if status_code == 0:
                status_desc = "FAILED"
            elif status_code == 200:
                status_desc = "OK"
            elif status_code >= 400:
                status_desc = "ERROR"
            else:
                status_desc = "OTHER"

            report.append(f"| {status_code} | {status_desc} | {count} |")
        report.append("")

        # Error details
        if self.error_urls:
            report.append("## DETAILED ERROR REPORT\n")

            for status_code in sorted(self.error_urls.keys()):
                if status_code == 0:
                    report.append("### FAILED REQUESTS\n")
                else:
                    report.append(f"#### HTTP {status_code} ERRORS\n")

                for url in self.error_urls[status_code]:
                    report.append(f"- {url}")
                report.append("")

        # All visited URLs by depth
        report.append("## ALL VISITED PAGES BY DEPTH\n")

        for depth in range(max(self.url_depth.values()) + 1 if self.url_depth else 0):
            urls_at_depth = [url for url, d in self.url_depth.items() if d == depth]
            if urls_at_depth:
                report.append(f"### Depth {depth} ({len(urls_at_depth)} pages)\n")
                for url in sorted(urls_at_depth):
                    status = self.url_status.get(url, "Unknown")
                    report.append(f"- [{status}] {url}")
                report.append("")

        return "\n".join(report)


def main():
    """
    Main function to handle command line arguments and run the crawler.
    """
    parser = argparse.ArgumentParser(
        description="Crawl a website and generate a comprehensive report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawl-site.py https://example.com
  python crawl-site.py https://staging.example.com --max-depth 2
  python crawl-site.py https://dev.example.com --delay 0.5
        """,
    )

    parser.add_argument("url", help="The base URL to start crawling from")

    parser.add_argument(
        "--max-depth", type=int, default=3, help="Maximum depth to crawl (default: 3)"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--output", help="Output file for the report (default: print to console)"
    )

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url

    # Create crawler instance
    crawler = SiteCrawler(base_url=args.url, max_depth=args.max_depth, delay=args.delay)

    crawling_interrupted = False

    try:
        # Run crawler
        crawler.crawl()

    except KeyboardInterrupt:
        print("\nCrawling interrupted by user")
        print("Generating partial report...")
        crawling_interrupted = True
    except Exception as e:
        logger.error(f"Fatal error during crawling: {e}")
        print("Generating partial report...")
        crawling_interrupted = True

    # Generate and output report (even if crawling was interrupted)
    try:
        report = crawler.generate_report(is_partial=crawling_interrupted)

        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(report)
                print(f"Report saved to {args.output}")
            except IOError as e:
                print(f"Error writing to {args.output}: {e}")
                print("\n" + report)
        else:
            print(report)

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
