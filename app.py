from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)
COUNT_FILE = 'tray_counts.txt'
LOG_FILE = 'system.log'
TRAYS = ['B1', 'B2', 'B3', 'B4']

def read_counts():
    counts = {tray: 0 for tray in TRAYS}
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3 and parts[0] in TRAYS:
                    counts[parts[0]] = int(parts[2])
    return counts

def read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return f.readlines()[-30:]  # Last 30 log lines for brevity
    return []

def write_counts(counts):
    with open(COUNT_FILE, 'w') as f:
        for tray in TRAYS:
            f.write(f"{tray} count: {counts[tray]}\n")

@app.route('/')
def index():
    counts = read_counts()
    logs = read_log()
    tray_full = any(c >= 4 for c in counts.values())
    full_trays = [tray for tray, c in counts.items() if c >= 4]
    return render_template(
        'index.html',
        counts=counts,
        logs=logs,
        tray_full=tray_full,
        full_trays=full_trays
    )

@app.route('/reset', methods=['POST'])
def reset():
    counts = {tray: 0 for tray in TRAYS}
    write_counts(counts)
    # Optionally clear log file
    open(LOG_FILE, 'w').close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)