#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from datetime import datetime
from PIL import Image, ExifTags
import piexif
from PIL.ExifTags import TAGS

def is_timestamp_filename(filename):
    """Check if filename is a timestamp with supported extension."""
    pattern = r'^(\d{10})\.(jpg|jpeg|png|gif|mp4|mov|avi|mkv)$'
    match = re.match(pattern, filename.lower())
    if match:
        return {"type": "timestamp", "timestamp": int(match.group(1)), "extension": match.group(2), "original": match.group(0)}
    # Check for IMG_YYYYMMDD_HHMMSS or MP4_YYYYMMDD_HHMMSS
    pattern2 = r'^(img|mp4)_(\d{8})_(\d{6})\.(jpg|jpeg|png|gif|mp4|mov|avi|mkv)$'
    match2 = re.match(pattern2, filename.lower())
    if match2:
        date_part = match2.group(2)
        time_part = match2.group(3)
        dt_str = f"{date_part}{time_part}"
        try:
            dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            timestamp = int(dt.timestamp())
            return {"type": "datetime", "timestamp": timestamp, "extension": match2.group(4), "original": match2.group(0)}
        except Exception:
            return None
    return None

def update_image_exif(file_path, timestamp):
    """Update EXIF data for image files."""
    # Check if file is an image that supports EXIF
    try:
        # Convert timestamp to EXIF datetime format
        dt = datetime.fromtimestamp(timestamp)
        exif_datetime = dt.strftime("%Y:%m:%d %H:%M:%S")
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ['.jpg', '.jpeg']:
            return False  # Only JPG/JPEG support EXIF data
        
        # Load existing EXIF data
        try:
            exif_dict = piexif.load(file_path)
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Update DateTimeOriginal, DateTime, and DateTimeDigitized
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_datetime
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_datetime
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_datetime
        
        # Save EXIF data back to the file
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)
        return True
    except Exception as e:
        print(f"Failed to update EXIF data for {file_path}: {str(e)}")
        return False

def process_files(folder_path):
    """Process all files in the given folder."""
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        return

    processed_count = 0
    exif_updated_count = 0
    renamed_count = 0
    skipped_count = 0
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(file_path):
            continue
            
        info = is_timestamp_filename(filename)
        if not info:
            skipped_count += 1
            continue
            
        timestamp = info["timestamp"]
        extension = info["extension"]
        
        try:
            # Convert timestamp to datetime
            file_datetime = datetime.fromtimestamp(timestamp)
            
            # Format for display and filename
            formatted_time = file_datetime.strftime('%Y-%m-%d %H:%M:%S')
            new_filename = file_datetime.strftime('%Y%m%d_%H%M%S') + '.' + extension
            new_file_path = os.path.join(folder_path, new_filename)
            
            # Avoid overwriting existing files
            if new_filename != filename and os.path.exists(new_file_path):
                print(f"Skip renaming {filename} to {new_filename}: target exists.")
                skipped_count += 1
                continue
            
            if new_filename != filename:
                os.rename(file_path, new_file_path)
                renamed_count += 1
                file_path = new_file_path  # Update file path for subsequent operations
            
            # Set file access and modification times
            os.utime(file_path, (timestamp, timestamp))
            
            # Update EXIF data for image files
            exif_updated = False
            if extension.lower() in ['jpg', 'jpeg']:
                exif_updated = update_image_exif(file_path, timestamp)
                if exif_updated:
                    exif_updated_count += 1
            
            status = "Processed" + (" (EXIF updated)" if exif_updated else "")
            print(f"{status}: {filename} → {new_filename} ({formatted_time})")
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            
    print(f"\nSummary: Processed {processed_count} files (renamed {renamed_count}, updated EXIF for {exif_updated_count}), skipped {skipped_count} files")

def main():
    if len(sys.argv) != 2:
        print("Usage: python file_name_is_timestamp.py <folder_path>")
        return
        
    folder_path = sys.argv[1]
    print(f"Processing files in: {folder_path}")
    process_files(folder_path)

if __name__ == "__main__":
    main()
