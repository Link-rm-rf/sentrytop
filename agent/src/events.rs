use crossterm::event::KeyEvent;
use crate::telemetry::TelemetryData;

pub enum AppEvent {
    Input(KeyEvent),
    Tick,
    TelemetryUpdate(TelemetryData),
}
