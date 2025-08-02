from flask import Flask, request, render_template, jsonify, send_from_directory
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os, json

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

VIN_HISTORY_FILE = "vin_history.json"
vin_history = {}
off_duty = False

if os.path.exists(VIN_HISTORY_FILE):
    with open(VIN_HISTORY_FILE, "r") as f:
        vin_history = json.load(f)

def save_vin_history():
    with open(VIN_HISTORY_FILE, "w") as f:
        json.dump(vin_history, f, indent=2)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

@app.route('/check_vin/<vin>')
def check_vin(vin):
    duplicate = vin in vin_history
    return jsonify({"duplicate": duplicate})

@app.route('/', methods=['GET','POST'])
def dealer():
    global off_duty
    if request.method == 'POST':
        vin = request.form.get('vin')
        kms = request.form.get('kms')
        dealer_name = request.form.get('dealer_name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if vin not in vin_history:
            vin_history[vin] = []
        vin_history[vin].append({
            "dealer_name": dealer_name,
            "email": email,
            "phone": phone,
            "date": now,
            "kms": kms
        })
        save_vin_history()

        photos = request.files.getlist('photos')
        for idx, photo in enumerate(photos[:12]):
            filename = secure_filename(f"{vin}_{now}_{idx}_{photo.filename}")
            photo.save(os.path.join(UPLOAD_FOLDER, filename))

        return "<h2 style='text-align:center;font-family:sans-serif;'>Thanks for your submission!<br>Someone is looking at it right now.</h2><div style='text-align:center;margin-top:20px;'><a href='/' style='padding:10px 15px;background:#A8D5BA;color:black;text-decoration:none;border-radius:8px;'>Submit Another</a></div>"
    return render_template('dealer.html', off_duty=off_duty)

@app.route('/admin')
def admin():
    now = datetime.now()
    for vin, entries in vin_history.items():
        for e in entries:
            submit_time = datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S")
            e['overdue'] = (now - submit_time) > timedelta(minutes=35) and not e.get('value')
            e['duplicate'] = len(vin_history[vin]) > 1
    return render_template('admin.html', vin_history=vin_history)

@app.route('/toggle_off_duty', methods=['POST'])
def toggle_off_duty():
    global off_duty
    off_duty = not off_duty
    return jsonify({"off_duty": off_duty})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
