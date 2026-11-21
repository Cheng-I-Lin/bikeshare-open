# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

DROP test_temp_hum_interaction (temp * hum): Added and tested the temperature-humidity interaction to determine whether it improves bike-sharing demand prediction. Ridge validation R² increased from 0.6475 to 0.6493 (+0.0018), while HGB validation R² decreased from 0.2185 to 0.2129 (-0.0056). The Ridge improvement was below the 0.01 threshold, so the feature is not worth keeping in the final model. All 17 tests passed.
