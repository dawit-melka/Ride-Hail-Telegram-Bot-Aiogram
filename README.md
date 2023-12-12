# Ride-Hail-Telegram-Bot-Aiogram
## Overview

The Ride Hail Telegram Bot is a Python-based Telegram bot built with the Aiogram library. It enables users to hail rides by connecting passengers with nearby drivers. The bot provides a convenient and efficient way for users to request rides and for drivers to accept ride requests.

## Features

    ### Passenger Features:
        - Request a ride by providing location and destination details.
        - Receive notifications when a nearby driver accepts the ride.
        - Start and complete the ride with ease.

    ### Driver Features:
        - Receive ride requests from nearby passengers.
        - Accept or decline ride requests.
        - Provide details about the accepted ride.

## Getting Started
### Prerequisites

    Python (version 3.11.*)
    Aiogram library (version 3.2.0)
    aiosqlite (version 0.19.0)

### Installation

1) Clone the repository:

```bash
git clone https://github.com/dawit-melka/Ride-Hail-Telegram-Bot-Aiogram.git
```


2) Install dependencies:

```bash
pip install -r requirements.txt
```
3) Configure the bot token:

Create a .env file in the project root and add your Telegram bot token:

```env
    TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Usage

1) Run the bot:

    ```bash
    python main.py
    ```

2) Interact with the bot on Telegram:
        - Manage profile
        - Start a ride request as a passenger.
        - Accept or decline ride requests as a driver.
        - Access ride history