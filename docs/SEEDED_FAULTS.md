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
