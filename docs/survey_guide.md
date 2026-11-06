# Learning to work with SPACE 2024

## 1. Understand what one row means

Each row represents one respondent. The original CSV contains 260 columns:
259 documented variables and one exported row index. Repeated columns such as
`QA5A_1` and `QA5A_2` describe separate diary payments made by the same person.
They do not make the source one-row-per-transaction.

The case study focuses on respondent-level experience and attitudes. A diary
transaction analysis is a separate extension requiring a long-format table.

## 2. Read questions before choosing metrics

| Module | Variables used here | What it measures |
| --- | --- | --- |
| Acceptance | QA9_1 to QA9_5 | Preferred method unavailable, restricted, always available, or no in-store payments |
| In-store technical problems | QA10_1 to QA10_4 | Past-month card, mobile, self-checkout problems, or no issues |
| Online difficulties | QB7_1, QB7_21 to QB7_26, QB7_3 | Problems with diary-day online payments, or no difficulties |
| Payment preference | QQ3 | Cash, cashless or no clear preference |
| Online authentication | QB8 | Credentials, extra verification or biometrics |
| Privacy | QQ16_1 to QQ16_4 | Privacy concerns, no concern, or no digital payments |
| Adoption | QQ18_1 to QQ18_10 | Up to three factors encouraging a new solution, or no interest |
| Segmentation | COUNTRY, AGE, D1, FIELD, ROUND | Country, age, gender, interview mode and fieldwork round |
| Survey weighting | Gross_weight | Final combined pan-European grossing weight |

Use `docs/question_dictionary.csv` for the original question text and options.
Use `docs/metric_dictionary.csv` for the analysis-specific bases and outcomes.

## 3. Separate three reasons for an empty-looking answer

An **explicit No** selects the “no issues” option. It is a real, valid negative
outcome for an any-problem metric.

A **skip** means a question may not apply. People who did not report an online
payment on the diary day are outside that online-difficulty question's scope.

An **all-zero multi-select set** selects none of the substantive options. It
does not select “no issues” either. The public file does not identify its
precise reason reliably. Keep it outside the primary base.

For example, a question with card, mobile, cash self-checkout and no-issue
columns must include at least one selected option to count as substantive.

```python
issue_columns = ['QA10_1', 'QA10_2', 'QA10_3']
response_columns = issue_columns + ['QA10_4']
valid = raw[response_columns].eq(1).any(axis=1) & raw.QA9_5.ne(1)
any_issue = raw[issue_columns].eq(1).any(axis=1)
```

Codes `999998` and `999999` usually mean refusal and don't know, rather than
extreme values. `999997` is a special skip/non-event code in several modules.
Decode each question from its dictionary. Never replace every zero in the
dataset with missing: zeros are legitimate non-selection or No codes.

## 4. Build the numerator and denominator together

For a weighted problem prevalence:

1. Select valid, in-scope respondents.
2. Mark which of those respondents report the problem.
3. Sum the weights for positive respondents.
4. Divide by the sum of weights for all valid respondents.

Suppose one respondent with weight 1 reports a problem and another with
weight 3 reports no problem. The unweighted share is 50%, but the weighted
share is 25%. In both cases the actual response count is **n = 2**.

Gross weights are not extra survey responses. A normalized version of the
same weights produces the same percentage. The synthetic tests verify this.

## 5. Respect multi-answer questions

A person who selects a card problem and a mobile problem belongs once in the
any-problem numerator. Adding the separate shares double-counts that person.
The component percentages may sum to more than the any-problem share.

Adoption factors also overlap. About 38% selecting ease of use and about 38%
selecting security does not imply 76% selecting one or the other. The union
needs a separate respondent-level calculation.

## 6. Distinguish person, payment and period

“23% reported a problem at least once in the past month” does not mean 23% of
transactions failed. The survey does not supply a matched denominator of
payment attempts for that monthly recall question.

Do not compare a monthly in-store problem rate directly with a diary-day
online difficulty rate as if the time exposure were equal.

Similarly, cashless **preference** does not measure cashless transaction
**usage**. Different questions answer different business questions.

## 7. Compare groups without overclaiming

Age and country groups differ in how often they pay, which methods they use,
their income, exposure and reporting. Descriptive differences identify where
to investigate. They do not isolate an effect of age or nationality.

The project holds country mix fixed for one age comparison. The result
barely changes, but other explanations remain. Survey mode also shows large
differences. Telephone and web samples were not randomly assigned, and the
web sample uses a non-probability panel.

Kish effective sample size measures concentration of weights. It does not
account for the complete survey design or solve panel-selection bias.

## 8. Tell the business story

A useful finding has four parts:

> **Evidence:** 8.0% of valid online-difficulty respondents reported payment-detail entry problems.
> **Interpretation:** data entry is one plausible point of friction in checkout.
> **Next test:** assess form validation and recovery using checkout telemetry and usability testing.
> **Limit:** the survey does not identify a causal effect or predict revenue uplift.

The strongest carousel statements summarize evidence. Recommendations
should identify a test, its owner and the success measure needed next.

## Suggested learning sequence

1. Read the codebook rows for QA10 and reproduce its valid response count.
2. Calculate the in-store issue share without weights, then with weights.
3. Repeat for Portugal or Slovakia and explain the new denominator.
4. Compare one multi-answer component with the respondent union.
5. Read the sensitivity outputs before choosing a headline.
6. Review every carousel claim against its metric and reference period.

The notebook follows this sequence and contains the executed outputs.
