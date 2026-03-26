-- SheldonOS — Database Initialization
-- Creates all required tables for SheldonOS operation.

-- ─── Opportunities ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source            VARCHAR(64) NOT NULL,
    category          VARCHAR(64) NOT NULL,
    title             TEXT NOT NULL,
    description       TEXT,
    raw_signal        JSONB DEFAULT '{}',
    score             FLOAT DEFAULT 0.0,
    estimated_roi_pct FLOAT DEFAULT 0.0,
    estimated_revenue_usd FLOAT DEFAULT 0.0,
    confidence_pct    FLOAT DEFAULT 0.0,
    recommended_company VARCHAR(32),
    status            VARCHAR(32) DEFAULT 'pending',
    detected_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_category ON opportunities(category);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(score DESC);

-- ─── Simulation Inputs ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_inputs (
    simulation_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id    UUID REFERENCES opportunities(opportunity_id),
    event_description TEXT NOT NULL,
    event_category    VARCHAR(64),
    time_horizon_days INT DEFAULT 7,
    population_size   INT DEFAULT 10000,
    market_question   TEXT,
    current_market_odds FLOAT DEFAULT 0.5,
    raw_data          JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Simulation Outputs ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_outputs (
    simulation_id     UUID PRIMARY KEY REFERENCES simulation_inputs(simulation_id),
    -- MiroFish results
    social_sentiment_score FLOAT,
    adoption_probability   FLOAT,
    viral_coefficient      FLOAT,
    resistance_index       FLOAT,
    dominant_narrative     TEXT,
    mirofish_confidence    FLOAT,
    -- Percepta results
    true_probability       FLOAT,
    expected_value         FLOAT,
    kelly_fraction         FLOAT,
    confidence_interval_low  FLOAT,
    confidence_interval_high FLOAT,
    -- Recommendation
    recommendation         VARCHAR(16),  -- EXECUTE | REVIEW | PASS
    direction              VARCHAR(8),   -- long | short
    completed_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Trade Signals ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trade_signals (
    signal_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id     UUID REFERENCES simulation_inputs(simulation_id),
    market_platform   VARCHAR(32) NOT NULL,  -- polymarket | kalshi
    market_id         VARCHAR(256) NOT NULL,
    direction         VARCHAR(8) NOT NULL,   -- long | short
    position_size_usd FLOAT NOT NULL,
    confidence_pct    FLOAT NOT NULL,
    expected_value    FLOAT NOT NULL,
    status            VARCHAR(32) DEFAULT 'pending',  -- pending | approved | executed | rejected
    tx_hash           VARCHAR(256),
    pnl_usd           FLOAT,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    executed_at       TIMESTAMPTZ
);

-- ─── Workflows ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id    UUID REFERENCES opportunities(opportunity_id),
    name              TEXT NOT NULL,
    company_id        VARCHAR(32) NOT NULL,
    goal              TEXT,
    status            VARCHAR(32) DEFAULT 'pending',
    tasks_total       INT DEFAULT 0,
    tasks_complete    INT DEFAULT 0,
    tasks_failed      INT DEFAULT 0,
    revenue_usd       FLOAT DEFAULT 0.0,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    completed_at      TIMESTAMPTZ
);

-- ─── Agent Heartbeats ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    heartbeat_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        VARCHAR(32) NOT NULL,
    team_id           VARCHAR(64),
    agent_id          VARCHAR(128) NOT NULL,
    task_id           UUID,
    tokens_used       INT DEFAULT 0,
    status            VARCHAR(32),
    result            JSONB,
    reported_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_agent ON agent_heartbeats(agent_id);
CREATE INDEX IF NOT EXISTS idx_heartbeats_company ON agent_heartbeats(company_id);

-- ─── Revenue Ledger ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS revenue_ledger (
    ledger_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        VARCHAR(32) NOT NULL,
    source            VARCHAR(64) NOT NULL,  -- prediction_market | saas | bug_bounty | research
    amount_usd        FLOAT NOT NULL,
    description       TEXT,
    workflow_id       UUID REFERENCES workflows(workflow_id),
    recorded_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_revenue_company ON revenue_ledger(company_id);
CREATE INDEX IF NOT EXISTS idx_revenue_source ON revenue_ledger(source);

-- ─── System Metrics ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_number      INT NOT NULL,
    opportunities_detected INT DEFAULT 0,
    opportunities_approved INT DEFAULT 0,
    opportunities_executed INT DEFAULT 0,
    total_revenue_usd FLOAT DEFAULT 0.0,
    cycle_duration_seconds FLOAT,
    recorded_at       TIMESTAMPTZ DEFAULT NOW()
);
