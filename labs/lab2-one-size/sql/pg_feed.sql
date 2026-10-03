-- Procesamiento «outbound» en postgres:
-- cada mensaje se guarda primero en feed_trip y un trigger actualiza los contadores.
-- El umbral de alerta (100 en el paper) lo fija el script con SET lab2.umbral = N;
-- current_setting() lo lee dentro del trigger, en la misma sesión.
DROP TABLE IF EXISTS feed_trip, agg_pago, alarma_vendor CASCADE;

CREATE TABLE feed_trip (
    vendor_id     smallint,
    payment_type  smallint,
    fare_amount   numeric(10,2),
    trip_distance double precision
);

CREATE TABLE agg_pago (
    payment_type smallint PRIMARY KEY,
    n            bigint NOT NULL,
    suma         numeric NOT NULL
);

CREATE TABLE alarma_vendor (
    vendor_id  smallint PRIMARY KEY,
    anomalias  bigint NOT NULL,
    alertas    bigint NOT NULL
);

CREATE OR REPLACE FUNCTION feed_trip_after() RETURNS trigger AS $$
BEGIN
    INSERT INTO agg_pago VALUES (NEW.payment_type, 1, NEW.fare_amount)
    ON CONFLICT (payment_type)
    DO UPDATE SET n = agg_pago.n + 1, suma = agg_pago.suma + EXCLUDED.suma;

    -- Anomalía: viaje sin distancia o sin tarifa. Cada `umbral` por proveedor, una alerta (Count100).
    IF NEW.trip_distance <= 0 OR NEW.fare_amount <= 0 THEN
        INSERT INTO alarma_vendor VALUES (NEW.vendor_id, 1, 0)
        ON CONFLICT (vendor_id)
        DO UPDATE SET anomalias = alarma_vendor.anomalias + 1,
                      alertas = alarma_vendor.alertas
                                + CASE WHEN (alarma_vendor.anomalias + 1)
                                       % current_setting('lab2.umbral')::int = 0
                                  THEN 1 ELSE 0 END;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER feed_trip_counts AFTER INSERT ON feed_trip
FOR EACH ROW EXECUTE FUNCTION feed_trip_after();
