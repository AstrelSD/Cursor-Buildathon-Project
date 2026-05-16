# 🌾 project.md: Production-Grade Multi-Agent Agri-Lend Specification

## 1. Executive System Topology & Architectural Vision
Agri-Lend is an enterprise-grade, asynchronous AI credit underwriting engine tailored for smallholder farmers in Sri Lanka[cite: 2]. By replacing archaic, high-friction paper applications and slow physical farm inspections with a distributed multi-agent AI pipeline, it calculates real-time agronomic risk profiles, intersects them with live localized market vectors, and establishes automated decision parameters for micro-credit approvals[cite: 2].

The system architecture utilizes a split-brain model designed to optimize cost, latency, and reasoning capability across state-of-the-art LLMs:
1. **Orchestration, Parsing, and Logic Extraction:** Handled by OpenAI GPT-4o due to its strict compliance with deterministic JSON schemas.
2. **Heavy Multimodal Computer Vision Analysis:** Handled by Google Gemini 1.5 Pro due to its massive native context window and superior capability processing raw spatial video frames and image metadata[cite: 2].

┌─────────────────────────────────────────────────────────────────────────────┐
│                          NEXT.JS FRONTEND VIEWPORT                          │
│  ┌───────────────────────────┐               ┌───────────────────────────┐  │
│  │ RealtimeVoiceConsole     │               │ UnderwritingTerminal      │  │
│  │ (ElevenLabs Client State) │               │ (Supabase Realtime Stream)│  │
│  └─────────────┬─────────────┘               └─────────────▲─────────────┘  │
└────────────────┼───────────────────────────────────────────┼────────────────┘
│ (Bidirectional WebSockets)                │
▼                                           │
┌────────────────────────────────────────────────────────────┼────────────────┐
│                          FASTAPI BACKEND CORE              │                │
│  ┌───────────────────────────┐                             │                │
│  │ ConversationCoordinator   │                             │                │
│  │ (OpenAI GPT-4o Structured)│                             │                │
│  └─────────────┬─────────────┘                             │                │
│                │                                           │                │
│                ▼                                           │ (Row Updates)  │
│    ┌───────────────────────────────────┐                   │                │
│    │ Parallel Agent Processing Layer   │                   │                │
│    │                                   │                   │                │
│    │ ├──> VisionAgronomistAgent        │                   │                │
│    │ │    (Gemini 1.5 Pro Vision) ─────┼──────────────┐    │                │
│    │ │                                 │              │    │                │
│    │ └──> MarketIntelligenceRagAgent   │              ▼    │                │
│    │      (Supabase Vector Search)     │       ┌───────────┴───────────┐    │
│    └───────────────────┬───────────────┘       │ PERSISTENT DATA LAYER │    │
│                        │                       │  (Supabase/Postgres)  │    │
│                        ▼                       └───────────▲───────────┘    │
│  ┌───────────────────────────────────┐                     │                │
│  │ QuantUnderwriterAgent             │                     │                │
│  │ (OpenAI GPT-4o Risk Synthesis)    ├─────────────────────┘                │
│  └───────────────────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘


---

## 2. Complete Relational Database & Vector Schema (Supabase SQL)

Execute this script within your Supabase SQL Editor to provision the exact relational, constraint, and vector tracking structures required:

```sql
-- Enable Vector Extension for Localized Economic Semantic RAG Search
create extension if not exists vector;

-- Clean existing entities to guarantee idempotent migration execution
drop table if exists public.loans cascade;
drop table if exists public.market_intelligence cascade;
drop table if exists public.profiles cascade;

-- 1. Persistent User Profile Registration Ledger
create table public.profiles (
    id uuid references auth.users on delete cascade primary key,
    full_name text not null,
    phone text not null check (phone ~ '^\+94[0-9]{9}$'), -- Enforce structural Sri Lankan international formatting
    district text not null check (district in ('Anuradhapura', 'Polonnaruwa', 'Ampara', 'Kurunegala', 'Nuwaraliya')),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Localized Market Economics & Weather Risk Vector Reference Matrix
create table public.market_intelligence (
    id uuid default gen_random_uuid() primary key,
    crop_type text not null,
    district text not null,
    base_yield_index numeric(5,2) not null, -- Normalized baseline district performance metrics
    market_volatility_coefficient numeric(3,2) not null, -- Range: 0.00 to 1.00 (High inflation/instability risk indicators)
    weather_risk_score numeric(5,2) not null, -- Real-time rainfall anomaly coefficients
    metadata jsonb default '{}'::jsonb, -- Deep history markers
    embedding vector(1536) not null -- Generated explicitly via OpenAI text-embedding-3-small
);

-- 3. Core Multi-Agent Multi-Stage Underwriting Ledger
create table public.loans (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references public.profiles(id) on delete cascade not null,
    crop_type text not null,
    declared_acreage numeric(10,2) not null internal check (declared_acreage > 0),
    requested_amount numeric(12,2) not null internal check (requested_amount >= 5000.00),
    
    -- Multimodal Vision Verification Engine Fields
    ai_verified_acreage numeric(10,2),
    crop_health_matrix jsonb default null, -- Expected format validation: {chlorophyll_index: float, anomaly_flag: boolean, classification: string}
    
    -- RAG Verification Metrics
    market_volatility_index numeric(3,2),
    
    -- Comprehensive Risk Processing Vectors
    calculated_risk_score numeric(5,2) check (calculated_risk_score >= 0.00 and calculated_risk_score <= 100.00),
    rejection_reason text default null,
    
    -- System State Machine Synchronization Controls
    status text default 'draft' check (status in ('draft', 'analyzing', 'underwriting', 'approved', 'disbursed', 'rejected')),
    multimodal_evidence_url text, -- Explicit pointer to verified bucket file inside Supabase Storage
    transaction_reference text unique default null, -- Mimics actual clearing tracking references from core banks
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indexing structures to optimize ultra-low lookup speeds during multi-agent queries
create index idx_loans_user_id on public.loans(user_id);
create index idx_loans_status on public.loans(status);
3. Strict Multi-Agent Workflow Execution Design
Phase 1: Intake & Context Gathering (ElevenLabs WebSocket Interface)
Actor: ConversationCoordinator (OpenAI GPT-4o + ElevenLabs Client Interface)

Mechanism: Continuous bidirectional audio streaming connection. ElevenLabs coordinates local dialect translations. As the farmer speaks naturally about their field requirements, the stream runs through a formatting schema to capture values instantly without form entries.

Deterministic Output Format:

JSON
{ "crop_type": "Paddy", "declared_acreage": 2.5, "requested_amount": 75000.00 }

*   **Database Write:** Mutation hooks fire instantly to generate a primary record inside `public.loans` with a configuration flag of `status = 'draft'`.

### Phase 2: Parallelized Underwriting Data Enrichment Pipeline
Upon user confirming upload of image/video file stream to the Supabase Storage Bucket, the backend hooks trigger a non-blocking asynchronous executor (`BackgroundTasks` in FastAPI), dropping the main request into an internal state change `status = 'analyzing'`. Two agents process concurrently:

#### Agent A: The Multimodal Vision Agronomist
*   **Actor:** `VisionAgronomistAgent` (Google Gemini 1.5 Pro via GenAI SDK)
*   **Inputs:** Direct binary image stream/URL from Supabase Storage + user declared application bounds.
*   **System Directives:** Inspect structural crop features. Perform deep evaluation for visual pathology identifiers, dead leaf foliage percentages, chlorosis patterns, and geographical bounds to estimate size[cite: 2].
*   **Output Format Contract:**
    ```json
    { "estimated_acreage": 2.45, "chlorophyll_index": 0.82, "disease_detected": false, "health_score": 88 }
    
Agent B: Market Intelligence Semantic Vector RAG Agent
Actor: MarketIntelligenceRagAgent (OpenAI text-embedding-3-small + Supabase Vector Matching Engine)

Inputs: Spatial geographical keys (Farmer district metadata + target Crop type).

Mechanism: Generates real-time vector payload of application criteria, runs a cosine distance match against public.market_intelligence fields, and pulls structural risk boundaries.

Output Format Contract:

JSON
{ "market_volatility_coefficient": 0.35, "weather_risk_score": 12.5 }


### Phase 3: Risk Processing & Settlement Action
*   **Actor:** `QuantUnderwriterAgent` (OpenAI GPT-4o Engine)
*   **Mechanism:** Consumes the unified JSON objects output directly from Phase 2. Runs an immutable internal calculation formula:
    $$\text{Calculated Risk Score} = (0.5 \times (100 - \text{health\_score})) + (0.3 \times (\text{market\_volatility\_coefficient} \times 100)) + (0.2 \times (\min(\frac{|\text{declared\_acreage} - \text{estimated\_acreage}|}{\text{declared\_acreage}}, 1) \times 100))$$
*   **Constraint Enforcement Framework:** If the composite numeric risk metric registers above **45.00**, the workflow commits a structural database failure step (`status = 'rejected'`) and updates the user's view dashboard.
*   **Disbursement Trigger:** If risk values fall within acceptable ranges, status transitions to `approved`. The backend immediately interfaces with an external asynchronous simulation layer mimicking real-time fund settlement protocols. Upon receiving a structural success code, the ledger locks cleanly at `status = 'disbursed'`.

---

## 4. Production Workspace Directory Layout

```text
agri-lend/
├── supabase/
│   └── migrations/
│       └── 20260516110000_core_underwriting_protocol.sql
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # Main server lifecycle hooks, global state, CORS setups
│   │   ├── config.py                   # Decoupled strict pydantic BaseSettings management
│   │   ├── database.py                 # Async client instance manager for Supabase
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── vision_agronomist.py    # Google Gemini 1.5 Pro Multi-modal Processing Agent
│   │   │   ├── market_rag.py           # Supabase Vector search data execution engine
│   │   │   └── quant_underwriter.py    # OpenAI GPT-4o Financial Risk Evaluator Agent
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── loan.py                 # Core routing pathways for structural evaluation loops
│   └── requirements.txt                # Fixed pinning lock file for production python drivers
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx                # High-fidelity executive risk manager control dashboard
    │   │   └── apply/
    │   │       └── page.tsx            # Portal entry interface housing uploads and live pipelines
    │   ├── components/
    │   │   ├── RealtimeVoiceConsole.tsx # Interactive ElevenLabs streaming widget audio core
    │   │   ├── MultimodalUploader.tsx   # Direct chunked stream loader routing to Supabase buckets
    │   │   └── UnderwritingTerminal.tsx # Raw terminal displaying agent thinking traces via WebSockets
    │   └── lib/
    │       └── supabase.ts             # Instantiated global real-time web socket listener configs
5. Sequential Step-by-Step Cursor Composer Generation Prompts
Execute these precise prompts within Cursor Composer Mode (Cmd+I or Ctrl+I) sequentially. Allow each stage to execute completely before firing the subsequent phase.

Phase 1: Environment Definition, Configuration, and Storage Services
Target Directory: /backend

Plaintext
Using the instructions defined within @project.md:
1. Generate the absolute configurations in `app/config.py` leveraging Pydantic BaseSettings to enforce validation for OPENAI_API_KEY, GOOGLE_GENAI_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY.
2. Initialize `app/database.py` exporting a clean, long-lived thread-safe asynchronous wrapper using supabase-py client drivers.
3. Construct `app/main.py` configuring an explicit FastAPI instantiation. Inject wide CORS origins explicitly handling localhost:3000 mapping, initialize a standard base performance dashboard checkpoint at route `GET /health`, and register clean application lifespan event configurations.
Phase 2: Multimodal & Vector Intelligence Agent Systems
Target Directory: /backend

Plaintext
Using the design architecture in @project.md, build out the specialized intelligence agents:
1. Implement `app/agents/vision_agronomist.py`. Use the official google-genai library to access Gemini 1.5 Pro. Accept a string file pointer corresponding to an image path hosted inside a Supabase bucket. Craft a high-fidelity internal system prompt to analyze the crop conditions, checking for visual blight, localized pest indicators, and structural field size alignment. Return a strict, valid Pydantic model contract.
2. Implement `app/agents/market_rag.py`. Build an asynchronous sequence that constructs a 1536-dimensional array by hitting OpenAI's text-embedding-3-small endpoint with the user's localized spatial features. Write a raw postgrest or direct raw client call executing a cosine similarity matching calculation against the `public.market_intelligence` database entity.
Phase 3: The Risk Underwriter Agent and Pipeline Orchestration
Target Directory: /backend

Plaintext
According to the specification inside @project.md:
1. Build `app/agents/quant_underwriter.py`. Utilize OpenAI GPT-4o engine leveraging strict structured response formats via dynamic BaseModel payload contracts. It must consume variables passed from the Vision Agronomist and Market RAG layers and run the specific Risk Calculation equation. Output a final decision payload containing score, calculated approval flags, and granular categorical logs.
2. Construct `app/routers/loan.py` establishing an asynchronous endpoint `POST /api/loans/{loan_id}/evaluate`. This must drop the initialization loop into background task execution loops immediately, responding with a clean HTTP 202 Accepted. The async background loop runs the entire multi-agent validation chain sequentially, writing persistent mutation hooks directly to the Supabase tables at each step.
Phase 4: High-Fidelity Next.js Analytics Framework & Terminal Front-end View
Target Directory: /frontend

Plaintext
According to the layout detailed inside @project.md:
1. Build an enterprise-level, modern responsive banking dashboard view in `src/app/page.tsx` using Tailwind CSS and components matching shadcn patterns. Create dark glass panels tracking key banking arrays: Total Capital Deployed (LKR), Pipeline Active Evaluations, Regional Risk Breakdown, and an interactive structural ledger displaying data directly from the Supabase public.loans table.
2. Create `src/components/UnderwritingTerminal.tsx`. This element must open long-lived real-time streaming event capture listeners directly onto the Supabase database. When table changes are broadcast, it outputs an ongoing streaming log of code actions mimicking an open engineer trace console panel (e.g., '[PROCESSING] Vision Agent processing spatial field matrices... [PASSED] Underwriter verification confirmed. Generating bank wire sequence...').
Phase 5: Low-Latency ElevenLabs Conversational Socket Core
Target Directory: /frontend

Plaintext
Using the specifications inside @project.md:
1. Construct `src/components/RealtimeVoiceConsole.tsx`. Design an abstract floating action portal containing complex audio visualization wave loops when engaged.
2. Wire up native browser MediaRecorder configurations capturing raw chunks from the user microphone. Establish clean, high-performance bidirectional WebSocket pipelines transmitting and processing streaming audio pipelines natively back and forth from ElevenLabs standard low-latency conversational pipeline drivers.
6. Failure Recovery & Strict Execution Constraints
Multimodal Asset Failures: If a user provides an unrecognizable image file, the VisionAgronomistAgent must catch the validation exception natively, output an explicit flag identifying unreadable evidence, and short-circuit the pipeline immediately by updating status = 'rejected' with a clear explanation: "Evaluation failed: Crop imagery unreadable."

Idempotent Execution Guarantees: Ensure the FastAPI backend evaluates row configurations prior to triggering downstream agent components. If an evaluation endpoint is targeted on an application that registers a state status value of approved, disbursed, or underwriting, it must return an exception code to prevent redundant computation billing.

***

### 💡 Why this is a Masterclass Hackathon Structure:
* **The "Wow" Factor Console:** The `UnderwritingTerminal` frontend module is highly strategic. During a fast-paced 3-minute hackathon pitch to judges, watching a real-time terminal feed print out granular logic lines tracking exactly what each agent is doing provides definitive proof of working technical complexity.
* **Flawless Cursor Contextual Alignment:** The rigid mathematical structuring, typed schema formats, and explicit file boundaries make it incredibly easy for Cursor to process this file in its context buffer and output perfect code blocks without losing tracking context. 

Open up your terminal, fire up Cursor, activate Composer, and watch it bring this ent