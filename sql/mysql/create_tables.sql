-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: online_learning_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `course_info`
--

DROP TABLE IF EXISTS `course_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_info` (
  `course_id` varchar(50) NOT NULL,
  `course_name` varchar(150) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `course_level` varchar(30) DEFAULT NULL,
  `course_duration_days` int DEFAULT NULL,
  `instructor_rating` decimal(4,2) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='课程基础信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `course_stat`
--

DROP TABLE IF EXISTS `course_stat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_stat` (
  `course_id` varchar(50) NOT NULL,
  `course_name` varchar(150) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `course_level` varchar(30) DEFAULT NULL,
  `course_duration_days` int DEFAULT NULL,
  `learner_count` bigint DEFAULT '0',
  `completion_count` bigint DEFAULT '0',
  `completion_rate` decimal(5,2) DEFAULT '0.00',
  `avg_study_time_hours` decimal(12,2) DEFAULT '0.00',
  `avg_progress_percentage` decimal(5,2) DEFAULT '0.00',
  `avg_video_completion_rate` decimal(5,2) DEFAULT '0.00',
  `avg_assignment_submit_rate` decimal(5,2) DEFAULT '0.00',
  `avg_quiz_score` decimal(5,2) DEFAULT '0.00',
  `avg_project_grade` decimal(5,2) DEFAULT '0.00',
  `avg_instructor_rating` decimal(4,2) DEFAULT '0.00',
  `avg_satisfaction_rating` decimal(4,2) DEFAULT '0.00',
  `avg_app_usage_percentage` decimal(5,2) DEFAULT '0.00',
  `update_date` date DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`course_id`),
  KEY `idx_category` (`category`),
  KEY `idx_course_level` (`course_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='课程资源效能统计表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `student_feature`
--

DROP TABLE IF EXISTS `student_feature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_feature` (
  `student_id` varchar(50) NOT NULL,
  `course_count` bigint DEFAULT '0',
  `completed_course_count` bigint DEFAULT '0',
  `completion_rate` decimal(5,2) DEFAULT '0.00',
  `total_study_time_hours` decimal(12,2) DEFAULT '0.00',
  `avg_session_duration_min` decimal(10,2) DEFAULT '0.00',
  `avg_login_frequency` decimal(10,2) DEFAULT '0.00',
  `avg_video_completion_rate` decimal(5,2) DEFAULT '0.00',
  `avg_progress_percentage` decimal(5,2) DEFAULT '0.00',
  `avg_assignment_submit_rate` decimal(5,2) DEFAULT '0.00',
  `avg_quiz_score` decimal(5,2) DEFAULT '0.00',
  `avg_project_grade` decimal(5,2) DEFAULT '0.00',
  `avg_discussion_participation` decimal(10,2) DEFAULT '0.00',
  `avg_peer_interaction_score` decimal(5,2) DEFAULT '0.00',
  `avg_app_usage_percentage` decimal(5,2) DEFAULT '0.00',
  `avg_satisfaction_rating` decimal(4,2) DEFAULT '0.00',
  `avg_days_since_last_login` decimal(10,2) DEFAULT '0.00',
  `total_assignments_missed` bigint DEFAULT '0',
  `update_date` date DEFAULT NULL,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生画像聚类特征表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `student_info`
--

DROP TABLE IF EXISTS `student_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_info` (
  `student_id` varchar(50) NOT NULL,
  `student_name` varchar(100) DEFAULT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `education_level` varchar(50) DEFAULT NULL,
  `employment_status` varchar(50) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `device_type` varchar(30) DEFAULT NULL,
  `internet_connection_quality` varchar(30) DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生基础信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `student_stat`
--

DROP TABLE IF EXISTS `student_stat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_stat` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `student_id` varchar(50) NOT NULL,
  `course_id` varchar(50) NOT NULL,
  `total_study_time_hours` decimal(12,2) DEFAULT '0.00',
  `avg_session_duration_min` decimal(10,2) DEFAULT '0.00',
  `course_progress_rate` decimal(5,2) DEFAULT '0.00',
  `course_completed` tinyint DEFAULT '0',
  `assignment_submit_rate` decimal(5,2) DEFAULT '0.00',
  `quiz_score_avg` decimal(5,2) DEFAULT '0.00',
  `project_grade` decimal(5,2) DEFAULT '0.00',
  `login_frequency` int DEFAULT '0',
  `video_completion_rate` decimal(5,2) DEFAULT '0.00',
  `discussion_participation` int DEFAULT '0',
  `peer_interaction_score` decimal(5,2) DEFAULT '0.00',
  `days_since_last_login` int DEFAULT '0',
  `app_usage_percentage` decimal(5,2) DEFAULT '0.00',
  `satisfaction_rating` decimal(4,2) DEFAULT '0.00',
  `update_date` date DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_student_course` (`student_id`,`course_id`),
  KEY `idx_student_id` (`student_id`),
  KEY `idx_course_id` (`course_id`)
) ENGINE=InnoDB AUTO_INCREMENT=100001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生课程学情指标表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'online_learning_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-10 17:18:31
