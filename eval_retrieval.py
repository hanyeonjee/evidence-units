"""
OmniDocBench Retrieval Evaluation
==================================
Official evaluation script for:
  "Evidence Units: Ontology-Grounded Document Organization
   for Parser-Independent Retrieval"

[Evaluation modes]
  Strict : evidence_context uses narrow context window (±2–3 elements)
  Fair   : evidence_context uses wider context window (±4–5 elements)
  score  = LCS(retrieved, gt_context) / len(gt_context)

[Supported tracks]
  GT w/o EU   — OmniDocBench GT annotations, element-level chunking (baseline)
  Parser w/EU — Pre-computed EU outputs from any parser (--docling-eu-dir / --mineru-eu-dir)

[Usage]
  # Baseline evaluation (GT annotations, no EU)
  python eval_retrieval.py \\
    --gt  OmniDocBench.json \\
    --qas qas.json \\
    --output results/

  # Cross-parser evaluation with pre-computed EU outputs
  python eval_retrieval.py \\
    --gt  OmniDocBench.json \\
    --qas qas.json \\
    --output results/ \\
    --docling-eu-dir path/to/eu_docling \\
    --mineru-eu-dir  path/to/eu_mineru
"""
from __future__ import annotations

import json
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ════════════════════════════════════════════════════════════════════
# 1. QA data structures
# ════════════════════════════════════════════════════════════════════

@dataclass
class RetrievalQA:
    qa_id: str
    image_name: str
    question: str
    evidence_context_strict: str
    evidence_context_fair: str
    evidence_source: str


def load_qas_from_file(qas_path: str) -> List[RetrievalQA]:
    with open(qas_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    qas = [RetrievalQA(
        qa_id=d["qa_id"], image_name=d["image_name"], question=d["question"],
        evidence_context_strict=d["evidence_context_strict"],
        evidence_context_fair=d["evidence_context_fair"],
        evidence_source=d["evidence_source"],
    ) for d in data]
    logger.info(f"Loaded {len(qas)} QA pairs from {qas_path}")
    return qas


# ════════════════════════════════════════════════════════════════════
# 2. Chunk structures
# ════════════════════════════════════════════════════════════════════

@dataclass
class Chunk:
    chunk_id: str
    image_name: str
    text: str
    source: str


def build_chunks_without_eu(gt_path: str, limit: int = 0) -> Dict[str, List[Chunk]]:
    """GT element-level chunking (no EU) — baseline."""
    with open(gt_path, "r", encoding="utf-8") as f:
        pages = json.load(f)
    if limit > 0:
        pages = pages[:limit]

    skip_types = {"abandon", "need_mask", "table_mask", "text_mask", "page_number", "header", "footer"}
    chunks_by_page = {}

    for page_entry in pages:
        image_name = Path(page_entry.get("page_info", {}).get("image_path", "unknown")).stem
        dets = page_entry.get("layout_dets", [])
        chunks = []
        for i, det in enumerate(sorted(dets, key=lambda d: d.get("order") if d.get("order") is not None else 999)):
            if det["category_type"] in skip_types or det.get("ignore", False):
                continue
            text = det.get("text", "").strip()
            if text:
                chunks.append(Chunk(chunk_id=f"{image_name}_{i}", image_name=image_name, text=text, source="without_eu"))
        if chunks:
            chunks_by_page[image_name] = chunks

    return chunks_by_page


# ════════════════════════════════════════════════════════════════════
# 3. Load pre-computed EU outputs
# ════════════════════════════════════════════════════════════════════

def build_chunks_from_eu_dir(
    eu_dir: str,
    without_eu: bool = False,
    qa_image_names: Optional[set] = None,
) -> Dict[str, List[Chunk]]:
    """
    Load chunks from a pre-computed EU output directory.

    Expected directory layout:
      eu_dir/
        with_eu/    {image_name}.json   ← EU-grouped chunks
        without_eu/ {image_name}.json   ← element-level chunks

    without_eu=False → load with_eu/
    without_eu=True  → load without_eu/
    """
    sub = "without_eu" if without_eu else "with_eu"
    target_dir = Path(eu_dir) / sub
    if not target_dir.exists():
        logger.warning(f"  {target_dir} does not exist.")
        return {}

    source_label = "without_eu" if without_eu else "with_eu"
    chunks_by_page: Dict[str, List[Chunk]] = {}

    for json_file in sorted(target_dir.glob("*.json")):
        image_name = json_file.stem
        if qa_image_names is not None and image_name not in qa_image_names:
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        chunks = []
        if without_eu:
            for item in items:
                text = (item.get("text") or "").strip()
                if text:
                    chunks.append(Chunk(
                        chunk_id=item.get("chunk_id", f"{image_name}_{len(chunks)}"),
                        image_name=image_name, text=text, source=source_label,
                    ))
        else:
            for eu_item in items:
                elements = eu_item.get("elements", [])
                texts = sorted(
                    [(e.get("order", 9999), e.get("text", "").strip()) for e in elements],
                    key=lambda x: x[0],
                )
                eu_text = "\n".join(t for _, t in texts if t)
                if eu_text.strip():
                    chunks.append(Chunk(
                        chunk_id=eu_item.get("eu_id", f"{image_name}_{len(chunks)}"),
                        image_name=image_name, text=eu_text, source=source_label,
                    ))

        if chunks:
            chunks_by_page[image_name] = chunks

    return chunks_by_page


# ════════════════════════════════════════════════════════════════════
# 4. Retrieval evaluation
# ════════════════════════════════════════════════════════════════════

def lcs_score(retrieved: str, ground_truth: str) -> float:
    """LCS-based retrieval score: LCS length / GT length (same as OHR-Bench)."""
    if not retrieved or not ground_truth:
        return 0.0
    m, n = len(retrieved), len(ground_truth)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if retrieved[i - 1] == ground_truth[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (n + 1)
    return prev[n] / n if n > 0 else 0.0


def evaluate_retrieval(
    qas: List[RetrievalQA],
    chunks_by_page: Dict[str, List[Chunk]],
    embed_model,
    top_k: int = 3,
    label: str = "",
    context_mode: str = "strict",
) -> Tuple[dict, List[dict]]:
    """
    Evaluate retrieval performance.

    context_mode:
      "strict" → narrow GT context → conservative EU delta estimate
      "fair"   → wider GT context  → liberal EU delta estimate
    """
    page_embeds: Dict[str, np.ndarray] = {}
    for page_name, chunks in chunks_by_page.items():
        texts = [c.text for c in chunks]
        if texts:
            embs = embed_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            page_embeds[page_name] = embs

    MAX_SCAN_K = 10
    results_by_source = defaultdict(lambda: {
        "lcs_sum": 0.0, "hit_sum": 0, "count": 0,
        "recall_at": {1: 0, 2: 0, 3: 0, 5: 0},
        "min_k_sum": 0.0, "min_k_count": 0,
        "token_sum": 0, "token_count": 0,
    })
    total_lcs = 0.0
    total_hit = 0
    total_count = 0
    recall_at = {1: 0, 2: 0, 3: 0, 5: 0}
    min_k_sum = 0.0
    min_k_found = 0
    token_when_hit_sum = 0
    token_when_hit_count = 0
    per_qa_traces: List[dict] = []

    for qa in qas:
        chunks = chunks_by_page.get(qa.image_name)
        embs = page_embeds.get(qa.image_name)
        if chunks is None or embs is None:
            continue

        gt_context = (
            qa.evidence_context_strict if context_mode == "strict"
            else qa.evidence_context_fair
        )

        q_emb = embed_model.encode([qa.question], convert_to_numpy=True)[0]
        sims = np.dot(embs, q_emb) / (np.linalg.norm(embs, axis=1) * np.linalg.norm(q_emb) + 1e-9)
        all_ranked = np.argsort(sims)[::-1][:MAX_SCAN_K]

        top_indices = all_ranked[:top_k]
        ret_text = "\n\n".join(chunks[idx].text for idx in top_indices)
        lcs = lcs_score(ret_text, gt_context)
        hit = 1 if lcs > 0.3 else 0

        total_lcs += lcs
        total_hit += hit
        total_count += 1

        src = qa.evidence_source
        results_by_source[src]["lcs_sum"] += lcs
        results_by_source[src]["hit_sum"] += hit
        results_by_source[src]["count"] += 1

        found_k = None
        for k in [1, 2, 3, 5]:
            k_text = "\n\n".join(chunks[idx].text for idx in all_ranked[:k])
            if lcs_score(k_text, gt_context) > 0.3:
                recall_at[k] += 1
                results_by_source[src]["recall_at"][k] += 1
                if found_k is None:
                    found_k = k

        if found_k is not None:
            min_k_sum += found_k
            min_k_found += 1
            results_by_source[src]["min_k_sum"] += found_k
            results_by_source[src]["min_k_count"] += 1

        top_k_chars = sum(len(chunks[idx].text) for idx in top_indices)
        if hit:
            token_when_hit_sum += top_k_chars
            token_when_hit_count += 1
            results_by_source[src]["token_sum"] += top_k_chars
            results_by_source[src]["token_count"] += 1

        per_qa_traces.append({
            "qa_id": qa.qa_id,
            "retrieved_chunks": [
                {"rank": rank + 1, "chunk_id": chunks[idx].chunk_id,
                 "sim": round(float(sims[idx]), 4), "text": chunks[idx].text}
                for rank, idx in enumerate(top_indices)
            ],
            "retrieved_text": ret_text,
            "gt_context": gt_context,
            "lcs": round(lcs, 4),
            "hit": bool(hit),
            "min_k": found_k,
        })

    avg_lcs = total_lcs / total_count if total_count > 0 else 0
    hit_rate = total_hit / total_count if total_count > 0 else 0

    result = {
        "label": label,
        "context_mode": context_mode,
        "avg_lcs": round(avg_lcs, 4),
        "hit_rate": round(hit_rate, 4),
        "total": total_count,
        "recall_at": {k: round(v / total_count, 4) if total_count > 0 else 0 for k, v in recall_at.items()},
        "avg_min_k": round(min_k_sum / min_k_found, 2) if min_k_found > 0 else None,
        "avg_token_per_hit": round(token_when_hit_sum / token_when_hit_count) if token_when_hit_count > 0 else None,
        "by_source": {},
    }
    for src, r in results_by_source.items():
        cnt = r["count"]
        result["by_source"][src] = {
            "avg_lcs": round(r["lcs_sum"] / cnt, 4) if cnt > 0 else 0,
            "hit_rate": round(r["hit_sum"] / cnt, 4) if cnt > 0 else 0,
            "count": cnt,
            "recall_at": {k: round(v / cnt, 4) if cnt > 0 else 0 for k, v in r["recall_at"].items()},
            "avg_min_k": round(r["min_k_sum"] / r["min_k_count"], 2) if r["min_k_count"] > 0 else None,
            "avg_token_per_hit": round(r["token_sum"] / r["token_count"]) if r["token_count"] > 0 else None,
        }
    return result, per_qa_traces


# ════════════════════════════════════════════════════════════════════
# 5. Print results
# ════════════════════════════════════════════════════════════════════

def print_comparison(results: List[dict]):
    print("\n" + "=" * 100)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 100)

    print(f"\n{'Method':<30s} {'Mode':<8s} {'Avg LCS':>8s} {'Hit@3':>8s} {'N':>6s}")
    print("-" * 65)
    for r in results:
        print(f"{r['label']:<30s} {r['context_mode']:<8s} {r['avg_lcs']:>8.4f} {r['hit_rate']:>8.4f} {r['total']:>6d}")

    print(f"\n{'Method':<30s} {'Mode':<8s} {'R@1':>7s} {'R@2':>7s} {'R@3':>7s} {'R@5':>7s} {'MinK':>7s} {'AvgTok':>8s}")
    print("-" * 85)
    for r in results:
        ra = r.get("recall_at", {})
        mk = r.get("avg_min_k")
        tk = r.get("avg_token_per_hit")
        print(f"{r['label']:<30s} {r['context_mode']:<8s} "
              f"{ra.get(1,0):>7.4f} {ra.get(2,0):>7.4f} {ra.get(3,0):>7.4f} {ra.get(5,0):>7.4f} "
              f"{mk if mk else 'N/A':>7} {tk if tk else 'N/A':>8}")

    all_sources = sorted({src for r in results for src in r.get("by_source", {})})
    if all_sources:
        print("\n" + "-" * 100)
        print("BY EVIDENCE SOURCE:")
        for src in all_sources:
            print(f"\n  [{src}]")
            print(f"  {'Method':<28s} {'Mode':<8s} {'LCS':>7s} {'R@1':>7s} {'R@3':>7s} {'MinK':>6s} {'N':>5s}")
            for r in results:
                s = r.get("by_source", {}).get(src)
                if s:
                    ra = s.get("recall_at", {})
                    mk = s.get("avg_min_k")
                    print(f"  {r['label']:<28s} {r['context_mode']:<8s} "
                          f"{s['avg_lcs']:>7.4f} {ra.get(1,0):>7.4f} {ra.get(3,0):>7.4f} "
                          f"{mk if mk else 'N/A':>6} {s['count']:>5d}")

    if len(results) >= 2:
        print("\n" + "-" * 80)
        print("DELTA (vs GT w/o EU, same context_mode):")
        baselines = {r["context_mode"]: r for r in results if r["label"] == "GT w/o EU"}
        for r in results:
            base = baselines.get(r["context_mode"])
            if base is None or r["label"] == "GT w/o EU":
                continue
            diff_lcs = r["avg_lcs"] - base["avg_lcs"]
            diff_r1 = r["recall_at"].get(1, 0) - base["recall_at"].get(1, 0)
            print(f"  [{r['context_mode']}] {r['label']:<30s}: "
                  f"LCS={diff_lcs:+.4f}  R@1={diff_r1:+.4f}")

    print("=" * 100)


# ════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Evidence Units — Retrieval Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--gt",             required=True, help="OmniDocBench GT JSON path")
    parser.add_argument("--qas",            required=True, help="Path to qas.json (distributed with this repo)")
    parser.add_argument("--output",         required=True, help="Output directory")
    parser.add_argument("--embed-model",    default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                                                           help="SentenceTransformer model name or path")
    parser.add_argument("--limit",          type=int, default=0,  help="Max pages to evaluate (0=all)")
    parser.add_argument("--top-k",          type=int, default=3,  help="Retrieval top-K")
    parser.add_argument("--docling-eu-dir", default="",           help="Pre-computed EU output dir (Docling)")
    parser.add_argument("--mineru-eu-dir",  default="",           help="Pre-computed EU output dir (MinerU)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load embedding model ──
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading embedding model: {args.embed_model}")
    embed_model = SentenceTransformer(args.embed_model)
    logger.info("Model loaded.")

    # ── Step 1: Load QAs ──
    qas = load_qas_from_file(args.qas)
    qa_image_names = {qa.image_name for qa in qas}
    all_results = []

    # ── Step 2: GT w/o EU (baseline) ──
    logger.info("Evaluating: GT w/o EU (baseline)...")
    wo_chunks = build_chunks_without_eu(args.gt, args.limit)
    logger.info(f"  {len(wo_chunks)} pages, {sum(len(v) for v in wo_chunks.values())} chunks")
    for mode in ["strict", "fair"]:
        r, _ = evaluate_retrieval(qas, wo_chunks, embed_model, args.top_k, "GT w/o EU", context_mode=mode)
        all_results.append(r)
        logger.info(f"  [GT w/o EU | {mode}] LCS={r['avg_lcs']:.4f}  R@1={r['recall_at'][1]:.4f}")

    # ── Step 3: Docling EU outputs (optional) ──
    if args.docling_eu_dir:
        for without_eu, tag in [(True, "Docling w/o EU"), (False, "Docling w/ EU")]:
            logger.info(f"Evaluating: {tag}...")
            chunks = build_chunks_from_eu_dir(args.docling_eu_dir, without_eu=without_eu, qa_image_names=qa_image_names)
            logger.info(f"  {len(chunks)} pages, {sum(len(v) for v in chunks.values())} chunks")
            for mode in ["strict", "fair"]:
                r, _ = evaluate_retrieval(qas, chunks, embed_model, args.top_k, tag, context_mode=mode)
                all_results.append(r)
                logger.info(f"  [{tag} | {mode}] LCS={r['avg_lcs']:.4f}  R@1={r['recall_at'][1]:.4f}")

    # ── Step 4: MinerU EU outputs (optional) ──
    if args.mineru_eu_dir:
        for without_eu, tag in [(True, "MinerU w/o EU"), (False, "MinerU w/ EU")]:
            logger.info(f"Evaluating: {tag}...")
            chunks = build_chunks_from_eu_dir(args.mineru_eu_dir, without_eu=without_eu, qa_image_names=qa_image_names)
            logger.info(f"  {len(chunks)} pages, {sum(len(v) for v in chunks.values())} chunks")
            for mode in ["strict", "fair"]:
                r, _ = evaluate_retrieval(qas, chunks, embed_model, args.top_k, tag, context_mode=mode)
                all_results.append(r)
                logger.info(f"  [{tag} | {mode}] LCS={r['avg_lcs']:.4f}  R@1={r['recall_at'][1]:.4f}")

    # ── Save & print ──
    print_comparison(all_results)

    result_path = output_dir / "retrieval_results.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    logger.info(f"Results saved: {result_path}")


if __name__ == "__main__":
    main()
