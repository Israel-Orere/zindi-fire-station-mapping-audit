# Reproduce the analysis

[Download the code and evidence package](https://github.com/Israel-Orere/zindi-fire-station-mapping-audit/raw/refs/heads/main/fire_station_audit_reproducibility.zip). It includes the Python scripts in `work/`, authored article sources, saved comparison evidence, output tables, input checksums and a README. If you have already extracted that ZIP, you already have the code; start from its main folder. The original large challenge files are fetched separately using the supplied downloader.

## Read the source code

- `work/run_discovery.py`: rebuild the OSM–Overture site comparisons in the four complete regions.
- `work/analyze_discovery.py` and `work/audit_name_displacements.py`: produce the regional summaries and name-matched discrepancy screen.
- `work/analyze_equity.py`: subgroup comparisons, matched comparisons and adjusted models.
- `work/equity_followup_checks.py`: the additional model and matching sensitivity checks.
- `work/build_story_overview.py` and `work/build_wildfire_story.py`: the article's regional and wildfire charts, with their underlying counts.
- `work/build_case_audit.py`: the case-review presentation, using the documented manual decisions and saved map windows.
- `work/build_report.py`: the readable article, using `work/story_writeup.md`, `work/story_analysis_notes.md` and this page's source.

## Download the original challenge inputs

Use Python 3.12 or later. Open a terminal in the extracted package's main folder and run:

```text
python -m pip install -r requirements.txt
python download_inputs.py
```

The downloader uses the public source URLs and verifies SHA-256 checksums in `outputs/input_manifest.json`. It downloads several hundred MB. Alternatively, set `ZINDI_DATA_DIR` to a folder containing those exact files. Saved OSM responses and local map windows are already included; no new historical OSM request is needed for the audited regions.

## Rebuild the analysis and figures

Run these commands from the same main folder, in order:

```text
python work/run_discovery.py eastern-ok eastern-wa maricopa-az northern-ca
python work/analyze_discovery.py
python work/audit_name_displacements.py
python work/render_figures.py
python work/build_case_audit.py
python work/analyze_equity.py
python work/equity_followup_checks.py
python work/build_equity_report.py
python work/validate_equity.py
python work/build_story_overview.py
python work/build_wildfire_story.py
python work/build_report.py
python work/validate_and_package.py
```

The package retains the evidence inputs used by these presentation scripts, including named-record evidence, the 11-case ledger and local map windows. The case decisions are documented human judgments: rebuilding the reports reproduces their presentation rather than independently re-verifying the public sources. The statistical procedures use seed `20261024` where applicable.

## Outputs and scope

The rebuilt article is `outputs/bias_discovery_visual_report.html`; readable text is in `outputs/bias_discovery_writeup.md`. Regional comparisons, model estimates, exposure groups, case evidence and validation results are saved alongside them.

Texas is excluded because its historical extraction is incomplete. Eastern Washington is supplementary. Snapshot dates, source attribution, licensing and complete limitations are in [the methodology](methodology.md) and [analysis notes](article_analysis_notes.md). These instructions reproduce the existing analysis and do not introduce new reference targets or a new leaderboard prediction.
