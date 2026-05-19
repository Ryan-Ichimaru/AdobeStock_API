import os
import sys
import time
import threading
from datetime import datetime
from watchdog.observers.polling import PollingObserver as Observer

# Import our custom modules
from image_processor import ImageHandler, INPUT_DIR

def main():
    print("="*50)
    print("Starting Stock Photo Automation System (Metadata Only)")
    print("="*50)
    
    # Start the watchdog observer for 1_Input directory
    print(f"[{datetime.now()}] Starting directory watcher on {INPUT_DIR}...")
    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping system...")
        observer.stop()
    
    observer.join()
    print("System stopped normally.")

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    main()
