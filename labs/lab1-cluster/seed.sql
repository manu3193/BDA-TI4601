-- Datos mínimos del ejemplo del Lab 1.
-- Son deliberadamente pocos: sirven para verificar localidad, no para el P1.

UPSERT INTO catalogo_producto (producto_id, sku, nombre, precio)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'SKU-CAFE', 'Café', 8.50),
  ('00000000-0000-0000-0000-000000000002', 'SKU-CACAO', 'Cacao', 12.00);

INSERT INTO pedido
  (region, pedido_id, producto_id, tienda, estado, monto, version)
VALUES
  ('cr-sj',    '10000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000001', 'tienda-sj', 'CREADO', 8.50, 0),
  ('cr-limon', '10000000-0000-0000-0000-000000000002',
   '00000000-0000-0000-0000-000000000002', 'tienda-limon', 'CREADO', 12.00, 0),
  ('us-east',  '10000000-0000-0000-0000-000000000003',
   '00000000-0000-0000-0000-000000000001', 'tienda-us', 'CREADO', 8.50, 0)
ON CONFLICT (region, pedido_id) DO NOTHING;

