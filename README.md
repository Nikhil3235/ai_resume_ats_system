# 🎯 Intelligent AI ATS Resume Scorer & Explainable Feedback System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Groq-Llama--3%20LPUs-F55036?style=for-the-badge&logo=fastapi&logoColor=white" alt="Groq Llama-3"/>
  <img src="https://img.shields.io/badge/Supabase-Auth%20%26%20PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/Render-Backend%20Live-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Render"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <strong>An enterprise-grade, privacy-first Applicant Tracking System (ATS) that combines Natural Language Processing (NLP), dense semantic vector embeddings, and Generative Large Language Models (LLMs) to eliminate false-negative resume rejections and provide explainable career feedback.</strong>
</p>

---

## 🌐 Live Cloud Deployments

| Component | Platform | Live URL | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Application** | Streamlit Community Cloud | [ai-resume-ats-system-nikhil.streamlit.app](https://ai-resume-ats-system-nikhil.streamlit.app/) | ![Live](https://img.shields.io/badge/Status-Live%20Online-brightgreen?style=flat-square) |
| **RESTful API Backend** | Render Cloud Web Services | [ai-resume-ats-backend-ko4r.onrender.com](https://ai-resume-ats-backend-ko4r.onrender.com/) | ![Healthy](https://img.shields.io/badge/Status-200%20OK-brightgreen?style=flat-square) |
| **Interactive API Docs** | Swagger UI / OpenAPI 3.0 | [onrender.com/docs](https://ai-resume-ats-backend-ko4r.onrender.com/docs) | ![Interactive](https://img.shields.io/badge/Docs-Swagger%20UI-blue?style=flat-square) |

---

## 💡 Problem Statement & Architectural Motivation

Traditional Applicant Tracking Systems (ATS) reject over **75% of qualified candidate resumes** due to naive string-matching algorithms, inflexible regex parsers, and a total lack of semantic understanding:
- ❌ **Exact-Match Keyword Traps:** Qualified candidates using synonyms (*e.g., "Deep Learning"* instead of *"Neural Networks"*) are rejected.
- ❌ **Opaque "Black-Box" Rejections:** Job seekers receive cold, automated rejection emails with zero constructive feedback.
- ❌ **Unvalidated Skill Bloat:** Candidates keyword-stuff their resumes without demonstrable project or work experience proof.

**Our Solution:** An end-to-end, multi-tiered AI evaluation system combining deterministic NLP entity extraction, dense semantic vector geometry, and fine-tuned Generative AI (Meta Llama-3 on Groq LPUs) to provide fair, transparent, and actionable diagnostic audits.

---

## ✨ Key Features & Technical Highlights

- 🧠 **Dense Semantic Similarity (No Keyword Traps):** Computes continuous cosine similarity between resume qualifications and Job Descriptions (JDs) using high-dimensional vector representations.
- 📊 **Multi-Rubric Deterministic Scoring (0–100%):**
  - **Formatting & Layout Hygiene (20%):** Audits contact headers, typography, length, and parsing readability.
  - **Keyword & Competency Recall (25%):** Evaluates high-frequency technical terminology coverage.
  - **Content & Experience Impact (25%):** Analyzes action verbs, quantifiable metrics, and impact density.
  - **Project-Backed Skill Validation (15%):** Cross-validates claimed skills against described engineering deliverables using fuzzy Levenshtein distance ($\ge 75\%$).
  - **ATS Technical Compliance (15%):** Evaluates privacy risks (address/zip leakage) and non-standard formatting.
- 🤖 **Explainable AI (XAI) Feedback Engine:** Powered by Meta Llama-3 running on Groq Cloud Language Processing Units (LPUs) with **<400ms inference**, synthesizing:
  - Top candidate strengths and achievements
  - Critical ATS parsing blockers and missing keywords
  - Concrete line-by-line bullet rewrites with quantifiable metrics
- 📑 **Instant Executive PDF Scorecard Export:** Integrated pure-Python ReportLab document compiler generates camera-ready, downloadable performance audit scorecards in **<400ms**.
- 🔐 **Enterprise Identity & Security:**
  - Google OAuth 2.0 & Email/Password authentication.
  - PKCE (Proof Key for Code Exchange) flow with resilient multi-candidate verifier caching.
  - Supabase PostgreSQL database with Row Level Security (RLS) and JWT verification.
- ⚡ **Ultra-Low Memory Footprint (<55MB RAM):** Optimized lazy-loading architecture ensuring zero Out-Of-Memory (OOM) crashes on low-resource cloud containers (Render Free Tier 512MB RAM).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER (STREAMLIT CLOUD)                  │
│   • Drag-and-Drop Resume Ingestion (PDF / DOCX)                             │
│   • Target Job Description Comparison View                                  │
│   • Plotly Analytical Radar Charts & Compatibility Gauges                   │
│   • 1-Click Executive PDF Audit Report Download                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / REST (Pydantic V2)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER (FASTAPI + UVICORN)                   │
│   • Endpoint: POST /api/v1/analyze-resume                                   │
│   • Asynchronous File Ingestion & Parsing (pdfplumber, python-docx)         │
│   • CORS Security & Bearer Token Authentication Gatekeeper                  │
└──────────────┬───────────────────────┬───────────────────────┬──────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────┐
│   LINGUISTIC NLP ENGINE │ │   SEMANTIC VECTORIZER   │ │ GROQ LLM INFERENCE │
│  • spaCy en_core_web_sm │ │  • L2 Normalized        │ │  • Meta Llama-3    │
│  • Tokenization & Lemmat│ │    HashingVectorizer    │ │  • Sub-400ms LPU   │
│  • Named Entity Recog   │ │  • Cosine Similarity    │ │  • JSON Feedback   │
│    (Skills, Exp, Edu)   │ │    Sim(v_r, v_jd)       │ │  • XAI Rewrites    │
└──────────────┬──────────┘ └──────────┬──────────────┘ └────────┬───────────┘
               │                       │                         │
               └───────────────────────┼─────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE & SECURITY (SUPABASE CLOUD)                  │
│   • Cloud PostgreSQL Database (User Analysis History & Telemetry)           │
│   • Row Level Security (RLS) & JWT Token Enforcement                        │
│   • Google OAuth 2.0 PKCE Session Management                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Formulation & Scoring Rubrics

### 1. Cosine Semantic Similarity
Given candidate resume vector $\vec{v}_r$ and job description vector $\vec{v}_{jd}$ in $n$-dimensional Euclidean space:

$$\text{Cosine Similarity}(\vec{v}_r, \vec{v}_{jd}) = \frac{\vec{v}_r \cdot \vec{v}_{jd}}{\|\vec{v}_r\| \|\vec{v}_{jd}\|} \quad \in [0.0, 1.0]$$

### 2. Job Description Match Percentage
Combines discrete fuzzy keyword coverage ($60\%$) with continuous dense semantic alignment ($40\%$):

$$\text{JD Match \%} = \left[ 0.60 \times \left(\frac{\text{Matched Keywords}}{\text{Total JD Keywords}}\right) + 0.40 \times \text{Cosine Similarity} \right] \times 100$$

### 3. Overall Composite ATS Score
Aggregates five orthogonal evaluation dimensions:

$$\text{Score}_{\text{total}} = 0.20 \cdot S_{\text{formatting}} + 0.25 \cdot S_{\text{keywords}} + 0.25 \cdot S_{\text{content}} + 0.15 \cdot S_{\text{skills}} + 0.15 \cdot S_{\text{compliance}}$$

---

## 🛠️ Tech Stack & Ecosystem

| Layer | Technologies | Role / Justification |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.10+, Uvicorn | Core runtime environment with asynchronous ASGI concurrency |
| **Backend API** | FastAPI, Pydantic V2 | High-performance RESTful routing and data contract validation |
| **Frontend UI** | Streamlit Community Cloud | Reactive, stateful single-page web dashboard with Plotly charts |
| **GenAI & LLM** | Groq Cloud API, Meta Llama-3 | Ultra-fast LPU inference (<400ms) for qualitative resume feedback |
| **NLP & Vectors** | spaCy (`en_core_web_sm`), Scikit-Learn | Industrial entity recognition and memory-efficient L2 vectorization |
| **Matching Algorithms** | RapidFuzz | Microsecond-level Levenshtein fuzzy string distance calculation |
| **Database & Auth** | Supabase (PostgreSQL), JWT, PKCE | Secure user identity, audit logging, and Row Level Security |
| **Document Processing** | ReportLab, pdfplumber, python-docx | Multi-format resume parsing and pure-Python dynamic PDF generation |
| **DevOps & Cloud** | Render, Streamlit Cloud, GitHub | Cloud continuous deployment and zero-downtime hosting |

---

## 📂 Project Structure

```
ai_resume_ats_system/
├── backend/
│   ├── api/
│   │   ├── auth.py                  # Supabase JWT token verification
│   │   └── routes.py                # RESTful endpoints (/analyze-resume, /health, /history)
│   ├── core/
│   │   └── config.py                # System settings, score weights, CORS configuration
│   ├── models/
│   │   └── schemas.py               # Pydantic V2 data validation schemas
│   ├── services/
│   │   ├── ats_scorer.py            # 5-pillar scoring engine & privacy detection
│   │   ├── embedder.py              # Lightweight L2 vectorizer (<50MB RAM footprint)
│   │   ├── feedback_engine.py       # Algorithmic issue identification & recommendations
│   │   ├── groq_parser.py           # Groq LLM parsing & structured JSON synthesis
│   │   ├── jd_matcher.py            # Resume vs. Job Description semantic matcher
│   │   ├── pdf_export.py            # ReportLab camera-ready PDF audit scorecard compiler
│   │   ├── resume_analyzer.py       # Orchestration pipeline linking NLP + Scoring + LLM
│   │   └── resume_parser.py         # Multi-format document stream extractor (PDF/DOCX)
│   ├── utils/
│   │   ├── file_utils.py            # Document hygiene utilities
│   │   └── matching.py              # Fuzzy keyword matching algorithms
│   └── main.py                      # FastAPI application entrypoint with lazy model loading
├── frontend/
│   ├── assets/
│   │   └── styles.css               # Professional dark-mode UI stylesheet
│   ├── services/
│   │   ├── api_client.py            # REST client communicating with Render backend
│   │   └── supabase_client.py       # Client-side auth, PKCE cache, and user sessions
│   ├── views/
│   │   ├── auth_view.py             # User authentication screens
│   │   ├── history_view.py          # Candidate previous analysis dashboard
│   │   ├── landing.py               # Product features & landing page
│   │   ├── resources.py             # ATS tips, resume guides & action verb glossary
│   │   └── scorer_view.py           # Core resume analysis, scorecards & PDF export
│   └── streamlit_app.py             # Streamlit single-page application entrypoint
├── RUN_PROJECT.bat                  # 1-Click local development launcher
├── requirements.txt                 # Clean, memory-optimized production dependencies
└── README.md                        # Project documentation
```

---

## 🚀 Local Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Nikhil3235/ai_resume_ats_system.git
cd ai_resume_ats_system
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate
```

### 3. Install Production Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Groq Cloud API Key
GROQ_API_KEY=your_groq_api_key_here

# Supabase Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# Service Endpoints
API_BASE_URL=http://localhost:8000
AUTH_REDIRECT_URL=http://localhost:8501
```

### 5. Launch the Application

#### Option A: 1-Click Batch Launcher (Windows)
Double-click `RUN_PROJECT.bat` or run:
```cmd
RUN_PROJECT.bat
```

#### Option B: Manual Execution
**Terminal 1 (Backend API):**
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend Dashboard):**
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

Access the frontend at `http://localhost:8501` and interactive API docs at `http://localhost:8000/docs`.

---

## 📡 RESTful API Documentation

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health check endpoint returning API readiness status | ❌ No |
| `POST` | `/api/v1/analyze-resume` | Ingests PDF/DOCX resume + optional JD, returns full analysis | ✅ Yes (Bearer JWT) |
| `GET` | `/api/v1/history` | Retrieves authenticated user's past evaluation scorecards | ✅ Yes (Bearer JWT) |
| `DELETE`| `/api/v1/history/{id}` | Permanently deletes a specific evaluation record | ✅ Yes (Bearer JWT) |

### Sample Analysis Response:
```json
{
  "overall_score": 84.5,
  "component_scores": {
    "formatting": 88.0,
    "keywords": 82.5,
    "content": 85.0,
    "skill_validation": 80.0,
    "ats_compatibility": 87.5
  },
  "jd_comparison": {
    "match_percentage": 78.4,
    "semantic_similarity": 0.812,
    "matched_keywords": ["Python", "FastAPI", "Docker", "PostgreSQL", "NLP"],
    "missing_keywords": ["Kubernetes", "Redis", "CI/CD Pipeline"],
    "skills_gap": ["Distributed Systems", "Cloud Deployment"]
  },
  "detailed_feedback": [
    {
      "category": "Impact",
      "severity": "medium",
      "message": "Add quantifiable metrics (e.g., % improvement, revenue growth) to experience bullet points."
    }
  ]
}
```

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute for academic and professional purposes.

---

<p align="center">
  Built with ❤️ by <strong>Nikhil Mali</strong> | Powered by <strong>FastAPI</strong>, <strong>Streamlit</strong>, <strong>Groq Cloud</strong>, and <strong>Supabase</strong>
</p>
