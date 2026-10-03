-- Tabla de hechos del almacén: una fila por viaje (row-store, heap de Postgres).
-- trip_id lo asigna el motor en el orden del CSV; Valkey usa el mismo número en la llave.
DROP TABLE IF EXISTS trips;

CREATE TABLE trips (
    trip_id               bigint GENERATED ALWAYS AS IDENTITY,
    vendor_id             smallint,
    pickup_at             timestamp,
    dropoff_at            timestamp,
    passenger_count       smallint,
    trip_distance         double precision,
    pickup_longitude      double precision,
    pickup_latitude       double precision,
    ratecode_id           smallint,
    store_and_fwd_flag    char(1),
    dropoff_longitude     double precision,
    dropoff_latitude      double precision,
    payment_type          smallint,
    fare_amount           numeric(10,2),
    extra                 numeric(10,2),
    mta_tax               numeric(10,2),
    tip_amount            numeric(10,2),
    tolls_amount          numeric(10,2),
    improvement_surcharge numeric(10,2),
    total_amount          numeric(10,2)
);
