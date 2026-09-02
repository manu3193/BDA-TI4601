-- Ejemplo cerrado del Lab 1; no es plantilla entregable del Proyecto 1.
-- El P1 exige que el equipo diseñe su propio dominio, claves y localidades.

CREATE TABLE IF NOT EXISTS catalogo_producto (
    producto_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku STRING NOT NULL UNIQUE,
    nombre STRING NOT NULL,
    precio DECIMAL(12, 2) NOT NULL CHECK (precio >= 0)
) LOCALITY GLOBAL;

CREATE TABLE IF NOT EXISTS pedido (
    region crdb_internal_region NOT NULL,
    pedido_id UUID NOT NULL DEFAULT gen_random_uuid(),
    producto_id UUID NOT NULL REFERENCES catalogo_producto (producto_id),
    tienda STRING NOT NULL,
    estado STRING NOT NULL DEFAULT 'CREADO',
    monto DECIMAL(12, 2) NOT NULL CHECK (monto >= 0),
    version INT8 NOT NULL DEFAULT 0,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (region, pedido_id)
) LOCALITY REGIONAL BY ROW AS region;

