import random
import hashlib
import os

names = ["Mohammed Alaoui", "Amina Benali", "Said Chraibi", "Youssef El Fassi", "Fatima Zahra", "Khalid Idrissi"]
departments = ["IT", "HR", "Finance", "Direction", "Logistique"]

output_file = "backup_rh_2025.sql"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("-- MySQL dump 10.13  Distrib 8.0.35, for Linux (x86_64)\n")
    f.write("-- Host: localhost    Database: rh_parlement\n")
    f.write("-- ------------------------------------------------------\n\n")
    
    f.write("DROP TABLE IF EXISTS `employes`;\n")
    f.write("CREATE TABLE `employes` (\n")
    f.write("  `id` int NOT NULL AUTO_INCREMENT,\n")
    f.write("  `nom_complet` varchar(255) NOT NULL,\n")
    f.write("  `email` varchar(255) NOT NULL,\n")
    f.write("  `departement` varchar(100) DEFAULT NULL,\n")
    f.write("  `password_hash` varchar(255) NOT NULL,\n")
    f.write("  `avatar_url` varchar(500) DEFAULT NULL,\n")
    f.write("  PRIMARY KEY (`id`)\n")
    f.write(") ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;\n\n")
    
    f.write("LOCK TABLES `employes` WRITE;\n")
    f.write("INSERT INTO `employes` VALUES \n")
    
    rows = []
    for i in range(1, 101):
        name = random.choice(names) + f" {i}"
        email = f"{name.split(' ')[0].lower()}.{name.split(' ')[1].lower()}@parlement.ma"
        dept = random.choice(departments)
        
        # Leurre: On cache un tracker dans l'avatar d'un administrateur (IT)
        if i == 42 and dept == "IT":
            avatar = "http://localhost:8000/api/assets/logo.png"
        else:
            avatar = f"https://intranet.parlement.ma/avatars/{i}.jpg"
            
        password = hashlib.sha256(f"Secret2025_{i}".encode()).hexdigest()
        
        row = f"({i},'{name}','{email}','{dept}','{password}','{avatar}')"
        rows.append(row)
        
    f.write(",\n".join(rows) + ";\n")
    f.write("UNLOCK TABLES;\n")

print(f"Generated {output_file}")
