<div align="center">

<img src="assets/banner.png" alt="Evidence Units Banner" width="800"/>

**English** | [한국어](docs/README_KO.md)

[![GitHub stars](https://img.shields.io/github/stars/hanyeonjee/evidence-units?style=social)](https://github.com/hanyeonjee/evidence-units/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/hanyeonjee/evidence-units?style=social)](https://github.com/hanyeonjee/evidence-units/network/members)
[![arXiv](https://img.shields.io/badge/arXiv-2025-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/XXXX.XXXXX)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)
[![Dataset](https://img.shields.io/badge/Dataset-OmniDocBench-blue)](https://huggingface.co/datasets/opendatalab/OmniDocBench)

**Evidence Units** is a parser-independent document organization framework that groups visual assets with their contextual text into semantically complete retrieval units — achieving consistent retrieval gains across any document parser.

</div>

---

## 🔍 What is an Evidence Unit?

An **Evidence Unit (EU)** is a semantically complete document unit that groups visual assets (tables, charts, figures) with their contextual text (captions, headers, labels, paragraphs) — constructed through ontology-grounded normalization that works regardless of which document parser you use.

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
| `qas.json` | 1,551 QA pairs generated from OmniDocBench v1.0 |

> Full EU construction pipeline is not included in this release.

---

## 🚀 Quick Start

```bash
git clone https://github.com/hanyeonjee/evidence-units
cd evidence-units
pip install sentence-transformers numpy
```

```bash
# Baseline evaluation (GT annotations, element-level)
python eval_retrieval.py \
    --gt   OmniDocBench.json \
    --qas  qas.json \
    --output results/
```

```bash
# Cross-parser evaluation with pre-computed EU outputs
python eval_retrieval.py \
    --gt              OmniDocBench.json \
    --qas             qas.json \
    --output          results/ \
    --docling-eu-dir  path/to/eu_docling \
    --mineru-eu-dir   path/to/eu_mineru
```

---

## 📊 Results on OmniDocBench (1,340 pages · 1,551 QA pairs)

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
