-- =====================
-- SECTION: CREATE DATABASE + USE
-- =====================
drop database sportsticketingdb;
CREATE DATABASE IF NOT EXISTS SportsTicketingDB;
USE SportsTicketingDB;

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
    TicketType ENUM('VIP', 'Standard', 'Economy'),
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
    SeatNumber VARCHAR(10),
    SeatType ENUM('VIP', 'Standard', 'Economy'),
    Status ENUM('available', 'booked', 'reserved', 'cancelled'),
    FOREIGN KEY (EventID) REFERENCES Events(EventID) ON DELETE CASCADE
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
(1, 'VIP', 1500000.00, 500),
(1, 'Standard', 800000.00, 15000),
(1, 'Economy', 400000.00, 24500),
(2, 'VIP', 1000000.00, 100),
(2, 'Standard', 500000.00, 2400),
(3, 'Standard', 1200000.00, 3000),
(4, 'VIP', 2000000.00, 1000),
(4, 'Economy', 500000.00, 14000);

-- Insert into Customers
INSERT INTO Customers (CustomerName, Email, PhoneNumber, Address, PasswordHash) VALUES
('Nguyễn Văn An', 'nguyenvan.an@example.com', '0901234567', 'Quận 1, TP. HCM', 'hash123'),
('Trần Thị Bích', 'bich.tran@example.com', '0912345678', 'Quận Cầu Giấy, Hà Nội', 'hash456'),
('Lê Hoàng Nam', 'nam.lehoang@example.com', '0923456789', 'Quận Hải Châu, Đà Nẵng', 'hash789'),
('Phạm Thu Hà', 'thuha.pham@example.com', '0934567890', 'TP. Thủ Đức, TP. HCM', 'hash012'),
('Vũ Đức Thắng', 'thang.vu@example.com', '0945678901', 'Quận Đống Đa, Hà Nội', 'hash345');

-- Insert into BoxOffices
INSERT INTO BoxOffices (OfficeName, Address, EventID) VALUES
('Phòng vé Mỹ Đình 1', 'Cửa Đông SVĐ Mỹ Đình', 1),
('Phòng vé Mỹ Đình 2', 'Cửa Tây SVĐ Mỹ Đình', 3),
('Phòng vé CIS', 'Cổng chính Nhà thi đấu CIS', 2),
('Phòng vé Thống Nhất', 'Đường Nguyễn Kim, Quận 10', 4),
('Phòng vé Ninh Bình', 'Nhà thi đấu tỉnh Ninh Bình', 5);

-- Insert into Seats (Events 1 & 2 have 40 seats each for testing; Events 3-5 have minimal seats for UI display)
INSERT INTO Seats (EventID, SeatNumber, SeatType, Status) VALUES
(1, 'V1', 'VIP', 'booked'),
(1, 'V2', 'VIP', 'available'),
(1, 'V3', 'VIP', 'available'),
(1, 'V4', 'VIP', 'available'),
(1, 'V5', 'VIP', 'available'),
(1, 'V6', 'VIP', 'available'),
(1, 'V7', 'VIP', 'available'),
(1, 'V8', 'VIP', 'available'),
(1, 'V9', 'VIP', 'available'),
(1, 'V10', 'VIP', 'available'),
(1, 'S1', 'Standard', 'booked'),
(1, 'S2', 'Standard', 'available'),
(1, 'S3', 'Standard', 'available'),
(1, 'S4', 'Standard', 'available'),
(1, 'S5', 'Standard', 'available'),
(1, 'S6', 'Standard', 'available'),
(1, 'S7', 'Standard', 'available'),
(1, 'S8', 'Standard', 'available'),
(1, 'S9', 'Standard', 'available'),
(1, 'S10', 'Standard', 'available'),
(1, 'S11', 'Standard', 'available'),
(1, 'S12', 'Standard', 'available'),
(1, 'S13', 'Standard', 'available'),
(1, 'S14', 'Standard', 'available'),
(1, 'S15', 'Standard', 'available'),
(1, 'S16', 'Standard', 'available'),
(1, 'S17', 'Standard', 'available'),
(1, 'S18', 'Standard', 'available'),
(1, 'S19', 'Standard', 'available'),
(1, 'E1', 'Economy', 'available'),
(1, 'E2', 'Economy', 'available'),
(1, 'E3', 'Economy', 'available'),
(1, 'E4', 'Economy', 'available'),
(1, 'E5', 'Economy', 'available'),
(1, 'E6', 'Economy', 'available'),
(1, 'E7', 'Economy', 'available'),
(1, 'E8', 'Economy', 'available'),
(1, 'E9', 'Economy', 'available'),
(1, 'E10', 'Economy', 'available'),
(2, 'V1', 'VIP', 'booked'),
(2, 'V2', 'VIP', 'available'),
(2, 'V3', 'VIP', 'available'),
(2, 'V4', 'VIP', 'available'),
(2, 'V5', 'VIP', 'available'),
(2, 'V6', 'VIP', 'available'),
(2, 'V7', 'VIP', 'available'),
(2, 'V8', 'VIP', 'available'),
(2, 'V9', 'VIP', 'available'),
(2, 'V10', 'VIP', 'available'),
(2, 'S1', 'Standard', 'booked'),
(2, 'S2', 'Standard', 'available'),
(2, 'S3', 'Standard', 'available'),
(2, 'S4', 'Standard', 'available'),
(2, 'S5', 'Standard', 'available'),
(2, 'S6', 'Standard', 'available'),
(2, 'S7', 'Standard', 'available'),
(2, 'S8', 'Standard', 'available'),
(2, 'S9', 'Standard', 'available'),
(2, 'S10', 'Standard', 'available'),
(2, 'S11', 'Standard', 'available'),
(2, 'S12', 'Standard', 'available'),
(2, 'S13', 'Standard', 'available'),
(2, 'S14', 'Standard', 'available'),
(2, 'S15', 'Standard', 'available'),
(2, 'S16', 'Standard', 'available'),
(2, 'S17', 'Standard', 'available'),
(2, 'S18', 'Standard', 'available'),
(2, 'S19', 'Standard', 'available'),
(2, 'S20', 'Standard', 'available'),
(2, 'S21', 'Standard', 'available'),
(2, 'S22', 'Standard', 'available'),
(2, 'S23', 'Standard', 'available'),
(2, 'S24', 'Standard', 'available'),
(2, 'S25', 'Standard', 'available'),
(2, 'S26', 'Standard', 'available'),
(2, 'S27', 'Standard', 'available'),
(2, 'S28', 'Standard', 'available'),
(2, 'S29', 'Standard', 'available'),
(3, 'S1', 'Standard', 'available'),
(4, 'V1', 'VIP', 'available');

-- Insert into Bookings
INSERT INTO Bookings (CustomerID, SeatID, TicketID, Status) VALUES
(1, 1, 1, 'confirmed'),
(2, 3, 2, 'confirmed'),
(3, 5, 4, 'confirmed'),
(4, 6, 5, 'confirmed'),
(5, 7, 6, 'pending');

-- Insert into Payments
INSERT INTO Payments (BookingID, Amount, PaymentMethod, PaymentStatus, PaidAt) VALUES
(1, 1500000.00, 'online', 'paid', CURRENT_TIMESTAMP),
(2, 800000.00, 'card', 'paid', CURRENT_TIMESTAMP),
(3, 1000000.00, 'online', 'paid', CURRENT_TIMESTAMP),
(4, 500000.00, 'cash', 'paid', CURRENT_TIMESTAMP),
(5, 1200000.00, 'online', 'pending', NULL);

-- =====================
-- SECTION: INDEXES
-- =====================
CREATE INDEX idx_seats_eventid ON Seats(EventID);
CREATE INDEX idx_seats_status ON Seats(Status);
CREATE INDEX idx_bookings_customerid ON Bookings(CustomerID);
CREATE INDEX idx_bookings_seatid ON Bookings(SeatID);
CREATE INDEX idx_tickets_eventid ON Tickets(EventID);

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
    DECLARE v_SeatType VARCHAR(20);
    DECLARE v_TicketEventID INT;
    DECLARE v_TicketType VARCHAR(20);
    
    -- Transaction rollback handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check seat availability, event, and type
    SELECT Status, EventID, SeatType INTO v_SeatStatus, v_SeatEventID, v_SeatType
    FROM Seats WHERE SeatID = p_SeatID FOR UPDATE;
    
    IF v_SeatStatus != 'available' THEN
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
    
    -- Insert into Bookings
    INSERT INTO Bookings (CustomerID, SeatID, TicketID, Status)
    VALUES (p_CustomerID, p_SeatID, p_TicketID, 'confirmed');
    
    SET @LastBookingID = LAST_INSERT_ID();
    
    -- Insert into Payments
    INSERT INTO Payments (BookingID, Amount, PaymentMethod, PaymentStatus)
    VALUES (@LastBookingID, v_TicketPrice, 'online', 'pending');
    
    -- Update Seat status (redundant with trigger but fulfilling direct requirement)
    UPDATE Seats SET Status = 'booked' WHERE SeatID = p_SeatID;
    
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
    
    -- Update Seats
    UPDATE Seats SET Status = 'available' WHERE SeatID = v_SeatID;
    
    -- Update Payments
    UPDATE Payments SET PaymentStatus = 'refunded' WHERE BookingID = p_BookingID;
    
    COMMIT;
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
    WHERE s.EventID = p_EventID AND p.PaymentStatus = 'paid';
    
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
        UPDATE Seats SET Status = 'booked' WHERE SeatID = NEW.SeatID;
    END IF;
END //

-- 2. trg_AfterBookingCancel
CREATE TRIGGER trg_AfterBookingCancel
AFTER UPDATE ON Bookings
FOR EACH ROW
BEGIN
    IF NEW.Status = 'cancelled' AND OLD.Status != 'cancelled' THEN
        UPDATE Seats SET Status = 'available' WHERE SeatID = NEW.SeatID;
    END IF;
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
CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'Admin123!';
GRANT ALL PRIVILEGES ON SportsTicketingDB.* TO 'admin_user'@'localhost';

-- 2. cashier_user
CREATE USER 'cashier_user'@'localhost' IDENTIFIED BY 'Cashier123!';
GRANT SELECT ON SportsTicketingDB.Events TO 'cashier_user'@'localhost';
GRANT SELECT ON SportsTicketingDB.Seats TO 'cashier_user'@'localhost';
GRANT SELECT ON SportsTicketingDB.Tickets TO 'cashier_user'@'localhost';
GRANT INSERT, UPDATE ON SportsTicketingDB.Bookings TO 'cashier_user'@'localhost';
GRANT INSERT, UPDATE ON SportsTicketingDB.Payments TO 'cashier_user'@'localhost';

-- 3. manager_user
CREATE USER 'manager_user'@'localhost' IDENTIFIED BY 'Manager123!';
GRANT SELECT ON SportsTicketingDB.* TO 'manager_user'@'localhost';

FLUSH PRIVILEGES;
