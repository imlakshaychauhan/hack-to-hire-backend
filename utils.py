import requests
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from credentials import x_rapidapi_host, x_rapidapi_key, account_sid, auth_token, twilio_phone_number, google_app_password, google_email
from db import get_users_from_database, update_user_info_to_database
from datetime import datetime

def getFlightInfo(flight_number):
    url = f'https://flightera-flight-data.p.rapidapi.com/flight/info?flnr={flight_number}'
    headers = {
        'x-rapidapi-host': x_rapidapi_host,
        'x-rapidapi-key': x_rapidapi_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        flight_info = response.json()
        if not flight_info:
            raise ValueError(f"No flight information found for flight number: {flight_number}")
        return flight_info
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


def send_email(to_email, subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = google_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(google_email, google_app_password)
        server.sendmail(google_email, to_email, msg.as_string())


def send_sms(to, body):
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=body,
        from_=twilio_phone_number,
        to= "+91" + to
    )

    print(f"Message sent to {to}. SID: {message.sid}")
    
def calculate_delay(scheduled, actual):
    scheduled_time = datetime.strptime(scheduled, '%Y-%m-%dT%H:%M:%S%z')
    actual_time = datetime.strptime(actual, '%Y-%m-%dT%H:%M:%S%z')
    delay_minutes = (actual_time - scheduled_time).total_seconds() / 60
    return delay_minutes

def check_flight_updates():
    users = get_users_from_database()
    for user in users:
        fln = user['fln']
        flight_info = getFlightInfo(fln)
        
        current_status = flight_info[0]["status"]
        current_arrival_gate = flight_info[0]["arrival_gate"]
        current_arrival_terminal = flight_info[0]["arrival_terminal"]
        current_departure_gate = flight_info[0]["departure_gate"]
        current_departure_terminal = flight_info[0]["departure_terminal"]
        current_delay = calculate_delay(flight_info[0]["scheduled_arrival_local"], flight_info[0]["actual_arrival_local"])
        
        if(user["last_status"] == "none" and user["last_arrival_gate"] == "none" and user["last_arrival_terminal"] == "none" and user["last_departure_gate"] == "none" and user["last_departure_terminal"] == "none" and user["last_delay"] == "none"):
            update_user_info_to_database(fln, current_status, current_arrival_gate, current_arrival_terminal, current_departure_gate, current_departure_terminal, current_delay)
            return

        if (user["last_status"] != current_status or
            user["last_arrival_gate"] != current_arrival_gate or
            user["last_arrival_terminal"] != current_arrival_terminal or
            user["last_departure_gate"] != current_departure_gate or
            user["last_departure_terminal"] != current_departure_terminal or
            user["last_delay"] != current_delay):
            message = f"Your flight {fln} has updates:\n"
            if user["last_status"] != current_status:
                message += f"Status changed to {current_status}.\n"
            if user["last_arrival_gate"] != current_arrival_gate:
                message += f"Arrival gate changed to {current_arrival_gate}.\n"
            if user["last_arrival_terminal"] != current_arrival_terminal:
                message += f"Arrival terminal changed to {current_arrival_terminal}.\n"
            if user["last_departure_gate"] != current_departure_gate:
                message += f"Departure gate changed to {current_departure_gate}.\n"
            if user["last_departure_terminal"] != current_departure_terminal:
                message += f"Departure terminal changed to {current_departure_terminal}.\n"
            if user["last_delay"] != current_delay:
                message += f"Delay is now {current_delay:.2f} minutes.\n"
            if user["email"]:
                send_email(user["email"], f"Flight {fln} Status Update", message)
            if user["phone_number"]:
                send_sms(user["phone_number"], message)

            update_user_info_to_database(fln, current_status, current_arrival_gate, current_arrival_terminal, current_departure_gate, current_departure_terminal, current_delay)
