-- DECEPTR v1 — Schéma MySQL 8
-- Tables : Alerts, Attackers, IoCs, Campaigns, Users, Rapports_DGSSI

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','soc_analyst','threat_hunter','auditeur') NOT NULL DEFAULT 'soc_analyst',
    active        TINYINT(1)   NOT NULL DEFAULT 1,
    last_login    DATETIME     NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Compte admin par défaut : admin / deceptr2025
-- Hash bcrypt généré pour "deceptr2025"
INSERT INTO users (username, password_hash, role)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKBYRZSCXLBkfJC', 'admin')
ON DUPLICATE KEY UPDATE username=username;


CREATE TABLE IF NOT EXISTS iocs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ip_address    VARCHAR(45)  NOT NULL UNIQUE,
    country_iso   VARCHAR(5),
    country_name  VARCHAR(100),
    city          VARCHAR(100),
    latitude      DECIMAL(10,6) DEFAULT 0,
    longitude     DECIMAL(10,6) DEFAULT 0,
    asn           VARCHAR(20),
    org           VARCHAR(255),
    abuse_score   INT DEFAULT 0,
    vt_malicious  INT DEFAULT 0,
    known_c2      TINYINT(1) DEFAULT 0,
    mitre_technique VARCHAR(20),
    mitre_tactic    VARCHAR(50),
    mitre_tech_name VARCHAR(150),
    max_severity    ENUM('LOW','MEDIUM','HIGH','CRITICAL') DEFAULT 'LOW',
    max_risk_score  INT DEFAULT 0,
    hit_count       INT DEFAULT 1,
    first_seen      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_abuse (abuse_score),
    INDEX idx_severity (max_severity),
    INDEX idx_country (country_iso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS attackers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ip_address    VARCHAR(45) NOT NULL UNIQUE,
    usernames_tried TEXT,
    passwords_tried TEXT,
    login_success_count INT DEFAULT 0,
    login_attempt_count INT DEFAULT 0,
    first_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ip_address) REFERENCES iocs(ip_address) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS alerts (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_id        VARCHAR(36) NOT NULL,
    src_ip          VARCHAR(45) NOT NULL,
    rule_name       VARCHAR(50) NOT NULL,
    title           VARCHAR(255),
    detail          TEXT,
    severity        ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'LOW',
    event_type      VARCHAR(50),
    mitre_technique VARCHAR(20),
    mitre_tactic    VARCHAR(50),
    mitre_tech_name VARCHAR(150),
    risk_score      INT DEFAULT 0,
    country_iso     VARCHAR(5),
    country_name    VARCHAR(100),
    abuse_score     INT DEFAULT 0,
    vt_malicious    INT DEFAULT 0,
    known_c2        TINYINT(1) DEFAULT 0,
    acknowledged    TINYINT(1) DEFAULT 0,
    acknowledged_by VARCHAR(50),
    acknowledged_at DATETIME,
    notes           TEXT,
    timestamp       DATETIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_severity (severity),
    INDEX idx_src_ip (src_ip),
    INDEX idx_created (created_at),
    INDEX idx_mitre (mitre_technique)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS campaigns (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    src_ip          VARCHAR(45) NOT NULL,
    techniques      TEXT,
    event_count     INT DEFAULT 1,
    max_severity    ENUM('LOW','MEDIUM','HIGH','CRITICAL') DEFAULT 'LOW',
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_campaign_ip (src_ip),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS rapports_dgssi (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    reference       VARCHAR(50) UNIQUE,
    periode_debut   DATETIME,
    periode_fin     DATETIME,
    total_incidents INT DEFAULT 0,
    nb_critique     INT DEFAULT 0,
    nb_eleve        INT DEFAULT 0,
    nb_moyen        INT DEFAULT 0,
    nb_faible       INT DEFAULT 0,
    ips_uniques     INT DEFAULT 0,
    contenu_json    JSON,
    genere_par      VARCHAR(50),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS honeytokens (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    token_id      VARCHAR(100) NOT NULL UNIQUE,
    token_type    VARCHAR(50) NOT NULL,
    filepath      VARCHAR(255) NOT NULL,
    description   TEXT,
    triggered     TINYINT(1) DEFAULT 0,
    last_trigger_ip VARCHAR(45),
    last_trigger_date DATETIME,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
