CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    level TEXT,
    apr JSONB,
    pip INTEGER NOT NULL DEFAULT 0,
    joiningdate DATE NOT NULL,
    gh_username TEXT,
    ranking FLOAT8,
    roi FLOAT8 CHECK (roi >= 0),
    report_id TEXT
);
