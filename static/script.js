async function loadRoomData() {

    const response = await fetch(`/api/room/${ROOM_ID}`);
    const data = await response.json();

    const timeElement = document.getElementById("time");
    const dateElement = document.getElementById("date");

    if (timeElement) {
        timeElement.innerText = data.time;
    }

    if (dateElement) {
        dateElement.innerText = data.date;
    }

    const statusCard = document.getElementById("status-card");
    const statusText = document.getElementById("status-text");

    if (statusCard && statusText) {

        if (data.current_booking) {
            statusCard.className = "status-card busy";
            statusText.innerText = `Занята: ${data.current_booking}`;
        } else {
            statusCard.className = "status-card free";
            statusText.innerText = "Свободна";
        }
    }

    document.querySelectorAll(".slot").forEach(slotElement => {

        if (!slotElement.id.startsWith("slot-")) {
            return;
        }

        const slotTime = slotElement.id.replace("slot-", "");

        const statusElement = slotElement.querySelector(".slot-status");

        if (!statusElement) {
            return;
        }

        const booking = data.slots[slotTime];

        slotElement.classList.remove("free", "busy");

        if (booking) {
            slotElement.classList.add("busy");
            statusElement.innerText = booking;
        } else {
            slotElement.classList.add("free");
            statusElement.innerText = "Свободно";
        }
    });

    setupAdminButtons(data);
}


function setupAdminButtons(data) {

    document.querySelectorAll(".admin-slot").forEach(button => {

        const slot = button.dataset.slot;

        const booking = data.slots[slot];

        button.classList.remove("free", "busy");

        if (booking) {
            button.classList.add("busy");
            button.innerText = `${slot} | ${booking}`;
        } else {
            button.classList.add("free");
            button.innerText = slot;
        }

        button.onclick = async () => {

            const nameInput = document.getElementById("name");

            const name = nameInput
                ? nameInput.value.trim()
                : "";

            try {

                if (booking) {

                    const response = await fetch("/api/free", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            room: ROOM_ID,
                            slot: slot
                        })
                    });

                    console.log("Слот освобожден", await response.json());

                } else {

                    if (!name) {
                        alert("Введите имя");
                        return;
                    }

                    const response = await fetch("/api/book", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            room: ROOM_ID,
                            slot: slot,
                            name: name
                        })
                    });

                    const result = await response.json();

                    console.log("Бронирование:", result);

                    if (!result.success) {
                        alert(result.message);
                    }
                }

                loadRoomData();

            } catch (error) {

                console.error("Ошибка:", error);

                alert("Ошибка соединения с сервером");
            }
        };
    });
}


loadRoomData();

setInterval(loadRoomData, 1000);