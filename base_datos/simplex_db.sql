-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: simplex_db
-- ------------------------------------------------------
-- Server version	8.4.7

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `coeficientes_objetivo`
--

DROP TABLE IF EXISTS `coeficientes_objetivo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coeficientes_objetivo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `problema_id` int NOT NULL,
  `variable` char(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coeficiente` decimal(15,6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `problema_id` (`problema_id`,`variable`),
  CONSTRAINT `coeficientes_objetivo_ibfk_1` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coeficientes_objetivo`
--

LOCK TABLES `coeficientes_objetivo` WRITE;
/*!40000 ALTER TABLE `coeficientes_objetivo` DISABLE KEYS */;
INSERT INTO `coeficientes_objetivo` VALUES (1,1,'a',3.000000),(2,1,'b',5.000000);
/*!40000 ALTER TABLE `coeficientes_objetivo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coeficientes_restriccion`
--

DROP TABLE IF EXISTS `coeficientes_restriccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coeficientes_restriccion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `restriccion_id` int NOT NULL,
  `variable` char(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `coeficiente` decimal(15,6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `restriccion_id` (`restriccion_id`,`variable`),
  CONSTRAINT `coeficientes_restriccion_ibfk_1` FOREIGN KEY (`restriccion_id`) REFERENCES `restricciones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coeficientes_restriccion`
--

LOCK TABLES `coeficientes_restriccion` WRITE;
/*!40000 ALTER TABLE `coeficientes_restriccion` DISABLE KEYS */;
INSERT INTO `coeficientes_restriccion` VALUES (1,1,'a',1.000000),(2,1,'b',0.000000),(3,2,'a',0.000000),(4,2,'b',2.000000),(5,3,'a',3.000000),(6,3,'b',2.000000);
/*!40000 ALTER TABLE `coeficientes_restriccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `iteraciones`
--

DROP TABLE IF EXISTS `iteraciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iteraciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `problema_id` int NOT NULL,
  `numero_iteracion` int NOT NULL,
  `fase` tinyint NOT NULL DEFAULT '2',
  `variable_entrante` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `variable_saliente` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fila_pivote` int DEFAULT NULL,
  `columna_pivote` int DEFAULT NULL,
  `elemento_pivote` decimal(15,6) DEFAULT NULL,
  `tabla_json` json NOT NULL,
  `operaciones_json` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `problema_id` (`problema_id`,`fase`,`numero_iteracion`),
  CONSTRAINT `iteraciones_ibfk_1` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `iteraciones`
--

LOCK TABLES `iteraciones` WRITE;
/*!40000 ALTER TABLE `iteraciones` DISABLE KEYS */;
INSERT INTO `iteraciones` VALUES (1,1,0,2,'b','h2',2,2,2.000000,'{\"filas\": [[\"Z\", -3, -5, 0, 0, 0, 0], [\"h1\", 1, 0, 1, 0, 0, 4], [\"h2\", 0, 2, 0, 1, 0, 12], [\"h3\", 3, 2, 0, 0, 1, 18]], \"columnas\": [\"Base\", \"a\", \"b\", \"h1\", \"h2\", \"h3\", \"Solución\"]}','[\"F2 = F2 / 2\", \"F0 = F0 + 5·F2\", \"F3 = F3 - 2·F2\"]'),(2,1,1,2,'a','h3',3,1,3.000000,'{\"filas\": [[\"Z\", -3, 0, 0, 2.5, 0, 30], [\"h1\", 1, 0, 1, 0, 0, 4], [\"b\", 0, 1, 0, 0.5, 0, 6], [\"h3\", 3, 0, 0, -1, 1, 6]], \"columnas\": [\"Base\", \"a\", \"b\", \"h1\", \"h2\", \"h3\", \"Solución\"]}','[\"F3 = F3 / 3\", \"F0 = F0 + 3·F3\", \"F1 = F1 - F3\"]'),(3,1,2,2,NULL,NULL,NULL,NULL,NULL,'{\"filas\": [[\"Z\", 0, 0, 0, 1.5, 1, 36], [\"h1\", 0, 0, 1, 0.3333333333333333, -0.3333333333333333, 2], [\"b\", 0, 1, 0, 0.5, 0, 6], [\"a\", 1, 0, 0, -0.3333333333333333, 0.3333333333333333, 2]], \"columnas\": [\"Base\", \"a\", \"b\", \"h1\", \"h2\", \"h3\", \"Solución\"]}','[]');
/*!40000 ALTER TABLE `iteraciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `problemas`
--

DROP TABLE IF EXISTS `problemas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `problemas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` enum('MAX','MIN') COLLATE utf8mb4_unicode_ci NOT NULL,
  `num_variables` tinyint NOT NULL,
  `num_restricciones` tinyint NOT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT `chk_num_variables` CHECK ((`num_variables` between 2 and 6))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `problemas`
--

LOCK TABLES `problemas` WRITE;
/*!40000 ALTER TABLE `problemas` DISABLE KEYS */;
INSERT INTO `problemas` VALUES (1,'Prueba desde la API','MAX',2,3,'2026-10-21 03:56:15');
/*!40000 ALTER TABLE `problemas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `restricciones`
--

DROP TABLE IF EXISTS `restricciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `restricciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `problema_id` int NOT NULL,
  `numero` tinyint NOT NULL,
  `signo` enum('<=','>=','=') COLLATE utf8mb4_unicode_ci NOT NULL,
  `termino_independiente` decimal(15,6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `problema_id` (`problema_id`,`numero`),
  CONSTRAINT `restricciones_ibfk_1` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `restricciones`
--

LOCK TABLES `restricciones` WRITE;
/*!40000 ALTER TABLE `restricciones` DISABLE KEYS */;
INSERT INTO `restricciones` VALUES (1,1,1,'<=',4.000000),(2,1,2,'<=',12.000000),(3,1,3,'<=',18.000000);
/*!40000 ALTER TABLE `restricciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resultados`
--

DROP TABLE IF EXISTS `resultados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resultados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `problema_id` int NOT NULL,
  `estado` enum('OPTIMO','INFACTIBLE','NO_ACOTADO') COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor_z` decimal(20,6) DEFAULT NULL,
  `solucion_json` json DEFAULT NULL,
  `total_iteraciones` int DEFAULT NULL,
  `calculado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `problema_id` (`problema_id`),
  CONSTRAINT `resultados_ibfk_1` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resultados`
--

LOCK TABLES `resultados` WRITE;
/*!40000 ALTER TABLE `resultados` DISABLE KEYS */;
INSERT INTO `resultados` VALUES (1,1,'OPTIMO',36.000000,'{\"a\": 2, \"b\": 6}',3,'2026-10-21 05:40:58');
/*!40000 ALTER TABLE `resultados` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-23 19:42:02
