# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- 2026-11-20: DROP test_temp_hum_interaction (temp * hum): Added and tested the temperature-humidity interaction to determine whether it improves bike-sharing demand prediction. Ridge validation R² increased from 0.6475 to 0.6493 (+0.0018), while HGB validation R² decreased from 0.2185 to 0.2129 (-0.0056). The Ridge improvement was below the 0.01 threshold, so the feature is not worth keeping in the final model. All 17 tests passed.
- 2026-11-23: Reject log1p, square-root, and Yeo-Johnson target transformations: all reduced validation R^2 compared with untransformed HGB (0.2399 -> 0.1649, 0.1722, and 0.2051).
- 2026-11-23: Use first-differencing experimentally: predicting daily changes mitigates the need for HGB to extrapolate absolute demand. Validation R^2 0.2399 -> 0.6194, MAE 1276.7 -> 814.0.
- 2026-11-23: Verify first-differencing against raw calendar dates: all 530 training and validation lag values matched the previous day's actual count, supporting leakage-free one-day-ahead target reconstruction.
- 2026-11-23: Retain the untransformed production pipeline and saved metrics: first-differencing is competitive with ridge (R^2 0.6194 vs. 0.6493, MAE 814.0 vs. 829.9), but remains a validation-only experiment.
- 2026-11-25: Favor persistence for deployment: despite lower test R^2 than ridge (0.5099 vs. 0.5835), persistence achieves lower MAE (840.1 vs. 946.6) without model training or additional features.
