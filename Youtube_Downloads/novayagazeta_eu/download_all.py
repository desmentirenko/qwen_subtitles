#!/usr/bin/env python3
"""
Script to download all video metadata and subtitles from a YouTube channel.
Uses yt-dlp for metadata and youtube-transcript-api for subtitles.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, YouTubeRequestFailed

OUTPUT_DIR = Path("/workspace/Youtube_Downloads/novayagazeta_eu")
CHANNEL_URL = "https://www.youtube.com/@novayagazeta_eu/videos"

def get_video_urls():
    """Get all video URLs from the channel using yt-dlp flat playlist."""
    print("Fetching video URLs from channel...")
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s|%(url)s", CHANNEL_URL],
        capture_output=True, text=True, timeout=120
    )
    lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    videos = []
    for line in lines:
        parts = line.split('|', 2)
        if len(parts) >= 3:
            videos.append({
                'id': parts[0],
                'title': parts[1],
                'url': parts[2]
            })
    print(f"Found {len(videos)} videos")
    return videos

def get_video_metadata(video_url):
    """Get video metadata using yt-dlp with multiple client fallbacks."""
    clients = ['ios', 'mweb', 'tv']
    
    for client in clients:
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", 
                 "--extractor-args", f"youtube:player_client={client}",
                 "--socket-timeout", "30",
                 "--retry-sleep", "2",
                 video_url],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    continue
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    
    return None

def download_subtitles(video_id, output_path):
    """Download all available subtitles for a video."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        subtitles_data = {}
        
        # Collect all manual (uploaded by creator) subtitles
        manual_found = False
        for transcript in transcript_list:
            if not transcript.is_generated:
                lang_code = transcript.language_code
                lang_name = transcript.language
                try:
                    data = transcript.fetch()
                    key = f"{lang_code}"
                    subtitles_data[key] = {
                        "language": lang_name,
                        "language_code": lang_code,
                        "type": "manual",
                        "data": [
                            {"start": entry.start, "duration": entry.duration, "text": entry.text}
                            for entry in data
                        ]
                    }
                    manual_found = True
                    print(f"    Downloaded manual subtitles: {lang_name}")
                except Exception as e:
                    print(f"    Error fetching manual {lang_code}: {e}")
        
        # Get auto-generated subtitle for main language
        # First try to find auto-generated in same language as manual ones
        auto_found = False
        for transcript in transcript_list:
            if transcript.is_generated:
                try:
                    data = transcript.fetch()
                    subtitles_data["auto"] = {
                        "language": transcript.language,
                        "language_code": transcript.language_code,
                        "type": "auto-generated",
                        "data": [
                            {"start": entry.start, "duration": entry.duration, "text": entry.text}
                            for entry in data
                        ]
                    }
                    auto_found = True
                    print(f"    Downloaded auto-generated subtitles: {transcript.language}")
                    break
                except Exception as e:
                    continue
        
        if subtitles_data:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(subtitles_data, f, ensure_ascii=False, indent=2)
            return True, len(subtitles_data)
        return False, 0
        
    except TranscriptsDisabled:
        return False, 0
    except YouTubeRequestFailed:
        return False, 0
    except Exception as e:
        print(f"    Error: {e}")
        return False, 0

def main():
    # Create output directories
    metadata_dir = OUTPUT_DIR / "metadata"
    subtitles_dir = OUTPUT_DIR / "subtitles"
    metadata_dir.mkdir(exist_ok=True)
    subtitles_dir.mkdir(exist_ok=True)
    
    # Get all video info
    videos = get_video_urls()
    
    if not videos:
        print("No videos found!")
        return
    
    # Save video URLs list
    with open(OUTPUT_DIR / "video_urls.txt", 'w', encoding='utf-8') as f:
        for video in videos:
            f.write(video['url'] + '\n')
    
    all_metadata = []
    total_subtitles = 0
    videos_with_subs = 0
    
    for i, video in enumerate(videos):
        video_id = video['id']
        print(f"\n[{i+1}/{len(videos)}] Processing: {video_id}")
        print(f"  Title: {video['title'][:60]}...")
        
        # Get metadata
        metadata = get_video_metadata(video['url'])
        if metadata:
            all_metadata.append(metadata)
            
            # Save individual metadata file
            meta_file = metadata_dir / f"{video_id}.info.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"  Saved metadata")
        else:
            print(f"  Failed to get metadata")
            continue
        
        # Download subtitles
        sub_file = subtitles_dir / f"{video_id}.subtitles.json"
        success, count = download_subtitles(video_id, sub_file)
        if success:
            videos_with_subs += 1
            total_subtitles += count
            print(f"  Saved {count} subtitle track(s)")
        else:
            print(f"  No subtitles available")
        
        # Rate limiting
        if (i + 1) % 10 == 0:
            print(f"  Pausing for rate limiting...")
            time.sleep(5)
    
    # Save combined metadata JSON
    combined_meta_file = OUTPUT_DIR / "all_videos_metadata.json"
    with open(combined_meta_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total videos: {len(videos)}")
    print(f"Videos with metadata: {len(all_metadata)}")
    print(f"Videos with subtitles: {videos_with_subs}")
    print(f"Total subtitle tracks: {total_subtitles}")
    print(f"\nOutput folder: {OUTPUT_DIR}")
    print(f"  - Metadata: {metadata_dir}/")
    print(f"  - Subtitles: {subtitles_dir}/")
    print(f"  - Combined metadata: {combined_meta_file}")
    print(f"  - Video URLs: {OUTPUT_DIR / 'video_urls.txt'}")

if __name__ == "__main__":
    main()
