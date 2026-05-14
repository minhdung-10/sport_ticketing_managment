-- =========================================================================================
-- REFACTORED SPORTS TICKETING SCHEMA
-- Changes from original version:
-- 1. Uses DROP DATABASE IF EXISTS for clean runs.
-- 2. Added UNIQUE(EventID, SeatNumber) constraint to Seats.
-- 3. Widened SeatNumber to VARCHAR(20).
-- 4. TicketType and SeatType are natively VARCHAR(50).
-- 5. sp_BookTicket variable widths adjusted to VARCHAR(50) to prevent truncation.
-- 6. Removed redundant UPDATE Seats from sp_CancelBooking (handled by trigger).
-- 7. Seed data for Events 1 & 2 directly uses realistic Vietnamese tiers.
-- 8. Bookings seed data uses dynamic subqueries instead of hardcoded IDs.
-- 9. Bookings strictly reference 'booked' seats and matching ticket types.
-- 10. SET GLOBAL event_scheduler = ON is commented out (requires DBA execution).
-- 11. User creation passwords replaced with 'CHANGE_ME_BEFORE_RUNNING'.
-- =========================================================================================

-- =====================
-- SECTION: CREATE DATABASE + USE
-- =====================
DROP DATABASE IF EXISTS SportsTicketingDB;
CREATE DATABASE IF NOT EXISTS SportsTicketingDB;
USE SportsTicketingDB;

-- Disable ONLY_FULL_GROUP_BY to allow DATE() in GROUP BY with DATE_FORMAT() in SELECT
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- =====================
-- SECTION: CREATE TABLE STATEMENTS
-- =====================
CREATE TABLE Events (
    EventID INT AUTO_INCREMENT PRIMARY KEY,
    EventName VARCHAR(255) NOT NULL,
    EventDate DATETIME NOT NULL,
    Venue VARCHAR(255) NOT NULL,
    TotalSeats INT,
    Status ENUM('upcoming', 'ongoing', 'completed', 'cancelled'),
    Logo1Path VARCHAR(255) DEFAULT NULL,
    Logo2Path VARCHAR(255) DEFAULT NULL,
    SeatMapPath VARCHAR(255) DEFAULT NULL
);

CREATE TABLE Tickets (
    TicketID INT AUTO_INCREMENT PRIMARY KEY,
    EventID INT,
    TicketType VARCHAR(50),
    Price DECIMAL(10,2),
    QuantityAvailable INT,
    FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE
);

CREATE TABLE Customers (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerName VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE,
    PhoneNumber VARCHAR(20),
    Address TEXT,
    PasswordHash VARCHAR(255),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE BoxOffices (
    BoxOfficeID INT AUTO_INCREMENT PRIMARY KEY,
    OfficeName VARCHAR(255),
    Address TEXT,
    EventID INT DEFAULT NULL,
    FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE SET NULL
);

CREATE TABLE Seats (
SeatID INT AUTO_INCREMENT PRIMARY KEY,
    EventID INT,
    SeatNumber VARCHAR(20),
    SeatType VARCHAR(50),
    Status ENUM('available', 'booked', 'reserved', 'cancelled'),
    ReservedAt TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE,
    UNIQUE (EventID, SeatNumber)
);

CREATE TABLE Bookings (
    BookingID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT,
    SeatID INT,
    TicketID INT,
    BookingDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('confirmed', 'cancelled', 'pending'),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (SeatID) REFERENCES Seats(SeatID),
    FOREIGN KEY (TicketID) REFERENCES Tickets(TicketID)
);

CREATE TABLE Payments (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    BookingID INT,
    Amount DECIMAL(10,2),
    PaymentMethod ENUM('cash', 'card', 'online'),
    PaymentStatus ENUM('paid', 'refunded', 'pending'),
    PaidAt TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (BookingID) REFERENCES Bookings(BookingID) ON DELETE CASCADE
);

-- =====================
-- SECTION: INSERT SAMPLE DATA
-- =====================
-- Insert into Events
INSERT INTO Events (EventName, EventDate, Venue, TotalSeats, Status, Logo1Path, Logo2Path, SeatMapPath) VALUES
('Trận chung kết Cúp Quốc Gia: Hà Nội FC vs Viettel', '2026-05-15 19:00:00', 'Sân vận động Mỹ Đình', 40000, 'upcoming', 'Logo_Hà_Nội_FC.png', 'Viettel_FC_2021.svg.png', 'football stadium.jpg'),
('Giải bóng rổ VBA: Saigon Heat vs Hanoi Buffaloes', '2026-06-10 18:30:00', 'Nhà thi đấu CIS', 2500, 'upcoming', 'saigonheatlogo.webp', 'hanoibuffaloes logo.png', 'basketball court.webp'),
('Quần vợt Vietnam Open 2026 - Chung kết đơn nam', '2026-07-20 15:00:00', 'Cung điền kinh trong nhà Mỹ Đình', 3000, 'upcoming', NULL, NULL, NULL),
('Giao hữu Quốc tế: ĐT Việt Nam vs ĐT Thái Lan', '2026-08-05 20:00:00', 'Sân vận động Thống Nhất', 15000, 'upcoming', NULL, NULL, NULL),
('Giải bóng chuyền nữ Quốc tế VTV Cup', '2026-09-12 17:00:00', 'Nhà thi đấu Ninh Bình', 5000, 'upcoming', NULL, NULL, NULL);

-- Insert into Tickets
INSERT INTO Tickets (EventID, TicketType, Price, QuantityAvailable) VALUES
-- Event 1: Football Stadium Pricing (Trận chung kết Cúp Quốc Gia)
(1, 'Khán đài A1', 150000.00, 500),
(1, 'Khán đài A2', 100000.00, 500),
(1, 'Khán đài A3', 100000.00, 500),
(1, 'Khán đài B',   70000.00, 1500),
(1, 'Khán đài C',   50000.00, 1000),
(1, 'Khán đài D',   50000.00, 1000),
-- Event 2: Basketball Court Pricing (Giải bóng rổ VBA)
(2, 'VIP A1', 700000.00, 100),
(2, 'Premium A1', 450000.00, 200),
(2, 'Heat Zone', 250000.00, 500),
(2, 'Standard A', 200000.00, 500),
(2, 'courtside', 2000000.00, 50),
(2, 'VIP B', 700000.00, 100),
(2, 'Premium B1', 450000.00, 200),
(2, 'Standard B', 200000.00, 500),
-- Events 3, 4
(3, 'Standard', 1200000.00, 3000),
(4, 'VIP', 2000000.00, 1000),
(4, 'Economy', 500000.00, 14000);

-- Insert into Customers
-- DEMO ONLY: all accounts use password  Demo@2026!
-- Hashes generated with bcrypt (cost=12). NEVER commit real user passwords.
INSERT INTO Customers (CustomerName, Email, PhoneNumber, Address, PasswordHash) VALUES
('Nguyễn Văn An',  'nguyenvan.an@example.com', '0901234567', 'Quận 1, TP. HCM',            '$2b$12$qUpmF2lOAjXo7LYDoCIBle52bZTMFnrhkJX/zjZSp/jUekIizBmR2'),
('Trần Thị Bích',  'bich.tran@example.com',    '0912345678', 'Quận Cầu Giấy, Hà Nội',      '$2b$12$MAfTaBPa6eKVDGK3P1xzbuUpVjJ.xk90WEMjKRCsHaLcksSmG0cIe'),
('Lê Hoàng Nam',   'nam.lehoang@example.com',  '0923456789', 'Quận Hải Châu, Đà Nẵng',     '$2b$12$Dw13Utf8H5nUhr7OdpI9j.7PoSRAdMclYJoNmxvKJ38829F7WmKDG'),
('Phạm Thu Hà',    'thuha.pham@example.com',   '0934567890', 'TP. Thủ Đức, TP. HCM',       '$2b$12$2gzjBWXfY6vJti0Ss6vt3esN.jzcBSfP3dYdG.vIvZvYfP1s3xdcW'),
('Vũ Đức Thắng',   'thang.vu@example.com',     '0945678901', 'Quận Đống Đa, Hà Nội',       '$2b$12$IX0yoKHSiuBUlFtb5IGiNeJBSsX65PiBGsfxRKa0T.JPk3rDpzRfS');

-- Insert into BoxOffices
INSERT INTO BoxOffices (OfficeName, Address, EventID) VALUES
('Phòng vé Mỹ Đình 1', 'Cửa Đông SVĐ Mỹ Đình', 1),
('Phòng vé Mỹ Đình 2', 'Cửa Tây SVĐ Mỹ Đình', 3),
('Phòng vé CIS', 'Cổng chính Nhà thi đấu CIS', 2),
('Phòng vé Thống Nhất', 'Đường Nguyễn Kim, Quận 10', 4),
('Phòng vé Ninh Bình', 'Nhà thi đấu tỉnh Ninh Bình', 5);

-- Insert into Seats
INSERT INTO Seats (EventID, SeatNumber, SeatType, Status) VALUES
-- Event 1
(1, 'A1-001', 'Khán đài A1', 'available'), (1, 'A1-002', 'Khán đài A1', 'available'), 
(1, 'A1-003', 'Khán đài A1', 'booked'),    (1, 'A1-004', 'Khán đài A1', 'available'), (1, 'A1-005', 'Khán đài A1', 'available'),
(1, 'A2-001', 'Khán đài A2', 'available'), (1, 'A2-002', 'Khán đài A2', 'booked'), 
(1, 'A2-003', 'Khán đài A2', 'available'), (1, 'A2-004', 'Khán đài A2', 'available'), (1, 'A2-005', 'Khán đài A2', 'available'),
(1, 'A3-001', 'Khán đài A3', 'available'), (1, 'A3-002', 'Khán đài A3', 'available'), 
(1, 'A3-003', 'Khán đài A3', 'available'), (1, 'A3-004', 'Khán đài A3', 'available'), (1, 'A3-005', 'Khán đài A3', 'available'),
(1, 'B-001', 'Khán đài B', 'available'), (1, 'B-002', 'Khán đài B', 'available'), (1, 'B-003', 'Khán đài B', 'available'),
(1, 'B-004', 'Khán đài B', 'available'), (1, 'B-005', 'Khán đài B', 'available'), (1, 'B-006', 'Khán đài B', 'available'),
(1, 'B-007', 'Khán đài B', 'available'), (1, 'B-008', 'Khán đài B', 'available'), (1, 'B-009', 'Khán đài B', 'available'),
(1, 'B-010', 'Khán đài B', 'available'), (1, 'B-011', 'Khán đài B', 'available'), (1, 'B-012', 'Khán đài B', 'available'),
(1, 'B-013', 'Khán đài B', 'available'), (1, 'B-014', 'Khán đài B', 'available'), (1, 'B-015', 'Khán đài B', 'available'),
(1, 'C-001', 'Khán đài C', 'available'), (1, 'C-002', 'Khán đài C', 'available'), (1, 'C-003', 'Khán đài C', 'available'),
(1, 'C-004', 'Khán đài C', 'available'), (1, 'C-005', 'Khán đài C', 'available'), (1, 'C-006', 'Khán đài C', 'available'),
(1, 'C-007', 'Khán đài C', 'available'), (1, 'C-008', 'Khán đài C', 'available'), (1, 'C-009', 'Khán đài C', 'available'),
(1, 'C-010', 'Khán đài C', 'available'),
(1, 'D-001', 'Khán đài D', 'available'), (1, 'D-002', 'Khán đài D', 'available'), (1, 'D-003', 'Khán đài D', 'available'),
(1, 'D-004', 'Khán đài D', 'available'), (1, 'D-005', 'Khán đài D', 'available'), (1, 'D-006', 'Khán đài D', 'available'),
(1, 'D-007', 'Khán đài D', 'available'), (1, 'D-008', 'Khán đài D', 'available'), (1, 'D-009', 'Khán đài D', 'available'),
(1, 'D-010', 'Khán đài D', 'available'),
-- Event 2
(2, 'VA1-001', 'VIP A1', 'available'), (2, 'VA1-002', 'VIP A1', 'booked'), 
(2, 'VA1-003', 'VIP A1', 'available'), (2, 'VA1-004', 'VIP A1', 'available'), (2, 'VA1-005', 'VIP A1', 'available'),
(2, 'PA1-001', 'Premium A1', 'available'), (2, 'PA1-002', 'Premium A1', 'available'),
(2, 'PA1-003', 'Premium A1', 'available'), (2, 'PA1-004', 'Premium A1', 'available'), (2, 'PA1-005', 'Premium A1', 'available'),
(2, 'HZ-001', 'Heat Zone', 'available'), (2, 'HZ-002', 'Heat Zone', 'available'), (2, 'HZ-003', 'Heat Zone', 'available'),
(2, 'HZ-004', 'Heat Zone', 'available'), (2, 'HZ-005', 'Heat Zone', 'booked'),    (2, 'HZ-006', 'Heat Zone', 'available'),
(2, 'HZ-007', 'Heat Zone', 'available'), (2, 'HZ-008', 'Heat Zone', 'available'), (2, 'HZ-009', 'Heat Zone', 'available'),
(2, 'HZ-010', 'Heat Zone', 'available'),
(2, 'SA-001', 'Standard A', 'available'), (2, 'SA-002', 'Standard A', 'available'),
(2, 'SA-003', 'Standard A', 'available'), (2, 'SA-004', 'Standard A', 'available'), (2, 'SA-005', 'Standard A', 'available'),
(2, 'CS-001', 'courtside', 'booked'),    (2, 'CS-002', 'courtside', 'available'),
(2, 'CS-003', 'courtside', 'available'), (2, 'CS-004', 'courtside', 'available'), (2, 'CS-005', 'courtside', 'available'),
(2, 'VB-001', 'VIP B', 'available'), (2, 'VB-002', 'VIP B', 'available'),
(2, 'VB-003', 'VIP B', 'available'), (2, 'VB-004', 'VIP B', 'available'), (2, 'VB-005', 'VIP B', 'available'),
(2, 'PB1-001', 'Premium B1', 'available'), (2, 'PB1-002', 'Premium B1', 'available'),
(2, 'PB1-003', 'Premium B1', 'available'), (2, 'PB1-004', 'Premium B1', 'available'), (2, 'PB1-005', 'Premium B1', 'available'),
(2, 'SB-001', 'Standard B', 'available'), (2, 'SB-002', 'Standard B', 'available'), (2, 'SB-003', 'Standard B', 'available'),
(2, 'SB-004', 'Standard B', 'available'), (2, 'SB-005', 'Standard B', 'available'), (2, 'SB-006', 'Standard B', 'available'),
(2, 'SB-007', 'Standard B', 'available'), (2, 'SB-008', 'Standard B', 'available'),    (2, 'SB-009', 'Standard B', 'available'),
(2, 'SB-010', 'Standard B', 'available'),
-- Events 3, 4
(3, 'S1', 'Standard', 'available'),
(4, 'V1', 'VIP', 'available');

-- Insert into Bookings
INSERT INTO Bookings (CustomerID, SeatID, TicketID, Status) VALUES
-- Event 1: Khán đài A1 (booked seat A1-003)
(1, (SELECT SeatID FROM Seats WHERE EventID = 1 AND SeatNumber = 'A1-003'), (SELECT TicketID FROM Tickets WHERE EventID = 1 AND TicketType = 'Khán đài A1'), 'confirmed'),
-- Event 1: Khán đài A2 (booked seat A2-002)
(2, (SELECT SeatID FROM Seats WHERE EventID = 1 AND SeatNumber = 'A2-002'), (SELECT TicketID FROM Tickets WHERE EventID = 1 AND TicketType = 'Khán đài A2'), 'confirmed'),
-- Event 2: VIP A1 (booked seat VA1-002)
(3, (SELECT SeatID FROM Seats WHERE EventID = 2 AND SeatNumber = 'VA1-002'), (SELECT TicketID FROM Tickets WHERE EventID = 2 AND TicketType = 'VIP A1'), 'confirmed'),
-- Event 2: courtside (booked seat CS-001)
(4, (SELECT SeatID FROM Seats WHERE EventID = 2 AND SeatNumber = 'CS-001'), (SELECT TicketID FROM Tickets WHERE EventID = 2 AND TicketType = 'courtside'), 'confirmed'),
-- Event 2: Heat Zone (booked seat HZ-005)
(5, (SELECT SeatID FROM Seats WHERE EventID = 2 AND SeatNumber = 'HZ-005'), (SELECT TicketID FROM Tickets WHERE EventID = 2 AND TicketType = 'Heat Zone'), 'pending');

-- Insert into Payments
-- Amounts match the Tickets.Price of each booked seat's ticket type.
INSERT INTO Payments (BookingID, Amount, PaymentMethod, PaymentStatus, PaidAt) VALUES
(1, 150000.00, 'online', 'paid', CURRENT_TIMESTAMP),   -- Khán đài A1
(2, 100000.00, 'card', 'paid', CURRENT_TIMESTAMP),     -- Khán đài A2
(3, 700000.00, 'online', 'paid', CURRENT_TIMESTAMP),   -- VIP A1
(4, 2000000.00, 'cash', 'paid', CURRENT_TIMESTAMP),    -- courtside
(5, 250000.00, 'online', 'pending', NULL);             -- Heat Zone

-- =====================
-- SECTION: INDEXES
-- =====================
CREATE INDEX idx_seats_eventid ON Seats(EventID);
CREATE INDEX idx_seats_status ON Seats(Status);
CREATE INDEX idx_bookings_customerid ON Bookings(CustomerID);
CREATE INDEX idx_bookings_seatid ON Bookings(SeatID);
CREATE INDEX idx_tickets_eventid ON Tickets(EventID);
CREATE INDEX idx_seats_reserved ON Seats(Status, ReservedAt);

-- =====================
-- SECTION: VIEWS
-- =====================

-- 1. vw_SoldOutEvents
CREATE OR REPLACE VIEW vw_SoldOutEvents AS
SELECT e.EventID, e.EventName, e.EventDate, e.Venue
FROM Events e
JOIN Seats s ON e.EventID = s.EventID
GROUP BY e.EventID, e.EventName, e.EventDate, e.Venue
HAVING COUNT(s.SeatID) > 0 AND COUNT(s.SeatID) = SUM(CASE WHEN s.Status = 'booked' THEN 1 ELSE 0 END);

-- 2. vw_RevenueByEvent
CREATE OR REPLACE VIEW vw_RevenueByEvent AS
SELECT 
    e.EventID, 
    e.EventName, 
    COUNT(b.BookingID) AS TotalTicketsSold, 
    COALESCE(SUM(p.Amount), 0) AS TotalRevenue
FROM Events e
LEFT JOIN Seats s ON e.EventID = s.EventID
LEFT JOIN Bookings b ON s.SeatID = b.SeatID AND b.Status = 'confirmed'
LEFT JOIN Payments p ON b.BookingID = p.BookingID AND p.PaymentStatus = 'paid'
GROUP BY e.EventID, e.EventName;

-- 3. vw_SeatAvailability
CREATE OR REPLACE VIEW vw_SeatAvailability AS
SELECT 
    e.EventID, 
    e.EventName, 
    COUNT(s.SeatID) AS TotalSeats,
    COUNT(CASE WHEN s.Status = 'booked' THEN 1 END) AS BookedSeats,
    COUNT(CASE WHEN s.Status = 'available' THEN 1 END) AS AvailableSeats
FROM Events e
LEFT JOIN Seats s ON e.EventID = s.EventID
GROUP BY e.EventID, e.EventName;

-- =====================
-- SECTION: STORED PROCEDURES
-- =====================
DELIMITER //

-- 1. sp_BookTicket
CREATE PROCEDURE sp_BookTicket(IN p_CustomerID INT, IN p_SeatID INT, IN p_TicketID INT)
BEGIN
    DECLARE v_SeatStatus VARCHAR(20);
    DECLARE v_TicketPrice DECIMAL(10,2);
    DECLARE v_SeatEventID INT;
    DECLARE v_SeatType VARCHAR(50);
    DECLARE v_TicketEventID INT;
    DECLARE v_TicketType VARCHAR(50);

    -- Transaction rollback handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lock the seat row and read its current state
    SELECT Status, EventID, SeatType
    INTO v_SeatStatus, v_SeatEventID, v_SeatType
    FROM Seats WHERE SeatID = p_SeatID FOR UPDATE;

    -- sp_BookTicket runs only after payment is confirmed, so the seat just
    -- needs to still be claimable. A 'reserved' seat is the normal case; an
    -- 'available' seat means this customer's hold expired during checkout
    -- (the seat was not taken by anyone else, so the paid booking proceeds).
    -- A seat already 'booked' belongs to someone else and must be rejected.
    IF v_SeatStatus = 'booked' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seat has already been booked by another customer.';
    END IF;
    IF v_SeatStatus = 'cancelled' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seat is not available for booking.';
    END IF;

    -- Get ticket price, event, and type
    SELECT Price, EventID, TicketType INTO v_TicketPrice, v_TicketEventID, v_TicketType
    FROM Tickets WHERE TicketID = p_TicketID;

    -- Cross-event and seat/ticket type validation
    IF v_SeatEventID != v_TicketEventID THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ticket does not belong to the same event as the seat.';
    END IF;
    IF v_SeatType != v_TicketType THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ticket type does not match seat type.';
    END IF;

    -- Insert booking; trg_AfterBookingInsert transitions Seats to 'booked' and clears ReservedAt
    INSERT INTO Bookings (CustomerID, SeatID, TicketID, Status)
    VALUES (p_CustomerID, p_SeatID, p_TicketID, 'confirmed');

    SET @LastBookingID = LAST_INSERT_ID();

    -- Record the completed payment (sp_BookTicket runs only after payment is confirmed)
    INSERT INTO Payments (BookingID, Amount, PaymentMethod, PaymentStatus, PaidAt)
    VALUES (@LastBookingID, v_TicketPrice, 'online', 'paid', NOW());

    COMMIT;
END //

-- 2. sp_CancelBooking
CREATE PROCEDURE sp_CancelBooking(IN p_BookingID INT)
BEGIN
    DECLARE v_BookingStatus VARCHAR(20);
    DECLARE v_SeatID INT;
    
    -- Transaction rollback handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check booking status
    SELECT Status, SeatID INTO v_BookingStatus, v_SeatID FROM Bookings WHERE BookingID = p_BookingID FOR UPDATE;
    
    IF v_BookingStatus != 'confirmed' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking does not exist or is not confirmed.';
    END IF;
    
    -- Update Bookings
    UPDATE Bookings SET Status = 'cancelled' WHERE BookingID = p_BookingID;
    
    -- Update Payments
    UPDATE Payments SET PaymentStatus = 'refunded' WHERE BookingID = p_BookingID;
    
    COMMIT;
END //

-- 3. sp_ReserveSeat
CREATE PROCEDURE sp_ReserveSeat(IN p_SeatID INT)
BEGIN
    DECLARE v_SeatStatus VARCHAR(20);
    DECLARE v_ReservedAt TIMESTAMP;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lock the row so concurrent calls for the same seat are serialised
    SELECT Status, ReservedAt INTO v_SeatStatus, v_ReservedAt
    FROM Seats WHERE SeatID = p_SeatID FOR UPDATE;

    -- Accept if seat is free, or its previous reservation has expired
    IF v_SeatStatus = 'available'
       OR (v_SeatStatus = 'reserved' AND v_ReservedAt < NOW() - INTERVAL 10 MINUTE) THEN
        UPDATE Seats SET Status = 'reserved', ReservedAt = NOW() WHERE SeatID = p_SeatID;
        COMMIT;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seat is not available for reservation.';
    END IF;
END //

DELIMITER ;

-- =====================
-- SECTION: USER DEFINED FUNCTIONS
-- =====================
DELIMITER //

-- 1. fn_TotalRevenue
CREATE FUNCTION fn_TotalRevenue(p_EventID INT) RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE v_TotalRevenue DECIMAL(10,2);
    
    SELECT COALESCE(SUM(p.Amount), 0) INTO v_TotalRevenue
    FROM Payments p
    JOIN Bookings b ON p.BookingID = b.BookingID
    JOIN Seats s ON b.SeatID = s.SeatID
    WHERE s.EventID = p_EventID AND p.PaymentStatus = 'paid' AND b.Status = 'confirmed';
    
    RETURN v_TotalRevenue;
END //

-- 2. fn_TicketsSold
CREATE FUNCTION fn_TicketsSold(p_EventID INT) RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_TicketsSold INT;
    
    SELECT COUNT(b.BookingID) INTO v_TicketsSold
    FROM Bookings b
    JOIN Seats s ON b.SeatID = s.SeatID
    WHERE s.EventID = p_EventID AND b.Status = 'confirmed';
    
    RETURN v_TicketsSold;
END //

DELIMITER ;

-- =====================
-- SECTION: TRIGGERS
-- =====================
DELIMITER //

-- 1. trg_AfterBookingInsert
CREATE TRIGGER trg_AfterBookingInsert
AFTER INSERT ON Bookings
FOR EACH ROW
BEGIN
    IF NEW.Status = 'confirmed' THEN
        UPDATE Seats SET Status = 'booked', ReservedAt = NULL WHERE SeatID = NEW.SeatID;
    END IF;
END //

-- 2. trg_AfterBookingCancel
CREATE TRIGGER trg_AfterBookingCancel
AFTER UPDATE ON Bookings
FOR EACH ROW
BEGIN
    IF NEW.Status = 'cancelled' AND OLD.Status != 'cancelled' THEN
        UPDATE Seats SET Status = 'available', ReservedAt = NULL WHERE SeatID = NEW.SeatID;
    END IF;
END //

DELIMITER ;

-- =====================
-- SECTION: EVENT SCHEDULER
-- =====================
-- NOTE: Make sure to enable event scheduler on your DB server:
-- SET GLOBAL event_scheduler = ON;

DELIMITER //

CREATE EVENT IF NOT EXISTS evt_ExpireReservations
ON SCHEDULE EVERY 1 MINUTE
DO
BEGIN
    UPDATE Seats
    SET Status = 'available', ReservedAt = NULL
    WHERE Status = 'reserved'
      AND ReservedAt < NOW() - INTERVAL 10 MINUTE;
END //

DELIMITER ;

-- =====================
-- SECTION: SECURITY - USER ROLES
-- =====================
-- Drop users if they exist to avoid errors on re-run
DROP USER IF EXISTS 'admin_user'@'localhost';
DROP USER IF EXISTS 'cashier_user'@'localhost';
DROP USER IF EXISTS 'manager_user'@'localhost';

-- 1. admin_user
CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'CHANGE_ME_BEFORE_RUNNING';
GRANT ALL PRIVILEGES ON SportsTicketingDB.* TO 'admin_user'@'localhost';

-- 2. cashier_user
CREATE USER 'cashier_user'@'localhost' IDENTIFIED BY 'CHANGE_ME_BEFORE_RUNNING';
GRANT SELECT ON SportsTicketingDB.Events TO 'cashier_user'@'localhost';
GRANT SELECT ON SportsTicketingDB.Seats TO 'cashier_user'@'localhost';
GRANT SELECT ON SportsTicketingDB.Tickets TO 'cashier_user'@'localhost';
GRANT INSERT, UPDATE ON SportsTicketingDB.Bookings TO 'cashier_user'@'localhost';
GRANT INSERT, UPDATE ON SportsTicketingDB.Payments TO 'cashier_user'@'localhost';

-- 3. manager_user
CREATE USER 'manager_user'@'localhost' IDENTIFIED BY 'CHANGE_ME_BEFORE_RUNNING';
GRANT SELECT ON SportsTicketingDB.* TO 'manager_user'@'localhost';

FLUSH PRIVILEGES;
