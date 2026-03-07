-- Core Carrier Table
CREATE TABLE carriers (
    usdot_number VARCHAR(15) PRIMARY KEY,
    legal_name VARCHAR(255),
    dba_name VARCHAR(255),
    physical_address VARCHAR(255),
    physical_city VARCHAR(100),
    physical_state VARCHAR(2),
    physical_zip VARCHAR(10),
    telephone VARCHAR(20),
    power_units INTEGER,
    drivers INTEGER,
    mcs_150_date DATE,
    operation_classification VARCHAR(255),
    carrier_operation VARCHAR(255),
    cargo_classification TEXT,
    vmt_annual BIGINT,
    vmt_year INTEGER
);

-- Insurance & Authority Table
CREATE TABLE licensing_insurance (
    mc_number VARCHAR(15) PRIMARY KEY,
    usdot_number VARCHAR(15) REFERENCES carriers(usdot_number),
    authority_type VARCHAR(50),
    authority_status VARCHAR(50),
    authority_granted_date DATE,
    insurance_provider VARCHAR(255),
    policy_number VARCHAR(100),
    coverage_type VARCHAR(50),
    policy_effective_date DATE,
    policy_cancellation_date DATE
);

-- Safety & Accident Table (SMS Data)
CREATE TABLE safety_sms (
    usdot_number VARCHAR(15) PRIMARY KEY REFERENCES carriers(usdot_number),
    total_inspections INTEGER,
    total_crashes INTEGER,
    fatal_crashes INTEGER,
    injury_crashes INTEGER,
    tow_away_crashes INTEGER,
    unsafe_driving_percentile FLOAT,
    hos_compliance_percentile FLOAT,
    vehicle_maint_percentile FLOAT,
    driver_fitness_percentile FLOAT,
    controlled_substances_percentile FLOAT,
    vehicle_oos_rate FLOAT,
    driver_oos_rate FLOAT,
    national_avg_vehicle_oos FLOAT,
    national_avg_driver_oos FLOAT,
    last_update_date DATE
);

-- Active Leads View for Dashboard
CREATE VIEW active_leads AS
SELECT 
    c.usdot_number,
    c.legal_name,
    c.physical_state,
    c.power_units,
    c.drivers,
    c.cargo_classification,
    (c.vmt_annual / NULLIF(c.power_units, 0)) as vmt_per_truck,
    li.authority_granted_date,
    li.insurance_provider,
    li.policy_cancellation_date,
    s.total_crashes,
    s.unsafe_driving_percentile,
    s.vehicle_maint_percentile,
    s.vehicle_oos_rate
FROM carriers c
LEFT JOIN licensing_insurance li ON c.usdot_number = li.usdot_number
LEFT JOIN safety_sms s ON c.usdot_number = s.usdot_number
WHERE li.authority_status = 'ACTIVE';
