-- Инициализация базы данных калькулятора маркиз

CREATE TABLE IF NOT EXISTS leads (
    id          SERIAL PRIMARY KEY,
    phone       VARCHAR(20)  NOT NULL,
    city        VARCHAR(100) DEFAULT 'Не определён',
    calc_text   TEXT,
    channel     VARCHAR(20)  DEFAULT 'callback',  -- callback | whatsapp | telegram | max
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);

CREATE TABLE IF NOT EXISTS calc_history (
    id          SERIAL PRIMARY KEY,
    params_hash CHAR(32)     NOT NULL,
    result_json JSONB        NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calc_history_hash ON calc_history (params_hash);
CREATE INDEX IF NOT EXISTS idx_calc_history_created ON calc_history (created_at DESC);
