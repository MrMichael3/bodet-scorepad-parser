import socket
import json
import time


# Global filename generated once at script startup
timestamp = time.strftime("%Y%m%d_%H%M%S")
MESSAGE_LOG_FILE = f"all_messages_{timestamp}.bin"

# Enable or disable saving messages to a file
ENABLE_SAVE_MESSAGES = True

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


def process_message_by_type(message):
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
        print(f"Time: {mins:02}:{secs:02} | Home Score:{scorehome} | Guest Score: {scoreguest} ")
        return (message, '11', mins, secs, scorehome, scoreguest, period)

    elif msg_type == (0x31, 0x32):  # Message type 12
        # print(f"message Type: {msg_type})")
        return (message, '12', 'Type 12 Message Processed')

    elif msg_type == (0x31, 0x33):  # Message type 13
        # print(f"message Type: {msg_type})")
        return (message, '13', 'Type 13 Message Processed')

    return None

def write_status_to_json(scorehome, scoreguest, mins, secs, period, filename="matchfacts.json"):
    status = {
        "score_home": scorehome,
        "score_guest": scoreguest,
        "time": f"{mins:02}:{secs:02}",
        "period": period
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
                        if result:
                            if result[1] == '11':
                                # print(f"Message 11: Mins: {result[2]}, Secs: {result[3]}, Score Home: {result[4]}, Score Guest: {result[5]}, Period: {result[6]}, Raw: {[f'0x{byte:02X}' for byte in result[0]]}")
                                write_status_to_json(result[4], result[5], result[2], result[3], result[6])
                            elif result[1] == '12':
                                pass
                                # print(f"*** *** *** Message 12!!!!")
                                # print(f"Message {result[1]}: {result[2]}, Raw: {[f'0x{byte:02X}' for byte in result[0]]}")                            
                            elif result[1] == '13':
                                pass
                                # print(f"*** *** *** Message 13!!!!")
                                # print(f"Message {result[1]}: {result[2]}, Raw: {[f'0x{byte:02X}' for byte in result[0]]}")
                            
                            else: 
                                print(f"*** *** *** Another (unprocessed) message!!! ")
                                print(f"Message {result[1]}: {result[2]}, Raw: {[f'0x{byte:02X}' for byte in result[0]]}")

                    data = client_socket.recv(1024)  # Receive more data

    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()

# Example usage
host = '0.0.0.0'  # Listen on all interfaces
port = 4001  # Replace with your desired port
start_tcp_server(host, port)