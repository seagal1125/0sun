import os
import json
from PIL import Image, ExifTags
from datetime import datetime

# Configuration
IMAGE_DIR = "."
THUMB_DIR = "thumbnails"
OUTPUT_FILE = "gallery_data.json"
SUPPORTED_EXTS = {".jpg", ".jpeg"}
THUMB_SIZE = (400, 200) # Width, Height (approx aspect ratio for panorama)

# Helpers for converting GPS coordinates
def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1]
    seconds = dms[2]
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
        
    return decimal

def get_exif_data(image_path):
    try:
        # Open just to read EXIF, don't load whole image yet if possible
        img = Image.open(image_path)
        exif = img._getexif()
        
        date_str = None
        gps_info = None
        
        if exif:
            exif_data = {ExifTags.TAGS[k]: v for k, v in exif.items() if k in ExifTags.TAGS}
            date_str = exif_data.get("DateTimeOriginal")
            gps_info = exif_data.get("GPSInfo")
        
        lat = None
        lon = None
        
        if gps_info:
            gps_lat = gps_info.get(2)
            gps_lat_ref = gps_info.get(1)
            gps_lon = gps_info.get(4)
            gps_lon_ref = gps_info.get(3)
            
            if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
                lat = get_decimal_from_dms(gps_lat, gps_lat_ref)
                lon = get_decimal_from_dms(gps_lon, gps_lon_ref)
                
        return date_str, (lat, lon)
        
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {e}")
        return None, None

def generate_thumbnail(image_path, filename):
    if not os.path.exists(THUMB_DIR):
        os.makedirs(THUMB_DIR)
        
    thumb_path = os.path.join(THUMB_DIR, filename)
    
    # If thumbnail already exists, skip (basic cache check)
    if os.path.exists(thumb_path):
        return thumb_path
        
    try:
        print(f"Generating thumbnail for {filename}...")
        img = Image.open(image_path)
        # Convert to RGB if necessary (e.g. if RGBA)
        if img.mode in ('RGBA', 'P'):
            img = img.convert("RGB")
            
        img.thumbnail(THUMB_SIZE)
        img.save(thumb_path, "JPEG", quality=70)
        return thumb_path
    except Exception as e:
        print(f"Error creating thumbnail for {filename}: {e}")
        return None

# Manual Override Data (Filename -> {lat, lon, date})
# Use this to fix missing GPS or Date
MANUAL_DATA = {
    "sun0118.jpg": {
        "lat": 24.841396,
        "lon": 120.977613,
        "date": "2026:01:18 12:00:00"
    },
    "日光富裕0118.jpg": {
        "lat": 24.841396,
        "lon": 120.977613,
        "date": "2026:01:18 12:00:00" # Approximate
    }
}

def main():
    photos = []
    
    print("Scanning for photos...")
    
    for filename in os.listdir(IMAGE_DIR):
        ext = os.path.splitext(filename)[1].lower()
        if ext in SUPPORTED_EXTS:
            filepath = os.path.join(IMAGE_DIR, filename)
            date_str, coords = get_exif_data(filepath)
            
            # Default values if missing
            lat, lon = coords if coords and coords[0] is not None else (None, None)
            
            # Check Manual Data Override
            if filename in MANUAL_DATA:
                print(f"Applying manual data for {filename}")
                m_data = MANUAL_DATA[filename]
                # Only override if missing (or strictly override? Let's strictly override for these known files)
                lat = m_data.get("lat", lat)
                lon = m_data.get("lon", lon)
                if not date_str:
                    date_str = m_data.get("date")

            if lat is not None and lon is not None:
                # Generate Thumbnail
                thumb_path = generate_thumbnail(filepath, filename)
                
                photos.append({
                    "filename": filename,
                    "date": date_str if date_str else "Unknown Date",
                    "lat": lat,
                    "lon": lon,
                    "thumb": thumb_path if thumb_path else None
                })
                print(f"Processed: {filename}")
            else:
                print(f"Skipping {filename} (No GPS)")

    # Sort by date (newest first), then by filename (descending, so Chinese chars often come before English/ASCII if desired)
    photos.sort(key=lambda x: (x["date"], x["filename"]), reverse=True)

    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(photos, f, indent=4, ensure_ascii=False)
        
    print(f"Saved {len(photos)} photos to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
