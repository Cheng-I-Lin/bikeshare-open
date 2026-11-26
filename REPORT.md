# Methodology 07: Agentic Programming

## Exercise 5: Ridge vs. Persistence

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
