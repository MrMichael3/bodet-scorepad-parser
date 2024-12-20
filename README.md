# TCP Message Processor

This repository contains a Python script to process and analyze data transmitted over TCP. The script is designed to parse specific messages and extract details such as scores, time, and game period. It also writes the current status into a JSON file for easy integration with other systems.

## Features

- Captures real-time data from a TCP socket.
- Processes messages to extract:
  - Home team score.
  - Guest team score.
  - Current game time (minutes and seconds).
  - Current game period (including overtime indicated as "E").
- Filters and processes only messages with a specific type identifier (number `11`).
- Outputs the parsed information to the console and a JSON file.

## Prerequisites

- Python 3.6 or higher

## Installation

1. Clone the repository:
```bash
   git clone https://github.com/christoph-ernst/bodet-scorepad-parser.git
   cd bodet-scorepad-parser
```
2. Install any necessary dependencies (if applicable). This script does not require external libraries apart from the standard Python library.
   
## Usage
### Running the Script
1. Start the script:
```bash
python bodet-network.py
```
3. The script will listen for incoming TCP connections on the specified port (default is 4001).
4. Send data to the script over TCP using tools like socat or custom TCP clients. For example:
```bash
socat -u -d -d tcp4:127.0.0.1:4001 <data_source>
```
## Output
- Console Output: Each parsed message will be displayed in the console, showing the home score, guest score, time, and period.
- JSON File: The current status is saved to status.json in the following format:
```json
{
    "score_home": 50,
    "score_guest": 48,
    "time": "12:34",
    "period": 3
}
```

## Configuration
- Host and Port:
Modify the host and port variables in the script to change where the server listens for incoming connections:
```python
host = '0.0.0.0'  # Listen on all interfaces
port = 4001       # Default port
```
- JSON File Location:
The JSON file location can be customized by changing the filename parameter in the write_status_to_json function.

# How It Works
1. The script listens for TCP connections and receives data in chunks.
2. Messages are parsed according to predefined markers and structure.
3. Only messages with type 11 are processed further.
4. Extracted information includes:
  - Scores (home and guest teams).
  - Time (in minutes and seconds).
  - Period (handles regular periods as integers and "E" for overtime).
5. The results are printed to the console and saved to a JSON file.

## Example Input

A typical message might look like this in hex:
```
0x01 0x00 0x02 0x31 0x31 0x30 0x32 0x31 0x35 0x30 0x30 0x30 0x32 0x30 0x30 0x31 0x03
```

- 0x01: Start of message (SOH)
- 0x02: Start of text (STX)
- 0x31 0x31: Message type 11
- 0x30 0x32: Minutes (02)
- 0x31 0x35: Seconds (15)
- 0x30 0x30 0x30: Home score (0)
- 0x30 0x32 0x30: Guest score (20)
- 0x31: Period (1)
- 0x03: End of text (ETX)

## Example Output

Console:
```yaml
Message with number 11 (1): Mins: 2, Secs: 15, Score Home: 0, Score Guest: 20, Period: 1
```` 
JSON File:
```json
{
    "score_home": 0,
    "score_guest": 20,
    "time": "02:15",
    "period": 1
}
```
## License
This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3. See the LICENSE file for details.

