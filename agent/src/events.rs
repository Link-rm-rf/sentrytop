use sentrytop_common::ProcessEvent;
use crossterm::event::KeyEvent;
use crate::telemetry::TelemetryData;

pub enum AppEvent {
    Input(KeyEvent),
    Tick,
    TelemetryUpdate(TelemetryData),
    KernelEvent(ProcessEvent), // <--- Add this line
}
