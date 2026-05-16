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
    phone text not null check (phone ~ '^\+94[0-9]{9}$'),
    district text not null check (
        district in ('Anuradhapura', 'Polonnaruwa', 'Ampara', 'Kurunegala', 'Nuwaraliya')
    ),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Localized Market Economics & Weather Risk Vector Reference Matrix
create table public.market_intelligence (
    id uuid default gen_random_uuid() primary key,
    crop_type text not null,
    district text not null,
    base_yield_index numeric(5, 2) not null,
    market_volatility_coefficient numeric(3, 2) not null,
    weather_risk_score numeric(5, 2) not null,
    metadata jsonb default '{}'::jsonb,
    embedding vector(1536) not null
);

-- 3. Core Multi-Agent Multi-Stage Underwriting Ledger
create table public.loans (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references public.profiles(id) on delete cascade not null,
    crop_type text not null,
    declared_acreage numeric(10, 2) not null check (declared_acreage > 0),
    requested_amount numeric(12, 2) not null check (requested_amount >= 5000.00),
    ai_verified_acreage numeric(10, 2),
    crop_health_matrix jsonb default null,
    market_volatility_index numeric(3, 2),
    calculated_risk_score numeric(5, 2) check (
        calculated_risk_score >= 0.00 and calculated_risk_score <= 100.00
    ),
    rejection_reason text default null,
    status text default 'draft' check (
        status in ('draft', 'analyzing', 'underwriting', 'approved', 'disbursed', 'rejected')
    ),
    multimodal_evidence_url text,
    transaction_reference text unique default null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create index idx_loans_user_id on public.loans(user_id);
create index idx_loans_status on public.loans(status);
create index idx_market_intelligence_embedding on public.market_intelligence
    using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Cosine similarity search for MarketIntelligenceRagAgent
create or replace function public.match_market_intelligence(
    query_embedding vector(1536),
    match_count int default 1
)
returns table (
    id uuid,
    crop_type text,
    district text,
    base_yield_index numeric,
    market_volatility_coefficient numeric,
    weather_risk_score numeric,
    similarity double precision
)
language sql
stable
as $$
    select
        mi.id,
        mi.crop_type,
        mi.district,
        mi.base_yield_index,
        mi.market_volatility_coefficient,
        mi.weather_risk_score,
        1 - (mi.embedding <=> query_embedding) as similarity
    from public.market_intelligence mi
    order by mi.embedding <=> query_embedding
    limit match_count;
$$;
