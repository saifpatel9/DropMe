
-- DROP ME CAB BOOKING DATABASE SCHEMA

-- ========================
-- USER/PASSENGER TABLE
-- ========================
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    country_code VARCHAR(5),
    gender ENUM('Male', 'Female', 'Other'),
    profile_picture VARCHAR(255),
    description TEXT,
    payment_method VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    referral_code VARCHAR(50),
    referred_by VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ========================
-- DRIVER TABLE
-- ========================
CREATE TABLE Driver (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    gender ENUM('Male', 'Female', 'Other'),
    state VARCHAR(100),
    city VARCHAR(100),
    plate_number VARCHAR(20),
    manufacturer VARCHAR(100),
    color VARCHAR(50),
    manufacturing_year YEAR,
    seat_arrangement INT,
    full_address TEXT,
    availability BOOLEAN DEFAULT TRUE,
    upi_id VARCHAR(100),
    bank_name VARCHAR(100),
    ifsc_code VARCHAR(20),
    account_number VARCHAR(30),
    password_hash TEXT,
    daily_services BOOLEAN,
    rental_services BOOLEAN,
    outstation_services BOOLEAN,
    rating DECIMAL(3,2) DEFAULT 0.0,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    vehicle_type VARCHAR(50),
);

-- ========================
-- VEHICLE TABLE
-- ========================
CREATE TABLE Vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT,
    manufacturer VARCHAR(100),
    model_name VARCHAR(100),
    color VARCHAR(50),
    manufacturing_year YEAR,
    seat_arrangement INT,
    FOREIGN KEY (driver_id) REFERENCES Driver(driver_id)
);

-- ========================
-- SERVICE TYPE TABLE
-- ========================
CREATE TABLE ServiceType (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    number_of_seats INT,
    base_fare DECIMAL(10,2),
    min_fare DECIMAL(10,2),
    booking_fee DECIMAL(10,2),
    tax_percentage DECIMAL(5,2),
    price_per_minute DECIMAL(10,2),
    price_per_km DECIMAL(10,2),
    mileage BOOLEAN,
    daily_service BOOLEAN,
    rental_service BOOLEAN,
    outstation_service BOOLEAN,
    provider_commission DECIMAL(5,2),
    admin_commission DECIMAL(5,2),
    driver_cash_limit DECIMAL(10,2),
    picture VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================
-- BOOKING TABLE
-- ========================
CREATE TABLE Booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    driver_id INT,
    pickup_location VARCHAR(255),
    dropoff_location VARCHAR(255),
    pickup_latitude DECIMAL(9,6),
    pickup_longitude DECIMAL(9,6),
    drop_latitude DECIMAL(9,6),
    drop_longitude DECIMAL(9,6),
    scheduled_time DATETIME,
    status ENUM('Pending', 'Confirmed', 'Ongoing', 'Completed', 'Cancelled'),
    fare DECIMAL(10,2),
    distance_km DECIMAL(10,2),
    duration_min INT,
    service_type_id INT,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
    FOREIGN KEY (service_type_id) REFERENCES ServiceType(service_id)
);

-- ========================
-- WALLET TABLE
-- ========================
CREATE TABLE Wallet (
    wallet_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    used_amount DECIMAL(10,2),
    remaining_amount DECIMAL(10,2),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- ========================
-- PAYMENT TABLE
-- ========================
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    booking_id INT,
    payment_mode VARCHAR(50),
    amount DECIMAL(10,2),
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
);

-- ========================
-- PROMO CODE TABLE
-- ========================
CREATE TABLE PromoCode (
    promo_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    discount_amount DECIMAL(10,2),
    start_time DATETIME,
    expiry_time DATETIME,
    description TEXT,
    max_usage INT,
    max_usage_per_user INT,
    type ENUM('Flat', 'Percent')
);

-- ========================
-- RATING TABLE
-- ========================
CREATE TABLE Rating (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT,
    driver_id INT,
    booking_id INT,
    rating INT,
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passenger_id) REFERENCES User(user_id),
    FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
);

-- ========================
-- FEEDBACK TABLE
-- ========================
CREATE TABLE Feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    message TEXT,
    stars INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);
