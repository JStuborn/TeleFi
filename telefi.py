import argparse
import asyncio
import json
import multiprocessing
import os
import random
import re
import signal
from datetime import datetime
from functools import partial

import pandas as pd
import nltk

from colorama import Back, Fore, Style, init

from telethon.errors import ChannelPrivateError, FloodWaitError
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat, User

from utils.logging import *
from utils.banner import banner
from utils.chat_util import *
from processors.sia_an import CybersecuritySentimentAnalyzer
from processors.batch import BatchProcessor

# Global variables
current_batch = []
batch_counter = 1

# Ensure NLTK data is downloaded
def ensure_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        print_info("Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('vader_lexicon', quiet=True)

# Load configuration
def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

# Join channel by url
async def join_channel(client, channel_manager, link, max_retries=3):
    cleaned_link = clean_link(link)
    if not cleaned_link:
        print_warning(f"Invalid link format: {link}")
        return False

    retries = 0
    while retries < max_retries:
        try:
            entity = await client.get_entity(cleaned_link)
            entity_name = await get_entity_name(entity)
            
            if isinstance(entity, (Channel, Chat)):
                if entity.username:
                    await client(JoinChannelRequest(entity))
                else:
                    print_warning(f"Cannot join private channel {entity_name} without an invite link")
                    return False
            elif isinstance(entity, User):
                print_info(f"Entity {entity_name} is a user, no need to join")
            else:
                print_warning(f"Unknown entity type for {entity_name}")
                return False
            
            print_success(f"Successfully processed entity: {entity_name}")
            channel_manager.mark_as_joined(cleaned_link)
            return True

        except FloodWaitError as e:
            wait_time = min(e.seconds, 30)
            print_warning(f"FloodWaitError encountered. Waiting for {wait_time} seconds. (Attempt {retries + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
        except Exception as e:
            print_error(f"Failed to process entity {cleaned_link}: {e}")
        
        retries += 1
        await asyncio.sleep(1)

    print_warning(f"Max retries exceeded. Failed to process entity: {cleaned_link}")
    return False

# Manage discovered channels
class ChannelManager:
    def __init__(self):
        self.discovered_channels = set()
        self.joined_channels = set()
        self.processed_channels = set()
        self.channel_affiliations = {}
        self.initial_channels = set()

    def add_channel(self, link, source_channel=None):
        cleaned_link = clean_link(link)
        if cleaned_link and cleaned_link not in self.joined_channels and cleaned_link not in self.processed_channels:
            self.discovered_channels.add(cleaned_link)
            if source_channel:
                self.channel_affiliations[cleaned_link] = source_channel
            else:
                self.initial_channels.add(cleaned_link)  # Mark as initial channel if no source

    def mark_as_joined(self, link):
        cleaned_link = clean_link(link)
        if cleaned_link:
            self.joined_channels.add(cleaned_link)
            self.discovered_channels.discard(cleaned_link)

    def mark_as_processed(self, link):
        cleaned_link = clean_link(link)
        if cleaned_link:
            self.processed_channels.add(cleaned_link)
            self.discovered_channels.discard(cleaned_link)

    def has_unprocessed_channels(self):
        return len(self.discovered_channels) > 0

    def get_next_channel(self):
        if self.discovered_channels:
            return self.discovered_channels.pop()
        return None

    def get_affiliation(self, link):
        cleaned_link = clean_link(link)
        return self.channel_affiliations.get(cleaned_link, None)

    def display_status(self):
        print_subheader("Channel Status")
        print(f"  Channels waiting to be processed: {len(self.discovered_channels)}")
        print(f"  Channels joined: {len(self.joined_channels)}")
        print(f"  Channels processed: {len(self.processed_channels)}")

# keyboard interrupt (Ctrl+C)
def signal_handler(sig, frame):
    global current_batch, batch_counter
    print_warning(f"\nKeyboard interrupt received. Saving current batch and exiting...")
    save_current_batch(current_batch, batch_counter)
    exit(0)

# Save current batch to CSV
def save_current_batch(batch, batch_counter):
    if batch:
        df = pd.DataFrame(batch, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound'])
        
        # If sentiment analysis hasn't been done, do it now
        if df['Sentiment'].isnull().all():
            cybersecurity_sia = CybersecuritySentimentAnalyzer()
            df['Sentiment'] = df['Message'].apply(cybersecurity_sia.polarity_scores)
            df['Compound'] = df['Sentiment'].apply(lambda x: x['compound'] if isinstance(x, dict) else None)
        
        batch_filename = f"./batches/telegram_scraped_messages_batch_{batch_counter}.csv"
        df.to_csv(batch_filename, index=False)
        print_success(f"Saved batch {batch_counter} with {len(batch)} messages to {batch_filename}")
    else:
        print_info(f"No messages in the current batch.")

def analyze_sentiment(cybersecurity_sia, message):
    return cybersecurity_sia.polarity_scores(message)

def process_messages(messages, num_processes=multiprocessing.cpu_count()):
    df = pd.DataFrame(messages, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound'])
    
    cybersecurity_sia = CybersecuritySentimentAnalyzer()
    
    # Parallelize sentiment analysis
    with multiprocessing.Pool(processes=num_processes) as pool:
        partial_analyze = partial(analyze_sentiment, cybersecurity_sia)
        df['Sentiment'] = pool.map(partial_analyze, df['Message'])
    
    df['Compound'] = df['Sentiment'].apply(lambda x: x['compound'])
    
    generate_sentiment_report(df)
    return df

async def get_entity_name(entity):
    if isinstance(entity, User):
        return f"@{entity.username}" if entity.username else f"User({entity.id})"
    elif isinstance(entity, (Channel, Chat)):
        return entity.title or f"Channel({entity.id})"
    else:
        return f"Unknown({type(entity).__name__})"

async def scrape_messages(client, entity, message_limit, keywords, channel_manager, affiliated_channel=None):
    messages = []
    try:
        entity_name = await get_entity_name(entity)
        
        # if isinstance(entity, Channel):
        #     print_warning(f"Skipping channel: {entity_name}")
        #     return messages, entity_name
        
        async for message in client.iter_messages(entity, limit=message_limit):
            if message.text:
                if affiliated_channel:
                    print_info(f"Message from {Fore.CYAN}{Style.BRIGHT}{entity_name}{Style.RESET_ALL}.{Fore.YELLOW}{Style.BRIGHT} <-- {affiliated_channel}{Style.RESET_ALL}: {message.text}")
                else:
                    print_info(f"Message from {Fore.CYAN}{Style.BRIGHT}{entity_name}{Style.RESET_ALL}: {message.text}")
                messages.append([message.sender_id, message.date, message.text, None, None])
                
                # Process t.me links in the message
                links = extract_channel_links(message.text)
                for link in links:
                    channel_manager.add_channel(link, source_channel=entity_name)
            
            await asyncio.sleep(0.1)
    except FloodWaitError as e:
        print_warning(f"FloodWaitError in scrape_messages: {e}")
        await asyncio.sleep(min(e.seconds, 30))
    except Exception as e:
        print_error(f"Error scraping entity {entity_name}: {e}")
    
    return messages, entity_name

async def process_channels(client, channel_manager, message_depth, keywords, batch_processor):
    while channel_manager.has_unprocessed_channels():
        link = channel_manager.get_next_channel()
        print_info('Joining', link)

        affiliated_channel = channel_manager.get_affiliation(link)
        try:
            join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
            if join_success:
                entity = await client.get_entity(link)
                entity_messages, channel_name = await scrape_messages(client, entity, message_depth, keywords, channel_manager, affiliated_channel)
                
                # Add messages to batch processor with channel name and affiliation
                batch_processor.add_messages(entity_messages, channel_name, affiliated_channel)
            else:
                print_warning(f"Skipping entity {link} due to joining failure")
        except Exception as e:
            print_error(f"Failed to process entity {link}: {e}")
        finally:
            channel_manager.mark_as_processed(link)
        
        await asyncio.sleep(1)  # Small delay between processing channels

async def process_single_channel(client, channel_manager, link, message_depth, keywords):
    try:
        join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
        if join_success:
            entity = await client.get_entity(link)
            entity_name = await get_entity_name(entity)
            print_info(f"Scraping messages from: {entity_name}")
            entity_messages = await scrape_messages(client, entity, message_depth, keywords, channel_manager)
            return entity_messages
        else:
            print_warning(f"Skipping entity {link} due to joining failure")
    except Exception as e:
        print_error(f"Failed to process entity {link}: {e}")
    return []

async def retry_with_backoff(coroutine, max_retries=5, base_delay=1, max_delay=60):
    retries = 0
    while True:
        try:
            return await coroutine
        except FloodWaitError as e:
            if retries >= max_retries:
                raise
            delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
            print_warning(f"FloodWaitError encountered. Retrying in {delay:.2f} seconds. (Attempt {retries + 1}/{max_retries})")
            await asyncio.sleep(delay)
            retries += 1
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise

async def run_scraper(config, message_depth, channel_depth):
    await client.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        channel_manager = ChannelManager()
        cybersecurity_sia = CybersecuritySentimentAnalyzer()
        batch_processor = BatchProcessor(cybersecurity_sia=cybersecurity_sia)
        
        # Add initial channels from config
        for link in config['initial_channel_links']:
            channel_manager.add_channel(link)
        
        start_time = datetime.now()
        print_header(f"Scraping started at {start_time}")

        depth = 0
        while channel_manager.has_unprocessed_channels() and depth < channel_depth:
            print_subheader(f"Crawling at depth {depth + 1}/{channel_depth}")
            channel_manager.display_status()
            
            await process_channels(client, channel_manager, message_depth, config['message_keywords'], batch_processor)
            
            depth += 1
            
            # Allow time for rate limiting
            await asyncio.sleep(5)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print_header(f"Scraping completed at {end_time}")
        print_info(f"Total duration: {duration}")
        print_info(f"Total messages scraped: {batch_processor.total_messages}")
        print_info(f"Total channels processed: {len(channel_manager.processed_channels)}")

        # Finalize batch processing and generate report
        batch_processor.finalize()

    except Exception as e:
        print_error(f"An error occurred during scraping: {e}")
    finally:
        await client.disconnect()

async def process_all_channels(client, channel_manager, message_depth, keywords):
    all_messages = []
    channels_to_process = list(channel_manager.discovered_channels)
    
    for link in channels_to_process:
        try:
            join_success = await retry_with_backoff(join_channel(client, channel_manager, link))
            if join_success:
                entity = await client.get_entity(link)
                entity_name = await get_entity_name(entity)
                print_info(f"Scraping messages from: {entity_name}")
                entity_messages = await scrape_messages(client, entity, message_depth, keywords, channel_manager)
                all_messages.extend(entity_messages)
                
                # Process newly discovered channels
                new_channels = channel_manager.get_new_channels()
                for new_link in new_channels:
                    channel_manager.add_channel(new_link)
            else:
                print_warning(f"Skipping entity {link} due to joining failure")
        except Exception as e:
            print_error(f"Failed to process entity {link}: {e}")
        
        await asyncio.sleep(1)  # Small delay between processing channels
    
    return all_messages

async def process_discovered_channels(client, channel_manager, message_depth, keywords, max_channels_per_depth):
    channels_processed = 0
    while channel_manager.discovered_channels and channels_processed < max_channels_per_depth:
        link = channel_manager.get_next_channel()
        if await join_channel(client, channel_manager, link):
            try:
                channel = await client.get_entity(link)
                print_info(f"Scraping messages from newly discovered channel: {channel.title}")
                await scrape_messages(client, channel, message_depth, keywords, channel_manager)
                channels_processed += 1
            except Exception as e:
                print_error(f"Failed to scrape newly discovered channel {link}: {e}")
        
        await asyncio.sleep(2)

if __name__ == "__main__":
    banner()
    ensure_nltk_data()

    parser = argparse.ArgumentParser(description='Telegram Content Crawler')
    parser.add_argument('--config', type=str, default='./config/config.json', help='Path to the configuration file')
    parser.add_argument('--message-depth', type=int, default=40, help='Number of messages to crawl per channel')
    parser.add_argument('--channel-depth', type=int, default=2, help='Depth of channel crawling')
    args = parser.parse_args()

    config = load_config(args.config)
    if config is None:
        exit(f"Config file '{args.config}' not found. Please rename '[/config/config.json.example] to [config.json] and enter correct details.")


    account = config.get('account')
    API_ID = account.get('api_id')
    API_HASH = account.get('api_hash')
    PHONE_NUMBER = account.get('phone_number')

    if not API_ID or not API_HASH or not PHONE_NUMBER:
        exit("API credentials are missing. Please provide them either as command-line arguments or in the script. (Line 664-666)")

    client = TelegramClient('TeleFi', API_ID, API_HASH)

    with client:
        client.loop.run_until_complete(run_scraper(config, args.message_depth, args.channel_depth))
