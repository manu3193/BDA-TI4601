-- Procesamiento «inbound» (Stonebraker y Çetintemel).
-- El mensaje no se guarda: pasa por esta lógica, que corre dentro de Valkey,
-- y solo quedan los contadores. Valkey ejecuta cada script de forma atómica:
-- ningún otro comando se intercala mientras corre.
--
-- Llaves que usa (todas son hashes):
--   agg:n             campo = payment_type, valor = cantidad de viajes
--   agg:suma          campo = payment_type, valor = suma de fare_amount
--   alarma:anomalias  campo = vendor_id,    valor = anomalías acumuladas
--   alarma:alertas    campo = vendor_id,    valor = alertas emitidas
--
-- ARGV[1] = payment_type, ARGV[2] = fare_amount, ARGV[3] = vendor_id,
-- ARGV[4] = '1' si el viaje es una anomalía, '0' si no.
-- ARGV[5] = umbral: cada cuántas anomalías de un proveedor se emite una alerta.
-- Devuelve 1 si este mensaje disparó una alerta, 0 si no.

local pt, fare, vendor, anom = ARGV[1], ARGV[2], ARGV[3], ARGV[4]
local umbral = tonumber(ARGV[5])

-- TODO 4 (paso 3b)
-- Escriba aquí lo mismo que hace el trigger feed_trip_after() de sql/pg_feed.sql,
-- pero con comandos de Valkey. Se llaman con redis.call('COMANDO', llave, campo, valor).
--   a) Sume 1 al campo pt de agg:n                    -> HINCRBY
--   b) Sume fare al campo pt de agg:suma              -> HINCRBYFLOAT
--   c) Si anom == '1' (es un string, no un número):
--        c1) sume 1 al campo vendor de alarma:anomalias; HINCRBY devuelve el valor nuevo
--        c2) si ese valor % umbral == 0, sume 1 al campo vendor de alarma:alertas
--            y devuelva 1
--   d) En cualquier otro caso, devuelva 0.
-- Verificación automática: las tres variantes de Valkey dan los mismos conteos y
-- alertas que Postgres. Borre la línea siguiente cuando termine.
return redis.error_reply('TODO 4: lua/feed.lua sin implementar')
