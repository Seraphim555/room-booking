from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json
import os
import logging

app = Flask(__name__)
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
    return """
    <h1>Система бронирования аудиторий</h1>

    <h2>Экраны аудиторий</h2>

    <ul>
        <li><a href='/room/101'>Аудитория 101</a></li>
        <li><a href='/room/102'>Аудитория 102</a></li>
        <li><a href='/room/103'>Аудитория 103</a></li>
    </ul>

    <h2>Панели бронирования</h2>

    <ul>
        <li><a href='/admin/101'>Бронирование 101</a></li>
        <li><a href='/admin/102'>Бронирование 102</a></li>
        <li><a href='/admin/103'>Бронирование 103</a></li>
    </ul>
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
    app.run(host="0.0.0.0", port=5000)