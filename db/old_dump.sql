/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.4.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: maxmontaj67_db
-- ------------------------------------------------------
-- Server version	11.4.3-MariaDB-1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `password_hash` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES
(1,'Customer_1','customer_user@example.com','+71234567890','Киселевка','2024-11-15 10:47:11',NULL),
(2,'customer_5','customer_user_5@example.com',NULL,NULL,'2024-11-22 07:20:34','$2b$12$a9K673t5niGFWFO3EJTSpOxuB1qF7/9pxEftpS1eeTOdJoBEwk6Dm');
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_id` int(11) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `status` enum('Ожидает','Выполняется','Завершён') NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `assigned_at` timestamp NULL DEFAULT NULL,
  `installer_id` int(11) DEFAULT NULL,
  `deadline_at` date DEFAULT NULL,
  `montage_date` date DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_orders_customer` (`customer_id`),
  KEY `fk_orders_installer` (`installer_id`),
  CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
  CONSTRAINT `fk_orders_installer` FOREIGN KEY (`installer_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES
(20,1,'Монтаж кондиционера в квартире','Выполняется','2024-11-20 10:21:07','2025-01-09 11:19:07','2025-01-09 11:19:07',3,'2025-01-17','2025-01-10',NULL),
(21,1,'Установка отопительной системы','Ожидает','2024-11-20 10:21:07','2024-12-03 16:39:37',NULL,NULL,NULL,NULL,NULL),
(22,1,'Ремонт системы вентиляции','Ожидает','2024-11-20 10:21:07','2024-12-03 16:39:37',NULL,NULL,NULL,NULL,NULL),
(23,1,'Монтаж кондиционера в офисе','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(24,1,'Установка отопительной системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(25,1,'Ремонт системы вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:58',NULL,NULL,NULL,NULL,NULL),
(26,1,'Чистка кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(27,1,'Установка системы охлаждения','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(28,1,'Настройка системы вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(29,1,'Ремонт отопительной системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(30,1,'Установка кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:03',NULL,NULL,NULL,NULL,NULL),
(31,1,'Обслуживание вентиляционной системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(32,1,'Установка климат-контроля','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:07',NULL,NULL,NULL,NULL,NULL),
(33,1,'Ремонт системы охлаждения','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(34,1,'Монтаж воздушного фильтра','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(35,1,'Замена кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(36,1,'Обслуживание климат-контроля','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(37,1,'Диагностика системы вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(38,1,'Ремонт компрессора','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(39,1,'Установка приточной вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:11',NULL,NULL,NULL,NULL,NULL),
(40,1,'Очистка фильтров кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(41,1,'Установка теплового насоса','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(42,1,'Диагностика охлаждающей системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(43,1,'Ремонт системы обогрева','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:15',NULL,NULL,NULL,NULL,NULL),
(44,1,'Настройка автоматизации системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(45,1,'Замена фильтров вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(46,1,'Установка наружного блока кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(47,1,'Очистка вентиляционной шахты','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:19',NULL,NULL,NULL,NULL,NULL),
(48,1,'Ремонт системы охлаждения','Ожидает','2024-12-03 17:15:27','2024-12-03 17:16:49',NULL,NULL,NULL,NULL,NULL),
(49,1,'Установка центрального кондиционера','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(50,1,'Монтаж воздуховода','Ожидает','2024-12-03 17:15:27','2024-12-03 17:15:27',NULL,NULL,NULL,NULL,NULL),
(51,1,'Настройка климатической системы','Ожидает','2024-12-03 17:15:27','2024-12-03 17:17:24',NULL,NULL,NULL,NULL,NULL),
(52,1,'Проверка системы вентиляции','Ожидает','2024-12-03 17:15:27','2024-12-04 08:37:26',NULL,NULL,NULL,NULL,'2024-12-04 08:37:04');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES
(1,'admin'),
(6,'blocked'),
(5,'customer'),
(2,'dispatcher'),
(4,'executor'),
(3,'specialist');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `role` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `phone` varchar(20) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `passport_series` varchar(4) DEFAULT NULL,
  `passport_number` varchar(6) DEFAULT NULL,
  `passport_issued_by` text DEFAULT NULL,
  `passport_issue_date` varchar(10) DEFAULT NULL,
  `photo_path` text DEFAULT 'images/foto_placeholder.png',
  `rating` float DEFAULT 5,
  `is_profile_complete` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `role` (`role`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role`) REFERENCES `roles` (`id`),
  CONSTRAINT `chk_passport_number` CHECK (`passport_number` regexp '^[0-9]{6}$'),
  CONSTRAINT `chk_passport_series` CHECK (`passport_series` regexp '^[0-9]{4}$')
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES
(1,'Бандура Юрий Васильевич','bandurayv@yandex.ru','$2b$12$5yoQzTLonhHL3C2wDZ26mOvMcSM43y8fCtgbjRhzrYCUvjQNCqJc2',1,'2024-11-24 17:09:40','+79107127340','Смоленск 55','1234','123456','МУР67','10.10.2008','images/user_1.jpg',5,1),
(2,'Dispatcher_1','dispatcher_user@example.com','$2b$12$6J5tq0BICVmgr2YHXZ8vM./NZ4kO/06bfvGSEDC8CiW6QZunjAxo.',1,'2024-11-24 17:09:40','None','Смоленск',NULL,NULL,NULL,NULL,'images/user_2.jpg',5,1),
(3,'Specialist_1','specialist_user@example.com','$2b$12$3OvuOZZtuRSj.ArPYXPtt.lPzEscxbGLwTJ8F6N6qPwtAsyif80.C',3,'2024-11-24 17:09:40','+79109101010','Смоленск','1234','123456','МУР67','01.01.2000','images/user_3.jpg',5,1),
(4,'Executor_1','executor_user@example.com','$2b$12$FMWRDnQpWv90mZ7hCNbtVOzIvWg9NZ1AcdNSCFSHIzWsZNyyRFMD2',4,'2024-11-24 17:09:40','/79008007060','Смоленск',NULL,NULL,NULL,NULL,'images/foto_placeholder.png',5,0),
(11,'Спец_9','Spets9@Spets9.ru','$2b$12$ww8v7JPvYlgJ4IfqTFYYvOcagOjKIHEypsWUdCD8PF1XGX4sQcVay',3,'2024-11-27 19:14:49',NULL,NULL,NULL,NULL,NULL,NULL,'images/foto_placeholder.png',5,0),
(12,'Спец_8','Spets8@Spets8.ru','$2b$12$IEUGUjxQMPrDl4LpPNAGZeyfl/paOG9mj81w2l8QIjt5rfk8.aTuO',6,'2024-11-27 19:46:12',NULL,NULL,NULL,NULL,NULL,NULL,'images/foto_placeholder.png',5,0);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-01-10  3:13:05
