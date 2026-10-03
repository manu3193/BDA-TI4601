-- Consulta de almacén (Stonebraker et al.): agregado sobre pocas columnas de muchas filas.
SELECT payment_type, AVG(fare_amount) AS tarifa_promedio, COUNT(*) AS viajes
FROM trips
GROUP BY payment_type
ORDER BY payment_type;
