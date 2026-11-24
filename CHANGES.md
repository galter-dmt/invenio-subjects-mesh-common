# Changes

Version 0.5.0 (released 2026-11-24)

*Breaking changes*
- feat: use new delta generator - `galter_subjects mesh deltas` CLI changes
- remove unused (and incorrect) MeSHNewReader

*Other changes*
- lint: lint with ruff

Version 0.4.0 (released 2026-10-22)

- refactor!: switch from asciimesh to xmlmesh as source data
    * Leverage advantages of XML data dump (no separate qualifiers)
    * Also update interfaces
    * This is a breaking change in most APIs
- fix: account for malformed replace.txt file

Version 0.2.0 (released 2026-01-28)

- account for NLM quirks
- clean up cli.py implementation

Version 0.1.0 (released 2026-01-27)

- Initial public release
