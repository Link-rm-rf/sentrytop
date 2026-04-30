import pexpect
import time
import sys

def test_cli():
    print("Starting CLI in mock mode...")
    # Use pexpect to spawn the TUI which simulates a real terminal
    child = pexpect.spawn('python3 sentrytop/sentrytop_cli.py --mock', encoding='utf-8', timeout=10)
    
    try:
        # Wait for the startup glitch animation and initial render
        time.sleep(2)
        
        print("Sending 'p' (pause)...")
        child.send('p')
        time.sleep(1)
        
        print("Sending 'p' (unpause)...")
        child.send('p')
        time.sleep(1)
        
        print("Sending 'v' (verbose toggle)...")
        child.send('v')
        time.sleep(1)
        
        print("Sending 'q' (quit)...")
        child.send('q')
        
        # Expect the process to exit
        child.expect(pexpect.EOF)
        print("Process exited cleanly.")
        
        # Check exit status
        if child.exitstatus != 0 and child.exitstatus is not None:
            print(f"Error: Non-zero exit status {child.exitstatus}")
            sys.exit(1)
            
    except pexpect.TIMEOUT:
        print("Error: TUI did not exit or respond in time.")
        child.kill(9)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        child.kill(9)
        sys.exit(1)

if __name__ == "__main__":
    test_cli()
