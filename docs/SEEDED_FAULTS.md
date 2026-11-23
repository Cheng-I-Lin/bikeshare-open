Fault 1: Forbidden Column Added to feature_columns()

Exact change: In src/features.py, the safe return statement was changed to append the forbidden casual column:

return [c for c in numeric if c not in FORBIDDEN] + ["casual"]

Red test output and actual PostToolUse hook stderr:

PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/alanlin/Downloads/bikeshare-open/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'dayofweek', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 9 passed in 0.67s

Agent repair: The coding agent was instructed to restore the original safe feature-selection logic. Its first repair attempt required further inspection because the displayed edit still showed two return statements. After a follow-up instruction and verification, the final function contained only:

return [c for c in numeric if c not in FORBIDDEN]

Agent turns: 1 turn to introduce the fault and trigger detection; 2 repair-related instructions, including the corrective follow-up. The final repair was confirmed by inspecting the file.

Final verification: Claude Code reported 18 passed in 1.25s. A subsequent git diff -- src/features.py produced no output, confirming the file matched its committed version.

Conclusion: The PostToolUse hook detected the forbidden column and reported the failing leakage test immediately after the edit. Because this hook runs after a modification, it detected the problem rather than preventing the file from being written.

================================================================================

Fault 2: Removing .shift(1) from cnt_roll_7

Exact change: Removed .shift(1) from the rolling-mean feature calculation in src/features.py.

Original:

out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()

Faulty:

out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()

This causes the rolling mean to include the current day's target value, introducing target leakage.

Actual PostToolUse hook stderr and red test output:

PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/alanlin/Downloads/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 0.52s

Agent repair: Restored the original expression with .shift(1) before .rolling(LAG_WARMUP).mean().

Agent turns: 1 turn to introduce and detect the fault; 1 turn to repair it.

Final test result reported by Claude Code:

18 passed in 1.17s

Independent verification:

79:    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()

git diff -- src/features.py produced no output, confirming that the temporary fault was completely removed.

Conclusion: The PostToolUse hook successfully detected target leakage caused by including the current day's target in a rolling-mean feature. The hook reported the failing test after the edit, allowing the coding agent to identify and repair the problem.

================================================================================

Fault 3: Weather Encoder Silently Accepts Unknown Categories

Exact change: In src/features.py, replaced the weather encoder's exception:

raise ValueError(f"unmapped weather labels: {sorted(unknown)}")

with:

return series.map(WEATHER_ORDER).astype(float)

This caused unknown weather categories to be mapped to NaN rather than rejected.

Original PostToolUse hook result: No stderr was produced. The existing leakage tests did not detect the fault.

Original test results: Claude Code reported that all 10 leakage tests and all 18 tests in the full suite passed while the fault was active.

New regression test: Added test_weather_encoder_raises_on_unknown_category() to tests/test_leakage.py, which supplies an unknown weather label and expects a ValueError.

Observed failing test: Claude Code reported the following pytest failure after adding the regression test:

Failed: DID NOT RAISE ValueError

The complete original pytest traceback was not captured in the conversation.

Repair: Restored the original raise ValueError(...) statement inside encode_weather().

Agent turns: 1 turn to introduce the fault, 1 turn to add the regression test (with two internal edit attempts), and 1 turn to repair the fault.

Final verification: All 19 tests passed. Inspection of src/features.py confirmed that the exception was restored, and git diff -- src/features.py produced no output.

Conclusion: The original PostToolUse hook failed to detect this seeded fault because the existing tests did not cover unknown weather categories. Adding a regression test exposed the bug and ensured that future removals of the exception would be detected.

================================================================================

Fault 4: Edit|Write Hook Misses Python Data Mutation via Bash

Exact change: Used Python's csv module through Claude Code's Bash tool to create a modified copy of data/raw/bike_daily.csv. The first data row's cnt value was increased by 1, and the result was saved as data/raw/fault4_probe.csv, leaving the original dataset unchanged.

python3 -I -c 'import csv; rows=list(csv.reader(open("data/raw/bike_daily.csv"))); rows[1][12]=str(int(rows[1][12])+1); out=open("data/raw/fault4_probe.csv","w",newline=""); w=csv.writer(out); w.writerows(rows); out.close()' && echo "Script completed successfully"

Bash tool output:

Script completed successfully

PostToolUse hook stderr: None. The hook did not execute because its matcher, "Edit|Write", does not include Bash tool calls. Therefore, the modified CSV was created without automatically triggering the leakage checker.

Modification observed: The file data/raw/fault4_probe.csv was successfully created, with the first data row's cnt value changed from 1229 to 1230. The original bike_daily.csv remained unchanged.

Original cp attempt: Initially, we attempted to demonstrate Fault #4 using Bash cp, but Claude Code denied the command before execution:

Permission to use Bash with command cp /tmp/bikeshare_fault4_backup.csv data/raw/fault4_probe.csv has been denied.

The command was denied despite having an exact matching entry in the Bash Allow list. Following the professor's suggestion, we used Python through Bash as an alternative to demonstrate the same hook coverage limitation.

What would have caught it: A PostToolUse hook that also matches Bash, combined with a raw-data integrity check, could detect unauthorized changes in data/raw/. A PreToolUse hook could also prevent certain unauthorized Bash operations before execution. The existing Edit|Write hook cannot detect these changes because it does not run after Bash commands.

Agent turns: 1 turn to execute the successful Python-based fault demonstration, excluding the earlier unsuccessful cp attempts.

Conclusion: Fault #4 successfully demonstrated that the PostToolUse hook does not cover file modifications performed through the Bash tool. Although the original cp command was blocked by Claude Code's permission system, the Python alternative successfully created a modified CSV without triggering the hook. This reveals a coverage gap in the hook configuration rather than a failure of the leakage tests themselves.
```
