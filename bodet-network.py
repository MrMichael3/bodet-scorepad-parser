import socket
import json

def calculate_lrc(frame):
    lrc = 0
    # XOR all bytes between Address (after SOH) and ETX (inclusive)
    for byte in frame[1:]:
        lrc ^= byte
        # print(f"byte: {hex(byte)} lrc: {hex(lrc)}") 

    # print(f"LRC before AND: {hex(lrc)}")
    lrc &= 0x7F
    # print(f"LRC after  AND: {hex(lrc)}")
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

def process_messages_with_number_11(messages):
    filtered_messages = []  # List to store messages with the number 11

    for message in messages:
        if not validate_lrc(message):
            print("LRC validation failed for message:", [f"0x{byte:02X}" for byte in message])
            continue    

        if len(message) > 17:
            if message[4] == 0x31 and message[5] == 0x31:  # Check positions [3] and [4]
                def interpret_byte(byte):
                    return 0 if byte == 0x20 else int(chr(byte)) if chr(byte).isdigit() else chr(byte)

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

                filtered_messages.append((message, mins, secs, scorehome, scoreguest, period))  # Add the message with mins and secs
            

        return filtered_messages

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
            print(f"Connection from {client_address}")

            with client_socket:
                data = client_socket.recv(1024)  # Receive up to 1024 bytes of data
                while data:
                    all_messages = process_data(data)

                    # Filter messages with number 11
                    messages_with_11 = process_messages_with_number_11(all_messages)

                    # Print the filtered messages and write to JSON
                    for i, (msg, mins, secs, scorehome, scoreguest, period) in enumerate(messages_with_11):
                        print(f"Message with number 11 ({i + 1}): Mins: {mins}, Secs: {secs}, Score Home: {scorehome}, Score Guest: {scoreguest}, Period: {period}, Raw Message: {[f'0x{byte:02X}' for byte in msg]}")
                        write_status_to_json(scorehome, scoreguest, mins, secs, period)

                    data = client_socket.recv(1024)  # Receive more data

    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()

# Example usage
host = '0.0.0.0'  # Listen on all interfaces
port = 4001  # Replace with your desired port
start_tcp_server(host, port)