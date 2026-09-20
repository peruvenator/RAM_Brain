"""Step 2: rapidfuzz name candidates for every Excel row against the cached FINTRX universe.

Run:  python scripts/match.py [--limit N] [--top 3] [--cutoff 75]
No network. Output: data/output/cand_name.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).parent))
from common import (CAND_NAME, COL_NAME, COL_RECORD_ID, COL_STATE, UNIVERSE,  # noqa: E402
                    is_blank, load_source, norm_state, read_jsonl, write_csv)
from normalize import normalize  # noqa: E402

FIELDS = ["source_row", "record_id", "source_name", "candidate_rank", "fintrx_item_id", "matched_name",
          "cand_city", "cand_state", "score", "score_aggressive", "method", "state_match"]
CHUNK = 500


def load_universe() -> list[dict]:
    seen, out = set(), []
    for r in read_jsonl(UNIVERSE):
        if r["item_id"] in seen or is_blank(r.get("name")):
            continue
        seen.add(r["item_id"])
        out.append(r)
    if not out:
        sys.exit(f"universe empty, run pull_universe.py first ({UNIVERSE})")
    return out


class UniverseIndex:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.norm = [normalize(r["name"]) for r in rows]
        self.norm_agg = [normalize(r["name"], aggressive=True) for r in rows]
        self.exact: dict[str, int] = {}
        for i, n in enumerate(self.norm):
            self.exact.setdefault(n, i)

    def lookup_exact(self, name) -> int | None:
        return self.exact.get(normalize(name))

    def best(self, name, cutoff: float = 95.0):
        hit = process.extractOne(normalize(name), self.norm, scorer=fuzz.token_set_ratio, score_cutoff=cutoff)
        return (hit[2], hit[1]) if hit else None


def candidate(src, rank, idx, score, s_agg, method, ux: UniverseIndex) -> dict:
    u = ux.rows[idx]
    return dict(source_row=src["source_row"], record_id=src[COL_RECORD_ID], source_name=src[COL_NAME],
                candidate_rank=rank, fintrx_item_id=u["item_id"], matched_name=u["name"],
                cand_city=u.get("city"), cand_state=norm_state(u.get("state")),
                score=round(float(score), 1), score_aggressive=round(float(s_agg), 1), method=method,
                state_match=bool(src["_state"]) and src["_state"] == norm_state(u.get("state")))


def match_all(df, ux: UniverseIndex, top: int, cutoff: float) -> list[dict]:
    srcs = df.to_dict("records")
    for s in srcs:
        s["_state"] = norm_state(s.get(COL_STATE))
        s["_norm"] = normalize(s.get(COL_NAME)) if not is_blank(s.get(COL_NAME)) else ""
        s["_agg"] = normalize(s.get(COL_NAME), aggressive=True) if s["_norm"] else ""
    out: list[dict] = []
    fuzzy = [s for s in srcs if s["_norm"] and s["_norm"] not in ux.exact]
    for s in srcs:
        if s["_norm"] and s["_norm"] in ux.exact:
            out.append(candidate(s, 1, ux.exact[s["_norm"]], 100.0, 100.0, "exact_normalized", ux))
    for start in range(0, len(fuzzy), CHUNK):
        block = fuzzy[start:start + CHUNK]
        sims = process.cdist([s["_norm"] for s in block], ux.norm, scorer=fuzz.token_set_ratio,
                             score_cutoff=cutoff, workers=-1, dtype=np.float32)
        k = min(top, sims.shape[1])
        part = np.argpartition(-sims, k - 1, axis=1)[:, :k]
        for bi, s in enumerate(block):
            idxs = part[bi]
            idxs = idxs[np.argsort(-sims[bi, idxs])]
            rank = 0
            for j in idxs:
                sc = float(sims[bi, j])
                if sc < cutoff:
                    continue
                rank += 1
                s_agg = fuzz.token_set_ratio(s["_agg"], ux.norm_agg[j]) if s["_agg"] else 0.0
                out.append(candidate(s, rank, int(j), sc, s_agg, "fuzzy_token_set", ux))
        print(f"fuzzy {min(start + CHUNK, len(fuzzy))}/{len(fuzzy)}", file=sys.stderr, flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--cutoff", type=float, default=75.0)
    args = ap.parse_args()
    df = load_source(args.limit)
    ux = UniverseIndex(load_universe())
    print(f"{len(df)} source rows vs {len(ux.rows)} universe firms")
    rows = match_all(df, ux, args.top, args.cutoff)
    write_csv(CAND_NAME, rows, FIELDS)
    have = {r["source_row"] for r in rows}
    print(f"wrote {CAND_NAME}: {len(rows)} candidates, {len(have)} rows with >=1, "
          f"{len(df) - len(have)} rows with none")


if __name__ == "__main__":
    main()
