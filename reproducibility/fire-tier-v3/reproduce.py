"""Rebuild the documented V3 fire-tier submission directly from supplied data.

Independent implementation of the rule published in the original conversation
on 8 October 2026. No prediction file or fitted baseline is a model input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely

# Original four-region organizer order followed by the added Washington panel.
REGIONS = ['eastern-ok', 'maricopa-az', 'northern-ca', 'south-central-tx', 'eastern-wa']


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def build(data: Path, out: Path, reference: Path | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    pieces, provenance, region_audits = [], [], []
    for region in REGIONS:
        sample_path = data / f'{region}-sample-submission.csv'
        tract_path = data / f'{region}-census-tracts.parquet'
        poi_path = data / f'{region}-overture-pois.parquet'
        sample = pd.read_csv(sample_path, usecols=['GEOID'], dtype={'GEOID': str})
        tracts = pq.read_table(tract_path, columns=['GEOID', 'pop_total', 'pct_urban', 'ALAND', 'geometry']).to_pandas()
        tracts['GEOID'] = tracts.GEOID.astype(str).str.zfill(11)
        panel = sample.merge(tracts, on='GEOID', how='left', validate='one_to_one')
        assert panel.geometry.notna().all(), region
        geometry = shapely.from_wkb(panel.geometry.to_numpy())
        tree = shapely.STRtree(geometry)
        counts = np.zeros(len(panel), dtype=int)
        n_pois = n_fire = n_unassigned = n_multitract = 0
        for batch in pq.ParquetFile(poi_path).iter_batches(batch_size=100000, columns=['categories', 'geometry']):
            categories = batch.column('categories').to_pylist()
            keep = np.asarray([isinstance(c, dict) and c.get('primary') == 'fire_department' for c in categories])
            n_pois += len(keep)
            if not keep.any():
                continue
            points = shapely.from_wkb(np.asarray(batch.column('geometry').to_pylist(), dtype=object)[keep])
            n_fire += len(points)
            pairs = tree.query(points, predicate='intersects')
            memberships = np.bincount(pairs[0], minlength=len(points))
            n_unassigned += int((memberships == 0).sum())
            n_multitract += int((memberships > 1).sum())
            np.add.at(counts, pairs[1], 1)
        urban = pd.to_numeric(panel.pct_urban, errors='coerce')
        pop = pd.to_numeric(panel.pop_total, errors='coerce')
        rural = urban.lt(0.5)  # NaN compares false: original missing-urban fallback.
        priority = rural & pop.ge(1500) & (counts == 0)
        panel['fire_primary_count'] = counts
        panel['rural'] = rural
        panel['tier'] = np.where(priority, 'rural_population_1500_plus_no_fire', np.where(rural, 'other_rural', 'urban_or_unknown'))
        panel['coverage_gap_score'] = np.where(priority, 0.12, np.where(rural, 0.08, 0.04))
        panel['region'] = region
        pieces.append(panel.drop(columns='geometry'))
        region_audits.append({'region': region, 'scored_tracts': len(panel), 'all_pois_scanned': n_pois,
                              'primary_fire_records': n_fire, 'fire_outside_scored_tracts': n_unassigned,
                              'fire_intersecting_multiple_tracts': n_multitract,
                              'tiers': panel.tier.value_counts().to_dict()})
        for p in [sample_path, tract_path, poi_path]:
            provenance.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha256(p)})
        print(region, region_audits[-1], flush=True)
    panel = pd.concat(pieces, ignore_index=True)
    assert len(panel) == 9794 and panel.GEOID.nunique() == 9794
    assert panel.GEOID.str.fullmatch(r'\d{11}').all()
    values = panel.coverage_gap_score.to_numpy()
    assert np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()
    csv_path = out / 'submission_overture_fire_tier_safe_v3.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['GEOID', 'coverage_gap_score'])
        for g, v in zip(panel.GEOID, values):
            w.writerow([g, f'{v:.10f}'])
    panel.to_csv(out / 'tract_audit.csv', index=False)
    expected_sha = 'be3673df36eec401677607f2a21592840302e4261757f0bf827b172aa4264daf'
    assert sha256(csv_path) == expected_sha, 'Output differs from the original V3 submission.'
    verification = None
    if reference:
        # Used only after generation, never to calculate predictions or order.
        ref = pd.read_csv(reference, dtype={'GEOID': str})
        aligned = ref.set_index('GEOID').coverage_gap_score.reindex(panel.GEOID).to_numpy()
        verification = {'reference_sha256': sha256(reference), 'exact_order': ref.GEOID.tolist() == panel.GEOID.tolist(),
                        'numeric_match': bool(np.array_equal(values, aligned)),
                        'max_abs_difference': float(np.max(np.abs(values - aligned))),
                        'byte_identical': csv_path.read_bytes() == reference.read_bytes()}
        assert verification['numeric_match'] and verification['byte_identical'], verification
    report = {'submission_id': 'E5ExTc9D', 'public_rmse': 0.086138688, 'private_rmse': 0.085824108,
              'method': 'Independent implementation of the original fixed V3 rule; no training or inherited predictions.',
              'rows': len(panel), 'unique_geoids': panel.GEOID.nunique(), 'output_sha256': sha256(csv_path),
              'tiers': panel.tier.value_counts().to_dict(), 'unknown_urban_share': int(panel.pct_urban.isna().sum()),
              'zero_population': int(panel.pop_total.eq(0).sum()), 'zero_land': int(panel.ALAND.eq(0).sum()),
              'region_audits': region_audits, 'inputs': provenance, 'verification': verification}
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ['inputs', 'region_audits']}, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--out', type=Path, default=Path('results'))
    parser.add_argument('--reference', type=Path, help='Optional submitted CSV, used only for post-build equality verification.')
    args = parser.parse_args()
    build(args.data_dir, args.out, args.reference)
