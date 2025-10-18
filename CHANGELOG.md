# MickTrace Changelog - Python Logging Library

All notable changes to MickTrace Python logging library will be documented in this file.

**Created by [Ajay Agrawal](https://github.com/ajayagrawalgit) | [LinkedIn](https://www.linkedin.com/in/theajayagrawal/)**

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2025-10-19 - Update GCP Handler and Version Bump
### Added
- **GCP Handler** - Added `GoogleCloudHandler`, `GCPHandler`, and `AsyncGCPHandler` as user-friendly aliases for Stackdriver handlers

### Changed
- **Handler Type Support** - Added support for `"gcp"` handler type in configuration (in addition to existing `"stackdriver"`)
- **New Handler Files** - Created `gcp.py` and `async_gcp.py` modules for better discoverability and remove CNAME from the root repository
- **Acknowledgments** - Added professional acknowledgments section for integration mentions in README

### Fixed
- **README Examples** - Updated Google Cloud Logging examples to use `"gcp"` handler type instead of `"stackdriver"`
- **Handler Exports** - Updated `handlers/__init__.py` to export GCP handler aliases


## [Unreleased] - 2025-10-18 - GCP Handler Alias & Documentation
### Added
- **GCP Handler Alias** - Added `GoogleCloudHandler`, `GCPHandler`, and `AsyncGCPHandler` as user-friendly aliases for Stackdriver handlers
- **Handler Type Support** - Added support for `"gcp"` handler type in configuration (in addition to existing `"stackdriver"`)
- **New Handler Files** - Created `gcp.py` and `async_gcp.py` modules for better discoverability
- **Acknowledgments** - Added professional acknowledgments section for integration mentions in README

### Changed
- **README Examples** - Updated Google Cloud Logging examples to use `"gcp"` handler type instead of `"stackdriver"`
- **Handler Exports** - Updated `handlers/__init__.py` to export GCP handler aliases

## [Unreleased] - 2025-10-18 - CI/CD Enhancements
### Added
- **Automated linting workflow** - GitHub Actions workflow for autopep8 linting on push and pull requests
  - Runs autopep8 checks automatically on `main` and `add-autopep8-wf` branches
  - Provides helpful PR comments with fix instructions when linting fails
  - Includes pip dependency caching for faster CI runs
  - Confirms successful linting with positive feedback comments

### Changed
- Enhanced CI/CD pipeline with automated code quality checks
- Improved developer feedback loop with actionable linting messages

---

## [1.0.1] - 2025-10-10 - PEP8 Compliance & Tooling Updates
### Changed
- **PEP8 compliance improvements** - Enhanced code formatting and style consistency across the codebase
- **Package management enhancements** - Added automated package update scripts for better maintenance

### Fixed
- Code style consistency issues resolved
- Improved test coverage and reliability
- Enhanced async example implementations

### Added
- Automated package update utilities
- Enhanced development tooling and scripts
- Improved code quality checks

---

## [1.0.3] - 2025-10-10 - Datadog Integration & Packaging
### Added
- Built-in Datadog integration: `DatadogHandler` added to `micktrace.handlers` for easy logs forwarding to Datadog Logs Intake (HTTP).
- Optional extra `datadog` in `pyproject.toml` now installs `datadog` and `requests` when users run `pip install micktrace[datadog]`.
- Example: `examples/datadog_example.py` demonstrating how to configure `micktrace` to send structured logs to Datadog using `DATADOG_API_KEY` environment variable.

### Changed
- Logger factory now recognizes handler type `datadog` when provided in configuration dictionaries.

### Fixed
- Cleanup of temporary test artifacts and improved import-safety for optional integrations.

---

## [1.0.0] - 2025-01-01 - Production Release
### Added - Python Logging Features
- **Async-native Python logging** with sub-microsecond overhead when disabled
- **Structured logging by default** with JSON, logfmt, and custom formatters
- **Zero-configuration setup** - works immediately out of the box
- **Library-first design** - no global state pollution, safe for Python libraries
- **Context propagation** - automatic request/trace context across async boundaries
- **Cloud platform integrations** - AWS CloudWatch, Azure Monitor, Google Cloud Logging
- **Analytics integrations** - Datadog, New Relic, Elasticsearch, Prometheus
- **Hot-reload configuration** - change log levels and formats without restart
- **Comprehensive testing** - 200+ tests ensuring production reliability
- **Full type safety** - complete type hints for excellent IDE support
- **Performance optimized** - memory efficient with automatic cleanup
- **Production ready** - thread-safe, async-safe, error resilient
- Memory handler for testing support
- Environment variable configuration
- Hot-reload configuration support
- Multiple output formats (JSON, logfmt, structured, simple)
- Comprehensive test suite with 100% core functionality coverage

### Features
- Zero configuration required for libraries
- Sub-microsecond overhead when disabled
- Thread-safe and multiprocessing safe
- Automatic caller information tracking
- Exception logging with full traceback capture
- Level-based filtering
- Extensible handler and formatter system
- Python 3.8+ compatibility with proper typing

### Documentation
- Comprehensive README with examples
- API documentation with type hints
- Usage examples for all major features
- Integration guides for libraries and applications
- Performance optimization tips

