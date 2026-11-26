# Methodology 07: Agentic Programming

## 1. Results

The objective of this project is to forecast daily Capital
Bikeshare demand using calendar, weather, and historical demand
features while preventing target leakage and maintaining temporal
validity.

After accounting for missing calendar dates and lag warm-up,
714 observations remained. The dataset was divided chronologically
into 348 training observations from 2011, 182 validation
observations from the first half of 2012, and 184 test
observations from the second half of 2012.

The proposed feature was a temperature-humidity interaction,
calculated as temp * hum. The motivation was that the effect of
temperature on bicycle usage might depend on humidity, rather
than both variables contributing independently.

The following table presents the original before-and-after
feature experiment.

| Configuration | Model | Valid R² | Valid MAE | Test R² | Test MAE |
|---|---|---:|---:|---:|---:|
| Before | Mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | Ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | HGB | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After | Mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After | Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After | Ridge | 0.6493 | 829.9 | 0.5835 | 946.6 |
| After | HGB | 0.2129 | 1292.6 | -0.5867 | 2034.4 |

MAE is measured in daily rental counts. The before configuration
contains 14 features, while the after configuration contains 15.

The currently committed untransformed metrics reproduce the
baseline and Ridge results in the after configuration but report
HGB validation R² of 0.2399, validation MAE of 1276.7, test R²
of -0.4588, and test MAE of 1955.3. The cause of this discrepancy
has not been independently established. Differences in
scikit-learn versions are one possible explanation.

## 2. Headline finding

The primary finding is that methodological validity matters more
than achieving an apparently impressive prediction score.
The exact identity casual + registered = cnt makes a perfect
prediction score possible through target leakage, but such a
model cannot provide a meaningful forecast because the target
components are unavailable at prediction time.

Under a chronological evaluation, the mean baseline performs
poorly, with a test R² of -2.1441. This indicates that the
training-period average is not representative of demand during
the test period. Ridge performs substantially better because it
can extrapolate relationships learned from historical demand
and other predictors.

In contrast, histogram gradient boosting performs poorly on
the later test period. Its tree-based structure has difficulty
extrapolating beyond the demand levels represented in training.
The negative test R² therefore reflects the limitations of the
model under distribution shift rather than automatically
indicating a programming error.

The temperature-humidity interaction produced only a small
improvement in Ridge validation R², from 0.6475 to 0.6493,
an increase of 0.0018. This improvement was below the predefined
threshold of 0.01. The original HGB validation R² also decreased
from 0.2185 to 0.2129.

Consequently, the methodological recommendation was DROP.
The interaction implementation and its tests remain in the
repository, and the current committed metrics use the
15-feature configuration. Retaining the implementation should
not be interpreted as evidence that the interaction meaningfully
improves forecasting performance.

The experiment demonstrates why theoretically plausible
features should be evaluated against explicit numerical
criteria rather than accepted solely because an agent
successfully implements them.

## 3. Exercise 4: Target transformation

To investigate whether alternative target representations could
improve HGB performance, I evaluated four transformations against
an untransformed HGB reference model using the validation set.

All transformations were fitted using training information only,
and predictions were evaluated on the original rental-count scale.

| Model or transformation | Valid R² | Valid MAE | Change in R² |
|---|---:|---:|---:|
| Original HGB | 0.2399 | 1276.7 | 0.0000 |
| Log1p | 0.1649 | 1340.0 | -0.0750 |
| Square root | 0.1722 | 1337.9 | -0.0677 |
| Yeo-Johnson | 0.2051 | 1307.1 | -0.0348 |
| First-differencing | 0.6194 | 814.0 | +0.3795 |
| Ridge reference | 0.6493 | 829.9 | N/A |
| Persistence reference | 0.4507 | 900.6 | N/A |

Logarithmic, square-root, and Yeo-Johnson transformations all
performed worse than the untransformed HGB reference. These
transformations alter the distribution of the target but do not
directly resolve the difficulty of predicting demand levels
outside the training distribution.

First-differencing was substantially more effective. Instead
of predicting the absolute number of rentals, the model
predicted the difference between today's demand and yesterday's
observed demand:

    difference = cnt_today - cnt_yesterday

Predictions were reconstructed as:

    predicted_cnt_today = cnt_yesterday + predicted_difference

This representation is scientifically defensible for rolling
one-day-ahead forecasting because yesterday's observed demand is
available when predicting today's demand. It allows the model
to learn daily fluctuations rather than directly extrapolating
absolute demand levels.

To verify temporal alignment, all 348 training and 182 validation
one-day lag values were compared against actual counts from the
previous calendar date in the raw dataset. All 530 comparisons
passed. The training target reconstruction was also verified
numerically.

First-differencing increased HGB validation R² by 0.3795 and
reduced MAE by approximately 36.24%. Although it did not exceed
Ridge in R², it achieved a lower MAE of 814.0 compared with
829.9 for Ridge.

These findings suggest that the target representation can be
more important than increasing model complexity. However, the
result is limited to the validation period and assumes access
to the previous day's actual demand. It does not establish
performance for multi-day forecasting or the held-out test period.

The transformation experiment is therefore retained separately
in experiment_hgb_log.py, while reports/metrics.json contains
the untransformed pipeline results.

## 4. Exercise 5: Ridge vs persistence

Although Ridge achieves a higher test R² than persistence
(0.5835 compared with 0.5099), I would favor deploying the
persistence baseline for routine daily bike-sharing demand
forecasting. Persistence achieves a test MAE of 840.1 rentals,
compared with 946.6 for Ridge, meaning Ridge produces approximately
12.7% greater average absolute prediction error despite explaining
more variation in demand. Although Ridge outperforms persistence
on both validation metrics, its advantage does not consistently
generalize to the test period. From an operational perspective,
MAE is particularly meaningful because it directly represents the
magnitude of daily forecasting errors in rental counts. Persistence
also requires no model training, weather features, or parameter
estimation, making it simpler to maintain. Unless large forecasting
errors carry disproportionately higher operational costs, the
modest improvement in test R² does not provide sufficient
justification for deploying Ridge over persistence.

## 5. Attribution

The primary coding agent used in this project was Claude Code
connected to Ollama, using the local bikeshare-coder model derived
from qwen3.5:9b with a 65,536-token context window. ChatGPT was
also used for methodological guidance, debugging, code assistance,
documentation, and interpretation of experimental results.

The local coding agent assisted with the implementation and
testing of the temperature-humidity interaction, the raw-column
classification test, seeded fault experiments, the weather
encoder regression test, and initial target transformation
experiments. The final transformation script required additional
ChatGPT-assisted corrections to the first-differencing target
and calendar-based lag verification.

My responsibilities included executing and inspecting the
experiments, checking numerical results, evaluating whether
the proposed feature justified its inclusion, approving
methodological decisions, verifying tests, and managing the
repository's commit history.

Four controlled faults were investigated. The exercises
demonstrated that existing tests could detect forbidden
features and incorrectly aligned rolling means, but did not
initially detect an unknown weather category. A regression test
was subsequently added. The Bash-based raw-data probe also
demonstrated a limitation of hooks that monitor only Edit and
Write operations.

A custom seed-fault skill was created to formalize controlled
fault introduction, test verification, documentation, and
restoration of the original implementation.

The Claude Agent SDK was used to generate an automated audit
of the repository. The auditor reported no detected leakage,
valid temporal methodology, appropriate baseline reporting,
and reproducibility, with high confidence. These conclusions
represent the agent's assessment rather than an independent
guarantee of correctness.

The central lesson from this assignment is that successful
agent-generated execution is not sufficient evidence of
scientific validity. Explicit methodological constraints,
deterministic tests, baseline comparisons, and human review
remain necessary when using coding agents for data science.
