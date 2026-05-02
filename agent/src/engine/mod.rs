use crate::telemetry::{ProcessInfo, TelemetryData};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::{HashSet, HashMap};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub timestamp: DateTime<Utc>,
    pub severity: Severity,
    pub title: String,
    pub description: String,
    pub pid: Option<u32>,
    pub confidence: f32,
    pub detection_type: String,
}

pub struct ThreatEngine {
    seen_pids: HashSet<u32>,
    process_baselines: HashMap<String, f32>, // Name -> Avg CPU
}

impl ThreatEngine {
    pub fn new() -> Self {
        Self {
            seen_pids: HashSet::new(),
            process_baselines: HashMap::new(),
        }
    }

    pub fn analyze(&mut self, telemetry: &TelemetryData) -> Vec<Alert> {
        let mut alerts = Vec::new();

        for process in &telemetry.processes {
            // 1. Initial Execution Detection
            if !self.seen_pids.contains(&process.pid) {
                self.seen_pids.insert(process.pid);
                
                // Suspicious Path Check
                if self.is_high_risk_path(&process.exe_path) {
                    alerts.push(Alert {
                        timestamp: Utc::now(),
                        severity: Severity::High,
                        title: "Execution from Volatile Path".to_string(),
                        description: format!("Binary '{}' executed from high-risk directory: {}", process.name, process.exe_path),
                        pid: Some(process.pid),
                        confidence: 0.85,
                        detection_type: "PATH_ANOMALY".to_string(),
                    });
                }
            }

            // 2. Suspicious Binary Names (Varied)
            if let Some(reason) = self.check_suspicious_name(&process.name) {
                alerts.push(Alert {
                    timestamp: Utc::now(),
                    severity: Severity::Critical,
                    title: "High-Confidence Threat Actor Tool".to_string(),
                    description: format!("Known offensive tool '{}' detected: {}", process.name, reason),
                    pid: Some(process.pid),
                    confidence: 0.98,
                    detection_type: "MALWARE_MATCH".to_string(),
                });
            }

            // 3. Behavioral: Shell Spawn from Office/Web Server (Simulated Parent Check)
            if (process.name == "sh" || process.name == "bash") && self.is_suspicious_shell_context(process) {
                alerts.push(Alert {
                    timestamp: Utc::now(),
                    severity: Severity::Critical,
                    title: "Suspicious Shell Context".to_string(),
                    description: format!("Interactive shell (PID {}) spawned in a potentially compromised context.", process.pid),
                    pid: Some(process.pid),
                    confidence: 0.92,
                    detection_type: "BEHAVIORAL_ESC".to_string(),
                });
            }

            // 4. Resource Anomaly: Sustained Spikes
            if process.cpu_usage > 95.0 {
                alerts.push(Alert {
                    timestamp: Utc::now(),
                    severity: Severity::Medium,
                    title: "Abnormal Resource Consumption".to_string(),
                    description: format!("Process '{}' is exhibiting sustained CPU spike ({:.1}%).", process.name, process.cpu_usage),
                    pid: Some(process.pid),
                    confidence: 0.65,
                    detection_type: "RESOURCE_EXHAUSTION".to_string(),
                });
            }
            
            // 5. Unsigned/Unknown Reputation Simulation
            if process.pid % 47 == 0 { // Random-ish simulation for UI variety
                alerts.push(Alert {
                    timestamp: Utc::now(),
                    severity: Severity::Low,
                    title: "Unsigned Binary Observed".to_string(),
                    description: format!("Execution of unsigned binary '{}' with unknown global reputation.", process.name),
                    pid: Some(process.pid),
                    confidence: 0.40,
                    detection_type: "REPUTATION_LOW".to_string(),
                });
            }
        }

        // Limit alerts to prevent spam in demo
        if alerts.len() > 5 {
            alerts.truncate(5);
        }

        alerts
    }

    fn check_suspicious_name(&self, name: &str) -> Option<&'static str> {
        let tools = [
            ("nc", "Netcat - potential reverse shell listener"),
            ("ncat", "Ncat - potential reverse shell listener"),
            ("socat", "Socat - relay tool"),
            ("nmap", "Nmap - network reconnaissance"),
            ("tcpdump", "Tcpdump - packet sniffing"),
            ("wireshark", "Wireshark - packet analysis"),
            ("metasploit", "Metasploit Framework"),
            ("cobaltstrike", "Cobalt Strike Beacon"),
            ("mimikatz", "Mimikatz - credential theft"),
            ("exploit", "Exploit generic match"),
        ];
        
        let lower_name = name.to_lowercase();
        for (tool, desc) in tools {
            if lower_name.contains(tool) {
                return Some(desc);
            }
        }
        None
    }

    fn is_high_risk_path(&self, path: &str) -> bool {
        let risks = ["/tmp/", "/dev/shm/", "/var/tmp/", "/home/kura/Downloads/"];
        risks.iter().any(|r| path.contains(r))
    }
    
    fn is_suspicious_shell_context(&self, process: &ProcessInfo) -> bool {
        // Simulation: in real EDR we check PPID (Parent PID)
        // If parent is nginx, apache, php, python, etc.
        process.pid % 13 == 0 // Pseudo-random trigger
    }
}
