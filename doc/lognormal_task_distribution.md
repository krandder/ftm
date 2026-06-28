# Lognormal Task Distribution

The optional `use_lognormal_task_distribution` flag replaces the hardcoded
FTM task threshold quantiles with a smooth lognormal distribution over task
requirements.

When enabled:

- `full_automation_requirements_training` is interpreted as the 99th percentile
  training requirement, not the hardest task requirement.
- `flop_gap_training` still pins the gap between the 20th percentile and that
  99th percentile.
- The same 99th-percentile interpretation is used for runtime requirements.
- `n_labour_tasks` is forced to `10000`, so the model can distinguish 99.0%,
  99.9%, and the last task bucket.
- The playground and Python timeline metrics report 99%, 99.9%, and 100%
  automation years for both goods/services and R&D.
- The old `training_requirements_steepness` and
  `runtime_requirements_steepness` discretization is skipped in this mode.

The generated task thresholds use:

```text
log10(requirement_p) = mu + sigma * NormalQuantile(p)
```

with `mu` and `sigma` chosen so:

```text
requirement_20% = full_automation_requirement / flop_gap
requirement_99% = full_automation_requirement
```

Example import scenario:

```json
{
  "full_automation_requirements_training": 6e31,
  "flop_gap_training": 1e4,
  "use_lognormal_task_distribution": true,
  "runtime_training_max_tradeoff": 1e100
}
```
