CREATE DATABASE IF NOT EXISTS fuel_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fuel_analysis;

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_code VARCHAR(30) NOT NULL UNIQUE,
  vehicle_type VARCHAR(60) NOT NULL,
  fuel_type VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS fuel_records (
  record_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  fill_date DATE NOT NULL,
  odometer_km DECIMAL(10,1) NOT NULL,
  litres DECIMAL(10,2) NOT NULL,
  total_cost DECIMAL(10,2) NOT NULL,
  full_tank_flag BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_record_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
  CONSTRAINT chk_odometer_nonnegative CHECK (odometer_km >= 0),
  CONSTRAINT chk_litres_positive CHECK (litres > 0),
  CONSTRAINT chk_cost_nonnegative CHECK (total_cost >= 0),
  INDEX idx_vehicle_date (vehicle_id, fill_date)
);
