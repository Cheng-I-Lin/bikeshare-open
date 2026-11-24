"""Exercise 4: HGB target transformation comparison."""

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import PowerTransformer

from src.config import PROCESSED, TARGET
from src.features import feature_columns
from src.ingest import load_raw
from src.train import MODELS, temporal_split


def verify_lag(train, valid):
    """Verify lagged counts against the original raw dataset."""

    raw = load_raw().sort_values("dteday")
    raw_counts = raw.set_index("dteday")[TARGET]

    assert raw_counts.index.is_unique, "Duplicate raw dates"

    for name, part in [("Train", train), ("Validation", valid)]:
        previous_dates = (
            pd.to_datetime(part["dteday"])
            - pd.Timedelta(days=1)
        )

        expected = previous_dates.map(raw_counts)

        assert expected.notna().all(), (
            f"{name}: Missing previous-day observations"
        )

        np.testing.assert_array_equal(
            part["cnt_lag_1"].to_numpy(),
            expected.to_numpy(),
            err_msg=f"{name}: Incorrect lag alignment",
        )

        print(
            f"PASS: {name} lag verification "
            f"({len(part)} rows)"
        )


def evaluate(y_true, predictions):
    return (
        r2_score(y_true, predictions),
        mean_absolute_error(y_true, predictions),
    )


def main():
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, _ = temporal_split(df)

    X_train = train[cols]
    X_valid = valid[cols]

    y_train = train[TARGET].to_numpy()
    y_valid = valid[TARGET].to_numpy()

    lag_train = train["cnt_lag_1"].to_numpy()
    lag_valid = valid["cnt_lag_1"].to_numpy()

    print("=" * 70)
    print("EXERCISE 4: HGB TARGET TRANSFORMATIONS")
    print("=" * 70)

    print(f"Training rows: {len(train)}")
    print(f"Validation rows: {len(valid)}")
    print(f"Number of features: {len(cols)}")
    print(f"Features: {', '.join(cols)}")

    # Verify past-only lag alignment before fitting.
    print("\nLAG VERIFICATION")
    verify_lag(train, valid)

    results = {}

    def fit_hgb(target):
        model = clone(MODELS["hgb"])
        model.fit(X_train, target)
        return model.predict(X_valid)

    # 1. Original HGB
    pred_original = fit_hgb(y_train)
    results["Original"] = evaluate(
        y_valid, pred_original
    )

    # 2. Log1p transformation
    pred_log = fit_hgb(np.log1p(y_train))
    results["Log1p"] = evaluate(
        y_valid, np.expm1(pred_log)
    )

    # 3. Square-root transformation
    pred_sqrt = fit_hgb(np.sqrt(y_train))
    results["Sqrt"] = evaluate(
        y_valid, pred_sqrt ** 2
    )

    # 4. Yeo-Johnson transformation
    transformer = PowerTransformer(
        method="yeo-johnson",
        standardize=False,
    )

    y_train_yj = transformer.fit_transform(
        y_train.reshape(-1, 1)
    ).ravel()

    pred_yj = fit_hgb(y_train_yj)

    pred_yj_original = transformer.inverse_transform(
        pred_yj.reshape(-1, 1)
    ).ravel()

    results["Yeo-Johnson"] = evaluate(
        y_valid, pred_yj_original
    )

    print(
        f"\nYeo-Johnson lambda: "
        f"{transformer.lambdas_[0]:.4f}"
    )

    # 5. First-differencing transformation
    y_train_diff = y_train - lag_train

    np.testing.assert_allclose(
        y_train_diff + lag_train,
        y_train,
    )

    print("PASS: Training target reconstruction")

    pred_diff = fit_hgb(y_train_diff)
    pred_reconstructed = lag_valid + pred_diff

    results["First-diff"] = evaluate(
        y_valid, pred_reconstructed
    )

    # Production Ridge and persistence benchmarks
    benchmarks = {}

    for name in ["ridge", "baseline_persistence"]:
        model = clone(MODELS[name])
        model.fit(X_train, train[TARGET])

        benchmarks[name] = evaluate(
            y_valid, model.predict(X_valid)
        )

    # Report validation results on the original count scale.
    original_r2, original_mae = results["Original"]

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    print(
        f"{'Model':<24}"
        f"{'R2':>10}"
        f"{'MAE':>12}"
        f"{'Delta R2':>12}"
    )

    for name, (r2, mae) in results.items():
        print(
            f"{name:<24}"
            f"{r2:>10.4f}"
            f"{mae:>12.1f}"
            f"{r2 - original_r2:>+12.4f}"
        )

    print("\nBENCHMARKS")

    for name, (r2, mae) in benchmarks.items():
        print(
            f"{name:<24}"
            f"{r2:>10.4f}"
            f"{mae:>12.1f}"
        )

    best_name = max(
        results, key=lambda name: results[name][0]
    )

    best_r2, best_mae = results[best_name]
    ridge_r2, ridge_mae = benchmarks["ridge"]

    print(f"\nBest HGB variant: {best_name}")
    print(f"R2 improvement: {best_r2 - original_r2:+.4f}")
    print(
        f"MAE reduction: "
        f"{100 * (original_mae - best_mae) / original_mae:.2f}%"
    )
    print(f"R2 difference vs Ridge: {best_r2 - ridge_r2:+.4f}")
    print(f"MAE difference vs Ridge: {best_mae - ridge_mae:+.1f}")

    print("\nExperiment completed successfully.")
    print("Validation only; test set not evaluated.")
    print("Production metrics and raw data unchanged.")


if __name__ == "__main__":
    main()
