import time
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
from nltk.sentiment import SentimentIntensityAnalyzer

from colorama import Back, Fore, Style, init

from telethon.errors import ChannelPrivateError, FloodWaitError
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat, User

from utils.logging import *

from jinja2 import Environment, FileSystemLoader

class BatchProcessor:
    def __init__(self, batch_size=1000, cybersecurity_sia=None):
        self.batch = []
        self.batch_size = batch_size
        self.batch_counter = 1
        self.total_messages = 0
        self.cybersecurity_sia = cybersecurity_sia or CybersecuritySentimentAnalyzer()
        self.all_messages_df = pd.DataFrame(columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound', 'Channel Name', 'Affiliated Channel'])

    def add_messages(self, messages, channel_name, affiliated_channel):
        messages_with_info = [
            message + [channel_name, affiliated_channel if affiliated_channel else "Initial Config"]
            for message in messages
        ]
        self.batch.extend(messages_with_info)
        self.total_messages += len(messages)
        if len(self.batch) >= self.batch_size:
            self.save_batch()

    def save_batch(self):
        if self.batch:
            df = pd.DataFrame(self.batch, columns=['Sender ID', 'Date', 'Message', 'Sentiment', 'Compound', 'Channel Name', 'Affiliated Channel'])
            df['Sentiment'] = df['Message'].apply(self.cybersecurity_sia.polarity_scores)
            df['Compound'] = df['Sentiment'].apply(lambda x: x['compound']).astype(float)
            
            batch_filename = f"./batches/telegram_scraped_messages_batch_{self.batch_counter}.csv"
            df.to_csv(batch_filename, index=False)
            print_success(f"Saved batch {self.batch_counter} with {len(self.batch)} messages to {batch_filename}")
            
            # Ensure consistent dtypes
            for col in df.columns:
                if col in self.all_messages_df.columns:
                    df[col] = df[col].astype(self.all_messages_df[col].dtype)
            
            self.all_messages_df = pd.concat([self.all_messages_df, df], ignore_index=True)
            
            self.batch = []
            self.batch_counter += 1

    def generate_final_report(self):
        print_info(f"Generating final report. Total messages: {len(self.all_messages_df)}")
        
        if self.all_messages_df.empty:
            print_warning("No messages to generate report from.")
            return
        
        generate_sentiment_report(self.all_messages_df)

    def finalize(self):
        self.save_batch()  # Save any remaining messages
        self.generate_final_report()

    def __del__(self):
        self.save_batch()  # Save any remaining messages when the object is destroyed

def generate_sentiment_report(df):
    try:
        # Ensure Compound is float
        df['Compound'] = pd.to_numeric(df['Compound'], errors='coerce')

        # Calculate average sentiment scores
        avg_sentiment = pd.DataFrame(df['Sentiment'].dropna().tolist()).mean()

        # Categorize messages based on compound sentiment
        df['Sentiment_Category'] = df['Compound'].apply(lambda x: 
            'High Alert' if x <= -0.5 else
            'Potential Threat' if -0.5 < x <= -0.1 else
            'Neutral' if -0.1 < x < 0.1 else
            'Potentially Positive' if 0.1 <= x < 0.5 else
            'Very Positive'
        )
        sentiment_counts = df['Sentiment_Category'].value_counts()
        total_messages = len(df)

        # Calculate overall sentiment score
        overall_score = avg_sentiment.get('compound', 0) * 100

        # Get top concerning and positive messages
        top_threats = df.nsmallest(5, 'Compound')
        top_positives = df.nlargest(5, 'Compound')

        # Prepare the data for the report
        report_data = {
            'total_messages': total_messages,
            'overall_score': overall_score,
            'interpretation': interpret_overall_score(overall_score),
            'sentiment_counts': sentiment_counts,
            'categories': [
                ('High Alert', 'Severe Threats'),
                ('Potential Threat', 'Potential Threats'),
                ('Neutral', 'Neutral Messages'),
                ('Potentially Positive', 'Potentially Positive'),
                ('Very Positive', 'Strong Security Indicators')
            ],
            'top_threats': top_threats[['Message', 'Compound']],
            'top_positives': top_positives[['Message', 'Compound']],
            'date_generated': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        # Render the HTML report
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('report_template.html')
        html_content = template.render(report_data)

        # Save the report to HTML file
        report_filename = f'./reports/report-{int(time.time())}.html'
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print_success(f"Sentiment analysis report generated and saved to '{report_filename}'")

        # Print the sentiment category counts to the console with colors
        print_info("Sentiment Category Counts:")
        for category, description in report_data['categories']:
            count = sentiment_counts.get(category, 0)
            percentage = (count / total_messages) * 100
            color = get_category_color(category)
            print(f"{color}{category}: {count} ({percentage:.1f}%){Style.RESET_ALL}")

    except Exception as e:
        print_error(f"Error generating sentiment report: {e}")
        print_error(f"DataFrame info:\n{df.info()}")

# HTML template for the report (create this file as `report_template.html` in the same directory)
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment Analysis Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f9;
            color: #333;
        }
        h1 {
            color: #444;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .report-summary {
            margin-bottom: 20px;
        }
        .highlight {
            color: #d9534f;
        }
    </style>
</head>
<body>
    <h1>Sentiment Analysis Report</h1>
    <p><strong>Date Generated:</strong> {{ date_generated }}</p>
    <div class="report-summary">
        <p><strong>Total Messages Analyzed:</strong> {{ total_messages }}</p>
        <p><strong>Overall Sentiment Score:</strong> {{ overall_score }}/100</p>
        <p><strong>Interpretation:</strong> {{ interpretation }}</p>
    </div>

    <h2>Message Sentiment Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Description</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
        </thead>
        <tbody>
            {% for category, description in categories %}
            <tr>
                <td>{{ category }}</td>
                <td>{{ description }}</td>
                <td>{{ sentiment_counts.get(category, 0) }}</td>
                <td>{{ (sentiment_counts.get(category, 0) / total_messages) * 100 }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Top 5 Most Concerning Messages (Potential Threats)</h2>
    <table>
        <thead>
            <tr>
                <th>Message</th>
                <th>Threat Level (Compound Score)</th>
            </tr>
        </thead>
        <tbody>
            {% for row in top_threats.itertuples() %}
            <tr>
                <td>{{ row.Message[:100] }}...</td>
                <td>{{ row.Compound }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Top 5 Most Positive Messages (Potential Security Improvements)</h2>
    <table>
        <thead>
            <tr>
                <th>Message</th>
                <th>Positivity Level (Compound Score)</th>
            </tr>
        </thead>
        <tbody>
            {% for row in top_positives.itertuples() %}
            <tr>
                <td>{{ row.Message[:100] }}...</td>
                <td>{{ row.Compound }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

# Save the HTML template to a file (this is needed for the jinja2 template rendering)
with open('./templates/report_template.html', 'w', encoding='utf-8') as template_file:
    template_file.write(html_template)

# Helper function to interpret overall score
def interpret_overall_score(score):
    if score <= -50:
        return "Critical situation. Numerous severe threats detected. Immediate action required."
    elif -50 < score <= -10:
        return "Concerning situation. Multiple potential threats identified. Heightened vigilance needed."
    elif -10 < score < 10:
        return "Neutral situation. No significant threats or improvements detected. Maintain standard security measures."
    elif 10 <= score < 50:
        return "Positive situation. Some potential security improvements identified. Consider implementing suggested measures."
    else:
        return "Very positive situation. Strong security indicators present. Continue current security practices and look for areas of improvement."

def get_category_color(category):
    color_map = {
        'High Alert': Fore.RED,
        'Potential Threat': Fore.YELLOW,
        'Neutral': Fore.WHITE,
        'Potentially Positive': Fore.LIGHTGREEN_EX,
        'Very Positive': Fore.GREEN
    }
    return color_map.get(category, '')
