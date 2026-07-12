#!/usr/bin/env python3
"""
Script to download YouTube video comments using yt-dlp and generate .info.json files.

Each .info.json file contains video metadata and a "comments" array where each comment has:
- author: The comment author's name
- text: The comment text
- like_count: Number of likes on the comment
- timestamp: Unix timestamp of when the comment was posted
- is_favorited: Whether the comment was hearted by the creator
- replies: Array of nested replies with the same metadata structure

Usage:
    python download_comments.py <video_url> [video_url2 ...]
    python download_comments.py --file <urls_file>

Examples:
    python download_comments.py https://www.youtube.com/watch?v=VIDEO_ID
    python download_comments.py --file video_urls.txt
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is not installed. Please install it with: pip install yt-dlp")
    sys.exit(1)


def format_comment(comment):
    """
    Format a comment object to include only the required fields.
    
    Args:
        comment: Raw comment data from yt-dlp
        
    Returns:
        Formatted comment dictionary with required fields
    """
    formatted = {
        "author": comment.get("author", "Unknown"),
        "text": comment.get("text", ""),
        "like_count": comment.get("like_count", 0),
        "timestamp": comment.get("timestamp", 0),
        "is_favorited": comment.get("is_favorited", False),
        "replies": []
    }
    
    # Process replies if they exist
    replies_data = comment.get("replies")
    if replies_data:
        reply_list = replies_data.get("replyList", [])
        formatted["replies"] = [format_comment(reply) for reply in reply_list]
    
    return formatted


def download_video_comments(video_url, output_dir="."):
    """
    Download comments for a single video and save to .info.json file.
    
    Args:
        video_url: URL of the YouTube video
        output_dir: Directory to save the .info.json file
        
    Returns:
        Path to the generated .info.json file, or None if failed
    """
    print(f"\nProcessing: {video_url}")
    
    # Configure yt-dlp options for downloading comments
    ydl_opts = {
        "writesubtitles": False,
        "writeautomaticsub": False,
        "skip_download": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "quiet": True,
        "no_warnings": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info including comments
            info = ydl.extract_info(video_url, download=False)
            
            if info is None:
                print(f"  Error: Could not extract information for {video_url}")
                return None
            
            # Get video ID for filename
            video_id = info.get("id", "unknown")
            video_title = info.get("title", "Unknown Video")
            
            print(f"  Video: {video_title}")
            
            # Extract and format comments
            raw_comments = info.get("comments", [])
            formatted_comments = [format_comment(comment) for comment in raw_comments]
            
            # Add formatted comments to info dict
            info["comments"] = formatted_comments
            
            # Generate output filename
            output_filename = f"{video_id}.info.json"
            output_path = os.path.join(output_dir, output_filename)
            
            # Write to JSON file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            
            print(f"  Comments downloaded: {len(formatted_comments)}")
            print(f"  Saved to: {output_path}")
            
            return output_path
            
    except Exception as e:
        print(f"  Error processing {video_url}: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video comments and generate .info.json files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "urls",
        nargs="*",
        help="YouTube video URL(s)"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="File containing video URLs (one per line)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".",
        help="Output directory for .info.json files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Collect all URLs
    urls = list(args.urls) if args.urls else []
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        
        with open(args.file, "r", encoding="utf-8") as f:
            file_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            urls.extend(file_urls)
    
    if not urls:
        parser.print_help()
        print("\nError: No video URLs provided")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Created output directory: {args.output}")
    
    # Process all videos
    print(f"Processing {len(urls)} video(s)...")
    
    successful = 0
    failed = 0
    
    for url in urls:
        result = download_video_comments(url, args.output)
        if result:
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(urls)}")
    
    if successful > 0:
        print(f"\n.info.json files saved to: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
