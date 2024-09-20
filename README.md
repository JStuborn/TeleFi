# TeleFi

*Please note that this project is still under development and may not be suitable for production use. Contributions and feedback are welcome!*

TeleFi (also known as TeleHunter) is a powerful tool for scraping and analyzing Telegram chat messages. It recursively collects data from Telegram channels and chats, processes sentiment analysis on the gathered text, and provides detailed reports for cybersecurity threat assessments.

---

## Features

- **Telegram Message Scraping**: Scrape messages from various Telegram chats, groups, and channels (with support to skip channels as needed).
- **Sentiment Analysis**: Analyze messages using the `SentimentIntensityAnalyzer` from the NLTK library to gauge sentiment, helping to identify potential cybersecurity threats.
- **Batch Processing**: Efficiently processes large volumes of messages in batches and saves them to CSV files for further analysis.
- **Recursive Link Extraction**: Automatically extracts `t.me` links within messages and follows them to gather more data from related channels or groups.
- **Sentiment Reporting**: Generates a comprehensive HTML report (`report-EPOCH.html`) based on message sentiment, categorizing messages into various threat levels such as High Alert, Potential Threat, Neutral, etc.
- **Concurrency Support**: Supports asynchronous scraping of Telegram messages to handle large datasets without overwhelming resources.
- **FloodWait Handling**: Detects and handles Telegram's flood wait limits, ensuring safe and compliant scraping.

---

## Installation

### Prerequisites

Before using TeleFi, ensure you have the following installed:

- Python 3.7 or later
- `pip` for installing dependencies

### Required Libraries

You can install the required Python libraries by running:

```bash
pip install -r requirements.txt
```

## Setup and Configuration

### Telegram API Credentials:

You’ll need a Telegram API ID and Hash, which you can obtain by registering your application at the Telegram Developer Portal.
Configuring Your API Credentials:

Place your API_ID, API_HASH, and PHONE_NUMBER in the `config.json` file or input them when prompted.

**YOU CAN GET YOUR API DETAILS AT https://my.telegram.org/apps**

Example `config.json`:
```json
{
    "initial_channel_links": [
      "https://t.me/",
      "https://t.me/",
      "https://t.me/"
    ],
    "message_keywords": ["hack", "carding", "malware", "exploit", "cracking"],
    "batch_size": 100,
    "account": {
      "api_id": 0,
      "api_hash": "YOUR_HASH",
      "phone_number": "YOUR_PHONE"
    }
}
```
## Usage
### Basic Usage
1. Run the Scraper:
To start scraping a Telegram entity (chat, group, or channel), run the following:
    ```
    python telefi.py --message-depth <message_limit> --channel-depth <depth>
    ```
2. Sentiment Analysis and Reporting:
After scraping, the tool will automatically perform sentiment analysis on the collected messages and generate an HTML report with the results. You can find the report in the root directory with a name in the format report-EPOCH.html.

3. Recursive Scraping:
TeleFi automatically identifies t.me links within messages, scrapes affiliated channels or groups, and performs sentiment analysis recursively.

### Example Output
TeleFi generates a well-organized sentiment report with the following key sections:
- Overall Sentiment Score: A general sentiment score based on all the messages.
- Message Breakdown by Category: Messages are categorized as High Alert, Potential Threat, Neutral, Potentially Positive, or Very Positive.
- Top Concerning Messages: A list of messages with the most negative sentiment.
- Top Positive Messages: A list of messages with the most positive sentiment.
