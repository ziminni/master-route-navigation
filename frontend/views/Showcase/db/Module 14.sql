CREATE TABLE `auth_user` (
  `auth_user_id` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(150),
  `email` varchar(255) UNIQUE
);

CREATE TABLE `media` (
  `media_id` int PRIMARY KEY AUTO_INCREMENT,
  `media_type` ENUM ('image', 'video', 'audio', 'file', 'link'),
  `path_or_url` text NOT NULL,
  `mime_type` varchar(100),
  `size_bytes` bigint,
  `checksum` varchar(64),
  `caption` varchar(150),
  `alt_text` varchar(150),
  `uploaded_by` int,
  `created_at` timestamp DEFAULT (now())
);

CREATE TABLE `project_media_map` (
  `media_id` int NOT NULL,
  `project_id` int NOT NULL,
  `sort_order` int,
  `is_primary` bool DEFAULT false,
  `created_at` timestamp DEFAULT (now()),
  PRIMARY KEY (`media_id`, `project_id`)
);

CREATE TABLE `competition_media_map` (
  `media_id` int NOT NULL,
  `competition_id` int NOT NULL,
  `sort_order` int,
  `is_primary` bool DEFAULT false,
  `created_at` timestamp DEFAULT (now()),
  PRIMARY KEY (`media_id`, `competition_id`)
);

CREATE TABLE `projects` (
  `projects_id` int PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(150) NOT NULL,
  `description` text,
  `submitted_by` int,
  `course_id` int,
  `organization_id` int,
  `status` text,
  `is_public` bool,
  `publish_at` timestamp,
  `created_at` timestamp,
  `updated_at` timestamp,
  `category` varchar(20),
  `context` varchar(50),
  `external_url` text,
  `author_display` varchar(150)
);

CREATE TABLE `project_members` (
  `project_members_id` int PRIMARY KEY AUTO_INCREMENT,
  `project_id` int,
  `user_id` int,
  `role` varchar(60),
  `contributions` varchar(255)
);

CREATE TABLE `project_tags` (
  `tag_id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(30) UNIQUE
);

CREATE TABLE `project_tag_map` (
  `project_id` int,
  `tag_id` int,
  PRIMARY KEY (`project_id`, `tag_id`)
);

CREATE TABLE `competitions` (
  `competition_id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `organizer` varchar(150),
  `start_date` date,
  `end_date` date,
  `related_event_id` int,
  `description` text,
  `event_type` varchar(50),
  `external_url` text,
  `submitted_by` int,
  `status` text DEFAULT 'draft',
  `is_public` bool DEFAULT false,
  `publish_at` timestamp,
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now())
);

CREATE TABLE `competition_achievements` (
  `achievement_id` int PRIMARY KEY AUTO_INCREMENT,
  `competition_id` int,
  `achievement_title` varchar(155) NOT NULL,
  `result_recognition` varchar(50),
  `specific_awards` varchar(255),
  `notes` text,
  `awarded_at` date
);

CREATE TABLE `competition_achievement_projects` (
  `achievement_id` int,
  `project_id` int,
  PRIMARY KEY (`achievement_id`, `project_id`)
);

CREATE TABLE `competition_achievement_users` (
  `achievement_id` int,
  `user_id` int,
  `role` varchar(60),
  PRIMARY KEY (`achievement_id`, `user_id`)
);

CREATE INDEX `project_media_map_index_0` ON `project_media_map` (`project_id`);

CREATE INDEX `project_media_map_index_1` ON `project_media_map` (`media_id`);

CREATE INDEX `competition_media_map_index_2` ON `competition_media_map` (`competition_id`);

CREATE INDEX `competition_media_map_index_3` ON `competition_media_map` (`media_id`);

ALTER TABLE `media` ADD FOREIGN KEY (`uploaded_by`) REFERENCES `auth_user` (`auth_user_id`);

ALTER TABLE `project_media_map` ADD FOREIGN KEY (`media_id`) REFERENCES `media` (`media_id`);

ALTER TABLE `project_media_map` ADD FOREIGN KEY (`project_id`) REFERENCES `projects` (`projects_id`);

ALTER TABLE `competition_media_map` ADD FOREIGN KEY (`media_id`) REFERENCES `media` (`media_id`);

ALTER TABLE `competition_media_map` ADD FOREIGN KEY (`competition_id`) REFERENCES `competitions` (`competition_id`);

ALTER TABLE `projects` ADD FOREIGN KEY (`submitted_by`) REFERENCES `auth_user` (`auth_user_id`);

ALTER TABLE `project_members` ADD FOREIGN KEY (`project_id`) REFERENCES `projects` (`projects_id`);

ALTER TABLE `project_members` ADD FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`auth_user_id`);

ALTER TABLE `project_tag_map` ADD FOREIGN KEY (`project_id`) REFERENCES `projects` (`projects_id`);

ALTER TABLE `project_tag_map` ADD FOREIGN KEY (`tag_id`) REFERENCES `project_tags` (`tag_id`);

ALTER TABLE `competitions` ADD FOREIGN KEY (`submitted_by`) REFERENCES `auth_user` (`auth_user_id`);

ALTER TABLE `competition_achievements` ADD FOREIGN KEY (`competition_id`) REFERENCES `competitions` (`competition_id`);

ALTER TABLE `competition_achievement_projects` ADD FOREIGN KEY (`achievement_id`) REFERENCES `competition_achievements` (`achievement_id`);

ALTER TABLE `competition_achievement_projects` ADD FOREIGN KEY (`project_id`) REFERENCES `projects` (`projects_id`);

ALTER TABLE `competition_achievement_users` ADD FOREIGN KEY (`achievement_id`) REFERENCES `competition_achievements` (`achievement_id`);

ALTER TABLE `competition_achievement_users` ADD FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`auth_user_id`);
