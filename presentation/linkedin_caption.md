How often does the payment experience fall short of what consumers need?

For this case study, I analysed the ECB's SPACE 2024 public-use data in Python:
40,981 consumers across 18 countries.

Among the findings:

- 23% of valid respondents reported an in-store technical payment problem at least once in the past month.
- 24% encountered a restriction on their preferred payment method.
- Security and ease of use were almost tied as the leading stated reasons to try a new payment solution.

The analysis also shows why survey definitions matter. Skipped answers are
different from “no problems”, multi-answer questions can overlap, and the
right denominator changes from one question to the next.

The carousel connects the findings to questions payment providers could
investigate next. The accompanying Python project includes the executed
notebook, metric definitions, sensitivity checks and reproducible code.

Source: European Central Bank, SPACE 2024. These are my weighted calculations
for the 18-country public-use file, which excludes Germany and the Netherlands.
They are descriptive findings, rather than transaction failure rates or
causal estimates.

#Payments #CustomerExperience #DataAnalytics #Python #SurveyResearch

---
Publishing note: add your real GitHub repository URL after uploading the project.
Review and run the notebook before posting. This note is not part of the caption.
