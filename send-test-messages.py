import socket
import time

# Constants for message parsing
SOH = b'\x01'  # Start of Header
STX = b'\x02'  # Start of Text
ETX = b'\x03'  # End of Text
LRC_LENGTH = 1  # Length of LRC byte

# File containing binary data
FILE_PATH = 'all_messages_20250112_175610.bin'
SERVER_ADDRESS = ('localhost', 4001)
INTERVAL = 500     # Interval between sending messages (in milliseconds)
                    # 1000 means 1 second / 100 means 0.1 sec

def extract_messages_from_file(file_path):
    """Extracts messages from the binary file."""
    messages = []
    with open(file_path, 'rb') as file:
        data = file.read()
    
    start = 0
    # start 2. Drittel
    start = 77000
    while start < len(data):
        soh_index = data.find(SOH, start)
        if soh_index == -1:
            break
        
        etx_index = data.find(ETX, soh_index)
        if etx_index == -1:
            break
        
        # Extract the message including SOH to ETX and LRC
        message_end = etx_index + 1 + LRC_LENGTH
        if message_end > len(data):
            break
        
        message = data[soh_index:message_end]
        messages.append(message)
        
        start = message_end
    
    return messages

def should_send_message(message):
#    """Check if the fourth and fifth bytes match valid message types."""
#    return len(message) > 5 and message[4] == 0x31 and message[5] == 0x31
    return (len(message) > 5 and 
            ((message[4] == 0x31 and message[5] == 0x31) or
             (message[4] == 0x31 and message[5] == 0x32) or
             (message[4] == 0x31 and message[5] == 0x33)))

def send_message_to_server(message, server_address):
    """Sends a single message to the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(server_address)
            s.sendall(message)
            print(f"Sent message: {message.hex()}")
        except ConnectionError as e:
            print(f"Failed to send message: {e}")

def main():
    messages = extract_messages_from_file(FILE_PATH)
    print(f"Extracted {len(messages)} messages.")
    
    for i, message in enumerate(messages):
#        if should_send_message(message):
            print(f"Sending message {i+1}/{len(messages)}")
            send_message_to_server(message, SERVER_ADDRESS)
            time.sleep(INTERVAL / 1000)  # Convert milliseconds to seconds
#        else:
#            print(f"Skipped message {i+1}/{len(messages)}: Does not meet criteria.")
#            print(f"Message: {message.hex()}")

if __name__ == '__main__':
    main()
