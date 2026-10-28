USE fuel_analysis;
INSERT INTO vehicles (vehicle_code, vehicle_type, fuel_type) VALUES
('CAR-01', 'Hatchback', 'Petrol'), ('BIKE-01', 'Motorcycle', 'Petrol')
ON DUPLICATE KEY UPDATE vehicle_type=VALUES(vehicle_type), fuel_type=VALUES(fuel_type);

-- Sample full-tank and partial fill records. Re-running this file is safe for vehicles,
-- but use a fresh database to avoid duplicate sample records.
INSERT INTO fuel_records (vehicle_id, fill_date, odometer_km, litres, total_cost, full_tank_flag)
SELECT v.vehicle_id, s.fill_date, s.odometer_km, s.litres, s.total_cost, s.full_tank_flag
FROM vehicles v JOIN (
  SELECT 'CAR-01' vehicle_code, '2026-01-05' fill_date, 10000.0 odometer_km, 35.0 litres, 3850.0 total_cost, TRUE full_tank_flag UNION ALL
  SELECT 'CAR-01', '2026-01-20', 10420.0, 15.0, 1650.0, FALSE UNION ALL
  SELECT 'CAR-01', '2026-02-02', 10850.0, 35.0, 4025.0, TRUE UNION ALL
  SELECT 'CAR-01', '2026-02-18', 11280.0, 34.0, 3910.0, TRUE UNION ALL
  SELECT 'BIKE-01', '2026-01-08', 5000.0, 10.0, 1100.0, TRUE UNION ALL
  SELECT 'BIKE-01', '2026-01-22', 5350.0, 9.0, 990.0, TRUE UNION ALL
  SELECT 'BIKE-01', '2026-02-10', 5720.0, 9.5, 1092.5, TRUE
) s ON s.vehicle_code=v.vehicle_code
WHERE NOT EXISTS (SELECT 1 FROM fuel_records r WHERE r.vehicle_id=v.vehicle_id AND r.fill_date=s.fill_date AND r.odometer_km=s.odometer_km);
