import pexpect
import time
import sys
import os

def test_integration():
    print("Starting CLI in integration mode (live pipe)...")
    env = os.environ.copy()
    env["NOSUDO"] = "1"
    
    child = pexpect.spawn('python3 sentrytop/sentrytop_cli.py', env=env, encoding='utf-8', timeout=10)
    
    try:
        # Wait for the startup glitch animation and initial render
        time.sleep(2)
        
        print("Waiting for correlator output to be processed...")
        time.sleep(2)
        
        print("Sending 'q' (quit)...")
        child.send('q')
        
        # Expect the process to exit
        child.expect(pexpect.EOF)
        print("Integration process exited cleanly.")
        
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
    test_integration()
