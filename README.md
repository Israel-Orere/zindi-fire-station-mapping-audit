# Fire-station mapping audit

**Fire-station sites in rural and more wildfire-exposed areas had fewer nearby fire-department listings. In Porum and Westport, the building is mapped locally while the department's listing points elsewhere.**

Evidence and reproducible analysis for the Zindi Bias Bounty Mapping Equity Challenge, by Israel Orere.

- [Read the article](outputs/bias_discovery_writeup.md)
- [Browse the code](work/)
- [Download the reproducibility package](fire_station_audit_reproducibility.zip)
- [Run instructions](outputs/reproduce_analysis.md)
- [Full equity analysis](outputs/equity_followup_report.md)
- [All 11 case reviews and sources](outputs/comprehensive_case_audit.md)
- [Methodology](outputs/methodology.md)
- [Analysis notes and limitations](outputs/article_analysis_notes.md)

## Reproduce

Download and extract the reproducibility ZIP, then follow its `outputs/reproduce_analysis.md`. It includes the Python scripts, saved OSM evidence, local map windows, case decisions and derived results. The original large challenge files are downloaded separately by `download_inputs.py`, with checksums verified against `outputs/input_manifest.json`.

The archive omits regenerable tract-geometry caches and the two largest derived tract tables. The ordered run instructions rebuild those files from the original challenge inputs. No fresh OSM request is needed for the four audited regions. Temporary editor backups, screenshots and notes comparing other submissions are excluded from this public release.

## Scope

1,372 OSM-mapped fire-station sites; four complete regions; 120 counties in the adjusted analysis. Overture snapshot 2026-08-19.0; OSM historical state 2026-08-01. Texas is excluded because its historical extraction is incomplete. Eastern Washington is supplementary.

The rural/urban result describes differences between map records. Its independent adjusted association is uncertain. The wildfire-exposure association persists across the reported checks. Unmatched records are not all verified omissions; operational coverage, causes, response delays and harm are not established. The three supported location errors were selected by a name screen, not a random sample of all stations.

## Licensing and attribution

Analysis code: [MIT](LICENSE). Original narrative and plots: CC BY 4.0, Israel Orere, 2026. OpenStreetMap-derived data: © OpenStreetMap contributors, ODbL 1.0. Overture and challenge-provider attributions and licenses are retained in the [methodology](outputs/methodology.md), named-record evidence and public-source register. No full third-party web pages or scanned vendor contract are redistributed.
