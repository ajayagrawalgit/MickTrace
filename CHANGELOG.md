# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-26

### Added
- Initial release of Micktrace
- Library-first design with zero global state pollution
- Async-native logging with context variable support
- Structured logging by default with JSON/logfmt output
- Comprehensive type hints and error handling
- Context management for request tracing
- Bound loggers for consistent context injection
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
