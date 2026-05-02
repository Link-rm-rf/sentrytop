use crate::engine::{Alert, Severity};
use anyhow::Result;
use rusqlite::{params, Connection};
use std::path::Path;

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        
        // Initialize tables with detection_type
        conn.execute(
            "CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                pid INTEGER,
                confidence REAL NOT NULL,
                detection_type TEXT
            )",
            [],
        )?;

        Ok(Self { conn })
    }

    pub fn log_alert(&self, alert: &Alert) -> Result<()> {
        self.conn.execute(
            "INSERT INTO alerts (timestamp, severity, title, description, pid, confidence, detection_type)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                alert.timestamp.to_rfc3339(),
                format!("{:?}", alert.severity),
                alert.title,
                alert.description,
                alert.pid,
                alert.confidence,
                alert.detection_type,
            ],
        )?;
        Ok(())
    }

    pub fn get_recent_alerts(&self, limit: usize) -> Result<Vec<Alert>> {
        let mut stmt = self.conn.prepare(
            "SELECT timestamp, severity, title, description, pid, confidence, detection_type 
             FROM alerts ORDER BY timestamp DESC LIMIT ?"
        )?;
        
        let alert_iter = stmt.query_map([limit], |row| {
            let timestamp_str: String = row.get(0)?;
            let severity_str: String = row.get(1)?;
            let detection_type: String = row.get(6).unwrap_or_else(|_| "UNKNOWN".to_string());
            
            Ok(Alert {
                timestamp: chrono::DateTime::parse_from_rfc3339(&timestamp_str).unwrap().with_timezone(&chrono::Utc),
                severity: match severity_str.as_str() {
                    "Critical" => Severity::Critical,
                    "High" => Severity::High,
                    "Medium" => Severity::Medium,
                    _ => Severity::Low,
                },
                title: row.get(2)?,
                description: row.get(3)?,
                pid: row.get(4)?,
                confidence: row.get(5)?,
                detection_type,
            })
        })?;

        let mut alerts = Vec::new();
        for alert in alert_iter {
            alerts.push(alert?);
        }
        Ok(alerts)
    }
}
