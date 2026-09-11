# PharmacyGuard — Setup & Deployment Guide

> 🌐 **Evaluating the Live Application?**  
> Skip local configuration and test immediately at: **[https://pharmacy-guard.vercel.app/](https://pharmacy-guard.vercel.app/)**  
> *(Pre-deployed with Amazon Bedrock and Strands Agent integration)*

This guide walks you through running **PharmacyGuard** locally on your workstation or deploying it to cloud infrastructure for evaluation and hackathon judging.

---

## Requirements

Ensure your machine meets the following prerequisites before proceeding:

- **Python:** Version `3.10.x`, `3.11.x`, or `3.12.x`
- **Node.js:** Version `18.x` or higher (includes `npm`)
- **AWS account:** Active AWS account with permissions for Amazon Bedrock
- **AWS credentials:** Valid AWS Access Key / Secret Key or an `AWS_BEARER_TOKEN_BEDROCK` API key
- **Amazon Bedrock model access:** Model access enabled for Anthropic Claude Sonnet (`us.anthropic.claude-sonnet-4-6` or `us.anthropic.claude-3-5-sonnet-20241022-v2:0`) in region `us-east-1`
- **Strands Agents SDK:** `strands-agents>=1.0.0` (installed via Python dependencies)

*(Note: If you do not have active AWS credentials, PharmacyGuard's built-in **Deterministic Fallback Engine** enables testing of all verification checks, inventory tracking, and student simulation workflows offline).*

---

## Clone Repository

Clone the project repository to your local machine and navigate into the root directory:

```powershell
git clone https://github.com/Nana-996/PharmacyGuard.git
cd PharmacyGuard
```

---

## Backend Setup

Set up a Python virtual environment and install the required dependencies:

### 1. Create Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Verify the backend packages are properly installed:
```powershell
python -c "import fastapi, strands, pydantic, boto3; print('Backend dependencies successfully verified!')"
```

---

## Frontend Setup

In a separate terminal window, install the React and Vite dependencies:

```powershell
cd frontend
npm install
```

Verify that the frontend builds cleanly without TypeScript or bundler errors:
```powershell
npm run build
```

---

## Environment Variables

Copy the `.env.example` template to create your local `.env` configuration file:

**On Windows (PowerShell):**
```powershell
copy .env.example .env
```

**On Linux / macOS:**
```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```ini
# ==============================================================================
# Amazon Bedrock Authentication
# ==============================================================================
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_bearer_token_here
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6

# ==============================================================================
# Security & JWT Session Configuration
# ==============================================================================
# If omitted or blank, an ephemeral CSPRNG secret is automatically generated per session:
JWT_SECRET_KEY=pharmacyguard-dev-secret-key-2026-hackathon
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000

# ==============================================================================
# Server & Environment Configuration
# ------------------------------------------------------------------------------
# Deployment mode reported by /health (e.g. competition_demo, production, staging, local_development):
ENVIRONMENT=competition_demo
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173

# ==============================================================================
# Competition Demo Guardrails & Rate Limiting
# ==============================================================================
DEMO_RATE_LIMIT_ENABLED=true
DEMO_MAX_REQ_PER_MINUTE=60
DEMO_MAX_AGENT_CALLS_PER_SESSION=20
DEMO_RESTRICT_ARBITRARY_PATIENTS=true
```

---

## Database Setup

PharmacyGuard uses a dual SQLite database architecture (`pharmacyguard.db` and `hospital_sim.db`) that automatically seeds on initial startup. To explicitly seed or reset the database with the preloaded test cases, run:

```powershell
python -c "from backend.data.database import initialize_database; initialize_database()"
```

This populates:
- **5 Preloaded Clinical Test Prescriptions:** (`RX-1001` through `RX-1005`)
- **50+ Hospital Pharmacy Formulary Items:** Live stock levels, batch numbers, and reorder levels
- **Clinical Guidelines & Interaction Knowledge Base:** Indication rules, allergy cross-reactivity matrices, and dosage boundaries
- **4 Demo User Accounts:** Staff Pharmacist, Chief Pharmacist, Pharmacy Student, and System Admin

---

## AWS Configuration

To enable Amazon Bedrock model inference, configure your AWS authentication via one of the following methods:

### Option A: AWS Bearer Token / API Key (Recommended for Quick Testing)
Add your Bedrock API token directly to `.env`:
```ini
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_bearer_token_here
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
```

### Option B: AWS CLI Credentials
If using the AWS CLI, configure standard IAM credentials:
```powershell
aws configure
```
- **AWS Access Key ID:** `YOUR_ACCESS_KEY`
- **AWS Secret Access Key:** `YOUR_SECRET_KEY`
- **Default region name:** `us-east-1`

### Test Bedrock Connectivity
Verify your Bedrock connection and model invocation with the built-in diagnostic test:
```powershell
python -m backend.tests.test_bedrock_connection
```

---

## Start Backend

Launch the FastAPI ASGI application with live reloading:

```powershell
# Ensure virtual environment is active
.venv\Scripts\activate

# Start Uvicorn on port 8000
python -m uvicorn backend.main:app --reload --port 8000
```

- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Start Frontend

In your frontend terminal window, start the Vite development server:

```powershell
cd frontend
npm run dev
```

The Vite dev server will start on port `5173`.

---

## Access Application

Open your browser and navigate to:

**[http://localhost:5173](http://localhost:5173)**

### One-Click Demo Login Accounts:
Use the quick sign-in cards on the login screen to test each role:

| Role | Profile | Email | Password | Primary Features |
|---|---|---|---|---|
| 🩺 **Staff Pharmacist** | Dr. Alex Reed, PharmD | `staff.pharmacist@hospital.dev` | `DevStaff123!` | Review queue, AI clinical checks, approve/override workflows |
| 📊 **Chief Pharmacist** | Dr. Eleanor Vance, PharmD | `chief.pharmacist@hospital.dev` | `DevChief123!` | Workload analytics, override audit ledger, inventory health |
| 🎓 **Pharmacy Student** | Sam Taylor, Intern | `student@hospital.dev` | `DevStudent123!` | Blind clinical simulations, case quizzes, AI coaching scores |

---

## Cloud Deployment (Vercel & Render Architecture)

For public evaluation and competition judging, PharmacyGuard is deployed as a high-availability split-architecture system:

```
┌─────────────────────────────────┐           ┌──────────────────────────────────────┐
│       Vercel Global CDN         │           │             Render PaaS              │
│    (React 19 + Tailwind v4)     │  REST/JWT │       (FastAPI + Strands Agent)      │
│  https://pharmacy-guard.vercel.app  │ ────────> │   https://pharmacyguard.onrender.com   │
└─────────────────────────────────┘           └───────────────────┬──────────────────┘
                                                                  │
                                                                  ▼
                                                      ┌───────────────────────────────┐
                                                      │        Amazon Bedrock         │
                                                      │  (Claude Sonnet in us-east-1) │
                                                      └───────────────────────────────┘
```

### 1. Frontend on Vercel
- **Repository Root:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable (Config):**
  - `VITE_API_URL`: `https://pharmacyguard.onrender.com`

### 2. Backend on Render
- **Environment:** Python 3 Web Service
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `AWS_BEARER_TOKEN_BEDROCK`: *(Bedrock API Key)*
  - `AWS_DEFAULT_REGION`: `us-east-1`
  - `BEDROCK_MODEL_ID`: `us.anthropic.claude-sonnet-4-6`
  - `CORS_ALLOWED_ORIGINS`: `*`

### 3. Zero Downtime Keep-Alive
- A free 10-minute HTTP ping is active via **UptimeRobot** against `https://pharmacyguard.onrender.com/health` to prevent cold starts during hackathon judging.

