### ### ###
# Version 0.2
# including longitudinal redundancy check (LRC) calculation to maintain integrity 


import socket
import json

def process_data(data):
    messages = []  # List to store extracted messages
    current_message = []  # Temporary list to store the current message bytes
    collecting = False  # Flag to indicate whether to collect bytes

    for byte in data:
        if byte == 0x01:  # Start of a new message
            collecting = False  # Reset collecting (ignore until STX)
        elif byte == 0x02:  # Start of Text (STX)
            collecting = True  # Start collecting bytes for the message
            current_message = []  # Initialize a new message array
        elif byte == 0x03:  # End of Text (ETX)
            if collecting:
                messages.append(current_message)  # Save the collected message
                collecting = False  # Stop collecting
        elif collecting:
            current_message.append(byte)  # Add byte to current message

    return messages

def process_messages_with_number_11(messages):
    filtered_messages = []  # List to store messages with the number 11

    for message in messages:
        if len(message) > 15 and message[1] == 0x31 and message[2] == 0x31:  # Check positions [1] and [2]
            def interpret_byte(byte):
                return 0 if byte == 0x20 else int(chr(byte)) if chr(byte).isdigit() else chr(byte)

            mins_tens = interpret_byte(message[5])
            mins_ones = interpret_byte(message[6])
            mins = (mins_tens * 10) + mins_ones

            secs_tens = interpret_byte(message[7])
            secs_ones = interpret_byte(message[8])
            secs = (secs_tens * 10) + secs_ones

            scorehome_hundreds = interpret_byte(message[9])
            scorehome_tens = interpret_byte(message[10])
            scorehome_ones = interpret_byte(message[11])
            scorehome = (scorehome_hundreds * 100) + (scorehome_tens * 10) + scorehome_ones

            scoreguest_hundreds = interpret_byte(message[12])
            scoreguest_tens = interpret_byte(message[13])
            scoreguest_ones = interpret_byte(message[14])
            scoreguest = (scoreguest_hundreds * 100) + (scoreguest_tens * 10) + scoreguest_ones

            period_byte = message[15]
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
    print(f"status {status}")

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
                        print(f"Message with number 11 ({i + 1}): Mins: {mins}, Secs: {secs}, Score Home: {scorehome}, Score Guest: {scoreguest}, Period: {period}")
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