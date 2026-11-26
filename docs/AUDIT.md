# Exercise 3: Peer Leakage Audit

## Repository and audit configuration

- Date: 2026-11-25
- Repository: https://github.com/randonDsc/bikeshare-open
- Audited commit: b0c0c59
- Agent: leakage-auditor
- Model: bikeshare-coder (Qwen 3.5 9B via Ollama)
- Scope: Entire repository implementation, not only the latest diff.

The initial background-subagent attempt was interrupted by an API
error. The audit was subsequently completed by launching Claude Code
directly with --agent leakage-auditor. The peer repository's source
files and committed metrics were not modified.

## Verbatim auditor output

Audit Verdict

All five methodology checks pass. The repository correctly implements temporal forecasting guardrails:

1. Target leakage: ✓ No forbidden columns (casual, registered, cnt) in feature set; lags use .shift(1) before aggregation (lines 78-83 in features.py); tests verify lag correctness (test_leakage.py).
2. Temporal ordering: ✓ Split is date-based, not random (lines 128-134 in train.py); all .fit() calls use only training data (lines 197, 228); LAG_WARMUP = 28 is a row-loss bound, not a lag construction parameter (line 84).
3. Calendar gaps: ✓ Gap-free calendar via reindex_to_calendar using pd.date_range(..., freq="D") (lines 49-55 in features.py); lags computed after reindexing.
4. Silent row loss: ✓ Only 56 rows lost (exactly LAG_WARMUP + LAG_WARMUP * missing_days, which is 28 + 28×1 = 56); bound asserted in test_contract.py line 74; no other unbounded .dropna().
5. Unreported baseline: ✓ Both mean baseline (R² = -0.69 valid, -1.77 test) and persistence baseline (R² = 0.45 valid, 0.51 test) reported alongside ridge (R² = 0.62 test) and hgb (R² = -0.46 test). The negative R² on hgb test is correctly exposed.

Final assessment: No findings that change numbers or invalidate conclusions. Implementation complies with all five methodology checks.

## Independent verification

I independently inspected the relevant source code, configuration,
decision log, and committed metrics. Because two shell commands
failed during the agent's audit, I also ran a separate read-only
diagnostic using load_raw(), build_features(), feature_columns(),
and temporal_split().

The diagnostic returned:

- Raw rows: 728
- Processed rows: 672
- Rows lost: 56
- LAG_WARMUP: 28
- Forbidden features: none
- Number of features: 15
- Training rows: 306
- Validation rows: 182
- Test rows: 184

The observed row loss agrees with the expected 28-day warm-up
and the 28 days following the missing calendar date. The feature
set and split sizes also agree with reports/metrics.json.

The committed, untransformed model scores are:

| Model | Valid R2 | Valid MAE | Test R2 | Test MAE |
|---|---:|---:|---:|---:|
| Mean | -0.6894 | 1877.3 | -1.7717 | 2659.6 |
| Persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Ridge | 0.6839 | 777.5 | 0.6239 | 879.3 |
| HGB | 0.2415 | 1296.6 | -0.4600 | 1952.4 |

These results confirm the auditor's reported numerical claims.
The metrics were inspected rather than regenerated.

## My verdict

I agree with the auditor's conclusion regarding the five
implementation checks. The target and its arithmetic components
are excluded from the feature set, lagged demand features are
constructed after calendar reindexing, the rolling averages
exclude the current day's target, and model fitting uses only
training observations. The observed row loss is consistent with
the longest historical window, and both required baselines are
reported alongside the fitted models.

However, I identified an additional experimental integrity concern
that the auditor did not report. In src/train.py, lines 198-199
and 221-224, the target transformation evaluation predicts and
scores both validation and test observations. The standard model
evaluation at lines 228-235 also includes the test split.

The teammate's docs/DECISIONS.md explicitly acknowledges that
test-set scores were printed during Exercise 4 and that an earlier
implementation ignored the --out argument and overwrote the
production metrics. The output-path issue was subsequently fixed.
The teammate also states that no methodological decisions were
based on the prematurely revealed test scores.

Although this does not establish target leakage or demonstrate
that the final numerical results are inflated, it weakens the
strict independence of the test set as a final evaluation.
The minimal improvement would be to introduce a validation-only
evaluation mode for feature and target transformation experiments,
with test evaluation enabled explicitly only after methodological
decisions have been finalized.

Overall, I accept the five implementation checks and find no
confirmed numerical error in the committed results based on the
available evidence. My acceptance is qualified by the documented
premature test-set exposure. The auditor was useful for checking
implementation-level safeguards, but independent human review
was necessary to identify this broader methodological limitation.
