# -*- coding: utf-8 -*-
"""
Extract_Nuclear_Rhetoric_Chronology.py

This script extracts nuclear interaction data from the structured PDF file.
It generates two JSON outputs:
1. Short entries: A list of concise summaries.
2. Long entries: A list of detailed descriptions with source links.

Based on the PDF: "Nuclear rhetoric and escalation management in Russia's war against Ukraine"
by Horovitz and Stolze
"""

import json
import re
from pypdf import PdfReader


def extract_all_entries_from_pdf(pdf_path):
    """Extract all numbered entries from the PDF chronology section."""
    reader = PdfReader(pdf_path)
    
    # The chronology starts around page 18 (0-indexed: 17)
    # Based on analysis, entries start from page 21 (0-indexed: 20)
    all_text = ""
    for i in range(17, min(200, len(reader.pages))):
        text = reader.pages[i].extract_text()
        if text:
            all_text += text + "\n"
    
    return all_text


def parse_entries(all_text):
    """Parse numbered entries from the extracted text."""
    # Pattern to match entries like "1. Warning", "2. Escalatory", "3. De-escalatory"
    # Handle variations in spacing and hyphenation
    pattern = r'(\d+)\.\s*(Warning|Escalatory|De-escalatory|De-\s*escalatory)\s*'
    
    entries = []
    matches = list(re.finditer(pattern, all_text))
    
    for idx, match in enumerate(matches):
        num = int(match.group(1))
        entry_type = match.group(2).replace("De-\n", "De-").replace("De- ", "De-")
        start_pos = match.end()
        
        # Get content until next entry or end
        if idx + 1 < len(matches):
            end_pos = matches[idx + 1].start()
        else:
            end_pos = len(all_text)
        
        content = all_text[start_pos:end_pos].strip()
        
        # Clean up the content - remove extra whitespace and fix line breaks
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'-\s+', '-', content)  # Fix hyphenated words split across lines
        
        entries.append({
            "num": num,
            "type": entry_type,
            "content": content
        })
    
    return entries


def determine_actor(content, entry_type):
    """Determine if the actor is RU (Russia) or W (West/NATO)."""
    # The chronology explicitly codes entries as RU or W at the start
    # Check for explicit markers first
    if re.search(r'\bRU\b', content[:100]):
        return "RU"
    if re.search(r'\bW\b\s*\[', content[:100]) or re.search(r'^\d+\.\s*W\s*\[', content[:50]):
        return "W"
    
    # Check for Western actors in the first portion of content
    western_indicators = [
        "Biden", "Truss", "Stoltenberg", "Macron", "Blinken", 
        "NATO foreign ministers", "European Union", "EU ",
        "US President", "British Foreign Secretary", "French Foreign Minister",
        "White House", "Pentagon", "State Department"
    ]
    
    # Check if it starts with Russian indicators
    russian_indicators = [
        "Putin", "Medvedev", "Lavrov", "Ryabkov", "Nechayev", "Shoigu",
        "Russia ", "Russian ", "Kremlin", "Moscow ", "Belarus",
        "Russian Defense Minister", "Russian Foreign Ministry"
    ]
    
    # Look at the first 400 characters to determine primary actor
    preview = content[:400]
    
    # Count indicators
    ru_count = sum(1 for ind in russian_indicators if ind.lower() in preview.lower())
    w_count = sum(1 for ind in western_indicators if ind.lower() in preview.lower())
    
    # If it's about Russian actions/statements, mark as RU
    # Otherwise, if primarily about Western responses, mark as W
    if ru_count > w_count:
        return "RU"
    elif w_count > ru_count:
        return "W"
    else:
        # Default based on entry type patterns in this chronology
        # Warning and Escalatory are often RU, De-escalatory often W
        return "RU" if entry_type in ["Warning", "Escalatory"] else "W"


def extract_date_from_content(content, entry_num):
    """Extract the date from entry content."""
    # Common date patterns
    date_patterns = [
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?',
        r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        r'\d{4}-\d{2}-\d{2}'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            date_str = match.group(0).strip()
            # Clean up the date format
            return date_str
    
    # Fallback based on known chronology order
    # This would need manual mapping for accuracy
    return "Date Unknown"


def extract_first_link(content):
    """Extract the first URL from content."""
    url_pattern = r'https?://[^\s\]\)]+'
    match = re.search(url_pattern, content)
    if match:
        url = match.group(0)
        # Clean up URL - remove trailing punctuation that might be caught
        url = re.sub(r'[.,;]+$', '', url)
        return url
    return None


def create_short_description(content, max_words=30):
    """Create a short description from the content."""
    # Remove URLs and footnotes
    clean_content = re.sub(r'\[https?://[^\]]+\]', '', content)
    clean_content = re.sub(r'https?://[^\s]+', '', clean_content)
    
    # Split into sentences
    sentences = re.split(r'[.!?]+\s+', clean_content)
    
    # Take first sentence or first N words
    if sentences and len(sentences[0]) > 20:
        short_desc = sentences[0].strip()
        if not short_desc.endswith('.'):
            short_desc += '.'
    else:
        words = clean_content.split()
        short_desc = ' '.join(words[:max_words])
        if len(words) > max_words:
            short_desc += "..."
    
    # Clean up
    short_desc = re.sub(r'\s+', ' ', short_desc).strip()
    return short_desc


def generate_short_entries(entries):
    """Generate short format entries."""
    short_list = []
    
    for entry in entries:
        actor = determine_actor(entry['content'], entry['type'])
        date_str = extract_date_from_content(entry['content'], entry['num'])
        description = create_short_description(entry['content'])
        
        short_list.append({
            "num": entry['num'],
            "date": date_str,
            "actor": actor,
            "type": entry['type'],
            "description": description
        })
    
    return short_list


def generate_long_entries(entries):
    """Generate long format entries with full descriptions and links."""
    long_list = []
    
    for entry in entries:
        actor = determine_actor(entry['content'], entry['type'])
        date_str = extract_date_from_content(entry['content'], entry['num'])
        
        # Extract link
        link = extract_first_link(entry['content'])
        
        # Clean description - remove URLs but keep the text
        desc = re.sub(r'\[\s*https?://[^\]]+\]', '', entry['content'])
        desc = re.sub(r'https?://[^\s]+', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # Remove footnote numbers like "18", "21" at end of sentences
        desc = re.sub(r'\s+\d+(?=\s|$)', '', desc)
        
        long_list.append({
            "num": entry['num'],
            "type": entry['type'],
            "actor": actor,
            "date": date_str,
            "description": desc,
            "link": link if link else "Link not found"
        })
    
    return long_list


def main():
    pdf_path = "chronology.pdf"
    
    print(f"Processing: {pdf_path}")
    
    # Extract text from PDF
    all_text = extract_all_entries_from_pdf(pdf_path)
    print(f"Extracted {len(all_text)} characters from PDF")
    
    # Parse entries
    entries = parse_entries(all_text)
    print(f"Found {len(entries)} entries")
    
    # Generate outputs
    short_entries = generate_short_entries(entries)
    long_entries = generate_long_entries(entries)
    
    # Save to files
    with open('short_entries.json', 'w', encoding='utf-8') as f:
        json.dump(short_entries, f, indent=2, ensure_ascii=False)
    
    with open('long_entries.json', 'w', encoding='utf-8') as f:
        json.dump(long_entries, f, indent=2, ensure_ascii=False)
    
    print("\nFiles created: short_entries.json, long_entries.json")
    
    # Display samples
    print("\n--- First 5 Short Entries ---")
    for entry in short_entries[:5]:
        print(f"{entry['num']}. [{entry['type']}] {entry['actor']} - {entry['date']}")
        print(f"   {entry['description'][:100]}...")
        print()
    
    print("\n--- First 2 Long Entries ---")
    for entry in long_entries[:2]:
        print(f"{entry['num']}. [{entry['type']}] {entry['actor']} - {entry['date']}")
        print(f"   Link: {entry['link']}")
        print(f"   {entry['description'][:200]}...")
        print()


if __name__ == "__main__":
    main()
