from flask import Flask, request, render_template, jsonify
from db import add_user_to_database, check_contact_in_db
from flask_cors import CORS
from flask_apscheduler import APScheduler
from utils import check_flight_updates, send_sms, send_email, getFlightInfo
import random
from const import otp_storage

app = Flask(__name__)
CORS(app)
scheduler = APScheduler()
scheduler.init_app(app)

@app.route('/')
def index():
    return render_template('index`.html')


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    email = data.get('email', "")
    phone_number = data.get('phone_number', "")
    fln = data.get('fln')

    if not fln or (not email and not phone_number):
        return jsonify({"error": "Flight number and either email or phone number are required", "is_user_added": False}), 400

    response = add_user_to_database(fln, email, phone_number)

    return jsonify({"message": "User added successfully", "id": str(response), "is_user_added": True}), 201


@app.route("/generate-otp/<flight_number>/<contact_type>/<contact>", methods=['GET'])
def generate_otp_for_verification(flight_number, contact_type, contact):
    if check_contact_in_db(flight_number, contact):
        return jsonify({"error": f"{contact_type} is already registered for flight number {flight_number}."}), 400

    otp = random.randint(1000, 9999)
    body = f"Your OTP for FlightTrack is {otp}\nYou will be notified for the flight: {flight_number}.\nPlease DO NOT share this OTP with anyone."

    if contact_type == 'phoneNumber':
        send_sms(contact, body)
    elif contact_type == 'email':
        subject = f"OTP For FlightTrack: Flight {flight_number}"
        send_email(contact, subject, body)
    else:
        return jsonify({"error": "Invalid contact type"}), 400

    otp_storage[contact] = otp

    return jsonify({"confirmation_message": f"OTP is successfully generated to your {contact_type}: {contact}"}), 200


@app.route("/verify-otp/<otp>/<contact>", methods=["GET"])
def verify_otp(otp, contact):
    try:
        otp = int(otp)
    except ValueError:
        return jsonify({"error": "Invalid OTP format"}), 400
    
    if contact not in otp_storage:
        return jsonify({"error": "Contact not found"}), 404
    
    stored_otp = otp_storage.get(contact)
    
    if stored_otp == otp:
        del otp_storage[contact]
        return jsonify({"message": "OTP verified successfully!"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 400


@app.route('/get_flight_details/<flight_number>', methods=['GET'])
def get_details(flight_number):
    
    response = getFlightInfo(flight_number)
    return jsonify(response)


scheduler.add_job(id='check_flights', func=check_flight_updates, trigger='interval', seconds=600)
scheduler.start()

if __name__ == '__main__':
    app.run(port=8000)
