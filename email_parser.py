#!/usr/bin/env python3

import csv
import os
import sys
import re
import time
from typing import List, Tuple, Set
from datetime import datetime
from pathlib import Path
import argparse
import tldextract
import html.parser
from difflib import SequenceMatcher

class EmailHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.emails = set()
        self.email_pattern = re.compile(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""", re.IGNORECASE)
        self.in_pre = False
        self.current_pre_content = []

    def handle_starttag(self, tag, attrs):
        # Check all attributes for email addresses
        for attr, value in attrs:
            if value:
                found_emails = self.email_pattern.findall(value)
                self.emails.update(found_emails)
        
        # Track when we enter a pre tag - debug use
        if tag == 'pre':
            self.in_pre = True

    def handle_endtag(self, tag):
        # When leaving a pre tag, process its content
        if tag == 'pre':
            self.in_pre = False
            full_content = ''.join(self.current_pre_content)
            found_emails = self.email_pattern.findall(full_content)
            self.emails.update(found_emails)
            self.current_pre_content = []

    def handle_data(self, data):
        # If we're in a pre tag, gather content
        if self.in_pre:
            self.current_pre_content.append(data)
        
        # checking for emails
        found_emails = self.email_pattern.findall(data)
        self.emails.update(found_emails)

class EmailParser:
    def __init__(self, similarity_threshold: float = 90.0, exclude_list: str = None):
        self.unique_emails = set()
        self.batch_size = 20
        self.current_batch = []
        self.output_file = None
        self.email_pattern = re.compile(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""")
        self.all_emails = []
        self.similarity_threshold = similarity_threshold
        self.processed_count = 0
        self.excluded_emails = set()
        
        if exclude_list:
            self.load_excluded_emails(exclude_list)

    def load_excluded_emails(self, exclude_file: str):
        """Load emails to exclude from the given CSV file."""
        try:
            with open(exclude_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # Skip empty rows
                        self.excluded_emails.add(row[0].lower())
        except Exception as e:
            print(f"Warning: Could not load exclude list: {str(e)}")

    def process_batch(self, source_file: str):
        if not self.current_batch:
            return
    
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for email in self.current_batch:
                # Skip if email is in exclude list
                if email.lower() in self.excluded_emails:
                    self.processed_count += 1
                    continue
                    
                similar_email, similarity = self.find_similar_email(email)
                writer.writerow([
                    email,
                    self.calculate_malformation_probability(email),
                    similar_email if similarity >= self.similarity_threshold else "",
                    f"{similarity:.2f}" if similarity >= self.similarity_threshold else "",
                    str(source_file)
                ])
                self.all_emails.append(email)
                self.processed_count += 1
                print(f"\rEmails processed: {self.processed_count} | Unique Emails: {len(self.unique_emails)}", end='', flush=True)
        self.current_batch = []

    def find_similar_email(self, email: str) -> Tuple[str, float]:
        highest_similarity = 0
        most_similar_email = ""
        
        # Compare with all previously processed emails
        for existing_email in self.all_emails:
            if existing_email != email:
                similarity = self.calculate_similarity(email, existing_email)
                if similarity > highest_similarity and similarity >= self.similarity_threshold:
                    highest_similarity = similarity
                    most_similar_email = existing_email
        
        # Check current batch
        for batch_email in self.current_batch:
            if batch_email != email:
                similarity = self.calculate_similarity(email, batch_email)
                if similarity > highest_similarity and similarity >= self.similarity_threshold:
                    highest_similarity = similarity
                    most_similar_email = batch_email
        
        return most_similar_email, highest_similarity

    def process_path(self, path: str):
        self.setup_output_file()
        path_obj = Path(path)
    
        print("\nStarting email parsing process...")
        print("Progress will update after each batch")
        print("-" * 50)
    
        if path_obj.is_file():
            print(f"Processing: {path_obj}")
            self.parse_file(path_obj)
            if self.current_batch:
                self.process_batch(path_obj)
        elif path_obj.is_dir():
            # Count files by type
            csv_files = list(path_obj.rglob('*.csv'))
            html_files = list(path_obj.rglob('*.html'))
            htm_files = list(path_obj.rglob('*.htm'))
            
            # Count subfolders
            folders = set()
            for pattern in ['*.csv', '*.html', '*.htm']:
                for file_path in path_obj.rglob(pattern):
                    folders.add(str(file_path.parent))
            folder_count = len(folders) - 1 if len(folders) > 0 else 0
            
            total_html = len(html_files) + len(htm_files)
            print(f"Found {len(csv_files) + total_html} files to process:")
            print(f" {len(csv_files)} CSV files")
            print(f" {total_html} HTML files")
            print(f" {folder_count} folders")
            print("")
            
            # Process CSV files
            for file_path in csv_files:
                self.parse_file(file_path)
                if self.current_batch:
                    self.process_batch(file_path)
            
            # Process HTML files
            for file_pattern in ['*.html', '*.htm']:
                for file_path in path_obj.rglob(file_pattern):
                    self.parse_file(file_path)
                    if self.current_batch:
                        self.process_batch(file_path)
            
            # Final output
            print("\n" + "-" * 50)
            print(f"Processing complete. Found {len(self.unique_emails)} unique email addresses.")
            print(f"Results saved to: {self.output_file}")

    def parse_file(self, file_path: Path):
        try:
            if file_path.suffix.lower() in ['.csv']:
                self.parse_csv_file(file_path)
            elif file_path.suffix.lower() in ['.html', '.htm']:
                self.parse_html_file(file_path)
            else:
                print(f"Unsupported file type: {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    def parse_csv_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    for field in row:
                        found_emails = self.email_pattern.findall(field)
                        for email in found_emails:
                            # Count every email as found before checking
                            self.processed_count += 1
                            if email.lower() not in self.unique_emails:
                                self.unique_emails.add(email.lower())
                                self.current_batch.append(email)
                                
                                if len(self.current_batch) >= self.batch_size:
                                    self.process_batch(file_path)
        except Exception as e:
            print(f"Error processing CSV file {file_path}: {str(e)}")

    def parse_html_file(self, file_path: Path):
        try:
            parser = EmailHTMLParser()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parser.feed(content)
                
            for email in parser.emails:
                # Count every email as found before checking
                self.processed_count += 1
                # Only add to batch if unique
                if email.lower() not in self.unique_emails:
                    self.unique_emails.add(email.lower())
                    self.current_batch.append(email)
                    
                    if len(self.current_batch) >= self.batch_size:
                        self.process_batch(file_path)
        except Exception as e:
            print(f"Error processing HTML file {file_path}: {str(e)}")

    def setup_output_file(self):
        """Setup the output CSV file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = Path(f"EMAIL_ADDRESSES_{timestamp}.csv")
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Email Address', 'Malformation Probability', 
                           'Similar Email', 'Similarity Percentage', 'Source File'])

 
    def calculate_similarity(self, email1: str, email2: str) -> float:
        return SequenceMatcher(None, email1.lower(), email2.lower()).ratio() * 100

    def calculate_malformation_probability(self, email: str) -> float:
        probability = 0.0
        
        # Check TLD
        ext = tldextract.extract(email)
        if not ext.suffix:
            probability += 0.4
        elif len(ext.suffix) > 6:  # Unusual TLD length
            probability += 0.2
            
        # Check for unusual number of subdomains (by 'dot' count)
        domain_parts = email.split('@')[1].split('.')
        if len(domain_parts) > 4:
            probability += 0.1
            
        # Check for unusual character count for "addressee"
        local_part = email.split('@')[0]
        if len(local_part) > 64:
            probability += 0.1
        
        # Check for consecutive special characters (... _+_++_)
        if re.search(r'[._%+-]{2,}', local_part):
            probability += 0.1
            
        # probability cannot exceed 1.0
        return min(probability, 1.0)


def main():
    parser = argparse.ArgumentParser(description='Extract and analyze email addresses from files.')
    parser.add_argument('path', help='Path to file or directory to process')
    parser.add_argument('-s', '--similarity', type=float, default=90.0,
                      help='Similarity threshold percentage (default: 90.0)')
    parser.add_argument('-e', '--exclude', type=str,
                      help='Path to CSV file containing emails to exclude')
    
    args = parser.parse_args()
    
    email_parser = EmailParser(
        similarity_threshold=args.similarity,
        exclude_list=args.exclude
    )
    email_parser.process_path(args.path)

if __name__ == '__main__':
    main()