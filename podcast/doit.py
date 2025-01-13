#!/usr/bin/env python3

import requests
import xml.etree.ElementTree as ET
import csv
import re
import argparse
from datetime import datetime
import html
import os
import speech_recognition as sr
from pydub import AudioSegment

class PodcastEpisode:
    def __init__(self, title, description, pub_date, audio_url):
        self.title = title
        self.description = self.strip_html_tags(html.unescape(description))
        self.pub_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
        self.audio_url = audio_url

    def __repr__(self):
        return f"PodcastEpisode(title={self.title}, pub_date={self.pub_date}, audio_url={self.audio_url})"

    @staticmethod
    def strip_html_tags(text):
        """Remove HTML tags from a string."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

def fetch_rss_feed(url):
    """Fetches the podcast RSS feed from the provided URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request was unsuccessful
    return response.content

def parse_rss_feed(xml_data):
    """Parses the RSS feed and returns a list of PodcastEpisode objects."""
    root = ET.fromstring(xml_data)
    episodes = []
    
    # Parse the XML data
    for item in root.findall('.//item'):
        title = item.find('title').text
        description = item.find('description').text
        pub_date = item.find('pubDate').text
        audio_url = item.find('enclosure').attrib.get('url')

        episode = PodcastEpisode(title, description, pub_date, audio_url)
        episodes.append(episode)
    
    return episodes

def read_latest_pub_date_from_csv(filename):
    """Reads the latest publication date from the CSV file."""
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            latest_date = None
            for row in reader:
                pub_date = datetime.strptime(row[2], '%a, %d %b %Y %H:%M:%S %z')
                if latest_date is None or pub_date > latest_date:
                    latest_date = pub_date
            return latest_date
    except FileNotFoundError:
        return None

def save_episodes_to_csv(episodes, filename):
    """Saves the list of PodcastEpisode objects to a CSV file."""
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['Title', 'Description', 'Publication Date', 'Audio URL'])
        for episode in episodes:
            writer.writerow([episode.title, episode.description, episode.pub_date.strftime('%a, %d %b %Y %H:%M:%S %z'), episode.audio_url])

def extract_date_components(pub_date):
    """Extracts the year, month, and day-of-month from the publication date."""
    year = pub_date.strftime('%Y')
    month = pub_date.strftime('%b')
    day_of_month = pub_date.strftime('%d')
    return [year, month, day_of_month]

def convert_speech_to_text(audio_filename, text_filename):
    """Converts speech in an audio file to text and saves it to a text file."""
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_mp3(audio_filename)
    audio.export(audio_filename.replace('.mp3', '.wav'), format='wav')
    with sr.AudioFile(audio_filename.replace('.mp3', '.wav')) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        with open(text_filename, 'w') as text_file:
            text_file.write(text)

def main():
    # Define a dictionary mapping pre-defined aliases to podcast URLs
    podcast_aliases = {
        'pk': 'https://rss.podplaystudio.com/2790.xml',
        'another_podcast': 'http://anotherexample.com/rss'
    }

    parser = argparse.ArgumentParser(description="Fetch and save podcast episodes from an RSS feed.")
    parser.add_argument('rss_feed_url', help="The URL of the podcast RSS feed. Or a pre-defined alias of a podcast.")
    parser.add_argument('--output', default='podcast_episodes.csv', help="The name of the output CSV file (default: podcast_episodes.csv).")
    parser.add_argument('--nosave', action='store_true', help="If set, do not save the audio files of new episodes.")
    
    args = parser.parse_args()

    if (args.output):
        csv_file = args.output
    
    rss_feed_url = args.rss_feed_url
    alias = None
    # Check if the provided RSS feed URL is an alias and update if it is
    if args.rss_feed_url in podcast_aliases:
        # Alias used
        rss_feed_url = podcast_aliases.get(args.rss_feed_url)
        alias = args.rss_feed_url
        csv_file = os.path.join(alias, alias + ".csv")
    else:
        # url used                                   
        if not args.output:
            print("Use of raw url requires --output arg. Use url alias or supply --output.")
            return 1
        
        csv_file = args.output

    # Create directory for the alias if it doesn't exist
    op_dir = os.path.dirname(csv_file)
    if not os.path.exists(op_dir):
        os.makedirs(op_dir)

    print(f"Fetching podcast episodes from: {rss_feed_url}")

    # Fetch and parse the RSS feed
    rss_feed_data = fetch_rss_feed(rss_feed_url)
    episodes = parse_rss_feed(rss_feed_data)
    
    # Read the latest publication date from the CSV file
    latest_pub_date = read_latest_pub_date_from_csv(csv_file)

    if latest_pub_date:
        print(f"Latest episode in {csv_file} file was published on: {latest_pub_date.strftime('%a, %d %b %Y %H:%M:%S %z')}")
    else:
        print("No episodes found in the CSV file.")
    
    # Filter episodes to only include those newer than the latest episode in the CSV file
    new_episodes = [episode for episode in episodes if latest_pub_date is None or episode.pub_date > latest_pub_date]
    
    # Save new episodes to the CSV file
    new_episodes.sort(key=lambda episode: episode.pub_date)
    save_episodes_to_csv(new_episodes, csv_file)

    # Print out the number of new episodes
    print(f"Number of new episodes: {len(new_episodes)}")

    if args.nosave:
        pass
    else:
        # Save the associated audio files to the output directory
        for episode in new_episodes:            
            audio_filename = os.path.join(op_dir, *extract_date_components(episode.pub_date),
                                          f"{episode.pub_date.strftime('%Y%m%d_%H%M%S')}_{re.sub(r'[^a-zA-Z0-9]', '_', episode.title)}.mp3")
            print(f"Saving audio file for episode to {audio_filename}...", end='', flush=True)

            # Ensure the path to audio_filename exists
            audio_dir = os.path.dirname(audio_filename)
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)

            # Check if the mp3 file already exists
            if os.path.exists(audio_filename):
                print(f"Audio file {audio_filename} already exists. Skipping download.")
                continue

            # Fetch and save
            audio_response = requests.get(episode.audio_url)
            audio_response.raise_for_status() 
            with open(audio_filename, 'wb') as audio_file:
                audio_file.write(audio_response.content)
            print(f" done")

            # Convert speech to text and save to a text file
            text_filename = audio_filename.replace('.mp3', '.txt')
            print(f"Converting audio to text and saving to {text_filename}...", end='', flush=True)
            convert_speech_to_text(audio_filename, text_filename)
            print(f" done")

    # Print out the titles of the new episodes
    for episode in new_episodes:
        print(episode.title)

if __name__ == "__main__":
    main()