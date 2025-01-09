# TCP Message Processor for Bodet Scorepad

This repository contains a Python script and additional files to process and analyze data transmitted over TCP from the [Bodet Scorepad](https://www.bodet-sport.com/products/sports-display-control/control-keyboard.html). 
The script is designed to parse specific messages and extract details such as scores, time, and game period. It also writes the current status into a JSON file for easy integration with other systems.

## Features

Currently the script *only listens for data related to floorball*. It can serve as a template for other sports.   

- Captures real-time data from a TCP socket.
- Filters and processes only messages with a few specific type identifiers (number `11, 12 and 13`).
- Message `11` contains the following data: 
  - Home team score.
  - Guest team score.
  - Current game time (minutes and seconds).
  - Current game period (including overtime indicated as "E").
- Message `12 and 13` contain data regarding penalties (which are not parsed yet). 
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
3. The script will listen for incoming TCP connections on the specified port (default is `4001`).
4. make sure to configure your Bodet Scorepad accordingly. The [Guide from Bodet](https://static.bodet-sport.com/images/stories/EN/support/Pdfs/manuals/Scorepad/608264-Network%20output%20and%20protocols-Scorepad.pdf) explains how to achive that.

### Testing
If you happen not to have a Scorepad with you all the time you can make use of the `send-test-messages.py` script. 
It will send some data to localhost:4001. By default the test data is read from the file `test-messages.bin`. 
In the script `bodet-network.py`  you also can enable the switch `ENABLE_SAVE_MESSAGES` which will save all messages the script receives from a Bodet Scorepad into a file for later replay.  

## Output
- Console Output: Each parsed message will be displayed in the console, showing the home score, guest score, time, and period.
Console:
```yaml
Time: 03:14 | Home Score:4 | Guest Score: 2
```` 
- JSON File: The current status is saved to `status.json` in the following format:
```json
{
    "score_home": 5,
    "score_guest": 4,
    "time": "12:34",
    "period": 3
}
```

## Configuration
- Host and Port:
Modify the `host` and `port` variables in the script to change where the server listens for incoming connections:
```python
host = '0.0.0.0'  # Listen on all interfaces
port = 4001       # Default port
```
- JSON File Location:
The JSON file location can be customized by changing the filename parameter in the `write_status_to_json` function.

# How It Works
1. The script listens for TCP connections and receives data in chunks.
2. Messages are parsed according to predefined markers and structure.
3. and LRC check is calculated over each received message to ensure integrity. 
4. Only messages with type `11, 12 and 13` are processed further.
   
   - message #11, #12 and #13 are related to floorball. For other message types see the [Guide from Bodet](https://static.bodet-sport.com/images/stories/EN/support/Pdfs/manuals/Scorepad/608264-Network%20output%20and%20protocols-Scorepad.pdf)
  
5. Extracted information includes:
   
   - Scores (home and guest teams).
   - Time (in minutes and seconds).
   - Period (handles regular periods as integers and "E" for overtime).
    
6. The results are printed to the console and saved to a JSON file.

## Example Input

A typical message might look like this in hex:
```
0x01 0x7f 0x02 0x47 0x31 0x31 0x80 0x37 0x20 0x34 0x30 0x37 0x20 0x30 0x31 0x20 0x30 0x30 0x31 0x03 0x2d

```

explanation to some of the messages: 
- Start of Heading (SOH)  = 01 hexadecimal
- Start of text (STX) = 02 hexadecimal
- End of text (ETX) = 03 hexadecimal
- after ETX an additional byte gets transmited. The
  - Longitudinal Redundancy Check (LRC)

All details about the structure of the messages can be found in the above linked manual from Bodet. 

## what's next
- implement additional message types
   -  Message #12: Home team players penalty
   -  Message #13: Guest team players penalty

## License
This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3. See the LICENSE file for details.

