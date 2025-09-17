#!/usr/bin/env python3
"""
Image and Video Organizer Script

This script organizes media files from various sources (WhatsApp, regular folders)
into a structured output directory with date filtering and deduplication.

Usage:

cp config.ini.example config.ini
vim config.ini  # Edit paths as needed
python gather_images.py --from-date YYYY-MM-DD [--to-date YYYY-MM-DD]
"""

import os
import sys
import argparse
import configparser
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import List, Dict
import re


class GatherImages:
    """Main class for organizing media files."""

    def __init__(self, config_path: str):
        """Initialize the organizer with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # File extensions for different media types (however we warn for anything else than jpg and mp4)
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}

        # Hash storage for duplicate detection
        self.file_hashes: Dict[str, str] = {}

        # Statistics
        self.stats = {
            'processed': 0,
            'duplicates': 0,
            'whatsapp_images': 0,
            'whatsapp_videos': 0,
            'regular_images': 0,
            'regular_videos': 0,
            'warnings': 0
        }

        # Warnings
        self.warnings: List[str] = []

    def warn(self, message: str):
        """Log a warning message."""
        self.stats['warnings'] += 1
        self.warnings.append(message)

    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""

    def is_duplicate(self, file_path: str) -> bool:
        """Check if file is a duplicate based on hash."""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return False

        if file_hash in self.file_hashes:
            print(f"Duplicate found: {file_path} (original: {self.file_hashes[file_hash]})")
            self.stats['duplicates'] += 1
            return True

        self.file_hashes[file_hash] = file_path
        return False

    def clean_filename(self, filename: str) -> str:
        """Clean filename according to rules."""
        name, ext = os.path.splitext(filename)

        # Remove prefixes from filenames
        if name.startswith(('IMG-', 'IMG_', 'VID_', 'VID-')):
            name = name[4:]
        ext = ext.lower()
        if (ext == '.jpeg'):
            ext = '.jpg'

        return name + ext

    def validate_filename_format(self, filename: str) -> bool:
        """Check if filename starts with YYYYMMDD_HHMMSS / YYMMDD-WAXXXX format and ends with .jpg or .mp4"""
        pattern = r'^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[_-]([W0-9][A0-9]\d{4})'
        if not filename.endswith(('.jpg', '.mp4')):
            return False
        return bool(re.match(pattern, filename))

    def get_file_date(self, file_path: str) -> datetime:
        """Extract date from filename or use file modification time."""
        filename = os.path.basename(file_path)

        # Try to extract date from filename (YYYYMMDD format)
        date_pattern = r'^(\d{4})(\d{2})(\d{2})'
        match = re.search(date_pattern, filename)

        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day)
            except ValueError:
                pass

        # Fall back to file modification time
        return datetime.fromtimestamp(os.path.getmtime(file_path))

    def is_in_date_range(self, file_path: str, from_date: datetime, to_date: datetime) -> bool:
        """Check if file is within the specified date range."""
        file_date = self.get_file_date(file_path)
        return from_date <= file_date <= to_date

    def get_unique_filename(self, target_dir: str, filename: str) -> str:
        """Get a unique filename if there are conflicts."""
        name, ext = os.path.splitext(filename)
        target_path = os.path.join(target_dir, filename)

        if not os.path.exists(target_path):
            return filename

        # For WhatsApp files, increment the WA number
        if 'WA' in name:
            # Pattern: YYYY-MM-DD-WA0001
            wa_pattern = r'(.*-WA)(\d+)$'
            match = re.match(wa_pattern, name)
            if match:
                prefix = match.group(1)
                current_num = int(match.group(2))

                # Find next available number
                for num in range(current_num + 1, current_num + 1000):
                    new_name = f"{prefix}{num:04d}{ext}"
                    if not os.path.exists(os.path.join(target_dir, new_name)):
                        return new_name

        # Generic approach: add number suffix
        counter = 1
        while os.path.exists(os.path.join(target_dir, f"{name}_{counter}{ext}")):
            counter += 1

        return f"{name}_{counter}{ext}"

    def copy_file(self, src_path: str, dest_dir: str, new_filename: str):
        """Copy file to destination with new filename."""
        os.makedirs(dest_dir, exist_ok=True)

        unique_filename = self.get_unique_filename(dest_dir, new_filename)
        dest_path = os.path.join(dest_dir, unique_filename)

        try:
            shutil.copy2(src_path, dest_path)
            os.chmod(dest_path, 0o644)
            print(f"Copied: {src_path} -> {dest_path}")
            self.stats['processed'] += 1
        except Exception as e:
            print(f"Error copying {src_path} to {dest_path}: {e}")

    def process_files(self, input_folders: List[str], folder_type: str,
                     output_base: str, from_date: datetime, to_date: datetime):
        """Process files from input folders."""

        for folder_path in input_folders:
            if not os.path.exists(folder_path):
                self.warn(f"Warning: Input folder does not exist: {folder_path}")
                continue

            print(f"Processing {folder_type} folder: {folder_path}")

            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_ext = os.path.splitext(filename)[1].lower()

                    # Skip non-media files
                    if file_ext not in self.image_extensions and file_ext not in self.video_extensions:
                        continue

                    # Check date range
                    if not self.is_in_date_range(file_path, from_date, to_date):
                        continue

                    # Check for duplicates
                    if self.is_duplicate(file_path):
                        print(f"Ignoring duplicate: {file_path}")
                        continue

                    # Clean filename
                    clean_name = self.clean_filename(filename)

                    # Validate filename format and warn if needed
                    if not self.validate_filename_format(clean_name):
                        self.warn(f"Warning: Filename doesn't match YYYYMMDD_HHMMSS format or has unexpected extension: {clean_name}")

                    # Determine destination folder
                    if folder_type == 'whatsapp_images':
                        dest_dir = os.path.join(output_base, "Whatsapp-Bilder")
                        self.stats['whatsapp_images'] += 1
                    elif folder_type == 'whatsapp_videos':
                        dest_dir = os.path.join(output_base, "Videos")
                        self.stats['whatsapp_videos'] += 1
                    elif file_ext in self.video_extensions:
                        dest_dir = os.path.join(output_base, "Videos")
                        self.stats['regular_videos'] += 1
                    else:
                        dest_dir = os.path.join(output_base, "Bilder")
                        self.stats['regular_images'] += 1

                    # Copy file
                    self.copy_file(file_path, dest_dir, clean_name)

    def run(self, from_date: datetime, to_date: datetime):
        """Main execution method."""
        print(f"Starting media organization from {from_date.date()} to {to_date.date()}")

        # Get output folder from config
        output_base_dir = self.config.get('output', 'base_folder')
        output_folder_name = f"allebilder-bis-{to_date.strftime('%Y-%m-%d')}"
        output_path = os.path.join(output_base_dir, output_folder_name)

        # Exit if output path already exists
        if os.path.exists(output_path):
            print(f"Error: Output directory '{output_path}' already exists. Exiting to avoid overwriting.")
            sys.exit(1)

        print(f"Output directory: {output_path}")
        # Create output directory structure
        os.makedirs(os.path.join(output_path, "Videos"), exist_ok=True)
        os.makedirs(os.path.join(output_path, "Whatsapp-Bilder"), exist_ok=True)
        os.makedirs(os.path.join(output_path, "Bilder"), exist_ok=True)

        # Process different folder types
        folder_types = [
            ('whatsapp_images', 'whatsapp_images'),
            ('whatsapp_videos', 'whatsapp_videos'),
            ('image_folders', 'image_folders')
        ]

        for config_section, folder_type in folder_types:
            if self.config.has_section(config_section):
                folders = []
                for key in self.config[config_section]:
                    folders.append(self.config[config_section][key])

                if folders:
                    self.process_files(folders, folder_type, output_path, from_date, to_date)

        # Print warnings
        if self.warnings:
            print("\nWarnings\n========")
            for warning in self.warnings:
                print(warning)

        print(f"\nOutput folder: {output_path}")

        # Print statistics
        self.print_statistics()

    def print_statistics(self):
        """Print processing statistics."""
        print("\n" + "="*50)
        print("PROCESSING STATISTICS")
        print("="*50)
        print(f"Total files processed: {self.stats['processed']}")
        print(f"Duplicates skipped: {self.stats['duplicates']}")
        print(f"WhatsApp images: {self.stats['whatsapp_images']}")
        print(f"WhatsApp videos: {self.stats['whatsapp_videos']}")
        print(f"Regular images: {self.stats['regular_images']}")
        print(f"Regular videos: {self.stats['regular_videos']}")
        print(f"Warnings: {self.stats['warnings']}")
        print("="*50)


def parse_date(date_string: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Use YYYY-MM-DD")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Organize images and videos from various folders with date filtering and deduplication"
    )
    parser.add_argument(
        '--from-date',
        type=parse_date,
        required=True,
        help='Start date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--to-date',
        type=parse_date,
        help='End date in YYYY-MM-DD format (default: yesterday)'
    )
    parser.add_argument(
        '--config',
        default='config.ini',
        help='Path to configuration file (default: config.ini)'
    )

    args = parser.parse_args()

    # Default to-date is yesterday
    if args.to_date is None:
        args.to_date = datetime.now() - timedelta(days=1)

    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found!")
        print("Please create a config.ini file with the following structure:")
        print("""
[whatsapp_images]
folder1 = /path/to/whatsapp/images1
folder2 = /path/to/whatsapp/images2

[whatsapp_videos]
folder1 = /path/to/whatsapp/videos1

[image_folders]
folder1 = /path/to/mixed/media1
folder2 = /path/to/mixed/media2

[output]
base_folder = /path/to/output/directory
        """)
        sys.exit(1)

    # Validate date range
    if args.from_date > args.to_date:
        print("Error: from-date must be before or equal to to-date")
        sys.exit(1)

    try:
        organizer = GatherImages(args.config)
        organizer.run(args.from_date, args.to_date)

    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
