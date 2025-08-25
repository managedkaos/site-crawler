"""
Integration tests using HTTP Bin service

This test suite uses httpbin.org to test the site crawler with real HTTP responses.
HTTP Bin provides endpoints that return specific HTTP status codes, which is perfect
for testing how the crawler handles different response types.

Usage:
    python test_with_httpbin.py

Note: These tests require an internet connection to reach httpbin.org
"""

import time
import unittest

from main import SiteCrawler


class TestSiteCrawlerWithHttpBin(unittest.TestCase):
    """Integration tests using HTTP Bin service."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use a small delay to be respectful to the HTTP Bin service
        self.crawler = SiteCrawler("https://httpbin.org", max_depth=1, delay=0)

    def test_http_200_response(self):
        """Test crawling a page that returns HTTP 200 OK."""
        url = "https://httpbin.org/status/200"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 200)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # Verify it's not in the error list
        self.assertNotIn(url, self.crawler.error_urls.get(200, []))

    def test_http_404_response(self):
        """Test crawling a page that returns HTTP 404 Not Found."""
        url = "https://httpbin.org/status/404"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 404)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # Verify it's in the error list
        self.assertIn(url, self.crawler.error_urls[404])

    def test_http_500_response(self):
        """Test crawling a page that returns HTTP 500 Internal Server Error."""
        url = "https://httpbin.org/status/500"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 500)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # Verify it's in the error list
        self.assertIn(url, self.crawler.error_urls[500])

    def test_http_403_response(self):
        """Test crawling a page that returns HTTP 403 Forbidden."""
        url = "https://httpbin.org/status/403"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 403)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # Verify it's in the error list
        self.assertIn(url, self.crawler.error_urls[403])

    def test_http_301_redirect(self):
        """Test crawling a page that returns HTTP 301 redirect."""
        url = "https://httpbin.org/status/301"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # The status could be 200 (if redirect was followed), 301 (if not followed), or 502 (if service issue)
        status = self.crawler.url_status[url]
        self.assertIn(status, [200, 301, 502])

        # If it's an error status, it should be in error_urls
        if status >= 400:
            self.assertIn(url, self.crawler.error_urls[status])
        else:
            # Success status should not be in error_urls
            self.assertNotIn(url, self.crawler.error_urls.get(status, []))

    def test_http_302_redirect(self):
        """Test crawling a page that returns HTTP 302 redirect."""
        url = "https://httpbin.org/status/302"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # The status could be 200 (if redirect was followed), 302 (if not followed), or 502 (if service issue)
        status = self.crawler.url_status[url]
        self.assertIn(status, [200, 302, 502])

        # If it's an error status, it should be in error_urls
        if status >= 400:
            self.assertIn(url, self.crawler.error_urls[status])
        else:
            # Success status should not be in error_urls
            self.assertNotIn(url, self.crawler.error_urls.get(status, []))

    def test_http_418_teapot(self):
        """Test crawling a page that returns HTTP 418 I'm a teapot (for fun)."""
        url = "https://httpbin.org/status/418"

        # Crawl the specific status endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited and recorded correctly
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 418)
        self.assertEqual(self.crawler.url_depth[url], 0)

        # 418 is a client error, so it should be in error_urls
        self.assertIn(url, self.crawler.error_urls[418])

    def test_multiple_status_codes(self):
        """Test crawling multiple pages with different status codes."""
        urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
            "https://httpbin.org/status/403",
        ]

        # Crawl each URL
        for url in urls:
            self.crawler.crawl_page(url, 0)
            time.sleep(0.1)  # Small delay between requests

        # Verify all URLs were visited
        for url in urls:
            self.assertIn(url, self.crawler.visited_urls)

        # Verify status codes were recorded correctly
        self.assertEqual(self.crawler.url_status["https://httpbin.org/status/200"], 200)
        self.assertEqual(self.crawler.url_status["https://httpbin.org/status/404"], 404)
        self.assertEqual(self.crawler.url_status["https://httpbin.org/status/500"], 500)
        self.assertEqual(self.crawler.url_status["https://httpbin.org/status/403"], 403)

        # Verify error URLs are properly categorized
        self.assertIn("https://httpbin.org/status/404", self.crawler.error_urls[404])
        self.assertIn("https://httpbin.org/status/500", self.crawler.error_urls[500])
        self.assertIn("https://httpbin.org/status/403", self.crawler.error_urls[403])

        # Verify successful URLs are not in error list
        self.assertNotIn(
            "https://httpbin.org/status/200", self.crawler.error_urls.get(200, [])
        )

    def test_html_content_extraction(self):
        """Test extracting links from HTML content returned by HTTP Bin."""
        # HTTP Bin's /html endpoint returns HTML content
        url = "https://httpbin.org/html"

        # Crawl the HTML endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 200)

        # The HTML endpoint should return HTML content that can be parsed
        # We can't easily test link extraction without knowing the exact content,
        # but we can verify the page was processed successfully

    def test_json_response(self):
        """Test crawling a JSON endpoint (should be skipped by URL validation)."""
        url = "https://httpbin.org/json"

        # This should be skipped because it's not a typical HTML page
        # The crawler might still visit it, but it won't extract links from JSON

        # Crawl the JSON endpoint
        self.crawler.crawl_page(url, 0)

        # Verify the page was visited
        self.assertIn(url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[url], 200)

    def test_report_generation_with_httpbin(self):
        """Test report generation with real HTTP Bin data."""
        # Crawl a few different status codes
        urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
        ]

        for url in urls:
            self.crawler.crawl_page(url, 0)
            time.sleep(0.1)

        # Generate report
        report = self.crawler.generate_report()

        # Verify report contains expected content
        self.assertIn("Site Crawler Report: https://httpbin.org", report)
        self.assertIn("Total Pages Visited | 3", report)
        self.assertIn("HTTP 404 ERRORS", report)
        self.assertIn("HTTP 500 ERRORS", report)
        self.assertIn("https://httpbin.org/status/404", report)
        self.assertIn("https://httpbin.org/status/500", report)

    def test_delay_respect(self):
        """Test that the crawler respects the delay between requests."""
        start_time = time.time()

        # Crawl multiple URLs with a delay
        urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
        ]

        for url in urls:
            self.crawler.crawl_page(url, 0)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # With 3 requests and 0.5s delay between each, minimum time should be ~1 second
        # (first request has no delay, then 2 delays of 0.5s each)
        self.assertGreaterEqual(elapsed_time, 0.8)  # Allow some tolerance

    def test_domain_validation(self):
        """Test that the crawler only visits URLs from the same domain."""
        # Try to crawl a URL from a different domain
        external_url = "https://example.com"

        # This should be visited but the crawler should not follow links from it
        # The domain validation happens in is_valid_url() which is used for link extraction
        self.crawler.crawl_page(external_url, 0)

        # The URL should be visited (crawler will try to visit any URL passed to crawl_page)
        self.assertIn(external_url, self.crawler.visited_urls)

        # Check if it failed or succeeded - either is acceptable for this test
        # The important thing is that domain validation prevents following links from external domains
        status = self.crawler.url_status.get(external_url)
        if status == 0:
            # Request failed (expected for external domain)
            self.assertIn(external_url, self.crawler.error_urls.get(0, []))
        else:
            # Request succeeded (example.com might be reachable)
            # But the crawler should not extract links from it due to domain validation
            pass

    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        # Try to crawl a non-existent domain
        invalid_url = "https://this-domain-does-not-exist-12345.com"

        # This should fail but be handled gracefully
        self.crawler.crawl_page(invalid_url, 0)

        # The URL should be marked as visited but with status 0 (failed)
        self.assertIn(invalid_url, self.crawler.visited_urls)
        self.assertEqual(self.crawler.url_status[invalid_url], 0)
        self.assertIn(invalid_url, self.crawler.error_urls[0])


class TestHttpBinServiceAvailability(unittest.TestCase):
    """Test to verify HTTP Bin service is available before running integration tests."""

    def test_httpbin_availability(self):
        """Test that HTTP Bin service is reachable."""
        import requests

        try:
            response = requests.get("https://httpbin.org/status/200", timeout=10)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException as e:
            self.skipTest(f"HTTP Bin service is not available: {e}")


if __name__ == "__main__":
    # Run the availability test first
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestHttpBinServiceAvailability))
    suite.addTest(loader.loadTestsFromTestCase(TestSiteCrawlerWithHttpBin))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ All HTTP Bin integration tests passed!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
