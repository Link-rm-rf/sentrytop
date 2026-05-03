#![no_std]

#[repr(C)]
#[derive(Clone, Copy)]
pub struct ProcessEvent {
    pub pid: u32,
    pub comm: [u8; 16], // Process name
}

#[cfg(feature = "user")]
unsafe impl aya::Pod for ProcessEvent {}
