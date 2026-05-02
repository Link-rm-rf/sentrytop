use sysinfo::System;
use sysinfo::Networks;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub cpu_usage: f32,
    pub memory_usage: u64,
    pub user: String,
    pub exe_path: String,
    pub command: String,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInfo {
    pub interface: String,
    pub rx_bytes: u64,
    pub tx_bytes: u64,
}

#[derive(Debug, Clone, Default)]
pub struct TelemetryData {
    pub cpu_load: Vec<f32>,
    pub total_memory: u64,
    pub used_memory: u64,
    pub processes: Vec<ProcessInfo>,
    pub network_interfaces: HashMap<String, NetworkInfo>,
    pub uptime: u64,
}

pub struct TelemetryCollector {
    sys: System,
    networks: Networks,
}

impl TelemetryCollector {
    pub fn new() -> Self {
        let mut sys = System::new_all();
        let networks = Networks::new_with_refreshed_list();
        sys.refresh_all();
        Self { sys, networks }
    }

    pub fn collect(&mut self) -> TelemetryData {
        self.sys.refresh_all();
        self.networks.refresh();
        
        let cpu_load = self.sys.cpus().iter().map(|cpu| cpu.cpu_usage()).collect();
        let total_memory = self.sys.total_memory();
        let used_memory = self.sys.used_memory();
        let uptime = System::uptime();

        let mut processes = Vec::new();
        for (pid, process) in self.sys.processes() {
            processes.push(ProcessInfo {
                pid: pid.as_u32(),
                name: process.name().to_string(),
                cpu_usage: process.cpu_usage(),
                memory_usage: process.memory(),
                user: process.user_id().map(|u| u.to_string()).unwrap_or_else(|| "N/A".to_string()),
                exe_path: process.exe().map(|p| p.to_string_lossy().to_string()).unwrap_or_else(|| "N/A".to_string()),
                command: process.cmd().join(" "),
                status: format!("{:?}", process.status()),
            });
        }

        processes.sort_by(|a, b| b.cpu_usage.partial_cmp(&a.cpu_usage).unwrap());

        let mut network_interfaces = HashMap::new();
        for (interface_name, data) in &self.networks {
            network_interfaces.insert(
                interface_name.clone(),
                NetworkInfo {
                    interface: interface_name.clone(),
                    rx_bytes: data.received(),
                    tx_bytes: data.transmitted(),
                },
            );
        }

        TelemetryData {
            cpu_load,
            total_memory,
            used_memory,
            processes,
            network_interfaces,
            uptime,
        }
    }
}
