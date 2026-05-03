#![no_std]
#![no_main]

use aya_ebpf::{
    macros::{kprobe, map},
    programs::ProbeContext,
    maps::PerfEventArray,
    EbpfContext,
};
use sentrytop_common::ProcessEvent;
use core::ptr::addr_of_mut;

#[map]
static mut EVENTS: PerfEventArray<ProcessEvent> = PerfEventArray::new(0);

#[kprobe]
pub fn sentrytop(ctx: ProbeContext) -> u32 {
    let _ = try_sentrytop(ctx);
    0
}

#[inline(always)]
fn try_sentrytop(ctx: ProbeContext) -> Result<u32, u32> {
    let pid = ctx.pid();
    let comm = ctx.command().map_err(|_| 1u32)?;
    let event = ProcessEvent { pid, comm };

    unsafe {
        // Use addr_of_mut to bypass the "shared reference to mutable static" error
        (*addr_of_mut!(EVENTS)).output(&ctx, &event, 0);
    }
    Ok(0)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
