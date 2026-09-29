# AI Usage Declaration

SRS 1.8 items 13-16. Each team member adds a row to the table and their own section below.

| Tool | Purpose | Files | Verified by |
|---|---|---|---|
| ChatGPT | Scaffolding Flask + RBAC + JWT boilerplate | backend skeleton, docs | Student 4A |


## Not AI-generated
Final predictions, classifications, recommendations, forecasts produced by team pipelines.

## Student 4A

### Modifications
- Reviewed and adapted every generated file.
- Verified RBAC matrix against SRS 1.6 (FR i-ii).
- Wrote and ran 21 tests locally.

### Testing performed
- All endpoints tested via curl.
- pytest suite 21 passed.

## Student 6 (Amal Rashad)

### Modifications
- Reviewed every generated file against the SRS and the repository.
- Kept the team's existing tests/conftest.py and pytest.ini; added the data fixtures separately in tests/data_fixtures.py.
- Fixed a syntax error caused when appending the fixture import to conftest.py.
- Registered the clean_layer marker in pytest.ini.
- Found missing packages in requirements.txt and reported them to Student 4.

### Testing performed
- Regenerated the full dataset (seed 42) in GitHub Codespaces, Python 3.14.
- python tests/tools/run_tests_with_report.py: 146 passed, 0 failed, 18 skipped (clean-layer tests wait for Spark cleaning).
- Generated independent quality counts (reports/evidence/) and sample data (sample_data/raw/).