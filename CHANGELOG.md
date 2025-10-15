# Changelog

All notable changes to this project will be documented in this file.

## [0.0.2]

### Added
- Pre-push hook
- `SceneStats` class
- Named functions for running 3rd party dependencies
- CLI tools related to settings: tomosar settings, tomosar reset, tomosar verbose, tomosar set, tomosar clear, tomosar add, tomosar remove

### Changed
- Updated `tomosar setup` to install pre-push hook
- Added dict-like methods to Masks object
- Updated __init__ to match new named functions for 3rd party dependencies
- Moved from environment variables to local settings (`.local/settings.json`)
- Changed `data_path()` to general purpose resource context manager named `resource()`

### Fixed
- Bug in loading Masks

## [0.0.1] - 2025-10-09

### Added
- Initial alpha release