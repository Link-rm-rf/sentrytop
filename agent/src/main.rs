use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{io, time::Duration};
use tokio::sync::mpsc;

mod app;
mod events;
mod ui;
mod telemetry;
mod engine;
mod db;

use crate::app::App;
use crate::events::AppEvent;
use crate::telemetry::TelemetryCollector;
use crate::db::Database;

#[tokio::main]
async fn main() -> Result<()> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Setup event bus
    let (tx, mut rx) = mpsc::channel(100);
    
    // Input handling task
    let input_tx = tx.clone();
    tokio::spawn(async move {
        loop {
            if event::poll(Duration::from_millis(10)).unwrap() {
                if let Event::Key(key) = event::read().unwrap() {
                    let _ = input_tx.send(AppEvent::Input(key)).await;
                }
            }
        }
    });

    // Tick task
    let tick_tx = tx.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_millis(50));
        loop {
            interval.tick().await;
            let _ = tick_tx.send(AppEvent::Tick).await;
        }
    });

    // Telemetry task
    let telemetry_tx = tx.clone();
    tokio::spawn(async move {
        let mut collector = TelemetryCollector::new();
        let mut interval = tokio::time::interval(Duration::from_secs(1));
        loop {
            interval.tick().await;
            let data = collector.collect();
            let _ = telemetry_tx.send(AppEvent::TelemetryUpdate(data)).await;
        }
    });

    // Initialize Database
    let db = Database::new("sentrytop.db")?;

    // Initialize App
    let mut app = App::new(db);
    
    while app.running {
        terminal.draw(|f| {
            ui::render(f, &app);
        })?;

        if let Some(event) = rx.recv().await {
            app.handle_event(event);
        }
    }

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    Ok(())
}
