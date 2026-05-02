use crate::events::AppEvent;
use crate::telemetry::TelemetryData;
use crate::engine::{Alert, ThreatEngine};
use crate::db::Database;
use std::time::Instant;
use std::collections::VecDeque;

#[derive(Debug, PartialEq, Eq, Clone)]
pub enum AppMode {
    Dashboard,
    Monitor,
    ProcessManager,
    NetworkInsight,
    AlertLogs,
    Investigation,
}

pub struct App {
    pub mode: AppMode,
    pub running: bool,
    pub start_time: Instant,
    pub last_tick: Instant,
    pub telemetry: TelemetryData,
    pub alerts: Vec<Alert>,
    pub threat_engine: ThreatEngine,
    pub db: Database,
    
    // History for visualizations
    pub cpu_history: VecDeque<f64>,
    pub mem_history: VecDeque<f64>,
    pub net_rx_history: VecDeque<f64>,
    pub net_tx_history: VecDeque<f64>,
    
    // UI State
    pub process_table_state: usize, // Selected index
    pub sidebar_index: usize,
}

impl App {
    pub fn new(db: Database) -> Self {
        let alerts = db.get_recent_alerts(200).unwrap_or_default();
        
        Self {
            mode: AppMode::Dashboard,
            running: true,
            start_time: Instant::now(),
            last_tick: Instant::now(),
            telemetry: TelemetryData::default(),
            alerts,
            threat_engine: ThreatEngine::new(),
            db,
            cpu_history: VecDeque::from(vec![0.0; 60]),
            mem_history: VecDeque::from(vec![0.0; 60]),
            net_rx_history: VecDeque::from(vec![0.0; 60]),
            net_tx_history: VecDeque::from(vec![0.0; 60]),
            process_table_state: 0,
            sidebar_index: 0,
        }
    }

    pub fn handle_event(&mut self, event: AppEvent) {
        match event {
            AppEvent::Input(key) => {
                use crossterm::event::{KeyCode, KeyModifiers};
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => self.running = false,
                    KeyCode::F(1) => { self.mode = AppMode::Dashboard; self.sidebar_index = 0; }
                    KeyCode::F(2) => { self.mode = AppMode::Monitor; self.sidebar_index = 1; }
                    KeyCode::F(3) => { self.mode = AppMode::ProcessManager; self.sidebar_index = 2; }
                    KeyCode::F(4) => { self.mode = AppMode::NetworkInsight; self.sidebar_index = 3; }
                    KeyCode::F(5) => { self.mode = AppMode::AlertLogs; self.sidebar_index = 4; }
                    
                    // Navigation
                    KeyCode::Down | KeyCode::Char('j') => {
                        if self.mode == AppMode::ProcessManager {
                            self.process_table_state = (self.process_table_state + 1).min(self.telemetry.processes.len().saturating_sub(1));
                        }
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        if self.mode == AppMode::ProcessManager {
                            self.process_table_state = self.process_table_state.saturating_sub(1);
                        }
                    }
                    _ => {}
                }
            }
            AppEvent::Tick => {
                self.last_tick = Instant::now();
            }
            AppEvent::TelemetryUpdate(data) => {
                self.update_history(&data);
                
                let new_alerts = self.threat_engine.analyze(&data);
                for alert in new_alerts {
                    let _ = self.db.log_alert(&alert);
                    self.alerts.push(alert);
                }
                self.telemetry = data;
                
                // Keep alert list manageable for UI performance
                if self.alerts.len() > 1000 {
                    self.alerts.drain(0..100);
                }
            }
        }
    }

    fn update_history(&mut self, data: &TelemetryData) {
        let cpu_avg = if data.cpu_load.is_empty() { 0.0 } else { (data.cpu_load.iter().sum::<f32>() / data.cpu_load.len() as f32) as f64 };
        let mem_pct = (data.used_memory as f64 / data.total_memory as f64) * 100.0;
        
        let mut total_rx = 0.0;
        let mut total_tx = 0.0;
        for net in data.network_interfaces.values() {
            total_rx += net.rx_bytes as f64;
            total_tx += net.tx_bytes as f64;
        }

        self.cpu_history.push_back(cpu_avg);
        self.cpu_history.pop_front();
        self.mem_history.push_back(mem_pct);
        self.mem_history.pop_front();
        
        // We calculate delta for rate later, for now just store raw to visualize changes
        self.net_rx_history.push_back(total_rx);
        self.net_rx_history.pop_front();
        self.net_tx_history.push_back(total_tx);
        self.net_tx_history.pop_front();
    }
}
