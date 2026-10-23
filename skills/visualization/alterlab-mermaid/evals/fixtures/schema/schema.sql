-- Lab data store (PostgreSQL 16). Fictional schema for the soil-microbiome lab.
-- Exported with: pg_dump --schema-only -t experiments -t samples -t measurements

CREATE TABLE experiments (
    experiment_id   SERIAL PRIMARY KEY,
    code            TEXT        NOT NULL UNIQUE,          -- e.g. 'SOIL-2026-04'
    title           TEXT        NOT NULL,
    pi_name         TEXT        NOT NULL,
    started_on      DATE        NOT NULL,
    protocol_doi    TEXT
);

CREATE TABLE samples (
    sample_id        SERIAL PRIMARY KEY,
    experiment_id    INTEGER     NOT NULL REFERENCES experiments (experiment_id) ON DELETE RESTRICT,
    parent_sample_id INTEGER     REFERENCES samples (sample_id) ON DELETE CASCADE,  -- aliquots point to their source sample
    label            TEXT        NOT NULL,
    collected_on     DATE        NOT NULL,
    depth_cm         NUMERIC(5, 1),
    UNIQUE (experiment_id, label)
);

CREATE TABLE measurements (
    measurement_id  BIGSERIAL PRIMARY KEY,
    sample_id       INTEGER     NOT NULL REFERENCES samples (sample_id) ON DELETE CASCADE,
    assay           TEXT        NOT NULL,                 -- 'pH', 'NO3', 'qPCR_16S', ...
    replicate       SMALLINT    NOT NULL DEFAULT 1,
    value           DOUBLE PRECISION NOT NULL,
    unit            TEXT        NOT NULL,
    measured_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sample_id, assay, replicate)
);

CREATE INDEX samples_experiment_id_idx ON samples (experiment_id);
CREATE INDEX samples_parent_sample_id_idx ON samples (parent_sample_id);
CREATE INDEX measurements_sample_id_idx ON measurements (sample_id);
