# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2021-04-16

### Changed
- Orbit dependency

## [0.3.0] - 2021-04-12

### Added
- Orbit wrapper

## [0.2.9] - 2021-04-09

### Added
- Store step

## [0.2.8] - 2021-04-06

### Added
- Adding numpy style docstrings to public methods and modules.

## [0.2.7] - 2021-03-29

### Changed
- Changed the link format of the references.md file.

## [0.2.6] - 2021-03-22

### Added
- Added `soam/db_migrations` and `test` to the exclude list of `interrogate`.

## [0.2.5] - 2021-03-22

### Changed
- Updated the README.md file.

## [0.2.4] - 2021-03-17

### Added
- `interrogate` to check docstring coverage.

## [0.2.3] - 2021-03-16

### Added
- Issue templates created.

## [0.2.2] - 2021-03-16

### Added
- `CONTRIBUTING.md` added

## [0.2.1] - 2021-03-16

### Changed
- Pinned SQLAlchemy version.

## [0.2.0] - 2021-03-15

### Added
- Prophet model wrapper from `pomopt` project.
- `add_future_dates` utils to add prediction dates onto time_series DataFrames.
- New tests for `Forecaster` module.

### Changed
- Forecaster inteface, simplified Forecaster task arguments.

### Removed
- Darts integration.

## [0.1.7] - 2021-03-15

### Added
- `.coveragerc` to set a min coverage percentage.

## [0.1.6] - 2021-03-12

### Fixed
- Changed dev depencency: `bump` to `bump2version`.
- Changelog previous number from `0.1.4` to `0.1.5`.

## [0.1.5] - 2021-03-11

### Fixed
- Refactor PDF reporting

## [0.1.4] - 2021-03-10

### Added
- `all` and `report` extras

## [0.1.3] - 2021-03-10

### Fixed
- Change doble quotes to single in SoaM version to fix CI.
- Fix missing bracket in PyPI badge at README.dm file.

## [0.1.2] - 2021-03-10

### Added
- Removed legacy `statsmodels` dep.

## [0.1.1] - 2021-03-08

### Added
- CHANGELOG.md file.
- Check version update in CI config.
- Include TAGs release.
- Upload SoaM package to PyPI from CI job.
- Pypi badge for current version.

### Changed
- Update CI configuration file to use stages.
