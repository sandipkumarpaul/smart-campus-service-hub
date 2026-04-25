-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 20, 2026 at 09:39 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smart_campus_service_hub`
--

-- --------------------------------------------------------

--
-- Table structure for table `academic_deadlines`
--

CREATE TABLE `academic_deadlines` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `deadline_datetime` datetime NOT NULL,
  `priority` enum('low','medium','high') DEFAULT 'medium',
  `reminder_enabled` tinyint(1) DEFAULT 1,
  `status` enum('pending','completed','missed') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `campus_events`
--

CREATE TABLE `campus_events` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `created_by` bigint(20) UNSIGNED NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `event_date` varchar(50) NOT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `location_text` varchar(255) DEFAULT NULL,
  `banner_image` varchar(255) DEFAULT NULL,
  `status` enum('upcoming','completed','cancelled') DEFAULT 'upcoming',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `target_audience` varchar(100) NOT NULL,
  `capacity_limit` int(11) NOT NULL,
  `recap_text` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `campus_events`
--

INSERT INTO `campus_events` (`id`, `created_by`, `title`, `description`, `category`, `event_date`, `start_time`, `end_time`, `location_text`, `banner_image`, `status`, `created_at`, `updated_at`, `target_audience`, `capacity_limit`, `recap_text`) VALUES
(1, 3, 'BRACU Tech Fest 2026', 'Join us for the biggest tech meetup of the semester. Free pizza, networking, and a keynote by alumni.', 'Social', '2026-05-15', NULL, NULL, 'Indoor Games Room', NULL, 'upcoming', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'All Students', 100, ''),
(2, 5, 'Python for Beginners Workshop', 'A hands-on, 2-hour crash course into Python programming. Bring your laptops!', 'Workshop', '2026-04-25', NULL, NULL, 'UB202 Computer Lab', NULL, 'upcoming', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Freshmen', 30, ''),
(3, 6, 'Calculus Survival Seminar', 'Tips and tricks to pass MAT120 without losing your mind.', 'Seminar', '2026-04-28', NULL, NULL, 'Online (Zoom)', NULL, 'upcoming', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Engineering Students', 0, ''),
(4, 1, 'Flow Fest', 'TBA', 'Workshop', '0000-00-00', NULL, NULL, 'Multipurpose Hall', NULL, 'upcoming', '2026-04-20 06:39:43', '2026-04-20 06:39:43', 'Students', 100, NULL),
(5, 1, 'Flow Fest', 'TBA', 'Workshop', '0000-00-00', NULL, NULL, 'Multipurpose Hall', NULL, 'upcoming', '2026-04-20 06:41:28', '2026-04-20 06:41:28', 'Students', 120, NULL),
(6, 1, 'Flow Fest', 'TBA', 'Workshop', 'Apr 24, 2026', NULL, NULL, 'Multipurpose Hall', NULL, 'upcoming', '2026-04-20 06:54:08', '2026-04-20 06:54:08', 'Students', 150, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `conversations`
--

CREATE TABLE `conversations` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `conversation_type` enum('private','group') DEFAULT 'private',
  `title` varchar(150) DEFAULT NULL,
  `created_by` bigint(20) UNSIGNED DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `context_type` varchar(50) NOT NULL,
  `context_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `conversations`
--

INSERT INTO `conversations` (`id`, `conversation_type`, `title`, `created_by`, `created_at`, `context_type`, `context_id`) VALUES
(1, 'private', 'Inquiry regarding Tutor', NULL, '2026-04-20 06:18:43', 'Tutor', 1),
(2, 'private', 'Inquiry regarding Study Partner', NULL, '2026-04-20 06:18:43', 'Study Partner', 2),
(3, 'private', 'Inquiry regarding Study Partner', NULL, '2026-04-20 07:05:20', 'Study Partner', 3),
(4, 'private', 'Inquiry regarding Study Partner', NULL, '2026-04-20 07:27:25', 'Study Partner', 4);

-- --------------------------------------------------------

--
-- Table structure for table `conversation_members`
--

CREATE TABLE `conversation_members` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `conversation_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `joined_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `course_code` varchar(30) NOT NULL,
  `course_title` varchar(150) NOT NULL,
  `department` varchar(120) DEFAULT NULL,
  `semester` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `deadline_reminders`
--

CREATE TABLE `deadline_reminders` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `deadline_id` bigint(20) UNSIGNED NOT NULL,
  `remind_at` datetime NOT NULL,
  `reminder_type` enum('email','in_app','sms') DEFAULT 'in_app',
  `is_sent` tinyint(1) DEFAULT 0,
  `sent_at` datetime DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `event_participants`
--

CREATE TABLE `event_participants` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `event_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `attendance_status` enum('interested','going','attended','cancelled') DEFAULT 'interested',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `event_participants`
--

INSERT INTO `event_participants` (`id`, `event_id`, `user_id`, `attendance_status`, `created_at`) VALUES
(1, 1, 2, 'going', '2026-04-20 06:18:43'),
(2, 1, 4, 'going', '2026-04-20 06:18:43'),
(3, 1, 5, 'interested', '2026-04-20 06:18:43'),
(4, 2, 3, 'going', '2026-04-20 06:18:43'),
(5, 2, 6, 'interested', '2026-04-20 06:18:43'),
(6, 1, 1, 'going', '2026-04-20 06:25:17'),
(7, 4, 1, 'going', '2026-04-20 06:39:57'),
(8, 6, 1, 'going', '2026-04-20 06:54:16'),
(9, 3, 1, 'going', '2026-04-20 07:03:54');

-- --------------------------------------------------------

--
-- Table structure for table `marketplace_items`
--

CREATE TABLE `marketplace_items` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `seller_id` bigint(20) UNSIGNED NOT NULL,
  `title` varchar(150) NOT NULL,
  `description` text DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `item_condition` enum('new','like_new','good','fair','used') DEFAULT 'good',
  `status` enum('available','reserved','sold','removed') DEFAULT 'available',
  `location_text` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `marketplace_item_images`
--

CREATE TABLE `marketplace_item_images` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `item_id` bigint(20) UNSIGNED NOT NULL,
  `image_path` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `marketplace_orders`
--

CREATE TABLE `marketplace_orders` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `item_id` bigint(20) UNSIGNED NOT NULL,
  `buyer_id` bigint(20) UNSIGNED NOT NULL,
  `seller_id` bigint(20) UNSIGNED NOT NULL,
  `agreed_price` decimal(10,2) NOT NULL,
  `status` enum('requested','confirmed','completed','cancelled') DEFAULT 'requested',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `conversation_id` bigint(20) UNSIGNED NOT NULL,
  `sender_id` bigint(20) UNSIGNED NOT NULL,
  `message_text` text DEFAULT NULL,
  `message_type` enum('text','image','file') DEFAULT 'text',
  `file_path` varchar(255) DEFAULT NULL,
  `is_seen` tinyint(1) DEFAULT 0,
  `sent_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `conversation_id`, `sender_id`, `message_text`, `message_type`, `file_path`, `is_seen`, `sent_at`) VALUES
(1, 1, 3, 'Hi Sandip! Are you still available to tutor CSE220 next Monday?', 'text', NULL, 1, '2026-04-20 06:18:43'),
(2, 1, 2, 'Yes, absolutely. Do you want to meet in UB2 or online?', 'text', NULL, 0, '2026-04-20 06:18:43'),
(3, 2, 4, 'Hey! I am also struggling with ER Diagrams. Can I join your group?', 'text', NULL, 0, '2026-04-20 06:18:43'),
(4, 2, 1, 'hi', 'text', NULL, 0, '2026-04-20 06:24:20'),
(5, 3, 1, 'Hi', 'text', NULL, 0, '2026-04-20 07:05:33'),
(6, 4, 10, 'Hi, this is a test message.', 'text', NULL, 0, '2026-04-20 07:27:36'),
(7, 4, 9, 'Hello from my side.', 'text', NULL, 0, '2026-04-20 07:28:00');

-- --------------------------------------------------------

--
-- Table structure for table `notes`
--

CREATE TABLE `notes` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `uploader_id` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `file_path` varchar(255) NOT NULL,
  `file_type` varchar(50) DEFAULT NULL,
  `semester` varchar(50) DEFAULT NULL,
  `tags` varchar(255) DEFAULT NULL,
  `downloads_count` int(11) DEFAULT 0,
  `visibility` enum('public','private') DEFAULT 'public',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `note_downloads`
--

CREATE TABLE `note_downloads` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `note_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `downloaded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `note_ratings`
--

CREATE TABLE `note_ratings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `note_id` bigint(20) UNSIGNED NOT NULL,
  `rater_id` bigint(20) UNSIGNED NOT NULL,
  `rating` tinyint(3) UNSIGNED NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `type` varchar(100) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `related_table` varchar(100) DEFAULT NULL,
  `related_id` bigint(20) UNSIGNED DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `message`, `related_table`, `related_id`, `is_read`, `created_at`) VALUES
(1, 1, 'system', 'Welcome to Smart Campus Service Hub!', 'Your account has been successfully created. Explore the dashboard.', NULL, NULL, 1, '2026-04-20 06:18:43'),
(2, 1, 'booking', 'New Tutoring Request', 'Dipto has requested a time slot for your CSE220 tutoring service.', NULL, NULL, 0, '2026-04-20 06:18:43'),
(3, 1, 'event', 'Event Reminder', 'BRACU Tech Fest is happening in 2 days!', NULL, NULL, 0, '2026-04-20 06:18:43');

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `reporter_id` bigint(20) UNSIGNED NOT NULL,
  `reported_user_id` bigint(20) UNSIGNED DEFAULT NULL,
  `target_type` enum('tutoring_listing','study_partner_post','marketplace_item','note','event','message','ride_share_post','skill_exchange_post','review') NOT NULL,
  `target_id` bigint(20) UNSIGNED NOT NULL,
  `reason` varchar(255) NOT NULL,
  `details` text DEFAULT NULL,
  `status` enum('pending','reviewing','resolved','rejected') DEFAULT 'pending',
  `reviewed_by` bigint(20) UNSIGNED DEFAULT NULL,
  `admin_note` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reviews`
--

CREATE TABLE `reviews` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `reviewer_id` bigint(20) UNSIGNED NOT NULL,
  `reviewee_id` bigint(20) UNSIGNED NOT NULL,
  `service_type` enum('tutoring','ride_share','skill_exchange','marketplace') NOT NULL,
  `reference_id` bigint(20) UNSIGNED NOT NULL,
  `rating` tinyint(4) NOT NULL CHECK (`rating` between 1 and 5),
  `comment` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `ride_bookings`
--

CREATE TABLE `ride_bookings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `ride_post_id` bigint(20) UNSIGNED NOT NULL,
  `passenger_id` bigint(20) UNSIGNED NOT NULL,
  `seats_requested` int(11) DEFAULT 1,
  `status` enum('pending','confirmed','rejected','completed','cancelled') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `ride_share_posts`
--

CREATE TABLE `ride_share_posts` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `driver_id` bigint(20) UNSIGNED NOT NULL,
  `start_location` varchar(255) NOT NULL,
  `destination` varchar(255) NOT NULL,
  `route_details` text DEFAULT NULL,
  `travel_date` date NOT NULL,
  `departure_time` time NOT NULL,
  `available_seats` int(11) NOT NULL DEFAULT 1,
  `price_per_seat` decimal(10,2) DEFAULT 0.00,
  `contact_info` varchar(255) DEFAULT NULL,
  `status` enum('open','full','completed','cancelled') DEFAULT 'open',
  `pickup_latitude` decimal(10,7) DEFAULT NULL,
  `pickup_longitude` decimal(10,7) DEFAULT NULL,
  `destination_latitude` decimal(10,7) DEFAULT NULL,
  `destination_longitude` decimal(10,7) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `saved_items`
--

CREATE TABLE `saved_items` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `target_type` enum('tutoring_listing','study_partner_post','marketplace_item','note','event','ride_share_post','skill_exchange_post','study_session') NOT NULL,
  `target_id` bigint(20) UNSIGNED NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `service_locations`
--

CREATE TABLE `service_locations` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `service_type` enum('tutor','ride_pickup','item_exchange') NOT NULL,
  `reference_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED DEFAULT NULL,
  `name` varchar(150) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,7) NOT NULL,
  `longitude` decimal(10,7) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `skill_exchange_posts`
--

CREATE TABLE `skill_exchange_posts` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `post_type` enum('offer','request') NOT NULL,
  `skill_name` varchar(120) NOT NULL,
  `description` text DEFAULT NULL,
  `preferred_exchange` varchar(255) DEFAULT NULL,
  `availability_text` varchar(255) DEFAULT NULL,
  `status` enum('open','closed') DEFAULT 'open',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `skill_exchange_requests`
--

CREATE TABLE `skill_exchange_requests` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `post_id` bigint(20) UNSIGNED NOT NULL,
  `requester_id` bigint(20) UNSIGNED NOT NULL,
  `message` text DEFAULT NULL,
  `status` enum('pending','accepted','rejected','completed','cancelled') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `study_partner_matches`
--

CREATE TABLE `study_partner_matches` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `post_id` bigint(20) UNSIGNED NOT NULL,
  `requester_id` bigint(20) UNSIGNED NOT NULL,
  `status` enum('pending','accepted','rejected','cancelled') DEFAULT 'pending',
  `message` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `study_partner_posts`
--

CREATE TABLE `study_partner_posts` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED DEFAULT NULL,
  `title` varchar(150) NOT NULL,
  `goals` text DEFAULT NULL,
  `preferred_study_time` varchar(150) DEFAULT NULL,
  `study_mode` enum('online','offline','both') DEFAULT 'both',
  `location_text` varchar(255) DEFAULT NULL,
  `status` enum('open','matched','closed') DEFAULT 'open',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `current_topic` varchar(150) NOT NULL,
  `prep_goal` varchar(50) NOT NULL,
  `study_style` varchar(50) NOT NULL,
  `group_size` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `study_partner_posts`
--

INSERT INTO `study_partner_posts` (`id`, `user_id`, `course_id`, `title`, `goals`, `preferred_study_time`, `study_mode`, `location_text`, `status`, `created_at`, `updated_at`, `current_topic`, `prep_goal`, `study_style`, `group_size`) VALUES
(1, 3, NULL, 'CSE471 Final Prep', 'Looking for serious people to break down the math behind backpropagation.', 'Weekends 10 AM', 'both', NULL, 'open', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Artificial Neural Networks', 'Deep Understanding', 'Active Discussion', 4),
(2, 5, NULL, 'CSE340 Midterm Cram', 'I have all the past questions, just need someone to solve them with me!', 'Thursday Evening', 'both', NULL, 'open', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Entity Relationship Diagrams', 'Exam Cram', 'Quiz Each Other', 2),
(3, 2, NULL, 'STA201 Study Session', 'Let us sit together, do our own assignments, and only talk if we get stuck.', 'Monday Afternoons', 'both', NULL, 'open', '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Probability Distributions', 'Homework Help', 'Silent Parallel', 3),
(4, 9, NULL, 'CSE471', 'Code Debugging', 'Monday Afternoon', 'both', NULL, 'open', '2026-04-20 07:26:26', '2026-04-20 07:26:26', 'Module 2', 'Quick Review', 'Active Discussion', 2);

-- --------------------------------------------------------

--
-- Table structure for table `study_sessions`
--

CREATE TABLE `study_sessions` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `created_by` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED DEFAULT NULL,
  `title` varchar(150) NOT NULL,
  `description` text DEFAULT NULL,
  `session_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `mode` enum('online','offline','both') DEFAULT 'both',
  `location_text` varchar(255) DEFAULT NULL,
  `google_calendar_event_id` varchar(255) DEFAULT NULL,
  `meeting_link` varchar(255) DEFAULT NULL,
  `status` enum('scheduled','completed','cancelled') DEFAULT 'scheduled',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `study_session_participants`
--

CREATE TABLE `study_session_participants` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `session_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `invitation_status` enum('pending','accepted','declined') DEFAULT 'pending',
  `joined_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `top_rated_tutors`
-- (See below for the actual view)
--
CREATE TABLE `top_rated_tutors` (
`tutor_id` bigint(20) unsigned
,`full_name` varchar(120)
,`department` varchar(120)
,`major` varchar(120)
,`total_reviews` bigint(21)
,`average_rating` decimal(6,2)
);

-- --------------------------------------------------------

--
-- Table structure for table `tutoring_bookings`
--

CREATE TABLE `tutoring_bookings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `tutoring_listing_id` bigint(20) UNSIGNED NOT NULL,
  `student_id` bigint(20) UNSIGNED NOT NULL,
  `session_date` date DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `note` text DEFAULT NULL,
  `status` enum('pending','accepted','rejected','completed','cancelled') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tutoring_listings`
--

CREATE TABLE `tutoring_listings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `tutor_id` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED DEFAULT NULL,
  `subject_title` varchar(150) NOT NULL,
  `description` text DEFAULT NULL,
  `availability_text` varchar(255) DEFAULT NULL,
  `hourly_rate` decimal(10,2) DEFAULT 0.00,
  `contact_info` varchar(255) DEFAULT NULL,
  `free_consult` varchar(10) NOT NULL,
  `mode` enum('online','offline','both') DEFAULT 'both',
  `location_text` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `rate_type` varchar(50) NOT NULL,
  `teaching_style` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tutoring_listings`
--

INSERT INTO `tutoring_listings` (`id`, `tutor_id`, `course_id`, `subject_title`, `description`, `availability_text`, `hourly_rate`, `contact_info`, `free_consult`, `mode`, `location_text`, `is_active`, `created_at`, `updated_at`, `rate_type`, `teaching_style`) VALUES
(1, 2, NULL, 'CSE220: Data Structures', NULL, 'Mon/Wed 4:00 PM - 6:00 PM', 500.00, NULL, 'Yes', 'both', 'UB2 Library Room 3', 1, '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Paid', 'I focus heavily on visual tracing of algorithms before writing any code.'),
(2, 4, NULL, 'FIN254: Intro to Finance', NULL, 'Tue/Thu 2:00 PM - 5:00 PM', 400.00, NULL, 'No', 'online', 'Google Meet', 1, '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Paid', 'Practical examples using real-world stock market data and Excel.'),
(3, 6, NULL, 'MAT110: Differential Calculus', NULL, 'Friday Mornings', 0.00, NULL, 'Yes', '', 'UB1 Cafeteria', 1, '2026-04-20 06:18:43', '2026-04-20 06:18:43', 'Barter', 'Patient step-by-step problem solving. I will not move on until you understand the core theorem.');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `full_name` varchar(120) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('student','admin','moderator') DEFAULT 'student',
  `department` varchar(120) DEFAULT NULL,
  `major` varchar(120) DEFAULT NULL,
  `semester` varchar(50) DEFAULT NULL,
  `student_id` varchar(50) DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_verified` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `full_name`, `username`, `email`, `phone`, `password_hash`, `role`, `department`, `major`, `semester`, `student_id`, `profile_image`, `bio`, `is_active`, `is_verified`, `created_at`, `updated_at`) VALUES
(1, 'System Admin', 'admin', 'admin@campushub.com', '01700000000', 'replace_with_real_hashed_password', 'admin', 'Administration', 'System', 'N/A', NULL, NULL, NULL, 1, 1, '2026-04-13 17:54:39', '2026-04-13 17:54:39'),
(2, 'Sandip Kumar Paul', 'sandip', 'sandip@g.bracu.ac.bd', NULL, 'hashedpwd123', 'student', 'CSE', 'Computer Science', NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 06:18:43', '2026-04-20 06:18:43'),
(3, 'Tanjila Afsari Rubina', 'tanjila', 'tanjila@g.bracu.ac.bd', NULL, 'hashedpwd123', 'student', 'CSE', 'Computer Science', NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 06:18:43', '2026-04-20 06:18:43'),
(4, 'Dipto Saha', 'dipto', 'dipto@g.bracu.ac.bd', NULL, 'hashedpwd123', 'student', 'BBS', 'Finance', NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 06:18:43', '2026-04-20 06:18:43'),
(5, 'Shumi Akter', 'shumi', 'shumi@g.bracu.ac.bd', NULL, 'hashedpwd123', 'student', 'CSE', 'Computer Science', NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 06:18:43', '2026-04-20 06:18:43'),
(6, 'Rahat Ahmed', 'rahat', 'rahat@g.bracu.ac.bd', NULL, 'hashedpwd123', 'student', 'MNS', 'Mathematics', NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 06:18:43', '2026-04-20 06:18:43'),
(9, 'Sandip Kumar Paul', 'sandip.kumar.paul@g.bracu.ac.bd', 'sandip.kumar.paul@g.bracu.ac.bd', NULL, 'pbkdf2:sha256:1000000$KW1uJdDTa5Whj10J$0e630c73e22302eb8a8e092edca78d7bd92cf55bf6e12d252c11dd662655003a', 'student', 'CSE', NULL, NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 07:24:44', '2026-04-20 07:24:44'),
(10, 'Tanjila Afsari Rubina', 'tanjila.afsari.rubina@g.bracu.ac.bd', 'tanjila.afsari.rubina@g.bracu.ac.bd', NULL, 'pbkdf2:sha256:1000000$UIxKSut9svw8uqUg$2522d8c9c35be31be53b89f76270aea68ea407631bc0d83e3c85fafdee369f2b', 'student', 'CSE', NULL, NULL, NULL, NULL, NULL, 1, 0, '2026-04-20 07:27:13', '2026-04-20 07:27:13');

-- --------------------------------------------------------

--
-- Table structure for table `user_courses`
--

CREATE TABLE `user_courses` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `course_id` bigint(20) UNSIGNED NOT NULL,
  `relation_type` enum('enrolled','interested','tutoring') DEFAULT 'enrolled',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `user_dashboard_summary`
-- (See below for the actual view)
--
CREATE TABLE `user_dashboard_summary` (
`user_id` bigint(20) unsigned
,`full_name` varchar(120)
,`total_notes_uploaded` bigint(21)
,`total_tutoring_posts` bigint(21)
,`total_items_posted` bigint(21)
,`total_deadlines` bigint(21)
,`total_study_sessions_created` bigint(21)
,`total_reviews_received` bigint(21)
,`average_rating` decimal(6,2)
);

-- --------------------------------------------------------

--
-- Table structure for table `user_locations`
--

CREATE TABLE `user_locations` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` bigint(20) UNSIGNED NOT NULL,
  `label` varchar(100) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure for view `top_rated_tutors`
--
DROP TABLE IF EXISTS `top_rated_tutors`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `top_rated_tutors`  AS SELECT `u`.`id` AS `tutor_id`, `u`.`full_name` AS `full_name`, `u`.`department` AS `department`, `u`.`major` AS `major`, count(`r`.`id`) AS `total_reviews`, round(avg(`r`.`rating`),2) AS `average_rating` FROM ((`users` `u` join `tutoring_listings` `tl` on(`tl`.`tutor_id` = `u`.`id`)) left join `reviews` `r` on(`r`.`reviewee_id` = `u`.`id` and `r`.`service_type` = 'tutoring')) GROUP BY `u`.`id`, `u`.`full_name`, `u`.`department`, `u`.`major` HAVING count(`r`.`id`) > 0 ORDER BY round(avg(`r`.`rating`),2) DESC, count(`r`.`id`) DESC ;

-- --------------------------------------------------------

--
-- Structure for view `user_dashboard_summary`
--
DROP TABLE IF EXISTS `user_dashboard_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `user_dashboard_summary`  AS SELECT `u`.`id` AS `user_id`, `u`.`full_name` AS `full_name`, (select count(0) from `notes` `n` where `n`.`uploader_id` = `u`.`id`) AS `total_notes_uploaded`, (select count(0) from `tutoring_listings` `tl` where `tl`.`tutor_id` = `u`.`id`) AS `total_tutoring_posts`, (select count(0) from `marketplace_items` `mi` where `mi`.`seller_id` = `u`.`id`) AS `total_items_posted`, (select count(0) from `academic_deadlines` `ad` where `ad`.`user_id` = `u`.`id`) AS `total_deadlines`, (select count(0) from `study_sessions` `ss` where `ss`.`created_by` = `u`.`id`) AS `total_study_sessions_created`, (select count(0) from `reviews` `r` where `r`.`reviewee_id` = `u`.`id`) AS `total_reviews_received`, (select round(avg(`r`.`rating`),2) from `reviews` `r` where `r`.`reviewee_id` = `u`.`id`) AS `average_rating` FROM `users` AS `u` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `academic_deadlines`
--
ALTER TABLE `academic_deadlines`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_academic_deadlines_user` (`user_id`),
  ADD KEY `fk_academic_deadlines_course` (`course_id`);

--
-- Indexes for table `campus_events`
--
ALTER TABLE `campus_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_campus_events_creator` (`created_by`);

--
-- Indexes for table `conversations`
--
ALTER TABLE `conversations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_conversations_creator` (`created_by`);

--
-- Indexes for table `conversation_members`
--
ALTER TABLE `conversation_members`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_conversation_member` (`conversation_id`,`user_id`),
  ADD KEY `fk_conversation_members_user` (`user_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `course_code` (`course_code`);

--
-- Indexes for table `deadline_reminders`
--
ALTER TABLE `deadline_reminders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_deadline_reminders_deadline` (`deadline_id`);

--
-- Indexes for table `event_participants`
--
ALTER TABLE `event_participants`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_event_user` (`event_id`,`user_id`),
  ADD KEY `fk_event_participants_user` (`user_id`);

--
-- Indexes for table `marketplace_items`
--
ALTER TABLE `marketplace_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_marketplace_items_seller` (`seller_id`),
  ADD KEY `idx_marketplace_items_status` (`status`);

--
-- Indexes for table `marketplace_item_images`
--
ALTER TABLE `marketplace_item_images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_marketplace_item_images_item` (`item_id`);

--
-- Indexes for table `marketplace_orders`
--
ALTER TABLE `marketplace_orders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_marketplace_orders_item` (`item_id`),
  ADD KEY `fk_marketplace_orders_buyer` (`buyer_id`),
  ADD KEY `fk_marketplace_orders_seller` (`seller_id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_messages_conversation` (`conversation_id`),
  ADD KEY `idx_messages_sender` (`sender_id`);

--
-- Indexes for table `notes`
--
ALTER TABLE `notes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notes_uploader` (`uploader_id`),
  ADD KEY `idx_notes_course` (`course_id`);

--
-- Indexes for table `note_downloads`
--
ALTER TABLE `note_downloads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_note_downloads_note` (`note_id`),
  ADD KEY `fk_note_downloads_user` (`user_id`);

--
-- Indexes for table `note_ratings`
--
ALTER TABLE `note_ratings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_note_rating_user` (`note_id`,`rater_id`),
  ADD KEY `fk_note_ratings_rater` (`rater_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notifications_user_read` (`user_id`,`is_read`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_reports_reporter` (`reporter_id`),
  ADD KEY `fk_reports_reported_user` (`reported_user_id`),
  ADD KEY `fk_reports_reviewed_by` (`reviewed_by`);

--
-- Indexes for table `reviews`
--
ALTER TABLE `reviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_reviews_reviewer` (`reviewer_id`),
  ADD KEY `idx_reviews_reviewee` (`reviewee_id`),
  ADD KEY `idx_reviews_service_type` (`service_type`);

--
-- Indexes for table `ride_bookings`
--
ALTER TABLE `ride_bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_ride_bookings_post` (`ride_post_id`),
  ADD KEY `fk_ride_bookings_passenger` (`passenger_id`);

--
-- Indexes for table `ride_share_posts`
--
ALTER TABLE `ride_share_posts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_ride_share_posts_driver` (`driver_id`),
  ADD KEY `idx_ride_share_posts_status` (`status`);

--
-- Indexes for table `saved_items`
--
ALTER TABLE `saved_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_saved_item` (`user_id`,`target_type`,`target_id`);

--
-- Indexes for table `service_locations`
--
ALTER TABLE `service_locations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_service_locations_user` (`user_id`);

--
-- Indexes for table `skill_exchange_posts`
--
ALTER TABLE `skill_exchange_posts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_skill_exchange_posts_user` (`user_id`);

--
-- Indexes for table `skill_exchange_requests`
--
ALTER TABLE `skill_exchange_requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_skill_exchange_requests_post` (`post_id`),
  ADD KEY `fk_skill_exchange_requests_requester` (`requester_id`);

--
-- Indexes for table `study_partner_matches`
--
ALTER TABLE `study_partner_matches`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_study_partner_matches_post` (`post_id`),
  ADD KEY `fk_study_partner_matches_requester` (`requester_id`);

--
-- Indexes for table `study_partner_posts`
--
ALTER TABLE `study_partner_posts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_study_partner_posts_user` (`user_id`),
  ADD KEY `fk_study_partner_posts_course` (`course_id`);

--
-- Indexes for table `study_sessions`
--
ALTER TABLE `study_sessions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_study_sessions_creator` (`created_by`),
  ADD KEY `fk_study_sessions_course` (`course_id`);

--
-- Indexes for table `study_session_participants`
--
ALTER TABLE `study_session_participants`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_study_session_participant` (`session_id`,`user_id`),
  ADD KEY `fk_study_session_participants_user` (`user_id`);

--
-- Indexes for table `tutoring_bookings`
--
ALTER TABLE `tutoring_bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_tutoring_bookings_listing` (`tutoring_listing_id`),
  ADD KEY `fk_tutoring_bookings_student` (`student_id`);

--
-- Indexes for table `tutoring_listings`
--
ALTER TABLE `tutoring_listings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_tutoring_listings_tutor` (`tutor_id`),
  ADD KEY `idx_tutoring_listings_course` (`course_id`),
  ADD KEY `idx_tutoring_listings_active` (`is_active`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `student_id` (`student_id`);

--
-- Indexes for table `user_courses`
--
ALTER TABLE `user_courses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_user_course_relation` (`user_id`,`course_id`,`relation_type`),
  ADD KEY `fk_user_courses_course` (`course_id`);

--
-- Indexes for table `user_locations`
--
ALTER TABLE `user_locations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_user_locations_user` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `academic_deadlines`
--
ALTER TABLE `academic_deadlines`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `campus_events`
--
ALTER TABLE `campus_events`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `conversations`
--
ALTER TABLE `conversations`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `conversation_members`
--
ALTER TABLE `conversation_members`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `deadline_reminders`
--
ALTER TABLE `deadline_reminders`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `event_participants`
--
ALTER TABLE `event_participants`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `marketplace_items`
--
ALTER TABLE `marketplace_items`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `marketplace_item_images`
--
ALTER TABLE `marketplace_item_images`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `marketplace_orders`
--
ALTER TABLE `marketplace_orders`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `notes`
--
ALTER TABLE `notes`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `note_downloads`
--
ALTER TABLE `note_downloads`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `note_ratings`
--
ALTER TABLE `note_ratings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reviews`
--
ALTER TABLE `reviews`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ride_bookings`
--
ALTER TABLE `ride_bookings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ride_share_posts`
--
ALTER TABLE `ride_share_posts`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `saved_items`
--
ALTER TABLE `saved_items`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `service_locations`
--
ALTER TABLE `service_locations`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `skill_exchange_posts`
--
ALTER TABLE `skill_exchange_posts`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `skill_exchange_requests`
--
ALTER TABLE `skill_exchange_requests`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `study_partner_matches`
--
ALTER TABLE `study_partner_matches`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `study_partner_posts`
--
ALTER TABLE `study_partner_posts`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `study_sessions`
--
ALTER TABLE `study_sessions`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `study_session_participants`
--
ALTER TABLE `study_session_participants`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tutoring_bookings`
--
ALTER TABLE `tutoring_bookings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tutoring_listings`
--
ALTER TABLE `tutoring_listings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `user_courses`
--
ALTER TABLE `user_courses`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_locations`
--
ALTER TABLE `user_locations`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `academic_deadlines`
--
ALTER TABLE `academic_deadlines`
  ADD CONSTRAINT `fk_academic_deadlines_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_academic_deadlines_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `campus_events`
--
ALTER TABLE `campus_events`
  ADD CONSTRAINT `fk_campus_events_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `conversations`
--
ALTER TABLE `conversations`
  ADD CONSTRAINT `fk_conversations_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `conversation_members`
--
ALTER TABLE `conversation_members`
  ADD CONSTRAINT `fk_conversation_members_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_conversation_members_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `deadline_reminders`
--
ALTER TABLE `deadline_reminders`
  ADD CONSTRAINT `fk_deadline_reminders_deadline` FOREIGN KEY (`deadline_id`) REFERENCES `academic_deadlines` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `event_participants`
--
ALTER TABLE `event_participants`
  ADD CONSTRAINT `fk_event_participants_event` FOREIGN KEY (`event_id`) REFERENCES `campus_events` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_event_participants_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `marketplace_items`
--
ALTER TABLE `marketplace_items`
  ADD CONSTRAINT `fk_marketplace_items_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `marketplace_item_images`
--
ALTER TABLE `marketplace_item_images`
  ADD CONSTRAINT `fk_marketplace_item_images_item` FOREIGN KEY (`item_id`) REFERENCES `marketplace_items` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `marketplace_orders`
--
ALTER TABLE `marketplace_orders`
  ADD CONSTRAINT `fk_marketplace_orders_buyer` FOREIGN KEY (`buyer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_marketplace_orders_item` FOREIGN KEY (`item_id`) REFERENCES `marketplace_items` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_marketplace_orders_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `fk_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_messages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notes`
--
ALTER TABLE `notes`
  ADD CONSTRAINT `fk_notes_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_notes_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `note_downloads`
--
ALTER TABLE `note_downloads`
  ADD CONSTRAINT `fk_note_downloads_note` FOREIGN KEY (`note_id`) REFERENCES `notes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_note_downloads_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `note_ratings`
--
ALTER TABLE `note_ratings`
  ADD CONSTRAINT `fk_note_ratings_note` FOREIGN KEY (`note_id`) REFERENCES `notes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_note_ratings_rater` FOREIGN KEY (`rater_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `fk_reports_reported_user` FOREIGN KEY (`reported_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_reports_reporter` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_reports_reviewed_by` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `reviews`
--
ALTER TABLE `reviews`
  ADD CONSTRAINT `fk_reviews_reviewee` FOREIGN KEY (`reviewee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_reviews_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `ride_bookings`
--
ALTER TABLE `ride_bookings`
  ADD CONSTRAINT `fk_ride_bookings_passenger` FOREIGN KEY (`passenger_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_ride_bookings_post` FOREIGN KEY (`ride_post_id`) REFERENCES `ride_share_posts` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `ride_share_posts`
--
ALTER TABLE `ride_share_posts`
  ADD CONSTRAINT `fk_ride_share_posts_driver` FOREIGN KEY (`driver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `saved_items`
--
ALTER TABLE `saved_items`
  ADD CONSTRAINT `fk_saved_items_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `service_locations`
--
ALTER TABLE `service_locations`
  ADD CONSTRAINT `fk_service_locations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `skill_exchange_posts`
--
ALTER TABLE `skill_exchange_posts`
  ADD CONSTRAINT `fk_skill_exchange_posts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `skill_exchange_requests`
--
ALTER TABLE `skill_exchange_requests`
  ADD CONSTRAINT `fk_skill_exchange_requests_post` FOREIGN KEY (`post_id`) REFERENCES `skill_exchange_posts` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_skill_exchange_requests_requester` FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `study_partner_matches`
--
ALTER TABLE `study_partner_matches`
  ADD CONSTRAINT `fk_study_partner_matches_post` FOREIGN KEY (`post_id`) REFERENCES `study_partner_posts` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_study_partner_matches_requester` FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `study_partner_posts`
--
ALTER TABLE `study_partner_posts`
  ADD CONSTRAINT `fk_study_partner_posts_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_study_partner_posts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `study_sessions`
--
ALTER TABLE `study_sessions`
  ADD CONSTRAINT `fk_study_sessions_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_study_sessions_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `study_session_participants`
--
ALTER TABLE `study_session_participants`
  ADD CONSTRAINT `fk_study_session_participants_session` FOREIGN KEY (`session_id`) REFERENCES `study_sessions` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_study_session_participants_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `tutoring_bookings`
--
ALTER TABLE `tutoring_bookings`
  ADD CONSTRAINT `fk_tutoring_bookings_listing` FOREIGN KEY (`tutoring_listing_id`) REFERENCES `tutoring_listings` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_tutoring_bookings_student` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `tutoring_listings`
--
ALTER TABLE `tutoring_listings`
  ADD CONSTRAINT `fk_tutoring_listings_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_tutoring_listings_tutor` FOREIGN KEY (`tutor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_courses`
--
ALTER TABLE `user_courses`
  ADD CONSTRAINT `fk_user_courses_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_user_courses_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_locations`
--
ALTER TABLE `user_locations`
  ADD CONSTRAINT `fk_user_locations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
