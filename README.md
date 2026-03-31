# 📄 Evidence Units

> **Evidence Units: Ontology-Grounded Document Organization for Parser-Independent Retrieval**
> *Yeonjee Han — GenApp Tech, KT (Korea Telecom)*

[![arXiv](https://img.shields.io/badge/arXiv-2025-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/XXXX.XXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Dataset](https://img.shields.io/badge/Dataset-OmniDocBench-blue)](https://huggingface.co/datasets/opendatalab/OmniDocBench)

---

## 🔍 What is an Evidence Unit?

An **Evidence Unit (EU)** is a semantically complete document chunk that groups visual assets (tables, charts, figures) with their contextual text (captions, headers, labels, paragraphs) — built through ontology-grounded normalization that works regardless of which document parser you use.

```
┌─────────────────────────────────────┐
│  section_header  "2.2 Methods"      │
│  table           [HTML data]        │  ← Evidence Unit
│  unit_label      "(Unit: mg/L)"     │
│  support_para    "As shown above…"  │
└─────────────────────────────────────┘
```

**Key property**: EU spatial footprints converge across parsers (MinerU, Docling, etc.) even when individual bounding boxes differ — making downstream retrieval parser-independent.

---

## 📦 This Repository

This repo releases the evaluation code and QA pairs used in the paper.

| File | Description |
|---|---|
| `eval_retrieval_combined.py` | Retrieval evaluation script (LCS, Recall@K, MinK) |
| `qas.json` | 4,107 QA pairs generated from OmniDocBench v1.0 |

> Full EU construction pipeline is not included in this release.

---

## 🚀 Quick Start

```bash
git clone https://github.com/yeonjee-han/evidence-units
cd evidence-units
pip install -r requirements.txt
```

```bash
# Run evaluation against your chunked output
python eval_retrieval_combined.py \
    --chunks your_chunks.json \
    --qas qas.json \
    --output results.json
```

---

## 📊 Results on OmniDocBench (1,355 pages · 4,107 QA pairs)

| Method | Avg LCS | Recall@1 | MinK ↓ |
|---|---|---|---|
| w/o EU (baseline) | 0.4417 | 0.157 | 2.70 |
| **w/ EU (ours)** | **0.7172** | **0.406** | **2.00** |
| Δ | **+0.275** | **+0.249** | **−0.70** |

Cross-parser consistency: ΔLCS ≈ +0.26–0.28 across GT, MinerU, and Docling.

---

## 🗂️ QA Pair Format

```json
{
  "qa_id": "omnidoc_table_0042",
  "type": "table",
  "question": "Table 1. Water quality in the experiments.",
  "evidence_node_ids": ["node_012", "node_013", "node_014"],
  "page_id": "scihub_page_002"
}
```

`type` is one of `table` · `figure` · `text`.

---

## 📝 Citation

```bibtex
@article{han2025evidenceunits,
  title     = {Evidence Units: Ontology-Grounded Document Organization
               for Parser-Independent Retrieval},
  author    = {Han, Yeonjee},
  journal   = {arXiv preprint arXiv:XXXX.XXXXX},
  year      = {2025}
}
```

---

## 📬 Contact

Questions or issues → [yeonjee.han@kt.com](mailto:yeonjee.han@kt.com)
