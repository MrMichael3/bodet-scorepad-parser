# Bodet Scorepad Message Parser (over TCP) 

This repository contains a Python script and additional files to receive and process messages from a [Bodet Scoreboard](https://www.bodet-sport.com/products/sports-display-control/control-keyboard.html) over a TCP connection. It extracts game-related information such as **match time, score, and penalties**, and logs received messages for future reference. Processed data is stored in a JSON file (`matchfacts.json`) for easy integration with other applications.

The script runs as a TCP server, listening for incoming messages, processing them based on predefined formats, and storing relevant match data. It also ensures message validation using LRC (Longitudinal Redundancy Check).

This script currently **only processes messages relating to floorball**. However, the script can serve as a template for other sports. An extension is possible at any time without great effort.

## Features

- **TCP Server**: Listens for incoming scoreboard data.
- **Real-time Processing**: Updates game status (score, match clock, penalties).
- **Message Validation**: Uses LRC to check data integrity.
- **Logging**: Optionally saves raw messages to a binary log file.
- **Configurable Delays**: Allows fine-tuning of message processing timing.
- **Multi-threading**: Efficiently handles incoming messages and processing tasks in separate threads.

## Configuration

The script reads configuration settings from a `config.ini` file. The following parameters can be customized:

### **Server Settings**
| Parameter | Default Value | Description |
|-----------|--------------|-------------|
| `host` | `0.0.0.0` | IP address to bind the TCP server |
| `port` | `4001` | Port number for incoming connections |

### **Logging Settings**
| Parameter | Default Value | Description |
|-----------|--------------|-------------|
| `MESSAGE_LOG_FILE` | `all_messages_<timestamp>.bin` | Filename for saving raw messages |
| `ENABLE_SAVE_MESSAGES` | `True` | Enables/disables message logging |

### **Processing Settings**
| Parameter | Default Value | Description |
|-----------|--------------|-------------|
| `PROCESS_DELAY_TENTHS` | `50` (5 seconds) | Delay before processing a message (in tenths of a second) |

## How It Works

1. **TCP Server**: The script starts a server on the configured `host` and `port`, waiting for scoreboard data.
2. **Message Reception**: Incoming messages are received, processed, and stored in a queue.
3. **Data Processing**: Messages are validated, interpreted, and converted into game status updates.
4. **Logging**: If enabled, raw messages are saved to a binary log file.
5. **JSON Output**: Processed match data is saved to `matchfacts.json`.

## Prerequisites

- Python 3.6 or higher


## Running the Script

Ensure you have Python 3 installed (and the required dependencies). Then, simply run:

```sh
python bodet-network.py
```



## Addtitonal information for those interested

### Bodet Scorepad setup

make sure to configure your Bodet Scorapad accordingly. 
The [Guide from Bodet](https://static.bodet-sport.com/images/stories/EN/support/Pdfs/manuals/Scorepad/608264-Network%20output%20and%20protocols-Scorepad.pdf) explains how to achive that.

Below is an example network setup for this project.

![Network Diagram](https://github.com/christoph-ernst/bodet-scorepad-parser/blob/main/graphics/network-example.png)

### Testing
If you happen not to have a Scorepad with you all the time you can make use of the `send-test-messages.py` script. 
It will send some data to localhost:4001. By default the test data is read from the file `test-messages.bin`. 
In the script `bodet-network.py`  you also can enable the switch `ENABLE_SAVE_MESSAGES` which will save all messages the script receives from a Bodet Scorepad into a file for later replay.  


### Example Input

A typical message might look like this in hex:
```
0x01 0x7f 0x02 0x47 0x31 0x31 0x80 0x37 0x20 0x34 0x30 0x37 0x20 0x30 0x31 0x20 0x30 0x30 0x31 0x03 0x2d

```

explanation to some of the transmitted frames: 
- 0x01 = Start of Heading (SOH) 
- 0x7f = Address (not further specified by Bodet) 
- 0x02 = Start of text (STX)
- several bytes containing the Message
- 0x03 = End of text (ETX) 
- 0x2d = after ETX an additional byte gets transmited. The
  - Longitudinal Redundancy Check (LRC)

All details about the structure of the messages can be found in the [linked manual from Bodet](https://static.bodet-sport.com/images/stories/EN/support/Pdfs/manuals/Scorepad/608264-Network%20output%20and%20protocols-Scorepad.pdf). 


### JSON File
The current status is saved to `status.json` in the working directory of the script . 
The format looks as follows: 
```json
{
    "score": {
        "home": 4,
        "guest": 1
    },
    "MatchClock": {
        "time": "17:35",
        "period": 2
    },
    "Penalties": {
        "HomeTeam": {
            "Player1": {
                "HPP1-active": 0,
                "HPP1-Time": "00:00"
            },
            "Player2": {
                "HPP2-active": 0,
                "HPP2-Time": "00:00"
            }
        },
        "GuestTeam": {
            "Player1": {
                "GPP1-active": 1,
                "GPP1-Time": "01:29"
            },
            "Player2": {
                "GPP2-active": 0,
                "GPP2-Time": "00:00"
            }
        }
    }
}

```
### integration with OBS

the author of this script is using OBS to embed the extracted data from the JSON file into a live stream. 
The necessary files (config and graphics) are located in the directories named `obs-scene-collection` and `graphics`. 
The following OBS plugins are required to guarantee proper function: 
- [URL/API Source](https://github.com/locaal-ai/obs-urlsource)
- [Advanced Scene Switcher](https://github.com/WarmUpTill/SceneSwitcher)

## what's next
- currently the script meets my needs. a new GUI would be nice though.
  
## License
This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3. See the LICENSE file for details.

