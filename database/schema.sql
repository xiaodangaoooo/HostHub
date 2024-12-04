/*
 * HostHub Database Setup
 * Created: December 2024
 * Description: Cultural exchange platform connecting travelers with hosts
 */

-- --------------------------------------------------------
-- Database Creation
-- --------------------------------------------------------
DROP DATABASE IF EXISTS hosthub;
CREATE DATABASE hosthub;
USE hosthub;

-- --------------------------------------------------------
-- Table Structure and Constraints
-- --------------------------------------------------------

-- Base user table
	CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_type ENUM('host', 'traveler') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Host table (depends on User)
CREATE TABLE Host (
    user_id INT PRIMARY KEY,
    rating DECIMAL(3,2) DEFAULT 0.0,
    preferred_language VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_rating CHECK (rating >= 0 AND rating <= 5)
);

-- Create Traveler table (depends on User)
CREATE TABLE Traveler (
    user_id INT PRIMARY KEY,
    language_spoken VARCHAR(255),
    skills TEXT,
    availability TEXT,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create Location table (no dependencies)
CREATE TABLE Location (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_location_search (country, state, city)
);

-- Create Listing table (depends on Host and Location)
CREATE TABLE Listing (
    listing_id INT PRIMARY KEY AUTO_INCREMENT,
    host_id INT NOT NULL,
    location_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    work_hour INT NOT NULL,
    duration_day INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive', 'completed', 'cancelled') DEFAULT 'active',
    work_type VARCHAR(100) NOT NULL,  -- Added this line
    FOREIGN KEY (host_id) REFERENCES Host(user_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES Location(location_id) ON DELETE CASCADE,
    INDEX idx_listing_status (status),
    INDEX idx_listing_host (host_id)
);

-- Create Application table (depends on Listing and Traveler)
CREATE TABLE Application (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    listing_id INT NOT NULL,
    traveler_id INT NOT NULL,
    date_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    introduction TEXT NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'withdrawn') DEFAULT 'pending',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reviewer_comments TEXT,
    FOREIGN KEY (listing_id) REFERENCES Listing(listing_id) ON DELETE CASCADE,
    FOREIGN KEY (traveler_id) REFERENCES Traveler(user_id) ON DELETE CASCADE,
    INDEX idx_application_status (status),
    INDEX idx_application_listing (listing_id),
    INDEX idx_application_traveler (traveler_id)
);

-- Create Message table (depends on User and Application)
CREATE TABLE Message (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    application_id INT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (application_id) REFERENCES Application(application_id) ON DELETE CASCADE,
    INDEX idx_message_participants (sender_id, receiver_id),
    INDEX idx_message_application (application_id)
);

-- Create Review table (depends on Traveler and Host)
CREATE TABLE Review (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    reviewer_id INT NOT NULL,
    host_id INT NOT NULL,
    rating DECIMAL(3,2) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'reported', 'hidden') DEFAULT 'active',
    FOREIGN KEY (reviewer_id) REFERENCES Traveler(user_id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES Host(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_review_rating CHECK (rating >= 0 AND rating <= 5),
    INDEX idx_review_host (host_id)
);

-- Create Notification table (depends on User)
CREATE TABLE Notification (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type ENUM('application_update', 'message', 'review', 'system') NOT NULL,
    related_id INT,  -- Can reference application_id, message_id, or review_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    status ENUM('unread', 'read', 'archived') DEFAULT 'unread',
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    INDEX idx_notification_user (user_id),
    INDEX idx_notification_status (status)
);

-- --------------------------------------------------------
-- User-Defined Functions
-- --------------------------------------------------------

-- Function to get total number of active listings for a host
CREATE FUNCTION GetHostActiveListingsCount(p_host_id INT) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE listing_count INT;
    SELECT COUNT(*) INTO listing_count
    FROM Listing
    WHERE host_id = p_host_id AND status = 'active';
    RETURN listing_count;
END //

-- Function to get application success rate for a traveler
CREATE FUNCTION GetTravelerSuccessRate(p_traveler_id INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
BEGIN
    DECLARE total_apps INT;
    DECLARE accepted_apps INT;
    
    SELECT COUNT(*), COUNT(CASE WHEN status = 'accepted' THEN 1 END)
    INTO total_apps, accepted_apps
    FROM Application
    WHERE traveler_id = p_traveler_id;
    
    IF total_apps = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN (accepted_apps * 100.0 / total_apps);
END //

DELIMITER ;

DELIMITER //

-- --------------------------------------------------------
-- Stored Procedures
-- --------------------------------------------------------

-- Procedure to handle listing application process
CREATE PROCEDURE ApplyToListing(
    IN p_traveler_id INT,
    IN p_listing_id INT,
    IN p_introduction TEXT,
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE listing_exists BOOLEAN;
    DECLARE already_applied BOOLEAN;
    
    -- Check if listing exists and is active
    SELECT EXISTS(
        SELECT 1 FROM Listing 
        WHERE listing_id = p_listing_id 
        AND status = 'active'
    ) INTO listing_exists;
    
    -- Check if already applied
    SELECT EXISTS(
        SELECT 1 FROM Application 
        WHERE traveler_id = p_traveler_id 
        AND listing_id = p_listing_id
    ) INTO already_applied;
    
    IF NOT listing_exists THEN
        SET p_success = FALSE;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Listing not found or inactive';
    ELSEIF already_applied THEN
        SET p_success = FALSE;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Already applied to this listing';
    ELSE
        INSERT INTO Application (listing_id, traveler_id, introduction)
        VALUES (p_listing_id, p_traveler_id, p_introduction);
        SET p_success = TRUE;
    END IF;
END //

-- Procedure to update listing status and handle related actions
CREATE PROCEDURE UpdateListingStatus(
    IN p_listing_id INT,
    IN p_new_status VARCHAR(20),
    IN p_host_id INT
)
BEGIN
    DECLARE is_owner BOOLEAN;
    
    -- Verify ownership
    SELECT EXISTS(
        SELECT 1 FROM Listing 
        WHERE listing_id = p_listing_id 
        AND host_id = p_host_id
    ) INTO is_owner;
    
    IF NOT is_owner THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Not authorized to update this listing';
    ELSE
        START TRANSACTION;
        
        -- Update listing status
        UPDATE Listing 
        SET status = p_new_status
        WHERE listing_id = p_listing_id;
        
        -- If completed/cancelled, update related applications
        IF p_new_status IN ('completed', 'cancelled') THEN
            UPDATE Application
            SET status = 'withdrawn'
            WHERE listing_id = p_listing_id
            AND status = 'pending';
        END IF;
        
        COMMIT;
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE EVENT cleanup_old_notifications
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- Archive old notifications
    UPDATE Notification
    SET status = 'archived'
    WHERE status = 'read'
    AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Delete very old archived notifications
    DELETE FROM Notification
    WHERE status = 'archived'
    AND created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
END //

DELIMITER ;


-- --------------------------------------------------------
-- Triggers
-- --------------------------------------------------------
DELIMITER //

CREATE TRIGGER before_host_insert
BEFORE INSERT ON Host
FOR EACH ROW
BEGIN
    DECLARE user_role VARCHAR(20);
    SELECT role_type INTO user_role FROM User WHERE user_id = NEW.user_id;
    IF user_role != 'host' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User must have role_type "host" to be inserted into Host table';
    END IF;
END //

CREATE TRIGGER before_traveler_insert
BEFORE INSERT ON Traveler
FOR EACH ROW
BEGIN
    DECLARE user_role VARCHAR(20);
    SELECT role_type INTO user_role FROM User WHERE user_id = NEW.user_id;
    IF user_role != 'traveler' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User must have role_type "traveler" to be inserted into Traveler table';
    END IF;
END //

CREATE TRIGGER after_review_insert
AFTER INSERT ON Review
FOR EACH ROW
BEGIN
    UPDATE Host
    SET rating = (
        SELECT AVG(rating)
        FROM Review
        WHERE host_id = NEW.host_id
        AND status = 'active'
    )
    WHERE user_id = NEW.host_id;
END //

CREATE TRIGGER after_review_update
AFTER UPDATE ON Review
FOR EACH ROW
BEGIN
    IF OLD.rating != NEW.rating OR OLD.status != NEW.status THEN
        UPDATE Host
        SET rating = (
            SELECT AVG(rating)
            FROM Review
            WHERE host_id = NEW.host_id
            AND status = 'active'
        )
        WHERE user_id = NEW.host_id;
    END IF;
END //

DELIMITER ;

DELIMITER //

-- --------------------------------------------------------
-- Sample Data Population
-- --------------------------------------------------------
INSERT INTO User (username, first_name, last_name, email, password_hash, role_type) VALUES
('john_host', 'John', 'Smith', 'john@example.com', 'hashed_password_1', 'host'),
('mary_host', 'Mary', 'Johnson', 'mary@example.com', 'hashed_password_2', 'host'),
('peter_traveler', 'Peter', 'Brown', 'peter@example.com', 'hashed_password_3', 'traveler'),
('sarah_traveler', 'Sarah', 'Davis', 'sarah@example.com', 'hashed_password_4', 'traveler'),
('mike_host', 'Mike', 'Wilson', 'mike@example.com', 'hashed_password_5', 'host'),
('lisa_traveler', 'Lisa', 'Anderson', 'lisa@example.com', 'hashed_password_6', 'traveler');

-- Insert Hosts
INSERT INTO Host (user_id, preferred_language) VALUES
(1, 'English'),
(2, 'English, Spanish'),
(5, 'English, French');

-- Insert Travelers
INSERT INTO Traveler (user_id, language_spoken, skills, availability) VALUES
(3, 'English, German', 'Gardening, Teaching', 'Available from June to August'),
(4, 'English, French', 'Farming, Cooking', 'Flexible schedule'),
(6, 'English, Spanish', 'Construction, Animal Care', 'Available year-round');

-- Insert Locations
INSERT INTO Location (country, state, city, zip_code) VALUES
('USA', 'California', 'San Francisco', '94105'),
('Canada', 'Ontario', 'Toronto', 'M5V 2T6'),
('USA', 'New York', 'Brooklyn', '11201'),
('France', NULL, 'Paris', '75001'),
('Spain', NULL, 'Barcelona', '08001');

-- Insert Listings
INSERT INTO Listing (host_id, location_id, title, description, work_hour, duration_day, work_type) VALUES
(1, 1, 'Farm Help Needed', 'Help needed with organic farming and animal care', 25, 30, 'Farming'),
(1, 2, 'Garden Maintenance', 'Looking for help with garden maintenance', 20, 14, 'Gardening'),
(2, 3, 'Teaching Assistant', 'Help needed with English teaching', 15, 60, 'Teaching'),
(2, 4, 'Eco-Building Project', 'Help with sustainable building project', 30, 45, 'Construction'),
(5, 5, 'Animal Sanctuary Help', 'Assistant needed for animal care', 25, 30, 'Animal Care');

-- Insert Applications
INSERT INTO Application (listing_id, traveler_id, introduction, status) VALUES
(1, 3, 'I have experience in organic farming and love working with animals.', 'pending'),
(1, 4, 'I am passionate about sustainable farming and eager to learn.', 'accepted'),
(2, 6, 'I have extensive gardening experience and am available immediately.', 'pending'),
(3, 3, 'I am a certified teacher and would love to help.', 'accepted'),
(4, 6, 'I have worked on several construction projects before.', 'rejected');

-- Insert Reviews
INSERT INTO Review (reviewer_id, host_id, rating, comment, status) VALUES
(3, 1, 4.5, 'Great experience working on the farm!', 'active'),
(4, 1, 5.0, 'Excellent host, learned a lot about organic farming', 'active'),
(3, 2, 4.0, 'Good teaching experience, supportive environment', 'active');

-- Insert Messages
INSERT INTO Message (sender_id, receiver_id, application_id, content) VALUES
(3, 1, 1, 'I would like to know more about the accommodation.'),
(1, 3, 1, 'We provide a private room with shared bathroom.'),
(4, 1, 2, 'When would you like me to start?'),
(1, 4, 2, 'Can you start next Monday?');

-- Insert Notifications
INSERT INTO Notification (user_id, title, content, type, related_id) VALUES
(3, 'New Message', 'You have a new message from John', 'message', 1),
(1, 'New Application', 'New application received for Farm Help listing', 'application_update', 1),
(4, 'Application Accepted', 'Your application has been accepted', 'application_update', 2),
(2, 'New Review', 'You received a new review', 'review', 3);