"""
Unit tests for Site Crawler
"""

import unittest
from unittest.mock import Mock, patch

from main import SiteCrawler, main


class TestSiteCrawler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.base_url = "https://example.com"
        self.crawler = SiteCrawler(self.base_url, max_depth=2, delay=0.1)

    def test_init(self):
        """Test SiteCrawler initialization."""
        crawler = SiteCrawler("https://test.com", max_depth=5, delay=2.0)

        self.assertEqual(crawler.base_url, "https://test.com")
        self.assertEqual(crawler.domain, "test.com")
        self.assertEqual(crawler.max_depth, 5)
        self.assertEqual(crawler.delay, 2.0)
        self.assertEqual(len(crawler.visited_urls), 0)
        self.assertEqual(len(crawler.url_status), 0)

    def test_init_with_trailing_slash(self):
        """Test initialization with trailing slash in URL."""
        crawler = SiteCrawler("https://example.com/", max_depth=3)
        self.assertEqual(crawler.base_url, "https://example.com")

    def test_is_valid_url_same_domain(self):
        """Test URL validation for same domain URLs."""
        valid_urls = [
            "https://example.com/page1",
            "https://example.com/page2/",
            "https://example.com/subdir/page.html",
            "http://example.com/page",
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.crawler.is_valid_url(url))

    def test_is_valid_url_different_domain(self):
        """Test URL validation for different domain URLs."""
        invalid_urls = [
            "https://other.com/page",
            "https://sub.other.com/page",
            "http://external-site.com/page",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.crawler.is_valid_url(url))

    def test_is_valid_url_file_extensions(self):
        """Test URL validation for file extensions that should be skipped."""
        invalid_urls = [
            "https://example.com/file.pdf",
            "https://example.com/image.jpg",
            "https://example.com/script.js",
            "https://example.com/style.css",
            "https://example.com/archive.zip",
            "https://example.com/icon.ico",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.crawler.is_valid_url(url))

    def test_is_valid_url_skip_paths(self):
        """Test URL validation for paths that should be skipped."""
        invalid_urls = [
            "https://example.com/api/users",
            "https://example.com/admin/dashboard",
            "https://example.com/wp-admin/",
            "https://example.com/cgi-bin/script",
            "https://example.com/mail/inbox",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.crawler.is_valid_url(url))

    def test_is_valid_url_protocols(self):
        """Test URL validation for different protocols."""
        # Valid protocols
        self.assertTrue(self.crawler.is_valid_url("https://example.com/page"))
        self.assertTrue(self.crawler.is_valid_url("http://example.com/page"))

        # Invalid protocols
        self.assertFalse(self.crawler.is_valid_url("ftp://example.com/file"))
        self.assertFalse(self.crawler.is_valid_url("mailto:user@example.com"))
        self.assertFalse(self.crawler.is_valid_url("tel:+1234567890"))

    def test_extract_links(self):
        """Test link extraction from HTML content."""
        html_content = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://other.com/external">External</a>
                <a href="/page3.pdf">PDF File</a>
                <a href="/api/data">API</a>
                <a href="https://example.com/subdir/page">Subdir Page</a>
            </body>
        </html>
        """

        links = self.crawler.extract_links(html_content, "https://example.com/")

        expected_links = {
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/subdir/page",
        }

        self.assertEqual(links, expected_links)

    def test_extract_links_with_relative_urls(self):
        """Test link extraction with relative URLs."""
        html_content = """
        <a href="relative/page">Relative</a>
        <a href="./current/page">Current</a>
        <a href="../parent/page">Parent</a>
        """

        links = self.crawler.extract_links(html_content, "https://example.com/base/")

        expected_links = {
            "https://example.com/base/relative/page",
            "https://example.com/base/current/page",
            "https://example.com/parent/page",
        }

        self.assertEqual(links, expected_links)

    def test_extract_links_empty_content(self):
        """Test link extraction from empty HTML content."""
        links = self.crawler.extract_links("", "https://example.com/")
        self.assertEqual(links, set())

    def test_extract_links_no_links(self):
        """Test link extraction from HTML with no links."""
        html_content = "<html><body><p>No links here</p></body></html>"
        links = self.crawler.extract_links(html_content, "https://example.com/")
        self.assertEqual(links, set())

    @patch("main.requests.Session")
    def test_crawl_page_success(self, mock_session):
        """Test successful page crawling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<a href="/page1">Page 1</a>'

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Create crawler and crawl
        crawler = SiteCrawler("https://example.com", max_depth=1)
        crawler.session = mock_session_instance

        crawler.crawl_page("https://example.com/", 0)

        # Verify page was visited
        self.assertIn("https://example.com/", crawler.visited_urls)
        self.assertEqual(crawler.url_status["https://example.com/"], 200)
        self.assertEqual(crawler.url_depth["https://example.com/"], 0)

    @patch("main.requests.Session")
    def test_crawl_page_http_error(self, mock_session):
        """Test crawling page with HTTP error."""
        # Mock response with 404 error
        mock_response = Mock()
        mock_response.status_code = 404

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Create crawler and crawl
        crawler = SiteCrawler("https://example.com")
        crawler.session = mock_session_instance

        crawler.crawl_page("https://example.com/missing", 0)

        # Verify error was recorded
        self.assertIn("https://example.com/missing", crawler.visited_urls)
        self.assertEqual(crawler.url_status["https://example.com/missing"], 404)
        self.assertIn("https://example.com/missing", crawler.error_urls[404])

    @patch("main.requests.Session")
    def test_crawl_page_request_exception(self, mock_session):
        """Test crawling page with request exception."""
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = Exception("Connection failed")
        mock_session.return_value = mock_session_instance

        # Create crawler and crawl
        crawler = SiteCrawler("https://example.com")
        crawler.session = mock_session_instance

        crawler.crawl_page("https://example.com/failed", 0)

        # Verify failure was recorded
        self.assertIn("https://example.com/failed", crawler.visited_urls)
        self.assertEqual(crawler.url_status["https://example.com/failed"], 0)
        self.assertIn("https://example.com/failed", crawler.error_urls[0])

    def test_crawl_page_depth_limit(self):
        """Test that crawling respects depth limit."""
        crawler = SiteCrawler("https://example.com", max_depth=1)

        # Mock the session to avoid actual requests
        crawler.session = Mock()

        # Try to crawl beyond max depth
        crawler.crawl_page("https://example.com/deep", 2)

        # Should not be visited due to depth limit
        self.assertNotIn("https://example.com/deep", crawler.visited_urls)

    def test_crawl_page_already_visited(self):
        """Test that already visited URLs are skipped."""
        crawler = SiteCrawler("https://example.com")

        # Mock the session to avoid actual requests
        crawler.session = Mock()

        # Mark URL as visited
        crawler.visited_urls.add("https://example.com/visited")

        # Try to crawl the same URL again
        crawler.crawl_page("https://example.com/visited", 0)

        # Should not make a request since it's already visited
        crawler.session.get.assert_not_called()

    def test_generate_report(self):
        """Test report generation."""
        crawler = SiteCrawler("https://example.com")

        # Add some test data
        crawler.visited_urls.add("https://example.com/")
        crawler.visited_urls.add("https://example.com/page1")
        crawler.url_status["https://example.com/"] = 200
        crawler.url_status["https://example.com/page1"] = 404
        crawler.url_depth["https://example.com/"] = 0
        crawler.url_depth["https://example.com/page1"] = 1
        crawler.error_urls[404].append("https://example.com/page1")

        report = crawler.generate_report()

        # Verify report contains expected content
        self.assertIn("Site Crawler Report: https://example.com", report)
        self.assertIn("Total Pages Visited | 2", report)
        self.assertIn("HTTP 404 ERRORS", report)
        self.assertIn("https://example.com/page1", report)

    def test_generate_report_partial(self):
        """Test partial report generation."""
        crawler = SiteCrawler("https://example.com")

        report = crawler.generate_report(is_partial=True)

        # Verify partial report indicator
        self.assertIn("PARTIAL REPORT", report)

    def test_generate_report_empty_crawl(self):
        """Test report generation with no pages visited."""
        crawler = SiteCrawler("https://example.com")

        report = crawler.generate_report()

        # Verify report contains expected content even with no pages
        self.assertIn("Site Crawler Report: https://example.com", report)
        self.assertIn("Total Pages Visited | 0", report)

    def test_crawl_recursive_behavior(self):
        """Test recursive crawling behavior."""
        crawler = SiteCrawler("https://example.com", max_depth=2)

        # Mock responses for different pages
        def mock_get(url, **kwargs):
            mock_response = Mock()
            if url == "https://example.com/":
                mock_response.status_code = 200
                mock_response.text = '<a href="/page1">Page 1</a>'
            elif url == "https://example.com/page1":
                mock_response.status_code = 200
                mock_response.text = '<a href="/page2">Page 2</a>'
            elif url == "https://example.com/page2":
                mock_response.status_code = 200
                mock_response.text = '<a href="/page3">Page 3</a>'
            else:
                mock_response.status_code = 404
            return mock_response

        crawler.session = Mock()
        crawler.session.get.side_effect = mock_get

        # Start crawling
        crawler.crawl_page("https://example.com/", 0)

        # Verify pages were visited at correct depths
        self.assertIn("https://example.com/", crawler.visited_urls)
        self.assertIn("https://example.com/page1", crawler.visited_urls)
        self.assertIn("https://example.com/page2", crawler.visited_urls)

        # page3 should not be visited due to depth limit
        self.assertNotIn("https://example.com/page3", crawler.visited_urls)

        # Verify depths
        self.assertEqual(crawler.url_depth["https://example.com/"], 0)
        self.assertEqual(crawler.url_depth["https://example.com/page1"], 1)
        self.assertEqual(crawler.url_depth["https://example.com/page2"], 2)

    def test_crawl_method(self):
        """Test the crawl method."""
        crawler = SiteCrawler("https://example.com")

        # Mock the crawl_page method to avoid actual requests
        with patch.object(crawler, "crawl_page") as mock_crawl_page:
            crawler.crawl()

            # Verify crawl_page was called with the base URL
            mock_crawl_page.assert_called_once_with("https://example.com", 0)


class TestMainFunction(unittest.TestCase):
    """Test the main function and command line argument parsing."""

    @patch("sys.argv", ["main.py", "https://example.com"])
    @patch("main.SiteCrawler")
    @patch("builtins.print")
    def test_main_basic_usage(self, mock_print, mock_crawler_class):
        """Test main function with basic usage."""
        mock_crawler = Mock()
        mock_crawler_class.return_value = mock_crawler

        main()

        # Verify crawler was created with correct arguments
        mock_crawler_class.assert_called_once_with(
            base_url="https://example.com", max_depth=3, delay=1.0
        )

        # Verify crawl and generate_report were called
        mock_crawler.crawl.assert_called_once()
        mock_crawler.generate_report.assert_called_once_with(is_partial=False)

    @patch("sys.argv", ["main.py", "example.com", "--max-depth", "5", "--delay", "0.5"])
    @patch("main.SiteCrawler")
    @patch("builtins.print")
    def test_main_with_options(self, mock_print, mock_crawler_class):
        """Test main function with command line options."""
        mock_crawler = Mock()
        mock_crawler_class.return_value = mock_crawler

        main()

        # Verify crawler was created with correct arguments
        mock_crawler_class.assert_called_once_with(
            base_url="https://example.com", max_depth=5, delay=0.5
        )

    @patch("sys.argv", ["main.py", "https://example.com", "--output", "report.md"])
    @patch("main.SiteCrawler")
    @patch("builtins.open", create=True)
    @patch("builtins.print")
    def test_main_with_output_file(self, mock_print, mock_open, mock_crawler_class):
        """Test main function with output file."""
        mock_crawler = Mock()
        mock_crawler.generate_report.return_value = "Test Report"
        mock_crawler_class.return_value = mock_crawler

        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        main()

        # Verify file was opened and written to
        mock_open.assert_called_once_with("report.md", "w")
        mock_file.write.assert_called_once_with("Test Report")

    @patch("sys.argv", ["main.py", "https://example.com"])
    @patch("main.SiteCrawler")
    @patch("builtins.print")
    def test_main_keyboard_interrupt(self, mock_print, mock_crawler_class):
        """Test main function handling KeyboardInterrupt."""
        mock_crawler = Mock()
        mock_crawler.crawl.side_effect = KeyboardInterrupt()
        mock_crawler_class.return_value = mock_crawler

        main()

        # Verify partial report was generated
        mock_crawler.generate_report.assert_called_once_with(is_partial=True)
        mock_print.assert_any_call("\nCrawling interrupted by user")
        mock_print.assert_any_call("Generating partial report...")

    @patch("sys.argv", ["main.py", "https://example.com"])
    @patch("main.SiteCrawler")
    @patch("builtins.print")
    def test_main_general_exception(self, mock_print, mock_crawler_class):
        """Test main function handling general exceptions."""
        mock_crawler = Mock()
        mock_crawler.crawl.side_effect = Exception("Test error")
        mock_crawler_class.return_value = mock_crawler

        main()

        # Verify partial report was generated
        mock_crawler.generate_report.assert_called_once_with(is_partial=True)
        mock_print.assert_any_call("Generating partial report...")


if __name__ == "__main__":
    unittest.main()
