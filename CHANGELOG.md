# Changelog

All notable changes to this project will be documented in this file.

## [2.0.4] - 2026-01-17
### Fixed
- Verified Trusted Publishing (OIDC) configuration with PyPI.
- Renamed CI workflow to `workflow.yml` to match PyPI expectations.

## [2.0.3] - 2026-01-17
### Changed
- **Renamed project to `redlock-ng`** to resolve PyPI naming conflict.
- Updated `pyproject.toml` and documentation to reflect new package name.

## [2.0.2] - 2026-01-17
### Fixed
- Resolved port binding conflict in CI/CD (removed conflicting `services` definition in GitHub Actions).

## [2.0.1] - 2026-01-17
### Fixed
- Fixed linting and typing errors (Ruff/Mypy) that were present in the initial 2.0.0 tag.
- Relaxed line length to 120 and enabled `pydantic.mypy`.

## [2.0.0] - 2026-01-17
### Added
- **Modernization Rewrite**: Complete rewrite of the library.
- **Asyncio Support**: Added `AsyncRedlock` using `redis-py` async client.
- **Type Safety**: fully typed codebase with strict Mypy compliance.
- **Robustness**: Added drift calculation, retry jitter, and proper quorum logic.
- **Testing**: Added property-based testing (Hypothesis) and network fault injection (Toxiproxy).
- **Tooling**: Switched to Poetry for dependency management.
