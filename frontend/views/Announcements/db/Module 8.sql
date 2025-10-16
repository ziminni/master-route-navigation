CREATE TABLE `auth_user` (
  `user_id` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(150) UNIQUE NOT NULL,
  `email` varchar(255),
  `full_name` varchar(255)
);

CREATE TABLE `approvals` (
  `approval_id` int PRIMARY KEY AUTO_INCREMENT,
  `approver_id` int,
  `status` varchar(30),
  `comment` text,
  `created_at` timestamp DEFAULT (now())
);

CREATE TABLE `announcements` (
  `announcement_id` int PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `body` text,
  `author_id` int,
  `publish_at` datetime,
  `expire_at` datetime,
  `location` varchar(255),
  `approval_id` int,
  `status` varchar(30) DEFAULT 'draft',
  `visibility` varchar(20) DEFAULT 'public',
  `priority` int DEFAULT 0,
  `is_pinned` boolean DEFAULT false,
  `pinned_until` datetime,
  `created_at` timestamp NOT NULL DEFAULT (now()),
  `created_by` int,
  `updated_at` timestamp,
  `updated_by` int,
  `deleted_at` timestamp,
  `note` text
);

CREATE TABLE `tags` (
  `tag_id` int PRIMARY KEY AUTO_INCREMENT,
  `tag_name` varchar(60) UNIQUE NOT NULL,
  `created_at` timestamp DEFAULT (now())
);

CREATE TABLE `announcement_tag_map` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `announcement_id` int,
  `tag_id` int
);

CREATE TABLE `announcement_reads` (
  `read_id` int PRIMARY KEY AUTO_INCREMENT,
  `announcement_id` int,
  `user_id` int,
  `has_read` boolean DEFAULT false,
  `read_time` timestamp,
  `device_info` varchar(255),
  `created_at` timestamp DEFAULT (now())
);

CREATE TABLE `announcement_audience` (
  `audience_id` int PRIMARY KEY AUTO_INCREMENT,
  `announcement_id` int,
  `scope_type` varchar(30) NOT NULL,
  `scope_target_id` int,
  `created_at` timestamp DEFAULT (now()),
  `expires_at` datetime,
  `note` text
);

CREATE TABLE `documents` (
  `document_id` int PRIMARY KEY AUTO_INCREMENT,
  `announcement_id` int,
  `file_name` varchar(255) NOT NULL,
  `file_path` varchar(1024) NOT NULL,
  `mime_type` varchar(100),
  `file_size_bytes` bigint,
  `checksum` varchar(128),
  `uploaded_by` int,
  `uploaded_at` timestamp DEFAULT (now()),
  `visible` boolean DEFAULT true,
  `expires_at` datetime,
  `version` varchar(32),
  `description` text
);

CREATE TABLE `reminders` (
  `reminder_id` int PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `body` text,
  `author_id` int,
  `remind_at` datetime,
  `repeat_interval` varchar(50),
  `priority` int DEFAULT 0,
  `is_active` boolean DEFAULT true,
  `is_snoozable` boolean DEFAULT true,
  `snooze_until` datetime,
  `visibility` varchar(20) DEFAULT 'private',
  `created_at` timestamp NOT NULL DEFAULT (now()),
  `created_by` int,
  `updated_at` timestamp,
  `updated_by` int,
  `expires_at` datetime,
  `note` text
);

CREATE TABLE `reminder_audience` (
  `audience_id` int PRIMARY KEY AUTO_INCREMENT,
  `reminder_id` int,
  `scope_type` varchar(30) NOT NULL,
  `scope_target_id` int,
  `created_at` timestamp DEFAULT (now()),
  `expires_at` datetime,
  `note` text
);

CREATE TABLE `reminder_acknowledgements` (
  `ack_id` int PRIMARY KEY AUTO_INCREMENT,
  `reminder_id` int,
  `user_id` int,
  `acknowledged` boolean DEFAULT false,
  `ack_time` timestamp,
  `device_info` varchar(255),
  `created_at` timestamp DEFAULT (now())
);

ALTER TABLE `approvals` ADD FOREIGN KEY (`approver_id`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `announcements` ADD FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `announcements` ADD FOREIGN KEY (`approval_id`) REFERENCES `approvals` (`approval_id`);

ALTER TABLE `announcements` ADD FOREIGN KEY (`created_by`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `announcements` ADD FOREIGN KEY (`updated_by`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `announcement_tag_map` ADD FOREIGN KEY (`announcement_id`) REFERENCES `announcements` (`announcement_id`);

ALTER TABLE `announcement_tag_map` ADD FOREIGN KEY (`tag_id`) REFERENCES `tags` (`tag_id`);

ALTER TABLE `announcement_reads` ADD FOREIGN KEY (`announcement_id`) REFERENCES `announcements` (`announcement_id`);

ALTER TABLE `announcement_reads` ADD FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `announcement_audience` ADD FOREIGN KEY (`announcement_id`) REFERENCES `announcements` (`announcement_id`);

ALTER TABLE `documents` ADD FOREIGN KEY (`announcement_id`) REFERENCES `announcements` (`announcement_id`);

ALTER TABLE `documents` ADD FOREIGN KEY (`uploaded_by`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `reminders` ADD FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `reminders` ADD FOREIGN KEY (`created_by`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `reminders` ADD FOREIGN KEY (`updated_by`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `reminder_audience` ADD FOREIGN KEY (`reminder_id`) REFERENCES `reminders` (`reminder_id`);

ALTER TABLE `reminder_acknowledgements` ADD FOREIGN KEY (`reminder_id`) REFERENCES `reminders` (`reminder_id`);

ALTER TABLE `reminder_acknowledgements` ADD FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`user_id`);

ALTER TABLE `reminder_acknowledgements` ADD FOREIGN KEY (`reminder_id`) REFERENCES `reminder_acknowledgements` (`ack_id`);
