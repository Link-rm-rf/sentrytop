# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-30

### Added
- **Core TUI:** Initial release of the `rich`-based Python terminal interface.
- **Producer/Consumer Pipeline:** Non-blocking async reading of stdout/stderr from the correlator.
- **Installation Script:** Automated dependency resolution and systemd service generation via `install.sh`.
- **Keyboard Controls:** Added `p` (pause), `v` (verbose), and `q` (quit) hotkeys without breaking terminal state.
- **Mock Correlator:** Added a mock generator (`--mock`) and a bash-based test correlator for integration testing.

### Changed
- Refactored `sentrytop_cli.py` to use exhaustive type hints, rigorous docstrings, and a centralized `CONFIG` dictionary.
- Optimized UI rendering tick-rate and added `deque` limits to prevent OOM errors over long uptimes.

### Fixed
- Addressed `psutil` exceptions missing in minimal environments.
- Handled `ConsoleError` from terminal resizing.
- Prevented unhandled stack traces bleeding into the console interface.

## [0.9.0] - 2026-03-15 (Pre-Release)

### Added
- Experimental C collector for `/proc` parsing.
- Experimental Java 21 engine utilizing Virtual Threads for correlation.
