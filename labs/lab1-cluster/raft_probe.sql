-- Tabla de control para observar mayoría Raft 2/3.
-- No usa REGIONAL BY ROW: el clúster docente tiene un solo nodo por región.

CREATE DATABASE IF NOT EXISTS ti4601_raft;

CREATE TABLE IF NOT EXISTS ti4601_raft.public.raft_probe (
    id INT8 PRIMARY KEY,
    version INT8 NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO ti4601_raft.public.raft_probe (id, version)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

