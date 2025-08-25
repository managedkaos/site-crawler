# Testing

## Unit Tests

Run the comprehensive unit test suite:

```bash
python -m unittest test_main.py -v
```

## Integration Tests with HTTP Bin

The project includes integration tests that use the [HTTP Bin](https://httpbin.org/) service to test the crawler with real HTTP responses for different status codes.

```bash
python test_with_httpbin.py
```

These tests verify:

- HTTP status code handling (200, 404, 500, 403, 418, etc.)
- Redirect handling (301, 302)
- Error handling for invalid URLs
- Domain validation
- Report generation with real data
- Delay respect between requests

**Note**: These tests require an internet connection to reach httpbin.org.
