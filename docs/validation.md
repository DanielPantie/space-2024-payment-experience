# Validation record

The release package was extracted into a clean directory with no raw data.
`python scripts/run_analysis.py` downloaded the ECB files, verified the CSV
checksum and successfully rebuilt the aggregate tables, figures, report,
10-page PDF and executed notebook. All eight tests then passed.

## Checks completed

- The source CSV contains 40,981 unique respondents and 18 countries.
- Source checksum: `0031ba01493a3e800907adaf83a9d457f9f1bd1cfc2e8ff3842e69ed8ba28b99`.
- Weights are positive and nonmissing.
- Multi-select exclusive responses and the adoption answer limit were checked.
- Synthetic tests distinguish selected, unselected, skipped and unknown answers.
- Weighted arithmetic, multi-answer unions, empty groups and weight-scale invariance pass.
- Headline estimates match source regression checks; country weights and the preference partition reconcile.
- All nine notebook code cells executed, with no error or stderr outputs.
- All ten PDF pages were rendered and visually reviewed. Individual PNG/SVG charts were also reviewed.
- The ZIP contains no raw ECB CSV/XLSX files, virtual environment or Python cache files.

## Scope of this evidence

The clean run used the dependency versions pinned in `requirements.txt` in
the preparation environment. It does not establish results in every Python
or operating-system version. PDF binary files can differ across runs because
their metadata includes creation time; the analysis tables and slide values
are the reproducible content.

These checks verify the implementation and its internal consistency. They
do not establish causal validity, eliminate survey selection bias or provide
a full survey-design variance estimate.
