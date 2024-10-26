from flask import Flask, request, jsonify, render_template
import cv2
import pytesseract
import qrcode
import datetime
import os
import sqlite3
from db_setup import init_db  # Import the init_db function

app = Flask(__name__)

# Set the path to your Tesseract installation (only necessary on Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Change this if necessary

# Database configuration
DATABASE = 'vehicles.db'

def read_number_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 100, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:  # Assuming the plate is rectangular
            x, y, w, h = cv2.boundingRect(approx)
            plate_img = frame[y:y + h, x:x + w]
            number_plate = pytesseract.image_to_string(plate_img, config='--psm 8')
            return number_plate.strip()
    return None

def sanitize_filename(filename):
    return ''.join(c if c.isalnum() or c in (' ', '_') else '_' for c in filename)

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    sanitized_data = sanitize_filename(data)
    qr_code_path = f"static/qrcodes/{sanitized_data}.png"
    
    img.save(qr_code_path)
    return qr_code_path

def get_next_slot():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM vehicles')
        count = cursor.fetchone()[0]
    return count + 1  # Next slot number

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/entry', methods=['POST'])
def entry():
    camera = cv2.VideoCapture(0)  # Use your camera index
    ret, frame = camera.read()
    camera.release()

    if not ret:
        return jsonify({'message': 'Unable to capture image'}), 500

    vehicle_number = read_number_plate(frame)
    if vehicle_number is None or vehicle_number.strip() == '':
        return jsonify({'message': 'Failed to capture number plate'}), 500

    slot_number = get_next_slot()
    entry_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rate_per_hour = 50  # INR

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO vehicles (vehicle_number, entry_time, slot, amount) VALUES (?, ?, ?, ?)',
                           (vehicle_number, entry_time, slot_number, rate_per_hour))
            conn.commit()  # Commit the transaction
    except Exception as e:
        return jsonify({'message': 'Failed to save vehicle details', 'error': str(e)}), 500

    qr_data = f"Vehicle: {vehicle_number}, Slot: {slot_number}, Entry Time: {entry_time}"
    qr_code_path = generate_qr_code(qr_data)

    return jsonify({
        'message': 'Vehicle registered successfully',
        'vehicle_number': vehicle_number,
        'slot': slot_number,
        'entry_time': entry_time,
        'qr_code': qr_code_path
    }), 200

@app.route('/exit', methods=['POST'])
def exit():
    data = request.get_json()
    vehicle_number = data.get('vehicle_number')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles WHERE vehicle_number = ?', (vehicle_number,))
        vehicle = cursor.fetchone()

    if vehicle is None:
        return jsonify({'message': 'Vehicle not found!'}), 404

    entry_time = vehicle[2]  # Entry time
    rate_per_hour = vehicle[4]  # Amount
    current_time = datetime.datetime.now()
    total_hours = (current_time - datetime.datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")).total_seconds() // 3600
    total_charge = total_hours * rate_per_hour

    # Prepare the exit slip
    slip = {
        'vehicle_number': vehicle_number,
        'entry_time': entry_time,
        'exit_time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
        'hours_parked': total_hours,
        'total_amount': total_charge,
    }

    # Provide payment options
    payment_options = {
        'cash': 'Proceed with cash payment.',
        'online': 'Scan QR code to pay online.'
    }

    return jsonify({
        'message': 'Exit processed successfully',
        'slip': slip,
        'payment_options': payment_options
    })

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    vehicle_number = data.get('vehicle_number')
    payment_method = data.get('payment_method')  # 'cash' or 'online'

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles WHERE vehicle_number = ?', (vehicle_number,))
        vehicle = cursor.fetchone()

    if vehicle is None:
        return jsonify({'message': 'Vehicle not found!'}), 404

    # Mark as paid
    cursor.execute('UPDATE vehicles SET is_paid = 1 WHERE vehicle_number = ?', (vehicle_number,))
    conn.commit()

    return jsonify({'message': 'Payment successful', 'payment_method': payment_method}), 200

@app.route('/delete_old_records', methods=['POST'])
def delete_old_records():
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=5)
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vehicles WHERE exit_time IS NOT NULL AND entry_time < ?', (threshold_date.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
    return jsonify({'message': 'Old records deleted successfully'}), 200

if __name__ == '__main__':
    os.makedirs('static/qrcodes', exist_ok=True)  # Create QR code directory if it doesn't exist
    init_db()  # Initialize the database
    app.run(debug=True)
