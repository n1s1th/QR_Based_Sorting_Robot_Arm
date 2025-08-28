import threading
import time
import serial
from flask import Flask, render_template, redirect, url_for, request
import os
from automated_tray_sorting import scan_qr_live_cropped_timeout
from automated_cell_selection import select_random_cell_and_format
import random

app = Flask(__name__)
COUNT_FILE = 'tray_counts.txt'
LOG_FILE = 'system.log'
TRAYS = ['B1', 'B2', 'B3', 'B4']

run_state = {'status': 'stopped'}  # can be 'stopped', 'running', 'paused'
tray_counts = {tray: 0 for tray in TRAYS}
controller_thread = None

def log_message(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

def read_counts():
    counts = {tray: 0 for tray in TRAYS}
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3 and parts[0] in TRAYS:
                    counts[parts[0]] = int(parts[2])
    return counts

def write_counts(counts):
    with open(COUNT_FILE, 'w') as f:
        for tray in TRAYS:
            f.write(f"{tray} count: {counts[tray]}\n")

def read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return f.readlines()[-30:]
    return []

def controller_loop(serial_port='/dev/ttyACM0', baud_rate=9600, camera_index=0):
    global tray_counts, controller_thread
    # Load previous tray counts
    tray_counts = read_counts()
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)
        log_message(f"Connected to Arduino on {serial_port}")
    except Exception as e:
        log_message(f"Serial connection error: {e}")
        run_state['status'] = 'stopped'
        controller_thread = None  # Clear thread reference
        return

    while True:
        # Handle stop/pause
        while run_state['status'] == 'paused':
            log_message("System paused.")
            time.sleep(2)
        if run_state['status'] == 'stopped':
            log_message("System stopped.")
            controller_thread = None  # Clear thread reference
            break

        # Stop if any tray is full
        full_trays = [tray for tray, count in tray_counts.items() if count >= 4]
        if full_trays:
            log_message(f"Tray(s) full: {', '.join(full_trays)}. System stopped. Please reset.")
            run_state['status'] = 'stopped'
            controller_thread = None  # Clear thread reference
            break

        # Wait for Arduino prompt for slider/arm action
        log_message("Waiting for Arduino to request slider/arm input...")
        while True:
            if run_state['status'] == 'paused':
                break
            if run_state['status'] == 'stopped':
                log_message("System stopped by user.")
                controller_thread = None  # Clear thread reference
                return
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {line}")
                if "slider position" in line:
                    break
            time.sleep(0.2)

        if run_state['status'] != 'running':
            continue

        # Automated cell selection, check for empty tray
        cell_label = select_random_cell_and_format()
        retry_count = 0
        while cell_label is None:
            log_message("No object detected in tray. Retrying in 10 seconds...")
            for _ in range(10):
                if run_state['status'] != 'running':
                    break
                time.sleep(1)
            cell_label = select_random_cell_and_format()
            retry_count += 1
            if retry_count >= 12:
                log_message("No object detected after multiple retries. System stopped.")
                run_state['status'] = 'stopped'
                controller_thread = None  # Clear thread reference
                return
        if run_state['status'] != 'running':
            continue

        # Random arm action
        arm_actions = ['a', 'b', 'c', 'd']
        arm = random.choice(arm_actions)
        log_message(f"Automated selection: Slider cell '{cell_label}', Arm '{arm}'")
        user_input = f"{cell_label} {arm}"

        # Send slider/arm input to Arduino
        ser.write((user_input + '\n').encode())
        log_message(f"Sent to Arduino: {user_input}")

        # Wait for READY_TO_SCAN from Arduino
        log_message("Waiting for Arduino to signal READY_TO_SCAN...")
        while True:
            if run_state['status'] == 'paused':
                break
            if run_state['status'] == 'stopped':
                log_message("System stopped by user.")
                controller_thread = None  # Clear thread reference
                return
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {line}")
                if "READY_TO_SCAN" in line:
                    break
            time.sleep(0.2)
        if run_state['status'] != 'running':
            continue

        # Scan QR code for tray selection
        log_message("Scanning QR code for tray number (live, 5s timeout)...")
        try:
            tray_code = scan_qr_live_cropped_timeout(camera_index=camera_index, timeout_sec=5)
            log_message(f"QR scan result: {tray_code}")
        except Exception as e:
            log_message(f"QR scan error: {e}")
            tray_code = None

        if tray_code not in [t.lower() for t in TRAYS]:
            log_message("No valid QR code detected. Defaulting to tray 'b4'.")
            tray_code = 'b4'
        else:
            log_message(f"Detected tray code: {tray_code}")

        ser.write((tray_code + '\n').encode())
        log_message(f"Sent to Arduino: {tray_code}")

        # Wait for ROUND_COMPLETE from Arduino
        log_message("Waiting for Arduino to signal ROUND_COMPLETE...")
        while True:
            if run_state['status'] == 'paused':
                break
            if run_state['status'] == 'stopped':
                log_message("System stopped by user.")
                controller_thread = None  # Clear thread reference
                return
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                log_message(f"Arduino: {response}")
                if "ROUND_COMPLETE" in response:
                    break
            time.sleep(0.2)
        if run_state['status'] != 'running':
            continue

        # Update counts and log to file
        tray_code = tray_code.upper()
        tray_counts[tray_code] += 1
        write_counts(tray_counts)

        log_message("Tray counts so far:")
        for key in TRAYS:
            log_message(f"{key} count: {tray_counts[key]}")
        log_message("Round complete. Ready for next round!\n")

    controller_thread = None  # Ensure thread reference is cleared on normal exit

@app.route('/', methods=['GET', 'POST'])
def index():
    global run_state
    counts = read_counts()
    logs = read_log()
    tray_full = any(c >= 4 for c in counts.values())
    full_trays = [tray for tray, c in counts.items() if c >= 4]
    return render_template(
        'index.html',
        counts=counts,
        logs=logs,
        tray_full=tray_full,
        full_trays=full_trays,
        run_status=run_state['status']
    )

@app.route('/control', methods=['POST'])
def control():
    global run_state, controller_thread
    cmd = request.form.get('cmd')
    if cmd == 'start':
        # Restart safety: join previous thread if still alive
        if run_state['status'] == 'stopped':
            if controller_thread is not None and controller_thread.is_alive():
                log_message("Waiting for previous controller thread to finish...")
                controller_thread.join(timeout=2)
            run_state['status'] = 'running'
            controller_thread = threading.Thread(target=controller_loop)
            controller_thread.daemon = True
            controller_thread.start()
        elif run_state['status'] == 'paused':
            run_state['status'] = 'running'
    elif cmd == 'pause':
        if run_state['status'] == 'running':
            run_state['status'] = 'paused'
    elif cmd == 'stop':
        run_state['status'] = 'stopped'
        # Optionally join thread to ensure clean stop
        if controller_thread is not None and controller_thread.is_alive():
            controller_thread.join(timeout=2)
        controller_thread = None
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    global tray_counts, run_state, controller_thread
    tray_counts = {tray: 0 for tray in TRAYS}
    write_counts(tray_counts)
    open(LOG_FILE, 'w').close()
    run_state['status'] = 'stopped'
    # Ensure thread is stopped and cleaned up
    if controller_thread is not None and controller_thread.is_alive():
        log_message("Waiting for previous controller thread to finish (reset)...")
        controller_thread.join(timeout=2)
    controller_thread = None
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)