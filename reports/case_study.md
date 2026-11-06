# Customer experience in European payments

## Business question

Where do consumers encounter payment friction, and what should a payment provider investigate or test next?

This is an independent analysis of the **ECB SPACE 2024 public-use file**, covering **40,981 consumers in 18 countries**. It studies consumers' payment experiences, choices and stated adoption factors. It does not measure merchant satisfaction with a terminal provider, brand-level service quality, NPS, retention or revenue impact.

## Executive findings

| Measure | Weighted share | Valid respondents |
| --- | --- | --- |
| Any in-store technical problem | 23.2% | 39404 |
| Preferred method unavailable or restricted | 23.6% | 38719 |
| Any online payment difficulty | 18.0% | 13884 |
| Prefer cashless payments | 57.6% | 40795 |
| Any privacy concern | 64.4% | 38579 |

All percentages use the supplied **Gross_weight** and a valid response base specific to the question. The results refer to the countries in this public file. They are not the ECB's full 20-country euro-area estimates.

1. **Preference and access do not always align.** 57.6% prefer cashless payments if offered a choice. Separately, 23.6% reported that their preferred payment method was unavailable or restricted at least once in the previous month. These figures describe different questions and populations; subtracting them would be meaningless.
2. **In-store problems are widespread enough to investigate.** 23.2% reported at least one technical problem in the past month. Card problems reached 14.3%, mobile problems 7.7% and cash self-checkout problems 4.0%. The common base is 39,404 valid respondents, rather than users of each method. Higher exposure to a method can produce more reports. These are not per-transaction failure rates.
3. **Online friction is broader than entering payment details.** 18.0% of 13,884 valid online-difficulty respondents reported an issue with the diary-day payments. Entering details was selected by 8.0%, banking-app redirect failures by 4.0%, and late one-time passwords by 3.2%. Multiple issues can overlap.
4. **Security and ease are almost tied as stated adoption factors.** Higher security (38.0%) and easier use (37.8%) lead the list, followed by lower price (32.6%). Innovative features reach 11.6%. The 0.23 percentage point difference between security and ease does not justify a claim that one clearly dominates the other. These are stated motivations, not proven adoption effects.
5. **Younger respondents report more in-store technical problems.** The weighted shares are 28.6% for ages 18-34, 23.9% for 35-54, and 19.7% for 55+. Holding country mix fixed produces very similar estimates (28.6%, 23.8%, 19.7%). This does not control for method use, payment frequency or reporting behaviour. It does not show that younger customers are less capable.

## Decisions and tests supported by the evidence

| Evidence | Proposed test or investigation | Success measure to collect | Main qualification |
| --- | --- | --- | --- |
| 23.2% report an in-store technical issue | Link merchant support cases to terminal, network and authorisation logs; identify recurring incident types | Incident recurrence, recovery time and transaction completion from operational logs | Survey responses cannot isolate the underlying cause or provider |
| 12.9% report card/mobile non-acceptance | Investigate acceptance coverage and clarity of minimum-payment policies in target merchant segments | Customer ability to use a preferred method, tracked with a clearly defined question | Merchant behaviour and payment-method availability differ from technical failures |
| 8.0% report payment-detail entry problems; 4.0% app redirects | Test form validation, clear error messages, and recovery after an authentication failure | Checkout completion, repeat attempts, authentication success and support contacts | Outcomes need an operational experiment, not an assumed uplift from survey percentages |
| Security and ease both reach about 38% as adoption factors | Test clearer security explanations alongside simpler task flows | Comprehension, task completion and take-up in a controlled pilot | Avoid inferring actual adoption from stated intentions |

These are hypotheses for investigation, not forecasts of ROI. The survey contains no direct revenue, churn or provider-cost outcome with which to quantify returns.

## How the survey works

SPACE combines a one-day payment diary with questions about usual behaviour and attitudes. Recruitment and follow-up used telephone interviews and web panels. Fieldwork spans September-November 2023 and April-June 2024. The public-use file is wide: one row per person, with repeated payment fields for diary transactions.

The file contains the 18 countries surveyed through Ipsos. Germany and the Netherlands ran separate surveys and are absent here. Czechia is outside SPACE's euro-area coverage. Portugal, Slovakia, Croatia, Slovenia and the Baltic countries are available, but this file does not support a Czech or complete CEE conclusion.

This case study deliberately uses respondent-level modules first. Transaction shares would require reshaping the repeated diary fields, a carefully defined transaction scope and an appropriate weighting approach. They are an extension rather than a necessary part of this consumer-experience analysis.

## Preparation and metric construction

1. Download the official ZIP and verify the CSV SHA-256. Preserve the original files in `data/raw/`.
2. Drop only the exported row-index column from the analysis copy. Preserve all original survey values.
3. Check respondent IDs, country coverage, positive nonmissing weights, special codes and multi-select consistency.
4. Create explicit valid-base flags. Retain an unknown outcome as `NA` rather than `False`.
5. Calculate a weighted share as `100 * sum(weights of positive valid responses) / sum(weights of all valid responses)`.
6. Export full-precision estimates and real response counts. Round only when communicating.

The source has **0 duplicate respondent IDs**, **0 missing weights** and **0 nonpositive weights**. The audit found no conflicts between the exclusive 'no problems' response and a selected problem, and no adoption-response rows with more than three selected options.

The all-zero issue matters: **1,173** rows have zeros for every in-store technical-problem option, and **404** have a skipped/missing technical-problem set. An all-zero set does not select the explicit 'no issues' option. Its reason cannot be recovered reliably from these binary fields, so it is excluded from the primary base. For online difficulties, **127** rows have an all-zero set and **26,970** are all missing. See `audit.json` for every question group.

## Reliability and sensitivity

- **Weighting:** Compare `metrics_weighted.csv` and `metrics_unweighted.csv`. The weighted in-store issue estimate is 23.2%; the unweighted estimate is 22.6%. Country sample sizes are not proportional to country populations, so the pooled unweighted share is not a population estimate.
- **Weight concentration:** For in-store technical issues, Kish effective n is about 12,675, versus 39,404 actual valid respondents. Kish n diagnoses concentration of weights only. It is not a complete design-based precision estimate.
- **Denominator sensitivity:** `denominator_sensitivity.csv` contrasts primary valid-base percentages with positive reports per eligible record, retaining non-substantive responses in the alternative denominator. The latter is not a problem-rate estimate. This check exposes rather than resolves uncertainty about missing responses.
- **Country mix:** Country-standardized age comparisons retain the overall valid population's country mix. They address one compositional difference and do not provide causal adjustment.
- **Survey mode:** In-store technical issues are reported by 25.7% in the telephone sample and 19.8% in the web sample. Selection, composition and interview mode may all contribute. Respondents were not randomly assigned to mode, so this gap is not an estimated interview-mode effect.
- **Uncertainty:** No formal confidence intervals, p-values or significance claims are supplied. The web component is non-probability sampling, and the public file lacks the full information needed for a defensible design-based variance analysis. Small subgroup results need additional care.

## Learning notes

**Prevalence versus failure rate:** 23.2% reporting at least one problem over a month does not mean 23.2% of payments failed. We do not know the total number of payment attempts corresponding to that recall period.

**Multiple answers:** One person can select both a card and mobile problem. Add the union of people for 'any issue', not the separate percentages. The script uses `.any(axis=1)`.

**Skip versus No:** A blank online response may reflect no online payment on the diary day. That respondent does not belong in the online-problem denominator. An explicit 'no difficulties' answer does belong.

**Period versus edition:** 'SPACE 2024' includes 2023 fieldwork. The survey rounds are separate cross-sectional samples; a round comparison is not individual-level change or a clean time trend.

**CX construct:** SPACE captures friction, access, preferences and perceptions. It does not supply the overall-satisfaction outcome that would support a conventional satisfaction-driver model. Avoid inventing a composite satisfaction score or NPS from unrelated questions.

## Sources

- [ECB SPACE landing page](https://www.ecb.europa.eu/stats/ecb_surveys/space/html/index.en.html)
- [Official microdata, codebook and labels](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/2024_SPACE_microdata.en.zip)
- [Questionnaire, Annex A](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_a.en.pdf)
- [Methodology, Annex B](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_b.en.pdf)
- [ECB use and attribution conditions](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html)

Source data: European Central Bank. All figures here are independent calculations using the public-use file and the explicit bases above. The analysis is not an ECB publication or endorsement. Raw data are downloaded separately; original ECB materials retain their source rights.
