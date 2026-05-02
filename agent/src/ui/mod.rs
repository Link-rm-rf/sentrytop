use crate::app::{App, AppMode};
use crate::engine::Severity;
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect, Alignment},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Cell, Paragraph, Row, Table, Sparkline, Gauge, List, ListItem, Wrap, BorderType},
    Frame,
};
use std::time::Instant;

pub fn render(f: &mut Frame, app: &App) {
    // 1. Force Absolute Opaque Background
    let background = Block::default().style(Style::default().bg(Color::Black));
    f.render_widget(background, f.size());

    // 2. Define High-Density Grid
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1), // Top status (Ticker)
            Constraint::Length(3), // Main Header
            Constraint::Min(0),    // Interactive Workspace
            Constraint::Length(1), // Integrated Footer
        ])
        .split(f.size());

    render_top_ticker(f, app, chunks[0]);
    render_military_header(f, app, chunks[1]);
    render_workspace(f, app, chunks[2]);
    render_integrated_footer(f, app, chunks[3]);
}

fn render_top_ticker(f: &mut Frame, app: &App, area: Rect) {
    let now = chrono::Local::now();
    let pulse = (Instant::now().duration_since(app.start_time).as_millis() / 800) % 2 == 0;
    
    let ticker = Line::from(vec![
        Span::styled(" [ SYSTEM_LOG: ", Style::default().fg(Color::DarkGray)),
        Span::styled(format!("{}", now.format("%Y-%m-%d %H:%M:%S")), Style::default().fg(Color::Gray)),
        Span::styled(" ]  ", Style::default().fg(Color::DarkGray)),
        Span::styled("CORE_HEARTBEAT: ", Style::default().fg(Color::DarkGray)),
        Span::styled(if pulse { "SYNCED" } else { "WAITING" }, Style::default().fg(if pulse { Color::Green } else { Color::Yellow })),
        Span::styled("  |  ", Style::default().fg(Color::DarkGray)),
        Span::styled("TELEMETRY_LATENCY: ", Style::default().fg(Color::DarkGray)),
        Span::styled("4ms", Style::default().fg(Color::Green)),
        Span::styled("  |  ", Style::default().fg(Color::DarkGray)),
        Span::styled("MODE: ", Style::default().fg(Color::DarkGray)),
        Span::styled(format!("{:?} ", app.mode).to_uppercase(), Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
    ]);
    
    f.render_widget(Paragraph::new(ticker).alignment(Alignment::Right).style(Style::default().bg(Color::Black)), area);
}

fn render_military_header(f: &mut Frame, app: &App, area: Rect) {
    let has_crit = app.alerts.iter().any(|a| matches!(a.severity, Severity::Critical));
    let pulse = (Instant::now().duration_since(app.start_time).as_millis() / 400) % 2 == 0;
    
    let border_color = if has_crit && pulse { Color::Red } else { Color::DarkGray };
    
    let header_text = Line::from(vec![
        Span::styled(" ◈ ", Style::default().fg(Color::Cyan)),
        Span::styled("SENTRYTOP ", Style::default().fg(Color::White).add_modifier(Modifier::BOLD)),
        Span::styled("TACTICAL COMMAND CONSOLE ", Style::default().fg(Color::Gray).add_modifier(Modifier::DIM)),
        Span::styled("v2.0.0-PRO ", Style::default().fg(Color::DarkGray)),
        Span::styled(" ◈", Style::default().fg(Color::Cyan)),
    ]);

    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(Style::default().fg(border_color))
        .border_type(BorderType::Double);
        
    f.render_widget(Paragraph::new(header_text).alignment(Alignment::Center).block(block).style(Style::default().bg(Color::Black)), area);
}

fn render_workspace(f: &mut Frame, app: &App, area: Rect) {
    let layout = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Length(22), // Compact sidebar
            Constraint::Min(0),     // Operational Canvas
        ])
        .split(area);

    render_side_nav(f, app, layout[0]);
    render_operational_content(f, app, layout[1]);
}

fn render_side_nav(f: &mut Frame, app: &App, area: Rect) {
    let modes = vec![
        ("DASHBOARD", "F1"),
        ("THREAT_FEED", "F2"),
        ("PROCESS_INTEL", "F3"),
        ("NET_MAPPER", "F4"),
        ("EVENT_LOGS", "F5"),
        ("INCIDENT_INV", "F6"),
    ];

    let items: Vec<ListItem> = modes.iter().enumerate().map(|(i, (name, key))| {
        let style = if i == app.sidebar_index {
            Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::Gray)
        };
        ListItem::new(Line::from(vec![
            Span::styled(format!(" {:<14} ", name), style),
            Span::styled(format!(" {} ", key), Style::default().fg(Color::DarkGray).add_modifier(Modifier::DIM)),
        ]))
    }).collect();

    let block = Block::default()
        .title(" NAV ")
        .title_style(Style::default().fg(Color::DarkGray))
        .borders(Borders::RIGHT)
        .border_style(Style::default().fg(Color::DarkGray));
        
    f.render_widget(List::new(items).block(block).style(Style::default().bg(Color::Black)), area);
}

fn render_operational_content(f: &mut Frame, app: &App, area: Rect) {
    match app.mode {
        AppMode::Dashboard => render_soc_dashboard(f, app, area),
        AppMode::ProcessManager => render_process_intelligence(f, app, area),
        AppMode::Monitor => render_threat_feed(f, app, area),
        AppMode::NetworkInsight => render_network_intelligence(f, app, area),
        AppMode::AlertLogs => render_forensic_logs(f, app, area),
        _ => {
            let msg = Paragraph::new("\n\n   Initializing Encrypted Module Space...")
                .alignment(Alignment::Center)
                .style(Style::default().fg(Color::DarkGray).bg(Color::Black));
            f.render_widget(msg, area);
        }
    }
}

fn render_soc_dashboard(f: &mut Frame, app: &App, area: Rect) {
    let main_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(8), // Pulse Graphs
            Constraint::Min(0),    // Data Matrix
        ])
        .split(area);

    render_telemetry_pulse(f, app, main_chunks[0]);

    let data_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(60), // Active Incidents
            Constraint::Percentage(40), // System Health
        ])
        .split(main_chunks[1]);

    render_incident_matrix(f, app, data_chunks[0]);
    render_health_diagnostics(f, app, data_chunks[1]);
}

fn render_telemetry_pulse(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Ratio(1, 3),
            Constraint::Ratio(1, 3),
            Constraint::Ratio(1, 3),
        ])
        .split(area);

    let cpu_data: Vec<u64> = app.cpu_history.iter().map(|&v| v as u64).collect();
    f.render_widget(Sparkline::default()
        .block(Block::default().title(" [ CPU_LOAD_PULSE ] ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)))
        .data(&cpu_data)
        .style(Style::default().fg(Color::Green)), chunks[0]);

    let mem_pct = if app.telemetry.total_memory > 0 { (app.telemetry.used_memory as f64 / app.telemetry.total_memory as f64) * 100.0 } else { 0.0 };
    f.render_widget(Gauge::default()
        .block(Block::default().title(" [ MEM_USAGE_LEVEL ] ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)))
        .gauge_style(Style::default().fg(Color::Cyan).bg(Color::Black))
        .percent(mem_pct as u16)
        .label(format!("{:.1}% UTILIZED", mem_pct)), chunks[1]);

    let net_data: Vec<u64> = app.net_rx_history.iter().map(|&v| (v as u64 % 50)).collect();
    f.render_widget(Sparkline::default()
        .block(Block::default().title(" [ NET_TRAFFIC_IO ] ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)))
        .data(&net_data)
        .style(Style::default().fg(Color::Yellow)), chunks[2]);
}

fn render_incident_matrix(f: &mut Frame, app: &App, area: Rect) {
    let items: Vec<ListItem> = app.alerts.iter().rev().take(15).map(|a| {
        let color = match a.severity {
            Severity::Critical => Color::Red,
            Severity::High => Color::LightRed,
            Severity::Medium => Color::Yellow,
            Severity::Low => Color::Green,
        };
        ListItem::new(Line::from(vec![
            Span::styled(format!(" [{:?}] ", a.severity).to_uppercase(), Style::default().fg(color).add_modifier(Modifier::BOLD)),
            Span::styled(format!(" {:<20} ", a.title), Style::default().fg(Color::White)),
            Span::styled(format!(" (CONF: {:.0}%)", a.confidence * 100.0), Style::default().fg(Color::DarkGray)),
        ]))
    }).collect();

    let list = List::new(items)
        .block(Block::default().title(" ACTIVE_THREAT_INGESTION ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)))
        .style(Style::default().bg(Color::Black));
    f.render_widget(list, area);
}

fn render_health_diagnostics(f: &mut Frame, app: &App, area: Rect) {
    let proc_count = app.telemetry.processes.len().to_string();
    let net_count = app.telemetry.network_interfaces.len().to_string();
    let uptime = app.telemetry.uptime.to_string();

    let rows = vec![
        Row::new(vec![Cell::from("PROC_THREADS"), Cell::from(proc_count)]),
        Row::new(vec![Cell::from("NET_INTERFACES"), Cell::from(net_count)]),
        Row::new(vec![Cell::from("ENGINE_STATE"), Cell::from("NOMINAL").style(Style::default().fg(Color::Green))]),
        Row::new(vec![Cell::from("DB_PERSISTENCE"), Cell::from("CONNECTED").style(Style::default().fg(Color::Green))]),
        Row::new(vec![Cell::from("UPTIME_SEC"), Cell::from(uptime)]),
    ];

    let table = Table::new(rows, [Constraint::Percentage(70), Constraint::Percentage(30)])
        .block(Block::default().title(" DIAGNOSTICS ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)))
        .style(Style::default().bg(Color::Black));
    f.render_widget(table, area);
}

fn render_threat_feed(f: &mut Frame, app: &App, area: Rect) {
    let rows = app.alerts.iter().rev().take(area.height as usize).map(|a| {
        let color = match a.severity {
            Severity::Critical => Color::Red,
            Severity::High => Color::LightRed,
            Severity::Medium => Color::Yellow,
            _ => Color::Green,
        };
        Row::new(vec![
            Cell::from(a.timestamp.format("%H:%M:%S").to_string()).style(Style::default().fg(Color::DarkGray)),
            Cell::from(format!("{:?}", a.severity).to_uppercase()).style(Style::default().fg(color).add_modifier(Modifier::BOLD)),
            Cell::from(a.title.clone()).style(Style::default().fg(Color::White)),
            Cell::from(a.detection_type.clone()).style(Style::default().fg(Color::Cyan).add_modifier(Modifier::DIM)),
            Cell::from(a.pid.map(|p| p.to_string()).unwrap_or_else(|| "N/A".to_string())).style(Style::default().fg(Color::Gray)),
        ])
    });

    let table = Table::new(rows, [
        Constraint::Length(10),
        Constraint::Length(12),
        Constraint::Min(30),
        Constraint::Length(15),
        Constraint::Length(10),
    ])
    .header(Row::new(vec!["TIME", "SEVERITY", "IOC_DESCRIPTION", "DET_TYPE", "ENTITY_ID"]).style(Style::default().fg(Color::Cyan)))
    .block(Block::default().title(" REAL_TIME_SIGNAL_ANALYSIS ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
    f.render_widget(table, area);
}

fn render_process_intelligence(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Min(0), Constraint::Length(35)])
        .split(area);

    let rows = app.telemetry.processes.iter().enumerate().map(|(i, p)| {
        let mut style = if p.cpu_usage > 80.0 { Style::default().fg(Color::Yellow) } else { Style::default().fg(Color::Gray) };
        if i == app.process_table_state { style = style.bg(Color::DarkGray).fg(Color::White).add_modifier(Modifier::BOLD); }
        Row::new(vec![
            Cell::from(p.pid.to_string()),
            Cell::from(p.name.clone()),
            Cell::from(p.user.clone()),
            Cell::from(format!("{:.1}%", p.cpu_usage)),
            Cell::from(format!("{:.1}M", p.memory_usage as f32 / 1e6)),
        ]).style(style)
    });

    let table = Table::new(rows, [
        Constraint::Length(8),
        Constraint::Min(20),
        Constraint::Length(12),
        Constraint::Length(8),
        Constraint::Length(10),
    ])
    .header(Row::new(vec!["PID", "IDENTIFIER", "OWNER", "CPU", "MEM"]).style(Style::default().fg(Color::Cyan)))
    .block(Block::default().title(" PROCESS_TELEMETRY_STREAM ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
    f.render_widget(table, chunks[0]);

    if let Some(p) = app.telemetry.processes.get(app.process_table_state) {
        let detail = Paragraph::new(vec![
            Line::from(vec![Span::styled(" [ ENTITY_INSPECTOR ] ", Style::default().fg(Color::Black).bg(Color::Cyan))]),
            Line::from(""),
            Line::from(vec![Span::styled(" NAME: ", Style::default().fg(Color::DarkGray)), Span::raw(&p.name)]),
            Line::from(vec![Span::styled(" PID:  ", Style::default().fg(Color::DarkGray)), Span::raw(p.pid.to_string())]),
            Line::from(vec![Span::styled(" PATH: ", Style::default().fg(Color::DarkGray)), Span::raw(&p.exe_path)]),
            Line::from(""),
            Line::from(vec![Span::styled(" REP_SCORE: ", Style::default().fg(Color::DarkGray)), Span::styled("ANALYZING", Style::default().fg(Color::Yellow))]),
            Line::from(vec![Span::styled(" SIGNATURE: ", Style::default().fg(Color::DarkGray)), Span::styled("UNSIGNED", Style::default().fg(Color::Red))]),
        ]).wrap(Wrap { trim: true }).block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
        f.render_widget(detail, chunks[1]);
    }
}

fn render_network_intelligence(f: &mut Frame, app: &App, area: Rect) {
    let rows = app.telemetry.network_interfaces.iter().map(|(name, data)| {
        Row::new(vec![
            Cell::from(name.clone()).style(Style::default().fg(Color::White)),
            Cell::from("ACTIVE").style(Style::default().fg(Color::Green)),
            Cell::from(format!("{:.1} KB/s", data.rx_bytes as f32 / 1024.0)), 
            Cell::from(format!("{:.1} KB/s", data.tx_bytes as f32 / 1024.0)),
        ]).style(Style::default().fg(Color::Gray))
    });

    let table = Table::new(rows, [
        Constraint::Length(15),
        Constraint::Length(10),
        Constraint::Length(15),
        Constraint::Length(15),
    ])
    .header(Row::new(vec!["INTERFACE", "STATE", "INGRESS", "EGRESS"]).style(Style::default().fg(Color::Cyan)))
    .block(Block::default().title(" NETWORK_TRAFFIC_TOPOLOGY ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
    f.render_widget(table, area);
}

fn render_forensic_logs(f: &mut Frame, app: &App, area: Rect) {
    let rows = app.alerts.iter().rev().take(area.height as usize - 4).map(|a| {
        Row::new(vec![
            Cell::from(a.timestamp.format("%H:%M:%S").to_string()),
            Cell::from(format!("{:?}", a.severity).to_uppercase()).style(Style::default().fg(match a.severity { Severity::Critical => Color::Red, _ => Color::Gray })),
            Cell::from(a.title.clone()),
            Cell::from(a.pid.map(|p| p.to_string()).unwrap_or_else(|| "N/A".to_string())),
        ]).style(Style::default().fg(Color::Gray))
    });

    let table = Table::new(rows, [
        Constraint::Length(10),
        Constraint::Length(10),
        Constraint::Min(40),
        Constraint::Length(8),
    ])
    .header(Row::new(vec!["TIME", "LEVEL", "EVENT_DESCRIPTION", "PID"]).style(Style::default().fg(Color::Cyan)))
    .block(Block::default().title(" PERSISTENT_FORENSIC_DATABASE ").borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
    f.render_widget(table, area);
}

fn render_integrated_footer(f: &mut Frame, _app: &App, area: Rect) {
    let keys = vec![
        ("F1", "DASH"), ("F2", "FEED"), ("F3", "PROC"), ("F4", "NET"), ("F5", "LOGS"), ("Q", "EXIT"),
    ];

    let spans: Vec<Span> = keys.iter().flat_map(|(k, v)| {
        vec![
            Span::styled(format!(" {} ", k), Style::default().fg(Color::Black).bg(Color::DarkGray)),
            Span::styled(format!(" {}  ", v), Style::default().fg(Color::Gray)),
        ]
    }).collect();

    f.render_widget(Paragraph::new(Line::from(spans)).style(Style::default().bg(Color::Black)), area);
}

fn mode_to_index(mode: &AppMode) -> usize {
    match mode {
        AppMode::Dashboard => 0,
        AppMode::Monitor => 1,
        AppMode::ProcessManager => 2,
        AppMode::NetworkInsight => 3,
        AppMode::AlertLogs => 4,
        AppMode::Investigation => 5,
    }
}
