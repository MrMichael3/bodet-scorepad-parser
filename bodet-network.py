import socket
import json
import time

# Global Configuration
host = '0.0.0.0'  # Listen on all interfaces
port = 4001  # Replace with your desired port
timestamp = time.strftime("%Y%m%d_%H%M%S")
MESSAGE_LOG_FILE = f"all_messages_{timestamp}.bin" # Global filename generated once at script startup
ENABLE_SAVE_MESSAGES = False # Enable (True) or disable (False) saving messages to a file

time = 0
scorehome = 0
scoreguest= 0
period = 0

homeplayer1_penalty_code = 0
homeplayer1_penalty_time = 0
homeplayer2_penalty_code = 0
homeplayer2_penalty_time = 0

guestplayer1_penalty_code = 0
guestplayer1_penalty_time = 0
guestplayer2_penalty_code = 0
guestplayer2_penalty_time = 0

def calculate_lrc(frame):
    lrc = 0
    # XOR all bytes between Address (after SOH) and ETX (inclusive)
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
    # print(f"calculated_lrc: {hex(calculated_lrc)} received_lrc: {hex(received_lrc)}") 
    return calculated_lrc == received_lrc

def process_data(data):
    messages = []  # List to store extracted messages
    current_message = []  # Temporary list to store the current message bytes
    collecting = False  # Flag to indicate whether to collect bytes

    for i, byte in enumerate(data):
        if byte == 0x01 and not collecting:  # Start of a new message (SOH)
            collecting = True
            current_message = [byte]  # Include SOH in the message
        elif collecting:
            current_message.append(byte)
            if byte == 0x03 and i + 1 < len(data):  # End of Text (ETX) followed by LRC
                current_message.append(data[i + 1])  # Include LRC
                messages.append(current_message)
                collecting = False  # Stop collecting

    return messages

def save_message_to_file(message):
    if ENABLE_SAVE_MESSAGES:
        with open(MESSAGE_LOG_FILE, "ab") as file:
            file.write(bytes(message))


def determine_penalty_code(value):
    # Returns:
    #     int: Returns 0 if the value is 128 or smaller, and 1 if it is 129 or larger.
    if value <= 128:
        return 0
    else:
        return 1


def process_message_by_type(message):
    global time
    global scorehome
    global scoreguest
    global period

    global homeplayer1_penalty_code
    global homeplayer1_penalty_time
    global homeplayer2_penalty_code
    global homeplayer2_penalty_time

    global guestplayer1_penalty_code
    global guestplayer1_penalty_time
    global guestplayer2_penalty_code
    global guestplayer2_penalty_time 

    # print(f"Full Message: {message}")
    def interpret_byte(byte):
        return 0 if byte == 0x20 else int(chr(byte)) if chr(byte).isdigit() else chr(byte)

    if not validate_lrc(message):
        print("LRC validation failed for message:", [f"0x{byte:02X}" for byte in message])
        return None

    
    msg_type = (message[4], message[5])
    # print(f"message Type: {msg_type}")
    if msg_type == (0x31, 0x31):  # Message type 11
        mins_tens = interpret_byte(message[8])
        mins_ones = interpret_byte(message[9])
        mins = (mins_tens * 10) + mins_ones

        secs_tens = interpret_byte(message[10])
        secs_ones = interpret_byte(message[11])
        secs = (secs_tens * 10) + secs_ones
        time = f"{mins:02}:{secs:02}"

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
        # print(f"Period: {period} | Time: {mins:02}:{secs:02} | Home Score:{scorehome} | Guest Score: {scoreguest} ")
        return (message, '11')

    elif msg_type == (0x31, 0x32):  # Message type 12
        # print(f"message Type: {msg_type})")
        # homeplayer1_penalty_code = 
        homeplayer1_penalty_code = determine_penalty_code(ord(interpret_byte(message[7])))
        # print(f"home Player 1 - Penalty Code: {hex(ord(homeplayer1_penalty_code))}") 
        homeplayer1_penalty_mins = interpret_byte(message[8])
        homeplayer1_penalty_secs_tens = interpret_byte(message[9])
        homeplayer1_penalty_secs_ones = interpret_byte(message[10])
        homeplayer1_penalty_secs = (homeplayer1_penalty_secs_tens * 10) + homeplayer1_penalty_secs_ones
        homeplayer1_penalty_time = f"{homeplayer1_penalty_mins:02}:{homeplayer1_penalty_secs:02}" 

        # homeplayer2_penalty_code = ord(interpret_byte(message[11]))
        homeplayer2_penalty_code = determine_penalty_code(ord(interpret_byte(message[11])))
        # print(f"home Player 1 - Penalty Code: {hex(ord(homeplayer1_penalty_code))}") 
        homeplayer2_penalty_mins = interpret_byte(message[12])
        homeplayer2_penalty_secs_tens = interpret_byte(message[13])
        homeplayer2_penalty_secs_ones = interpret_byte(message[14])
        homeplayer2_penalty_secs = (homeplayer2_penalty_secs_tens * 10) + homeplayer2_penalty_secs_ones
        homeplayer2_penalty_time = f"{homeplayer2_penalty_mins:02}:{homeplayer2_penalty_secs:02}" 

        # print(f"{homeplayer1_penalty_min}:{homeplayer1_penalty_secs}")
        #homeplayer2_penalty = interpret_byte(message[11])
        return (message, '12')

    elif msg_type == (0x31, 0x33):  # Message type 13
        # print(f"message Type: {msg_type})")
        guestplayer1_penalty_code = ord(interpret_byte(message[7]))
        guestplayer1_penalty_code = determine_penalty_code(ord(interpret_byte(message[7])))
        # print(f"Guest Player 1 - Penalty Code: {hex(ord(guestplayer1_penalty_code))}") 
        guestplayer1_penalty_mins = interpret_byte(message[8])
        guestplayer1_penalty_secs_tens = interpret_byte(message[9])
        guestplayer1_penalty_secs_ones = interpret_byte(message[10])
        guestplayer1_penalty_secs = (guestplayer1_penalty_secs_tens * 10) + guestplayer1_penalty_secs_ones
        guestplayer1_penalty_time = f"{guestplayer1_penalty_mins:02}:{guestplayer1_penalty_secs:02}" 

        # guestplayer2_penalty_code = ord(interpret_byte(message[11]))
        guestplayer2_penalty_code = determine_penalty_code(ord(interpret_byte(message[11])))
        # print(f"Guest Player 1 - Penalty Code: {hex(ord(guestplayer2_penalty_code))}") 
        guestplayer2_penalty_mins = interpret_byte(message[12])
        guestplayer2_penalty_secs_tens = interpret_byte(message[13])
        guestplayer2_penalty_secs_ones = interpret_byte(message[14])
        guestplayer2_penalty_secs = (guestplayer2_penalty_secs_tens * 10) + guestplayer2_penalty_secs_ones
        guestplayer2_penalty_time = f"{guestplayer2_penalty_mins:02}:{guestplayer2_penalty_secs:02}" 
        return (message, '13')
    return None

def write_status_to_json(filename="matchfacts.json"):
    global time
    global scorehome
    global scoreguest
    global period 

    global homeplayer1_penalty_code
    global homeplayer1_penalty_time
    global homeplayer2_penalty_code
    global homeplayer2_penalty_time

    global guestplayer1_penalty_code
    global guestplayer1_penalty_time
    global guestplayer2_penalty_code
    global guestplayer2_penalty_time 

    status = {
        "score": {
            "home": scorehome,
            "guest": scoreguest
        },
        "MatchClock" : {
            "time": time,
            "period": period
        },
        "Penalties" : {
            "HomeTeam" : {
                "Player1" : {
                    "HPP1-active" : homeplayer1_penalty_code,
                    "HPP1-Time": homeplayer1_penalty_time
                },
                "Player2" : {
                    "HPP2-active" : homeplayer2_penalty_code,
                    "HPP2-Time": homeplayer2_penalty_time
                }
            },
            "GuestTeam" : {
                "Player1" : {
                    "GPP1-active" : guestplayer1_penalty_code,
                    "GPP1-Time": guestplayer1_penalty_time
                },
                "Player2" : {
                    "GPP2-active" : guestplayer2_penalty_code,
                    "GPP2-Time": guestplayer2_penalty_time
                }
            }
        }
    }
    with open(filename, "w") as json_file:
        json.dump(status, json_file, indent=4)

def start_tcp_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Listening for TCP connections on {host}:{port}...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # print(f"Connection from {client_address}")
            with client_socket:
                data = client_socket.recv(1024)  # Receive up to 1024 bytes of data
                while data:
                    all_messages = process_data(data)
                    save_message_to_file(data)

                    for message in all_messages:
                        result = process_message_by_type(message)
                        consolemessage11 = consolemessage12 = consolemessage13 = " "
                        if result:
                            if result[1] == '11':
                                consolemessage11 = (f"Period: {period} | Time: {time} | Home Score:{scorehome} | Guest Score: {scoreguest} ")
                            elif result[1] == '12':
                                if homeplayer1_penalty_code:
                                    consolemessage12 = f"HomeTeam Penalty 1 Code: {homeplayer1_penalty_code} | Time: {homeplayer1_penalty_time} "
                                if homeplayer2_penalty_code:
                                    consolemessage12 = consolemessage12 + f"HomeTeam Penalty 2 Code: {homeplayer2_penalty_code} | Time: {homeplayer2_penalty_time} "   
                            elif result[1] == '13':
                                if guestplayer1_penalty_code:
                                    consolemessage13 = f"GuestTeam Penalty 1 Code: {guestplayer1_penalty_code} | Time: {guestplayer1_penalty_time} "
                                if guestplayer2_penalty_code:
                                    consolemessage13 = consolemessage13 + f"GuestTeam Penalty 2 Code: {guestplayer2_penalty_code} | Time: {guestplayer2_penalty_time} "   
                            else: 
                                print(f"*** *** *** Another (unprocessed) message!!! ")
                                print(f"Message {result[1]}: {result[2]}, Raw: {[f'0x{byte:02X}' for byte in result[0]]}")


                            consolmessage = consolemessage11 + consolemessage12 + consolemessage13
                            print(consolmessage)
                            write_status_to_json()

                    data = client_socket.recv(1024)  # Receive more data

    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()



# Example usage
start_tcp_server(host, port)