# Team Contribution Record

SRS v1.0 §1.8 items 1–2 and §1.10 item 17. Each member confirms their own row, and the git history must support every row.

| Member | Modules owned | Key files / folders | Commit days (1–5) | Can explain module (checked by / date) |
|---|---|---|---|---|
| Student 1: _name_ | Data engineering, Spark Steps 1–7 | `data_generator/`, `spark_jobs/` | | |
| Student 2: _name_ | Spark MLlib, Python pipeline, comparison | `python_pipeline/`, `models/` | | |
| Student 3: _name_ | Dashboards, recommendation engine, what-if | `src/`, `templates/`, `static/` | | |
| Student 4: _name_ | Backend, auth, database, export, deployment | `src/`, `database/` | | |
| Student 5: _name_ | _TBD_ | | | |
| Student 6: _name_ | Documentation, testing, evidence, submission | `documentation/`, `tests/`, `reports/` | | |

## How to fill "Commit days" from git

```bash
git shortlog -sne --all
git log --author="<name or email>" --date=short --pretty=format:"%ad %s"
```
