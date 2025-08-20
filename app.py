from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)
COUNT_FILE = 'tray_counts.txt'
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

def write_counts(counts):
    with open(COUNT_FILE, 'w') as f:
        for tray in TRAYS:
            f.write(f"{tray} count: {counts[tray]}\n")

@app.route('/')
def index():
    counts = read_counts()
    return render_template('index.html', counts=counts)

@app.route('/reset', methods=['POST'])
def reset():
    counts = {tray: 0 for tray in TRAYS}
    write_counts(counts)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)