## Representative Sampling Strategy

- For every uploaded dataset, we now construct an intelligent sample before sending context to GPT‑4.1.
- All columns are always preserved. If the dataset has ≤30 rows, we send the full dataset.
- For larger datasets, the sampler:
  - Captures numeric spread (min/median/max plus up to two outliers per numeric column).
  - Ensures each categorical value (and null category) is represented at least once.
  - Covers earliest, middle, and latest timestamps for datetime columns.
  - Adds rows with high missing values to expose edge cases.
  - Fills remaining slots with stratified rows to maintain overall diversity.
- Default sample size cap: 60 rows; can be tuned in `SampleSelector(max_rows=60)`.
- The sampler returns both the sampled rows and a short explanation string describing why those rows were chosen. The explanation is embedded in the LLM prompt so GPT‑4.1 understands the sampling rationale.
- Output format matches the input (lists of dicts for Excel/CSV once converted to dataframes); no columns are dropped or renamed.

