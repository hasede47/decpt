-- DECEPTR v1 — Procédures stockées
-- upsert_ioc()       : insère/met à jour un IoC (IP)
-- upsert_attacker()  : insère/met à jour le profil attaquant
-- update_campaign()  : regroupe les événements par IP en campagnes
-- get_dashboard_stats(): KPIs pour le dashboard

DELIMITER //

DROP PROCEDURE IF EXISTS upsert_ioc //
DROP PROCEDURE IF EXISTS upsert_attacker //
DROP PROCEDURE IF EXISTS update_campaign //
DROP PROCEDURE IF EXISTS get_dashboard_stats //

-- ── upsert_ioc ──────────────────────────────────────────────────────────────
CREATE PROCEDURE upsert_ioc(
    IN p_ip            VARCHAR(45),
    IN p_country_iso   VARCHAR(5),
    IN p_country_name  VARCHAR(100),
    IN p_city          VARCHAR(100),
    IN p_lat           DECIMAL(10,6),
    IN p_lon           DECIMAL(10,6),
    IN p_asn           VARCHAR(20),
    IN p_org           VARCHAR(255),
    IN p_abuse_score   INT,
    IN p_vt_malicious  INT,
    IN p_known_c2      TINYINT(1),
    IN p_mitre_tech    VARCHAR(20),
    IN p_mitre_tactic  VARCHAR(50),
    IN p_mitre_name    VARCHAR(150),
    IN p_severity      VARCHAR(10),
    IN p_risk_score    INT
)
BEGIN
    INSERT INTO iocs (
        ip_address, country_iso, country_name, city, latitude, longitude,
        asn, org, abuse_score, vt_malicious, known_c2,
        mitre_technique, mitre_tactic, mitre_tech_name,
        max_severity, max_risk_score, hit_count, first_seen, last_seen
    ) VALUES (
        p_ip, p_country_iso, p_country_name, p_city, p_lat, p_lon,
        p_asn, p_org, p_abuse_score, p_vt_malicious, p_known_c2,
        p_mitre_tech, p_mitre_tactic, p_mitre_name,
        p_severity, p_risk_score, 1, NOW(), NOW()
    )
    ON DUPLICATE KEY UPDATE
        abuse_score    = GREATEST(abuse_score, p_abuse_score),
        vt_malicious   = GREATEST(vt_malicious, p_vt_malicious),
        known_c2       = known_c2 OR p_known_c2,
        max_severity   = CASE
            WHEN FIELD(p_severity, max_severity, 'LOW','MEDIUM','HIGH','CRITICAL') >
                 FIELD(max_severity, 'LOW','MEDIUM','HIGH','CRITICAL')
            THEN p_severity ELSE max_severity END,
        max_risk_score = GREATEST(max_risk_score, p_risk_score),
        mitre_technique = IF(p_mitre_tech != '', p_mitre_tech, mitre_technique),
        mitre_tactic     = IF(p_mitre_tactic != '', p_mitre_tactic, mitre_tactic),
        mitre_tech_name  = IF(p_mitre_name != '', p_mitre_name, mitre_tech_name),
        hit_count      = hit_count + 1,
        last_seen      = NOW();
END //


-- ── upsert_attacker ─────────────────────────────────────────────────────────
CREATE PROCEDURE upsert_attacker(
    IN p_ip             VARCHAR(45),
    IN p_username       VARCHAR(100),
    IN p_password       VARCHAR(100),
    IN p_login_success  TINYINT(1)
)
BEGIN
    -- S'assurer que l'IoC existe (FK)
    INSERT IGNORE INTO iocs (ip_address) VALUES (p_ip);

    INSERT INTO attackers (
        ip_address, usernames_tried, passwords_tried,
        login_success_count, login_attempt_count, first_seen, last_seen
    ) VALUES (
        p_ip,
        IF(p_username != '', p_username, NULL),
        IF(p_password != '', p_password, NULL),
        IF(p_login_success = 1, 1, 0),
        IF(p_username != '' OR p_password != '', 1, 0),
        NOW(), NOW()
    )
    ON DUPLICATE KEY UPDATE
        usernames_tried = CASE
            WHEN p_username = '' THEN usernames_tried
            WHEN usernames_tried IS NULL THEN p_username
            WHEN usernames_tried NOT LIKE CONCAT('%', p_username, '%')
                THEN CONCAT(usernames_tried, ',', p_username)
            ELSE usernames_tried END,
        passwords_tried = CASE
            WHEN p_password = '' THEN passwords_tried
            WHEN passwords_tried IS NULL THEN p_password
            WHEN passwords_tried NOT LIKE CONCAT('%', p_password, '%')
                THEN CONCAT(passwords_tried, ',', p_password)
            ELSE passwords_tried END,
        login_success_count = login_success_count + IF(p_login_success = 1, 1, 0),
        login_attempt_count = login_attempt_count + IF(p_username != '' OR p_password != '', 1, 0),
        last_seen = NOW();
END //


-- ── update_campaign ─────────────────────────────────────────────────────────
-- Regroupe les événements par IP. Si la dernière activité de cette IP
-- date de moins de 30 minutes, met à jour la campagne existante.
-- Sinon, crée une nouvelle campagne (ou réinitialise si trop ancienne).
CREATE PROCEDURE update_campaign(
    IN p_ip          VARCHAR(45),
    IN p_technique   VARCHAR(20),
    IN p_severity    VARCHAR(10)
)
BEGIN
    DECLARE v_last_update DATETIME;
    DECLARE v_techniques  TEXT;

    SELECT updated_at, techniques INTO v_last_update, v_techniques
    FROM campaigns WHERE src_ip = p_ip LIMIT 1;

    IF v_last_update IS NULL THEN
        -- Nouvelle campagne
        INSERT INTO campaigns (src_ip, techniques, event_count, max_severity, started_at, updated_at)
        VALUES (p_ip, p_technique, 1, p_severity, NOW(), NOW());

    ELSEIF TIMESTAMPDIFF(MINUTE, v_last_update, NOW()) > 30 THEN
        -- Trop ancienne → réinitialiser la campagne
        UPDATE campaigns SET
            techniques   = p_technique,
            event_count  = 1,
            max_severity = p_severity,
            started_at   = NOW(),
            updated_at   = NOW()
        WHERE src_ip = p_ip;

    ELSE
        -- Mise à jour de la campagne active
        UPDATE campaigns SET
            techniques = IF(v_techniques NOT LIKE CONCAT('%', p_technique, '%'),
                            CONCAT(v_techniques, ',', p_technique), v_techniques),
            event_count  = event_count + 1,
            max_severity = CASE
                WHEN FIELD(p_severity, max_severity, 'LOW','MEDIUM','HIGH','CRITICAL') >
                     FIELD(max_severity, 'LOW','MEDIUM','HIGH','CRITICAL')
                THEN p_severity ELSE max_severity END,
            updated_at = NOW()
        WHERE src_ip = p_ip;
    END IF;
END //


-- ── get_dashboard_stats ─────────────────────────────────────────────────────
CREATE PROCEDURE get_dashboard_stats()
BEGIN
    SELECT
        (SELECT COUNT(*) FROM alerts) AS total_alerts,
        (SELECT COUNT(*) FROM alerts WHERE created_at >= NOW() - INTERVAL 24 HOUR) AS alerts_24h,
        (SELECT COUNT(*) FROM alerts WHERE severity = 'CRITICAL') AS total_critical,
        (SELECT COUNT(*) FROM alerts WHERE severity = 'HIGH') AS total_high,
        (SELECT COUNT(*) FROM iocs) AS total_iocs,
        (SELECT COUNT(*) FROM iocs WHERE known_c2 = 1) AS total_c2,
        (SELECT COUNT(*) FROM attackers) AS total_attackers,
        (SELECT COUNT(*) FROM campaigns WHERE updated_at >= NOW() - INTERVAL 1 HOUR) AS active_campaigns;
END //

DELIMITER ;
