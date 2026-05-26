from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json
import os
import logging

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

BOOKING_FILE = "bookings.json"


def generate_slots():
    slots = []

    start = datetime.strptime("09:00", "%H:%M")
    end = datetime.strptime("21:00", "%H:%M")

    while start < end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=30)

    return slots


def load_bookings():
    if not os.path.exists(BOOKING_FILE):
        return {}

    with open(BOOKING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bookings(data):
    with open(BOOKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.route("/")
def home():

    data = load_bookings()

    rooms = ["101", "102", "103", "201", "202", "203"]

    room_cards = ""

    for room in rooms:

        room_data = data.get(room, {})

        is_busy = len(room_data) > 0

        status_class = "busy" if is_busy else "free"

        status_text = "Занята" if is_busy else "Свободна"

        room_cards += f"""
        <div class="room-card {status_class}">

            <div class="room-card-header">

                <h2>Аудитория {room}</h2>

                <div class="room-status">
                    {status_text}
                </div>

            </div>

            <div class="room-buttons">

                <a href="/room/{room}" class="room-btn">
                    Экран аудитории
                </a>

            </div>

        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ru">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>Система аудиторий</title>

        <link
            rel="stylesheet"
            href="/static/style.css?v=10"
        >

    </head>

    <body>

        <div class="container">

            <div class="top-panel">

                <h1>Список аудиторий</h1>

                <div class="datetime">

                <div id="date"></div>
                <div id="time"></div>

            </div>

            </div>

            <div class="rooms-grid">

                {room_cards}

            </div>

        </div>
    
        <script>
            const ROOM_ID = "101";
        </script>

        <script src="/static/script.js"></script>

    </body>

    </html>
    """


@app.route("/room/<room_id>")
def room(room_id):

    logger.info(f"Открыт экран аудитории {room_id}")

    return render_template(
        "room.html",
        room_id=room_id,
        slots=generate_slots()
    )


@app.route("/admin/<room_id>")
def admin(room_id):

    logger.info(f"Открыта панель бронирования {room_id}")

    return render_template(
        "admin.html",
        room_id=room_id,
        slots=generate_slots()
    )


@app.route("/api/room/<room_id>")
def get_room(room_id):

    data = load_bookings()

    if room_id not in data:
        data[room_id] = {}

    now = datetime.now()
    current_slot = None

    for slot in generate_slots():
        slot_time = datetime.strptime(slot, "%H:%M")

        slot_end = slot_time + timedelta(minutes=30)

        current_minutes = now.hour * 60 + now.minute
        start_minutes = slot_time.hour * 60 + slot_time.minute
        end_minutes = slot_end.hour * 60 + slot_end.minute

        if start_minutes <= current_minutes < end_minutes:
            current_slot = slot
            break

    current_booking = data[room_id].get(current_slot, "")

    return jsonify({
        "slots": data[room_id],
        "current_slot": current_slot,
        "current_booking": current_booking,
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%d.%m.%Y")
    })


@app.route("/api/book", methods=["POST"])
def book():

    req = request.get_json()

    room = req["room"]
    slot = req["slot"]
    name = req["name"]

    logger.info(
    f"Бронирование: аудитория={room}, слот={slot}, пользователь={name}"
    )

    data = load_bookings()

    user_slots = 0

    for room_data in data.values():

        for booked_name in room_data.values():

            if booked_name.lower() == name.lower():
                user_slots += 1

    if user_slots >= 6:

        logger.warning(
            f"Превышен лимит слотов: пользователь={name}"
        )

        return jsonify({
            "success": False,
            "message": "Максимум 6 слотов на одного человека"
        })

    if room not in data:
        data[room] = {}

    if data[room].get(slot):
        return jsonify({
            "success": False,
            "message": "Слот уже занят"
        })

    data[room][slot] = name

    save_bookings(data)

    logger.warning(
    f"Попытка занять уже занятый слот: аудитория={room}, слот={slot}"
    )

    return jsonify({
        "success": True
    })


@app.route("/api/free", methods=["POST"])
def free_slot():

    req = request.get_json()

    room = req["room"]
    slot = req["slot"]

    logger.info(
    f"Освобождение слота: аудитория={room}, слот={slot}"
 )

    data = load_bookings()

    if room in data and slot in data[room]:
        del data[room][slot]

    save_bookings(data)

    return jsonify({
        "success": True
    })


if __name__ == "__main__":

    logger.info("Сервер запущен")

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )