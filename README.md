# SIH 2026 — PS ID 26103
# AI-Powered Predictive Analytics & Early Warning System for Infrastructure Project Monitoring

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-100%25-green.svg)]()

> **Organization:** Ministry of Statistics & Programme Implementation (MoSPI)
> **Data Source:** PAIMANA / OCMS Flash Reports | **PS ID:** 26103

## Overview

An AI-powered system that transforms India's infrastructure project monitoring from descriptive reporting to **predictive and prescriptive decision-support**. The system ingests monthly PAIMANA Flash Report PDFs, builds a longitudinal time-series dataset, trains ML models to predict cost overruns, time delays, and project risks, and serves insights through an explainable AI dashboard.

## Key Features

- **Cost Overrun Prediction** — Predict which projects will experience cost escalation
- **Time Delay Prediction** — Forecast schedule delays before they materialize
- **Project Risk Scoring** — Composite 0–100 risk score per project
- **Early Warning System** — Hybrid rule + ML alerts for proactive intervention
- **Explainable AI** — SHAP-based plain-language reasons for every risk flag
- **Interactive Dashboard** — Executive overview, drilldowns, and alerts

## Architecture

```
14 PAIMANA PDFs → PDF Extraction → Longitudinal Panel Dataset
  → Feature Engineering → ML Models (XGBoost/LightGBM)
  → Risk Scoring → Early Warning Engine
  → FastAPI Backend → React Dashboard → Decision-Making
```

## Project Structure

```
├── data/               # Data pipeline (PDFs → raw → master)
├── ml/                 # ML notebooks, features, models
├── backend/            # FastAPI REST API
├── frontend/           # React + TypeScript dashboard
├── infra/              # Docker, Nginx, monitoring
├── docs/               # Documentation
├── docker-compose.yml  # Full stack orchestration
└── requirements.txt    # Python dependencies
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Java Runtime (for tabula-py)

### Setup

```bash
# Clone the repository
git clone <repo-url>

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Start infrastructure services
docker-compose up -d postgres redis mlflow

# Run PDF extraction pipeline
python data/scripts/extract_report.py

# Run preprocessing pipeline
python data/scripts/merge_reports.py
python data/scripts/clean_master.py
python data/scripts/validate_master.py
```

## Tech Stack

| Layer | Technology |
|---|---|
| PDF Extraction | pdfplumber, camelot-py, tabula-py |
| Data Processing | pandas, numpy, rapidfuzz |
| ML Modeling | scikit-learn, XGBoost, LightGBM, CatBoost |
| Explainability | SHAP |
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | React, TypeScript, Vite, Recharts |
| DevOps | Docker, GitHub Actions, Prometheus |

## Dataset

14 monthly PAIMANA Flash Reports (July 2025 – August 2026) covering ~1,981 infrastructure projects across 17 Ministries and 22 sectors, with an aggregate cost of ~₹42.78 lakh crore.

