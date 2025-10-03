import threading
import queue
import socket
import time
import configparser
import requests


# Load configuration from file
config = configparser.ConfigParser()
config.read("config.ini")

# Server config
host = config.get("Server", "host", fallback="0.0.0.0")
port = config.getint("Server", "port", fallback=4001)
log_filename_base = config.get("Logging", "MESSAGE_LOG_FILE", fallback="all_messages")
timestamp = time.strftime('%Y%m%d_%H%M%S')
MESSAGE_LOG_FILE = f"{log_filename_base}_{timestamp}.bin"
ENABLE_SAVE_MESSAGES = config.getboolean("Logging", "ENABLE_SAVE_MESSAGES", fallback=True)
PROCESS_DELAY_TENTHS = config.getint("Processing", "PROCESS_DELAY_TENTHS", fallback=50)

# vMix config
USE_VMIX = config.getboolean("vMix", "enabled", fallback=False)
VMIX_HOST = config.get("vMix", "host", fallback="localhost")
VMIX_PORT = config.getint("vMix", "port", fallback=8088)
VMIX_INPUT = config.get("vMix", "input", fallback="Scoreboard")

FIELD_HOME_SCORE = config.get("vMixFields", "home_score", fallback="TxtHomeScore.Text")
FIELD_AWAY_SCORE = config.get("vMixFields", "away_score", fallback="TxtAwayScore.Text")

# Zeit-Felder
FIELD_MIN_TENS = config.get("vMixFields", "min_tens", fallback="TxtClockTimeM10.Text")
FIELD_MIN_ONES = config.get("vMixFields", "min_ones", fallback="TxtClockTimeM01.Text")
FIELD_COLON    = config.get("vMixFields", "colon", fallback="TxtClockTimeT.Text")
FIELD_SEC_TENS = config.get("vMixFields", "sec_tens", fallback="TxtClockTimeS10.Text")
FIELD_SEC_ONES = config.get("vMixFields", "sec_ones", fallback="TxtClockTimeS01.Text")

# Drittel-Feld
FIELD_PERIOD = config.get("vMixFields", "period", fallback="TxtClockPeriod.Text")

# Heim Strafen
FIELD_HOME_PEN1_M10 = config.get("vMixFields", "home_pen1_m10", fallback="TxtHomePen1M10.Text")
FIELD_HOME_PEN1_M01 = config.get("vMixFields", "home_pen1_m01", fallback="TxtHomePen1M01.Text")
FIELD_HOME_PEN1_COLON = config.get("vMixFields", "home_pen1_colon", fallback="TxtHomePen1T.Text")
FIELD_HOME_PEN1_S10 = config.get("vMixFields", "home_pen1_s10", fallback="TxtHomePen1S10.Text")
FIELD_HOME_PEN1_S01 = config.get("vMixFields", "home_pen1_s01", fallback="TxtHomePen1S01.Text")

FIELD_HOME_PEN2_M10 = config.get("vMixFields", "home_pen2_m10", fallback="TxtHomePen2M10.Text")
FIELD_HOME_PEN2_M01 = config.get("vMixFields", "home_pen2_m01", fallback="TxtHomePen2M01.Text")
FIELD_HOME_PEN2_COLON = config.get("vMixFields", "home_pen2_colon", fallback="TxtHomePen2T.Text")
FIELD_HOME_PEN2_S10 = config.get("vMixFields", "home_pen2_s10", fallback="TxtHomePen2S10.Text")
FIELD_HOME_PEN2_S01 = config.get("vMixFields", "home_pen2_s01", fallback="TxtHomePen2S01.Text")

# Gast Strafen
FIELD_AWAY_PEN1_M10 = config.get("vMixFields", "away_pen1_m10", fallback="TxtAwayPen1M10.Text")
FIELD_AWAY_PEN1_M01 = config.get("vMixFields", "away_pen1_m01", fallback="TxtAwayPen1M01.Text")
FIELD_AWAY_PEN1_COLON = config.get("vMixFields", "away_pen1_colon", fallback="TxtAwayPen1T.Text")
FIELD_AWAY_PEN1_S10 = config.get("vMixFields", "away_pen1_s10", fallback="TxtAwayPen1S10.Text")
FIELD_AWAY_PEN1_S01 = config.get("vMixFields", "away_pen1_s01", fallback="TxtAwayPen1S01.Text")

FIELD_AWAY_PEN2_M10 = config.get("vMixFields", "away_pen2_m10", fallback="TxtAwayPen2M10.Text")
FIELD_AWAY_PEN2_M01 = config.get("vMixFields", "away_pen2_m01", fallback="TxtAwayPen2M01.Text")
FIELD_AWAY_PEN2_COLON = config.get("vMixFields", "away_pen2_colon", fallback="TxtAwayPen2T.Text")
FIELD_AWAY_PEN2_S10 = config.get("vMixFields", "away_pen2_s10", fallback="TxtAwayPen2S10.Text")
FIELD_AWAY_PEN2_S01 = config.get("vMixFields", "away_pen2_s01", fallback="TxtAwayPen2S01.Text")

# Hintergrund Farbe für Strafen
FIELD_HOME_PEN1_FILL = config.get("vMixFields", "home_pen1_fill", fallback="RectHomePen1.FillColor")
FIELD_HOME_PEN2_FILL = config.get("vMixFields", "home_pen2_fill", fallback="RectHomePen2.FillColor")
FIELD_AWAY_PEN1_FILL = config.get("vMixFields", "away_pen1_fill", fallback="RectAwayPen1.FillColor")
FIELD_AWAY_PEN2_FILL = config.get("vMixFields", "away_pen2_fill", fallback="RectAwayPen2.FillColor")
COLOR_ACTIVE = "#FFF000FF"     # Gelb, 100% sichtbar
COLOR_INACTIVE = "#FFF00000"   # Transparent




# Global game state
status = {
    "score": {"home": 0, "guest": 0},
    "MatchClock": {"time": "00:00", "period": 0},
    "Penalties": {
        "HomeTeam": {
            "Player1": {"HPP1-active": 0, "HPP1-Time": "00:00"},
            "Player2": {"HPP2-active": 0, "HPP2-Time": "00:00"}
        },
        "GuestTeam": {
            "Player1": {"GPP1-active": 0, "GPP1-Time": "00:00"},
            "Player2": {"GPP2-active": 0, "GPP2-Time": "00:00"}
        }
    }
}

message_queue = queue.PriorityQueue()

if PROCESS_DELAY_TENTHS < 1:
    PROCESS_DELAY_TENTHS = 1

# === vMix API Updater ===
def update_vmix_field(field_name, value):
    try:
        function = "SetText"

        # SetColor verwenden, wenn es sich um ein Shape oder farbänderbares Element handelt
        if "FillColor" in field_name or "Fill" in field_name:
            function = "SetColor"

        response = requests.get(
            f"http://{VMIX_HOST}:{VMIX_PORT}/api/",
            params={
                "Function": function,
                "Input": VMIX_INPUT,
                "SelectedName": field_name,
                "Value": value
            },
            timeout=0.3
        )

        if response.status_code != 200:
            print(f"[vMix] Fehler bei {field_name}: HTTP {response.status_code}")
    except Exception as e:
        print(f"[vMix] Fehler: {e}")



def update_vmix_clock_and_score(time_str, period, home_score, guest_score):
    try:
        # Zerlege Zeit in einzelne Ziffern
        minutes, seconds = time_str.split(":")
        min_tens = minutes[0]
        min_ones = minutes[1]
        sec_tens = seconds[0]
        sec_ones = seconds[1]

        # Uhrzeit-Felder aktualisieren
        update_vmix_field(FIELD_MIN_TENS, min_tens)
        update_vmix_field(FIELD_MIN_ONES, min_ones)
        update_vmix_field(FIELD_COLON, ":")
        update_vmix_field(FIELD_SEC_TENS, sec_tens)
        update_vmix_field(FIELD_SEC_ONES, sec_ones)

        # Score aktualisieren
        update_vmix_field(FIELD_HOME_SCORE, str(home_score))
        update_vmix_field(FIELD_AWAY_SCORE, str(guest_score))

        # Drittel aktualisieren
        update_vmix_field(FIELD_PERIOD, str(period))

    except Exception as e:
        print("[vMix] Fehler beim Update der Felder:", e)

def update_vmix_penalties():
    try:
        def set_penalty_time(active, time_str, m10, m01, colon, s10, s01):
            if active and time_str and ":" in time_str:
                minutes, seconds = time_str.split(":")
                update_vmix_field(m10, minutes[0])
                update_vmix_field(m01, minutes[1])
                update_vmix_field(colon, ":")
                update_vmix_field(s10, seconds[0])
                update_vmix_field(s01, seconds[1])
            else:
                # Alles leeren
                update_vmix_field(m10, "")
                update_vmix_field(m01, "")
                update_vmix_field(colon, "")
                update_vmix_field(s10, "")
                update_vmix_field(s01, "")

        home_p1 = status["Penalties"]["HomeTeam"]["Player1"]
        home_p2 = status["Penalties"]["HomeTeam"]["Player2"]
        guest_p1 = status["Penalties"]["GuestTeam"]["Player1"]
        guest_p2 = status["Penalties"]["GuestTeam"]["Player2"]

        # Heimteam Strafen
        set_penalty_time(home_p1["HPP1-active"], home_p1["HPP1-Time"],
                         FIELD_HOME_PEN1_M10, FIELD_HOME_PEN1_M01, FIELD_HOME_PEN1_COLON, FIELD_HOME_PEN1_S10, FIELD_HOME_PEN1_S01)
        set_penalty_color(home_p1["HPP1-active"], FIELD_HOME_PEN1_FILL)

        set_penalty_time(home_p2["HPP2-active"], home_p2["HPP2-Time"],
                         FIELD_HOME_PEN2_M10, FIELD_HOME_PEN2_M01, FIELD_HOME_PEN2_COLON, FIELD_HOME_PEN2_S10, FIELD_HOME_PEN2_S01)
        set_penalty_color(home_p2["HPP2-active"], FIELD_HOME_PEN2_FILL)

        # Gastteam Strafen
        set_penalty_time(guest_p1["GPP1-active"], guest_p1["GPP1-Time"],
                         FIELD_AWAY_PEN1_M10, FIELD_AWAY_PEN1_M01, FIELD_AWAY_PEN1_COLON, FIELD_AWAY_PEN1_S10, FIELD_AWAY_PEN1_S01)
        set_penalty_color(guest_p1["GPP1-active"], FIELD_AWAY_PEN1_FILL)

        set_penalty_time(guest_p2["GPP2-active"], guest_p2["GPP2-Time"],
                         FIELD_AWAY_PEN2_M10, FIELD_AWAY_PEN2_M01, FIELD_AWAY_PEN2_COLON, FIELD_AWAY_PEN2_S10, FIELD_AWAY_PEN2_S01)
        set_penalty_color(guest_p2["GPP2-active"], FIELD_AWAY_PEN2_FILL)

    except Exception as e:
        print("[vMix] Fehler beim Update der Strafen:", e)

def set_penalty_color(active, fill_field):
    color = COLOR_ACTIVE if active else COLOR_INACTIVE  
    update_vmix_field(fill_field, color)



# === Utility ===
def calculate_lrc(frame):
    lrc = 0
    for byte in frame[1:]:
        lrc ^= byte
    lrc &= 0x7F
    if lrc < 32:
        lrc += 0x20
    return lrc

def validate_lrc(frame):
    if len(frame) < 3:
        return False
    calculated = calculate_lrc(frame[:-1])
    received = frame[-1]
    return calculated == received

def interpret_byte(byte):
    return 0 if byte == 0x20 else int(chr(byte)) if chr(byte).isdigit() else chr(byte)

def determine_penalty_code(value):
    return 0 if value <= 128 else 1


def process_data(data):
    messages = []
    current_message = []
    collecting = False

    for i, byte in enumerate(data):
        if byte == 0x01 and not collecting:
            collecting = True
            current_message = [byte]
        elif collecting:
            current_message.append(byte)
            if byte == 0x03 and i + 1 < len(data):
                current_message.append(data[i + 1])
                messages.append(current_message)
                collecting = False
    return messages

def save_message_to_file(message):
    if ENABLE_SAVE_MESSAGES:
        with open(MESSAGE_LOG_FILE, "ab") as file:
            file.write(bytes(message))

def process_message_by_type(message):
    global status

    if not validate_lrc(message):
        print("LRC validation failed:", [f"{byte:02X}" for byte in message])
        return None

    msg_type = (message[4], message[5])

    if msg_type == (0x31, 0x31):  # Zeit und Tore
        mins = interpret_byte(message[8]) * 10 + interpret_byte(message[9])
        secs = interpret_byte(message[10]) * 10 + interpret_byte(message[11])

        scorehome = interpret_byte(message[12]) * 100 + interpret_byte(message[13]) * 10 + interpret_byte(message[14])
        scoreguest = interpret_byte(message[15]) * 100 + interpret_byte(message[16]) * 10 + interpret_byte(message[17])
        period = interpret_byte(message[18]) if message[18] != 0x20 else 0

        status["score"]["home"] = scorehome
        status["score"]["guest"] = scoreguest
        status["MatchClock"]["time"] = f"{mins:02}:{secs:02}"
        status["MatchClock"]["period"] = period

        if USE_VMIX:
            update_vmix_clock_and_score(
                status["MatchClock"]["time"],
                status["MatchClock"]["period"],
                status["score"]["home"],
                status["score"]["guest"]
    )
            print("Home Penalties:", status["Penalties"]["HomeTeam"])
            print("Guest Penalties:", status["Penalties"]["GuestTeam"])

            update_vmix_penalties()


        return f"[Scorepad] ⏱ {status['MatchClock']['time']} | 🏒 Drittel {period} | 🏠 {scorehome} : {scoreguest}"

    elif msg_type == (0x31, 0x32):  # Message 12 (Home penalties)
        h1_code = determine_penalty_code(ord(interpret_byte(message[7])))
        h1_time = f"{interpret_byte(message[8]):02}:{interpret_byte(message[9]) * 10 + interpret_byte(message[10]):02}"

        h2_code = determine_penalty_code(ord(interpret_byte(message[11])))
        h2_time = f"{interpret_byte(message[12]):02}:{interpret_byte(message[13]) * 10 + interpret_byte(message[14]):02}"

        status["Penalties"]["HomeTeam"]["Player1"] = {"HPP1-active": h1_code, "HPP1-Time": h1_time}
        status["Penalties"]["HomeTeam"]["Player2"] = {"HPP2-active": h2_code, "HPP2-Time": h2_time}
        
        update_vmix_penalties()
        return "Updated Home Penalties"

    elif msg_type == (0x31, 0x33):  # Message 13 (Guest penalties)
        g1_code = determine_penalty_code(ord(interpret_byte(message[7])))
        g1_time = f"{interpret_byte(message[8]):02}:{interpret_byte(message[9]) * 10 + interpret_byte(message[10]):02}"

        g2_code = determine_penalty_code(ord(interpret_byte(message[11])))
        g2_time = f"{interpret_byte(message[12]):02}:{interpret_byte(message[13]) * 10 + interpret_byte(message[14]):02}"

        status["Penalties"]["GuestTeam"]["Player1"] = {"GPP1-active": g1_code, "GPP1-Time": g1_time}
        status["Penalties"]["GuestTeam"]["Player2"] = {"GPP2-active": g2_code, "GPP2-Time": g2_time}
        
        update_vmix_penalties()
        return "Updated Guest Penalties"

    return None

# === Threads ===
def message_receiver(server_socket):
    print(f"Listening for TCP connections on {host}:{port}...")
    if ENABLE_SAVE_MESSAGES:
        print(f"Logging to: {MESSAGE_LOG_FILE}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        with client_socket:
            data = client_socket.recv(1024)
            while data:
                messages = process_data(data)
                for message in messages:
                    save_message_to_file(message)
                    delivery_time = time.time()
                    message_queue.put((delivery_time, message))
                data = client_socket.recv(1024)

def message_processor():
    while True:
        try:
            _, message = message_queue.get(timeout=1)

            #current_time = time.time()
            #delivery_time, message = message_queue.get(timeout=1)
            #delivery_time += PROCESS_DELAY_TENTHS / 10.0

            #while current_time < delivery_time:
             #   time.sleep(0.05)
              #  current_time = time.time()

            result = process_message_by_type(message)
            if result:
                print(result)
        except queue.Empty:
            continue

# === Main ===
def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)

    threading.Thread(target=message_receiver, args=(server_socket,), daemon=True).start()
    threading.Thread(target=message_processor, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server_socket.close()

if __name__ == "__main__":
    start_tcp_server()
