use anyhow::{Context, Result, anyhow};
use aya::{
    include_bytes_aligned, 
    maps::AsyncPerfEventArray, // Fixed: Direct import path
    programs::KProbe, 
    Ebpf, 
    util::online_cpus
};
use aya_log::EbpfLogger;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{io, time::Duration};
use tokio::sync::mpsc;
use bytes::BytesMut;
use log::warn;

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
use sentrytop_common::ProcessEvent;

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Setup color-eyre and Terminal
    color_eyre::install().map_err(|e| anyhow!("Color-eyre init failed: {}", e))?;
    env_logger::init();
    
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let (tx, mut rx) = mpsc::channel(100);

    // 2. Load eBPF bytecode
    let data = include_bytes_aligned!(
        "../../target/bpfel-unknown-none/debug/libsentrytop_ebpf.so"
    );
    let mut bpf = Ebpf::load(data).context("Failed to load eBPF bytecode")?;
    
    if let Err(e) = EbpfLogger::init(&mut bpf) {
        warn!("failed to initialize eBPF logger: {}", e);
    }

    let program: &mut KProbe = bpf.program_mut("sentrytop")
        .context("eBPF program 'sentrytop' not found")?
        .try_into()?;
    program.load()?;
    program.attach("do_execve", 0)?;

    // 3. SPAWN TASKS

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

    let tick_tx = tx.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_millis(50));
        loop {
            interval.tick().await;
            let _ = tick_tx.send(AppEvent::Tick).await;
        }
    });

    // 4. Handle Kernel Event Stream
    let ebpf_tx = tx.clone();
    // Fix: Handle Option and Error conversion for online_cpus
    let mut perf_array = AsyncPerfEventArray::try_from(
        bpf.map_mut("EVENTS").ok_or_else(|| anyhow!("EVENTS map not found"))?
    )?;

    for cpu_id in online_cpus().map_err(|(s, _)| anyhow!(s))? {
        let mut buf = perf_array.open(cpu_id, None)?;
        let task_tx = ebpf_tx.clone();

        tokio::spawn(async move {
            let mut buffers = (0..10)
                .map(|_| BytesMut::with_capacity(1024))
                .collect::<Vec<_>>();

            loop {
                match buf.read_events(&mut buffers).await {
                    Ok(events) => {
                        for i in 0..events.read {
                            let data_ptr = buffers[i].as_ptr() as *const ProcessEvent;
                            let event = unsafe { std::ptr::read_volatile(data_ptr) };
                            let _ = task_tx.send(AppEvent::KernelEvent(event)).await;
                        }
                    }
                    Err(e) => warn!("Perf buffer error: {}", e),
                }
            }
        });
    }

    // 5. Main Loop
    let db = Database::new("sentrytop.db")?;
    let mut app = App::new(db);

    while app.running {
        terminal.draw(|f| ui::render(f, &app))?;
        if let Some(event) = rx.recv().await {
            app.handle_event(event);
        }
    }

    // 6. Cleanup
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen, DisableMouseCapture)?;
    terminal.show_cursor()?;

    Ok(())
}
