# Reproducible fire-tier baseline: E5ExTc9D

Best Documentation entry for the Zindi Bias Bounty Mapping Equity Challenge.
Author: Israel Orere (Zindi: Israel-Orere).

This independent implementation of the original 8 October V3 rule rebuilds the
submitted predictions directly from the supplied raw POI and tract files.
It is not the later, higher-scoring V6/V19/C3 or V8 blend. It does not read an
earlier model, fitted checkpoint or prediction as an input.

## Reproduce

Use Python 3.12 or newer and the pinned open-source requirements. From this folder:

```sh
python -m pip install -r requirements.txt
python download_inputs.py --data-dir data
python reproduce.py --data-dir data --out results
```

If the original five-region challenge files are already available, skip the
download and point `--data-dir` to that folder. The calculation itself is offline.
The optional reference is read only after predictions have been written and is
used only to test equality. It supplies no features, scores or row order.
The main run also checks the output against the recorded submission SHA-256.
The ZIP additionally includes the reference CSV for an optional byte comparison.

## Complete prediction rule

1. Keep the GEOIDs in each supplied sample file, in its original row order.
   Concatenate Eastern Oklahoma, Maricopa, Northern California, South-Central
   Texas, then Eastern Washington (the region added to the original panel).
2. Read tract population (`pop_total`), urban share (`pct_urban`) and geometry.
3. Scan all supplied Overture POIs. Count a fire record only when
   `categories.primary == "fire_department"`. Assign its point to an intersecting
   scored tract. No external facility reference or alternate-category inference
   enters the score. All primary-fire points in these inputs have exactly one
   scored-tract assignment, so boundary tie-breaking does not affect this output.
4. Set rural to `pct_urban < 0.5`. Set score to 0.12 for rural tracts with population
   at least 1,500 and no primary fire record; 0.08 for other rural tracts; 0.04 for
   urban tracts or unknown urban share. Write the two columns with ten decimals.

The 0.04 base and two 0.04 increments are declared heuristic levels, not fitted
missingness percentages. The population threshold is a fixed heuristic, not a
statutory fire-service standard. The model does not calculate separate road,
building or facility reference-relative components. It directly predicts the
competition composite through three transparent tiers.

## Verified result

Rebuilt from all 2,001,137 raw POIs on 1 November 2026. The output is byte-for-byte
identical to the actual E5ExTc9D CSV downloaded from the signed-in Zindi account.

- 9,794 unique 11-digit text GEOIDs; exact submitted order and two-column schema.
- 758 tracts receive 0.12; 1,095 receive 0.08; 7,941 receive 0.04.
- SHA-256: `be3673df36eec401677607f2a21592840302e4261757f0bf827b172aa4264daf`.
- Public RMSE 0.086138688; private RMSE 0.085824108, as displayed by Zindi on
  1 November. Hidden targets are unavailable; those errors are not computed locally.

`verification.json` contains every input hash, regional counts, validation and
comparison result. `tract_audit.csv` is generated on each run for row-level review.

## Edge cases and assumptions

- All 27 zero-population tracts are retained. Their urban share is missing in
  these inputs and they receive 0.04. Zero population never implies a zero gap.
- Both zero-land tracts remain in the scored panel. Land area is audit metadata,
  not a score input; there is no density division or special water adjustment.
- Unknown urban share takes the 0.04 fallback. A missing population, if introduced
  in another dataset, cannot trigger the 1,500-person condition.
- A zero mapped fire count is not proof that no fire station or service exists.
  Alternate categories, misplaced points, service across tract boundaries and
  genuinely low facility supply can all produce the same count.
- Duplicate POI rows are not resolved; the rule uses presence, so duplication
  inside one tract cannot change its tier. Operating status is not filtered.
- No positive evidence for a tract is silently dropped: all primary-fire records
  in this panel were spatially assigned; invalid/missing tract geometry fails.

## Validation and limits

There is no training, cross-validation, random seed, fitted coefficient or
calibration step in this rule. Reproduction tests establish implementation
identity, not that its rural-risk assumption is correct. The rule builds a rural
contrast into its predictions; that contrast cannot itself be presented as an
empirical discovery of bias. Real station coverage and response times are not
measured. The model also ignores roads/buildings, component applicability and
within-tier differences. These limits are explicit so the baseline can be tested,
criticized and improved without treating its scores as observed service deficits.

## Sources, attribution and provenance

- [Competition](https://zindi.world/competitions/bias-bounty-mapping-equity-challenge)
- [Challenge data](https://zindi.world/competitions/bias-bounty-mapping-equity-challenge/data)
- [Official source repository](https://source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge)
- Every original input URL, byte count and SHA-256 appears in `input_manifest.json`.

Only supplied samples, tract context/boundaries and Overture POIs enter the
calculation. No withdrawn TIGER road, Microsoft footprint, HIFLD, CBP, hidden
reference, external enrichment or leaderboard-derived tract label is read.
The original rule was published before this submission; this rebuild changes no
threshold or score using either the public or private results.

Attribute Overture Maps Foundation and upstream sources, including OpenStreetMap
contributors where applicable. Preserve the challenge's stated CC-BY-SA 4.0 and
the upstream layer terms (places: CDLA Permissive 2.0) documented in the supplied
README. Raw input files are downloaded from the official source, not bundled here.
New reproduction code is MIT licensed. ChatGPT assisted recovery, implementation,
verification and documentation; execution uses only open-source local packages.
