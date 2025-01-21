import threading
import queue
import socket
import time
import json

# Global Configuration
host = '0.0.0.0'
port = 4001
MESSAGE_LOG_FILE = f"all_messages_{time.strftime('%Y%m%d_%H%M%S')}.bin"
ENABLE_SAVE_MESSAGES = True
PROCESS_DELAY_TENTHS = 35  # Delay in tenths of a second (e.g., 50 = 5 seconds)

# Queue for sharing messages between threads
message_queue = queue.PriorityQueue()

# make sure no division by zero or negativ PROCESS_DELAY_TENTHS is configured
if PROCESS_DELAY_TENTHS < 1:
    PROCESS_DELAY_TENTHS = 1

# Global game status
status = {
    "score": {"home": 0, "guest": 0},
    "MatchClock": {"time": "00:00", "period": 0},
    "Penalties": {
        "HomeTeam": {"Player1": {"HPP1-active": 0, "HPP1-Time": "00:00"},
                     "Player2": {"HPP2-active": 0, "HPP2-Time": "00:00"}},
        "GuestTeam": {"Player1": {"GPP1-active": 0, "GPP1-Time": "00:00"},
                      "Player2": {"GPP2-active": 0, "GPP2-Time": "00:00"}}
    }
}

# Utility Functions
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
    calculated_lrc = calculate_lrc(frame[:-1])
    received_lrc = frame[-1]
    return calculated_lrc == received_lrc

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

def determine_penalty_code(value):
    return 0 if value <= 128 else 1

def write_status_to_json(filename="matchfacts.json"):
    with open(filename, "w") as json_file:
        json.dump(status, json_file, indent=4)

def process_message_by_type(message):
    global status

    def interpret_byte(byte):
        return 0 if byte == 0x20 else int(chr(byte)) if chr(byte).isdigit() else chr(byte)

    if not validate_lrc(message):
        print("LRC validation failed for message:", [f"0x{byte:02X}" for byte in message])
        return None

    msg_type = (message[4], message[5])

    if msg_type == (0x31, 0x31):  # Message type 11
        mins_tens = interpret_byte(message[8])
        mins_ones = interpret_byte(message[9])
        mins = (mins_tens * 10) + mins_ones

        secs_tens = interpret_byte(message[10])
        secs_ones = interpret_byte(message[11])
        secs = (secs_tens * 10) + secs_ones

        scorehome_hundreds = interpret_byte(message[12])
        scorehome_tens = interpret_byte(message[13])
        scorehome_ones = interpret_byte(message[14])
        scorehome = (scorehome_hundreds * 100) + (scorehome_tens * 10) + scorehome_ones

        scoreguest_hundreds = interpret_byte(message[15])
        scoreguest_tens = interpret_byte(message[16])
        scoreguest_ones = interpret_byte(message[17])
        scoreguest = (scoreguest_hundreds * 100) + (scoreguest_tens * 10) + scoreguest_ones

        period_byte = message[18]
        period = interpret_byte(period_byte) if period_byte != 0x20 else 0

        status["score"]["home"] = scorehome
        status["score"]["guest"] = scoreguest
        status["MatchClock"]["time"] = f"{mins:02}:{secs:02}"
        status["MatchClock"]["period"] = period
        return_message = "Updated Match Status | " + str(status["MatchClock"]["period"]) + " | " + status["MatchClock"]["time"]
        return return_message

    elif msg_type == (0x31, 0x32):  # Message type 12
        homeplayer1_penalty_code = determine_penalty_code(ord(interpret_byte(message[7])))
        homeplayer1_penalty_mins = interpret_byte(message[8])
        homeplayer1_penalty_secs_tens = interpret_byte(message[9])
        homeplayer1_penalty_secs_ones = interpret_byte(message[10])
        homeplayer1_penalty_secs = (homeplayer1_penalty_secs_tens * 10) + homeplayer1_penalty_secs_ones
        homeplayer1_penalty_time = f"{homeplayer1_penalty_mins:02}:{homeplayer1_penalty_secs:02}"

        status["Penalties"]["HomeTeam"]["Player1"] = {
            "HPP1-active": homeplayer1_penalty_code,
            "HPP1-Time": homeplayer1_penalty_time
        }
        return "Updated Home Penalties"

    elif msg_type == (0x31, 0x33):  # Message type 13
        guestplayer1_penalty_code = determine_penalty_code(ord(interpret_byte(message[7])))
        guestplayer1_penalty_mins = interpret_byte(message[8])
        guestplayer1_penalty_secs_tens = interpret_byte(message[9])
        guestplayer1_penalty_secs_ones = interpret_byte(message[10])
        guestplayer1_penalty_secs = (guestplayer1_penalty_secs_tens * 10) + guestplayer1_penalty_secs_ones
        guestplayer1_penalty_time = f"{guestplayer1_penalty_mins:02}:{guestplayer1_penalty_secs:02}"

        status["Penalties"]["GuestTeam"]["Player1"] = {
            "GPP1-active": guestplayer1_penalty_code,
            "GPP1-Time": guestplayer1_penalty_time
        }
        return "Updated Guest Penalties"

    return None

# Thread 1: Message Receiver
def message_receiver(server_socket):
    print(f"Listening for TCP connections on {host}:{port}...")
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            with client_socket:
                data = client_socket.recv(1024)
                while data:
                    messages = process_data(data)
                    for message in messages:
                        delivery_time = time.time() + (PROCESS_DELAY_TENTHS / 10)
                        message_queue.put((delivery_time, message))  # PriorityQueue stores by time
                    data = client_socket.recv(1024)
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()

# Thread 2: Message Processor
def message_processor():
    while True:
        try:
            current_time = time.time()
            delivery_time, message = message_queue.get(timeout=1)

            while current_time < delivery_time:
                print(f"Current Time: {current_time}")
                print(f"Deliver Time: {delivery_time}")
                time.sleep(0.05)
                current_time = time.time()

#            if delay < PROCESS_DELAY_TENTHS / 10.0:
#                time.sleep((PROCESS_DELAY_TENTHS / 10.0) - delay)

            result = process_message_by_type(message)
            if result:
                print(result)
                write_status_to_json()
        except queue.Empty:
            continue

# Start TCP server and threads
def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)

    receiver_thread = threading.Thread(target=message_receiver, args=(server_socket,))
    processor_thread = threading.Thread(target=message_processor)

    receiver_thread.start()
    processor_thread.start()

    receiver_thread.join()
    processor_thread.join()

if __name__ == "__main__":
    start_tcp_server()
''