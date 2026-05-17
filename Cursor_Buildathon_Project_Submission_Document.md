# CURSOR BUILDATHON
## PROJECT SUBMISSION DOCUMENT — Agri-Lend

**Track Technologies:** CURSOR | ELEVENLABS | OPENAI | GEMINI | VERCEL (Next.js) | Supabase  
**Partners:** CURSOR × TECHTALK360

---

### INSTRUCTIONS
* Completed submission for **Agri-Lend** by **Team Fortress**, based on `project.md`, the live codebase, and cited external references.
* *Confidential - For Authorized Use Only*

---

## TABLE OF CONTENTS
* **01** Project Overview
* **02** Problem Statement
* **03** Proposed Solution
* **04** Functional Requirements
* **05** Non-Functional Requirements
* **06** Technical Architecture
* **07** Security
* **08** User Stories & Use Cases
* **09** Target Users & Market
* **10** Business Model
* **11** Why This Project Leads the Track
* **12** Team & Roles

---

## SECTION 01: Project Overview

### Project Name & One-Line Pitch

**Agri-Lend** — Voice-first, AI-powered micro-credit underwriting for Sri Lankan smallholder farmers, from field conversation to bank disbursement in minutes.

### Summary

Smallholder farmers in Sri Lanka often wait weeks for manual credit decisions that depend on paper forms and physical inspections. **Agri-Lend** replaces that friction with a **voice-first** pipeline (primarily **English** via **ElevenLabs**): farmers speak their loan needs, upload crop evidence, and trigger a **multi-agent backend** that analyzes field imagery and market embeddings (**Google Gemini**), localized risk (**vector RAG** on Supabase), and a deterministic risk score (**OpenAI GPT-4o**). Approved loans complete with a disbursement reference; banking flows use the Seylan hackathon sandbox where available.

The product is built for **farmers** (intake and status) and **lenders / demo operators** (pipeline visibility). Core value is faster, evidence-based credit decisions grounded in agronomic and regional economic signals—not generic chatbot forms.

### Submission Details

| Field | Value |
|--------|--------|
| **Track** | Cursor Buildathon — multi-technology track (Cursor, ElevenLabs, OpenAI, Gemini, Vercel) |
| **Track integration** | **Cursor:** end-to-end build via Composer against `project.md`. **Gemini:** crop image analysis (`VisionAgronomistAgent`) and **market RAG embeddings** (primary embedding path for `match_market_intelligence`). **Vercel:** production deploy — [frontend](https://cursor-buildathon-project-c3e8.vercel.app/) and [backend API](https://cursor-buildathon-project-huiw.vercel.app/). **ElevenLabs + OpenAI:** English voice-first intake and structured underwriting logs. |
| **Team name** | **Fortress** |
| **Demo URL (frontend)** | https://cursor-buildathon-project-c3e8.vercel.app/ |
| **Demo URL (backend)** | https://cursor-buildathon-project-huiw.vercel.app/ (health: `/health`) |
| **Repository** | https://github.com/AstrelSD/Cursor-Buildathon-Project |

---

## SECTION 02: Problem Statement

### The Problem

Rural micro-credit for Sri Lankan smallholders remains **slow, document-heavy, and inconsistent**. Institutions struggle to verify declared acreage, crop health, and local market exposure without costly field visits. Farmers lose planting windows when capital arrives too late or is denied without transparent reasoning.

If unsolved, underserved farmers continue relying on informal lenders at higher cost, while banks bear operational overhead and elevated default risk from incomplete agronomic data.

### Why It Matters

**Who:** Smallholder farmers (often 1–5 acres) in districts such as Anuradhapura, Polonnaruwa, Ampara, Kurunegala, and Nuwara Eliya—plus rural finance officers evaluating their applications.

**Context:** Seasonal planting cycles, weather volatility, and district-level crop price swings make timing and localized risk assessment critical.

**Frequency & severity:** Credit need is **recurring every season**; delays of even 2–4 weeks can mean missed sowing or emergency borrowing. Policy and industry attention on rural credit has increased—e.g. Sri Lanka’s recurring **“Sarusara” rural credit subsidy** programs and EU-backed **AgriFI** windows targeting thousands of smallholders ([Asian Mirror, 2025](https://asianmirror.lk/news/2598/sarusara-rural-credit-scheme-to-be-implemented-annually-from-2025/); [EDFI MC, 2025](https://edfimc.eu/european-union-financed-agrifi-launches-country-window-sri-lanka-to-boost-smallholder-farmers/)).

**Current workarounds:** Paper applications, branch visits, and manual officer judgment. These fall short because they **do not scale**, are **weak on multimodal field proof**, and rarely incorporate **real-time localized market/weather vectors** in a single automated decision.

### Root Cause

The underlying cause is a **data and workflow gap**: agronomic truth (what is actually growing, how healthy it is, how large the plot is) and localized economic risk (district crop volatility, weather exposure) are **not fused at decision time** in a low-latency, auditable system farmers can use without branch visits.

---

## SECTION 03: Proposed Solution

### What the Product Does

Agri-Lend is a **split-brain, multi-agent underwriting engine**:

1. **Intake** — Farmer registers (Supabase Auth), then uses **voice** (ElevenLabs Agents) or a **web form** to supply crop type, acreage, and LKR amount. Transcripts are parsed by `ConversationCoordinator` (GPT-4o with Gemini/heuristic fallback) into structured fields and a `draft` loan row.
2. **Evidence** — Farmer uploads a crop image (JPEG/PNG/WebP, ≤10 MB) to Supabase Storage via the API or client uploader.
3. **Evaluation** — `POST /api/loans/{id}/evaluate` returns **202 Accepted** and runs `run_evaluation_pipeline` in the background:
   - **VisionAgronomistAgent** (Gemini) estimates acreage, health, disease signals, canopy metrics.
   - **MarketIntelligenceRagAgent** embeds district+crop context and queries `match_market_intelligence` (pgvector).
   - **QuantUnderwriterAgent** computes a weighted risk score; if ≤ threshold (default **45**), triggers **Seylan sandbox** CEFTS disbursement (or mock).
4. **Outcome** — Loan status moves `analyzing` → `underwriting` → `approved` → `disbursed` (or `rejected` with reason). Farmer dashboard shows history; repayment via **LankaQR** or **CEFTS** when configured.

### Key Features

| Feature | User need addressed |
|---------|---------------------|
| **RealtimeVoiceConsole** (ElevenLabs) | Voice-first, **English** conversational intake (form fallback for other languages). |
| **Structured voice → loan API** (`/api/voice/intake`) | No paper forms; instant draft loan from conversation transcript. |
| **Multimodal crop upload** | Prove field condition without an in-person agronomist visit. |
| **Parallel vision + market agents** | Faster enrichment; agronomic + economic risk in one pass. |
| **Deterministic risk scoring + GPT-4o audit logs** | Transparent, repeatable approve/reject with human-readable traces. |
| **Seylan disbursement & repayment APIs** | End-to-end “money movement” story for hackathon judges. |
| **Farmer dashboard + Supabase Realtime** | Live status updates on applications and repayments. |
| **Docker Compose stack** | Repeatable demo: API `:8000`, frontend `:3000`. |

### Scope

**In scope (this build):**
- Supabase Auth (register/login), profiles with Sri Lankan phone (`+94…`) and district.
- Full loan lifecycle states including `repayment_pending` and `repaid`.
- Multi-agent evaluation pipeline with idempotent re-evaluation guards.
- Hackathon Seylan sandbox wiring (disbursement/QR mocked when sandbox posting failed; account balance inquiry path retained).
- Voice intake + manual form fallback on `/apply`.

**Out of scope (deliberate):**
- Licensed production banking core integration (sandbox only).
- Mobile native apps (responsive web only).
- Legal KYC/AML beyond basic profile fields.
- **`UnderwritingTerminal.tsx` UI component** — log message helpers exist in `frontend/lib/loan-logs.ts` and Realtime is enabled on `loans`, but a dedicated terminal panel is not yet mounted in the UI (apply flow uses step progress + polling).
- MIRO / VO track tools — not present in runtime codebase (architecture documented in `project.md`).

---

## SECTION 04: Functional Requirements

### Must Have (all demonstrable)

| ID | Requirement |
|----|-------------|
| M1 | User can register/login with Supabase Auth and create a profile (name, `+94` phone, district). |
| M2 | Authenticated user can create a **draft** loan with crop, acreage ≥ 0, amount ≥ LKR 5,000. |
| M3 | User can upload crop evidence; system stores path in `multimodal_evidence_url`. |
| M4 | `POST /api/loans/{id}/evaluate` queues pipeline and returns **202**; status becomes `analyzing`. |
| M5 | Vision agent writes `ai_verified_acreage` and `crop_health_matrix`; market agent writes `market_volatility_index`. |
| M6 | Underwriter sets `calculated_risk_score`; rejects if score > `RISK_REJECTION_THRESHOLD` (45). |
| M7 | Approved loans transition to `disbursed` with `transaction_reference`. |
| M8 | Rejected loans include `rejection_reason` (e.g. unreadable imagery, risk threshold). |
| M9 | Re-evaluation blocked for `approved`, `disbursed`, `underwriting`, or concurrent `analyzing`. |
| M10 | Voice path: ElevenLabs session → transcript → `/api/voice/intake` → draft loan. |

### Should Have

| ID | Requirement |
|----|-------------|
| S1 | Farmer dashboard lists loans with realtime subscription updates. |
| S2 | Repayment via dynamic LankaQR (`/repayment/qr`) and CEFTS (`/repayment/cefts`). |
| S3 | Payout account captured on profile for CEFTS destination. |
| S4 | `GET /health` reports integration readiness (OpenAI, Gemini, ElevenLabs, Supabase). |
| S5 | Field health confidence UI on apply page after vision completes. |
| S6 | Gemini/OpenAI fallback chains for intake, embeddings, and vision retries. |

### Could Have / Won't Have (This Build)

| ID | Item | Decision |
|----|------|----------|
| C1 | Dedicated Underwriting Terminal UI | **Could** — helpers ready; **not shipped** as component. |
| C2 | Video evidence (not only images) | **Won't** — image MIME types only in API validation. |
| C3 | Officer/admin multi-tenant RBAC | **Won't** — farmer-centric auth only. |
| C4 | Multilingual voice (Tamil/Sinhala) | **Won't** — voice agent is **English-first**; Sinhala/Tamil supported in text intake parsing only. |
| C5 | Full live Seylan posting in demo | **Won't** — sandbox transfer/QR endpoints unstable; mock responses used except balance checks. |

---

## SECTION 05: Non-Functional Requirements

### Performance

- **Evaluate trigger:** HTTP **202** immediately; pipeline runs in FastAPI `BackgroundTasks` (target: user sees `analyzing` within ~1–2 s via poll/realtime).
- **Vision + market:** Parallelized via `asyncio.gather` in `evaluation.py` to reduce wall-clock vs sequential agents.
- **Typical pipeline:** Depends on Gemini/OpenAI latency (often **15–60 s** for vision + embed + underwrite); acceptable for async underwriting demo.
- **Concurrent usage:** Single-tenant hackathon demo; Supabase client uses retry (3×) on `httpx.ConnectError`. Scale-out would require job queue (Redis/Celery) instead of in-process background tasks.

### Reliability & Error Handling

- **Unreadable / missing evidence:** Status `rejected` with `"Evaluation failed: Crop imagery unreadable."`
- **Gemini quota:** `VisionQuotaError` with actionable message; optional `MOCK_VISION_ON_FAILURE=true` for demos.
- **Market RAG failure:** Reject with market unavailable message; vector match falls back to exact crop+district row, then defaults (`DEFAULT_MARKET`).
- **Bank errors:** Disbursement/repayment use mock fallbacks when Seylan sandbox posting fails; account balance inquiry may still call live sandbox when configured.
- **Supabase down:** `503` on API routes with configuration guidance.

### Usability

- **Design:** Green agrarian theme, glass-style panels, step-based apply flow (“Tell us → Upload → Get approved”).
- **Accessibility:** Voice alternative to forms; semantic status labels; loading states on async actions.
- **i18n:** **English-first** voice UI and application copy; `ConversationCoordinator` can still parse Tamil/Sinhala phrases in written transcripts if entered manually.

### Scalability

- **Today:** Monolithic FastAPI + Supabase BaaS + object storage.
- **To scale:** Move evaluation to queued workers; cache embeddings; read replicas; tighten RLS (remove demo `using (true)` policies); CDN for evidence images; separate voice token service rate limits.

---

## SECTION 06: Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NEXT.JS 15 FRONTEND (App Router)                        │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐ │
│  │ RealtimeVoiceConsole│  │ ApplyPageClient       │  │ FarmerDashboard │ │
│  │ (@elevenlabs/react) │  │ + MultimodalUploader  │  │ + RepaymentPanel│ │
│  └──────────┬──────────┘  └──────────┬───────────┘  └────────┬────────┘ │
└─────────────┼────────────────────────┼─────────────────────────┼──────────┘
              │ REST /api/voice/*       │ REST /api/loans/*       │ Supabase Realtime
              ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND (Python 3.x)                         │
│  routers: loan.py | voice.py | profile.py                                   │
│  services: evaluation.py | loan_intake.py | seylan_api_service.py         │
│  agents: conversation_coordinator | vision_agronomist | market_rag |      │
│          quant_underwriter                                                  │
└─────────────┬───────────────────────────────┬───────────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────────┐
│ OpenAI GPT-4o               │   │ Google Gemini (vision + embeddings)      │
│ ElevenLabs (signed WS URL)  │   │ Seylan sandbox (CEFTS, QR, Inquiry)       │
└─────────────────────────────┘   └─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SUPABASE: Postgres + Auth + Storage + pgvector (market_intelligence)        │
│ Tables: profiles | loans | market_intelligence                              │
│ RPC: match_market_intelligence(query_embedding, match_count)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **IDE / build** | Cursor Composer | Spec-driven generation from `project.md`; rapid multi-file coherence. |
| **Frontend** | Next.js 15, React, Tailwind | Modern SSR/CSR, Vercel-deployable, fast UI iteration. |
| **Voice UI** | `@elevenlabs/react` | Low-latency conversational agent with signed private URLs. |
| **Backend** | FastAPI, Pydantic Settings | Async-native, strict schemas, OpenAPI for hackathon APIs. |
| **Orchestration LLM** | OpenAI `gpt-4o` | Structured outputs (`beta.chat.completions.parse`) for intake & logs. |
| **Vision LLM** | Google GenAI `gemini-2.5-flash` (configurable) | Multimodal crop analysis; retries + calibration layer. |
| **Embeddings** | **Gemini** (`gemini-embedding-2` primary) | 1536-dim vectors for `market_intelligence` RAG (OpenAI optional fallback). |
| **Database** | Supabase (Postgres + pgvector) | Auth, RLS, Realtime, storage in one managed stack. |
| **Banking** | Seylan hackathon sandbox HTTP APIs | Balance inquiry where sandbox responds; transfer/QR mocked when endpoints failed. |
| **Hosting** | **Vercel** (production) + Docker Compose (local) | Frontend: [cursor-buildathon-project-c3e8.vercel.app](https://cursor-buildathon-project-c3e8.vercel.app/); API: [cursor-buildathon-project-huiw.vercel.app](https://cursor-buildathon-project-huiw.vercel.app/). |

### Data Flow (core evaluate journey)

1. **User** completes intake → `POST /api/loans` or `POST /api/voice/intake` → row `status=draft`.
2. **User** uploads image → `POST /api/loans/{id}/evidence/upload` → Storage bucket `loan-evidence` + DB path.
3. **User** submits → `POST /api/loans/{id}/evaluate` → **202**, background `run_evaluation_pipeline`.
4. **Pipeline** sets `analyzing`; downloads bytes from Storage.
5. **Parallel:**
   - Gemini vision → `VisionAnalysisResult` → update `ai_verified_acreage`, `crop_health_matrix`.
   - Embed `"crop + district"` → RPC `match_market_intelligence` → volatility & weather scores.
6. **Pipeline** sets `underwriting`; `QuantUnderwriterAgent.decide()` computes weighted risk score.
7. If approved → `disburse_loan_amount()` → Seylan CEFTS (mock or live) → `approved` then `disbursed` + `transaction_reference`.
8. **Frontend** polls/subscribes → dashboard and apply steps update.

### AI Integration

| Agent | Provider | Role |
|-------|----------|------|
| `ConversationCoordinator` | OpenAI GPT-4o (Gemini/heuristic fallback) | Transcript → `{ crop_type, declared_acreage, requested_amount }` |
| `VisionAgronomistAgent` | Gemini | Image → health, acreage estimate, disease flags, quality scores |
| `MarketIntelligenceRagAgent` | **Gemini embeddings** + Supabase vector | Localized volatility/weather context |
| `QuantUnderwriterAgent` | Deterministic formula + GPT-4o optional narrative | Risk score, approve/reject, disbursement trigger |

**Risk formula (implemented):** Weighted blend of health deficit, disease penalty, market volatility, weather risk, acreage variance, image quality, and crop-match confidence (`quant_underwriter.py`)—threshold compare to `RISK_REJECTION_THRESHOLD`.

### Known Technical Limitations

- **Seylan sandbox:** Transfer and QR flows returned errors during integration; the demo uses **mock disbursement/repayment responses** so the full loan lifecycle remains demonstrable. **Account balance inquiry** is the main path still exercised against the sandbox when available.
- **Underwriting terminal UI** not wired; realtime log derivation exists but is unused in pages.
- **Demo RLS policies** allow broad `select` on loans/profiles for dashboard reads—must be hardened for production.
- **Service role on backend** — all loan mutations trust `user_id` from client; no JWT verification on FastAPI routes yet.
- **Single-process background tasks** — not durable across API restarts.
- **Vision model naming** — defaults to `gemini-2.5-flash`, not legacy `gemini-1.5-pro` from original spec.

---

## SECTION 07: Security

### Authentication & Authorisation

- **Frontend:** Supabase Auth (email/password, session via `AuthProvider`).
- **Backend:** Uses **service role** key for DB/storage; expects `user_id` on create/list—**does not validate Supabase JWT** on API requests (hackathon gap).
- **Routes:** Apply and dashboard gated client-side (`isAuthenticated`); API trust model is weak for production.

### Data Handling

- **PII:** `profiles` store `full_name`, `phone`, `district`; optional payout account fields for CEFTS.
- **Evidence:** Crop images in private bucket `loan-evidence`; paths stored on loan row.
- **Passwords:** Managed by Supabase Auth (hashed server-side).
- **Loan outcomes:** Risk scores, rejection reasons, transaction references persisted for audit.

### API & Secret Management

- Secrets in **`backend/.env`** only (`OPENAI_API_KEY`, `GOOGLE_GENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `ELEVENLABS_API_KEY`, `SEYLAN_*`).
- **Frontend** exposes only `NEXT_PUBLIC_*` (Supabase anon key, API URL)—no provider secrets in client bundles.
- ElevenLabs **signed URLs** minted server-side via `GET /api/voice/signed-url`.
- `.env` files gitignored; `.env.example` documents required keys without values.

### Input Validation

- Pydantic models on all request bodies (acreage > 0, amount ≥ 5000, transcript min length).
- Upload: MIME allow-list, 10 MB cap, empty file rejected.
- SQL constraints: phone regex, district enum, loan status enum, risk score 0–100.
- Evaluation idempotency: HTTP **409** for invalid status transitions.

### Known Vulnerabilities or Gaps

| Gap | Reason not fixed in build |
|-----|---------------------------|
| API lacks JWT verification | Speed of hackathon; service role trusted client `user_id` |
| Permissive RLS read policies | Demo dashboard without complex policies |
| No rate limiting on evaluate | Time constraint |
| CSRF on API | Local/demo CORS only |

---

## SECTION 08: User Stories & Use Cases

### Core User Stories

1. *As a **smallholder farmer**, I want to **describe my loan needs by voice in English**, so that **I can apply quickly without typing long forms**.*
2. *As a **farmer**, I want to **upload a photo of my field**, so that **the bank can verify crop health without visiting my farm**.*
3. *As a **farmer**, I want to **see whether my loan was approved or rejected with a reason**, so that **I can fix issues or seek alternatives**.*
4. *As a **farmer**, I want to **view all my past applications in one dashboard**, so that **I can track disbursements and repayments**.*
5. *As a **farmer**, I want to **repay via QR or bank transfer**, so that **I can close my loan digitally**.*
6. *As a **lender demo operator**, I want to **trigger AI underwriting with one action**, so that **I can show end-to-end automation to stakeholders**.*
7. *As a **risk officer**, I want **a deterministic risk score with agent logs**, so that **decisions are explainable**.*
8. *As a **developer**, I want **`/health` integration flags**, so that **I can verify API keys before a live demo**.*

### Primary Use Case Walkthrough

| Step | User action | System action | User sees |
|------|-------------|---------------|-----------|
| 1 | Registers/logs in | Supabase Auth + profile trigger | Dashboard / Apply access |
| 2 | Opens `/apply`, starts voice | ElevenLabs WS via signed URL | Waveform + conversation |
| 3 | Describes paddy, 2.5 ac, LKR 75k | Transcript → GPT-4o intake → draft loan | Form fields populated |
| 4 | Uploads field photo | Storage upload + PATCH path | “Evidence attached” |
| 5 | Submits application | `evaluate` 202 → pipeline | Step 2 “AI agents analyzing…” |
| 6 | Waits (~30s) | Vision + RAG + underwriter + mock CEFTS | Risk/health cards or rejection |
| 7 | — | Status `disbursed` + reference | “Approved & disbursed · Ref …” |
| 8 | Later: repay | QR or CEFTS endpoints | Loan `repaid` on dashboard |

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| No image before evaluate | **422** — must upload evidence first |
| Double evaluate while analyzing | **409** conflict |
| Unreadable image / Gemini failure | `rejected` + vision rejection message |
| Risk > 45 | `rejected` + score exceeds threshold |
| Missing district on profile | `rejected` — district required for market RAG |
| Gemini quota exhausted | Rejection with retry guidance; optional mock vision flag |
| Seylan disbursement failure | `rejected` at underwriting with bank error text |
| Already repaid loan | Repayment endpoints return **409** |

---

## SECTION 09: Target Users & Market

### Primary User

**Sri Lankan smallholder farmers** (1–5 acres), often mobile-first. Pain: slow credit, opaque rejections, and inability to prove crop quality remotely. Agri-Lend addresses **speed**, **English voice-first intake** (with form fallback), and **evidence-based fairness**.

### Market Opportunity

- National policy momentum on **subsidized rural credit** and digital inclusion ([Sarusara scheme reporting, 2025](https://asianmirror.lk/news/2598/sarusara-rural-credit-scheme-to-be-implemented-annually-from-2025/)).
- **DFI and EU programs** explicitly funding smallholder productivity and finance partnerships in Sri Lanka ([AgriFI, 2025](https://edfimc.eu/european-union-financed-agrifi-launches-country-window-sri-lanka-to-boost-smallholder-farmers/)).
- **First segment:** Partner MFIs / rural banks in North Central and Eastern provinces with high paddy/maize concentration—pilot 500–2,000 loans via white-label Agri-Lend API.

### Competitive Landscape

| Alternative | Weakness vs Agri-Lend |
|-------------|------------------------|
| **Branch paper applications** | Slow, no multimodal AI, high opex per loan |
| **Generic digital lending apps** | Lack agronomic vision + district crop RAG |
| **Manual NGO/grant programs** | Not real-time; poor reuse of field photos for credit scoring |

---

## SECTION 10: Business Model

### Revenue Model

**B2B SaaS + usage-based API** to rural banks and MFIs: platform fee per underwriting decision + optional premium for live banking rails and custom risk models. Fits institutions that already lend but need **automation and auditability**.

### Pricing Hypothesis

- **LKR 150–400 per automated decision** (vs LKR 2,000+ manual field visit cost)—tiered by volume.
- **Enterprise:** monthly minimum + included decisions for institutions >1,000 loans/month.

### Go-to-Market

1. **Pilot with one sandbox partner bank** (Seylan hackathon relationship → production API).
2. **Demo at agrarian service centers** in Anuradhapura/Ampara with tablet + voice intake.
3. **First 10 customers:** 3 regional MFIs, 2 bank innovation teams, 5 agri-fintech integrators—outbound via TechTalk360 / Cursor partner network and Central Bank rural digitization forums.

### Roadmap

| Horizon | Deliverable |
|---------|-------------|
| **Now (hackathon)** | Voice + vision + RAG + mock/live sandbox disbursement + repayment |
| **0–3 months** | JWT-secured API, officer dashboard, Sinhala voice, mount Underwriting Terminal UI, production RLS |
| **12 months** | Licensed bank integration, mobile app, credit bureau hooks, portfolio risk analytics for institutions |

---

## SECTION 11: Why This Project Leads the Track

### Technical Edge

- **True multi-agent parallelism** (vision + market) with **split LLM providers** (Gemini for pixels, GPT-4o for structure)—not a single chatbot wrapper.
- **pgvector RAG** with SQL `match_market_intelligence` and seeded district economics.
- **Live on Vercel:** Public frontend and API deployments judges can open immediately.
- **Gemini at the core:** Same provider for **vision** and **embeddings**—tight multimodal + RAG story for the track.
- **Cursor-native delivery:** `project.md` → phased Composer prompts → cohesive repo structure proves track tooling mastery.

### Problem-Solution Fit

Problem (slow, opaque rural credit) maps **directly** to shipped flows: voice intake → evidence → scored decision → disbursement reference. Every demo step mirrors a real farmer journey.

### Execution Quality

- Live demo at [Agri-Lend on Vercel](https://cursor-buildathon-project-c3e8.vercel.app/), Dockerized local stack, and `/health` integration checks.
- Polished farmer UI (apply steps, dashboard, disbursement/repayment panels).
- Explicit failure messages and idempotent evaluate guards show production thinking.

### Real-World Potential

Aligns with **national rural credit expansion** and **international smallholder finance** trends. The architecture can white-label to any institution with Supabase + API keys—hackathon prototype is a credible **pilot engine**, not a slide-deck mock.

---

## SECTION 12: Team & Roles

### Team Members

| Name | Role | Contribution | Background |
|------|------|--------------|------------|
| **Jakshigan Jeyaseelan** | Full-stack / AI pipeline | FastAPI multi-agent orchestration, Gemini vision & embedding integration, Supabase schema and evaluation pipeline, backend Vercel deployment | Final-year Computer Science student and software engineer; backend systems and applied ML for fintech workflows. |
| **Sanjula Nelumdeniyage Dulsan** | Full-stack / Product & UX | Next.js application (landing, apply, dashboard), ElevenLabs voice-first flow, auth and farmer UX, frontend Vercel deployment | Final-year Computer Science student and software engineer; user-facing products and conversational interfaces. |

**GitHub:** https://github.com/AstrelSD/Cursor-Buildathon-Project

### Why This Team

**Fortress** is two final-year Computer Science students who also work as software engineers—combining academic rigor with day-to-day shipping experience. Jakshigan owned the agent pipeline and Gemini-centric analysis path; Sanjula owned the voice-first UI and end-to-end flows judges see on [the live demo](https://cursor-buildathon-project-c3e8.vercel.app/). Together the team delivered a coherent vertical slice—from English voice intake through multimodal underwriting to loan status on a public Vercel stack—rather than a disconnected API prototype.

---

## References

1. **Agri-Lend specification:** `project.md` (architecture, agents, risk formula, directory layout).
2. **Live demo:** [Frontend](https://cursor-buildathon-project-c3e8.vercel.app/) · [Backend API](https://cursor-buildathon-project-huiw.vercel.app/)  
3. **Codebase:** https://github.com/AstrelSD/Cursor-Buildathon-Project  
   - Backend pipeline: `backend/app/services/evaluation.py`  
   - Risk scoring: `backend/app/agents/quant_underwriter.py`  
   - Voice: `backend/app/routers/voice.py`, `frontend/components/RealtimeVoiceConsole.tsx`
4. **Sri Lanka rural credit policy context:** [Asian Mirror — Sarusara scheme, 2025](https://asianmirror.lk/news/2598/sarusara-rural-credit-scheme-to-be-implemented-annually-from-2025/)
5. **Smallholder finance programs:** [EDFI MC — AgriFI Sri Lanka window, 2025](https://edfimc.eu/european-union-financed-agrifi-launches-country-window-sri-lanka-to-boost-smallholder-farmers/)
6. **Financial support systems research:** [ASMP — Policy Research on Appropriate Financial Support System (PDF)](https://asmp.lk/wp-content/uploads/2025/03/Policy-Research-on-Appropriate-Financial-Support-System.pdf)
7. **Track partners:** Cursor × TechTalk360 Buildathon submission template.

---

*Confidential For Authorized Use Only | Cursor Buildathon Cursor x TechTalk360 Confidential*
