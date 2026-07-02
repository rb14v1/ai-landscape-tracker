"""
Process entries from 'entries raw.json' and add:
- Improved summary
- Category (Agentic AI or Other)
- Confidence level

This script is designed to be run with Claude as the processing engine.
"""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables being set externally

def load_entries():
    """Load entries from the raw JSON file — path read from DATA_INPUT_PATH env var"""
    input_path = Path(os.environ.get('DATA_INPUT_PATH', 'site/data/entries raw.json'))
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_entries():
    """Load existing processed entries if they exist — path read from DATA_OUTPUT_PATH env var"""
    output_path = Path(os.environ.get('DATA_OUTPUT_PATH', 'site/data/entries.json'))
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            # Create a lookup dictionary by entry ID
            existing_entries = {}
            for entry in existing_data.get('entries', []):
                entry_id = entry.get('id')
                if entry_id:
                    existing_entries[entry_id] = entry
            return existing_entries
    return {}

def save_entries(data):
    """Save processed entries to the output file — path read from DATA_OUTPUT_PATH env var"""
    output_path = Path(os.environ.get('DATA_OUTPUT_PATH', 'site/data/entries.json'))
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")

def analyze_entry(entry):
    """
    Analyze entry and return categorization.
    This needs to be filled in with actual AI analysis.
    """
    title = entry.get('title', '').lower()
    content = entry.get('content', '').lower()
    text = title + " " + content
    
    # Keywords that suggest Agentic AI
    agentic_keywords = [
        'agent', 'agentic', 'autonomous', 'tool use', 'function calling',
        'workflow', 'orchestration', 'multi-agent', 'task planning',
        'action', 'execute', 'codex', 'automation'
    ]
    
    # Check for agentic keywords
    agentic_score = sum(1 for keyword in agentic_keywords if keyword in text)
    
    # Basic categorization logic
    if agentic_score >= 2:
        category = "Agentic AI"
        confidence = min(75 + (agentic_score * 5), 95)
    elif agentic_score == 1:
        category = "Agentic AI"
        confidence = 75
    else:
        category = "Other"
        confidence = 75
    
    # Create a better summary from content
    content_str = entry.get('content', '')
    if len(content_str) > 200:
        summary = content_str[:197] + "..."
    else:
        summary = content_str
    
    return {
        'summary': summary,
        'category': category,
        'categoryConfidence': confidence
    }

def main():
    # Load data
    data = load_entries()
    entries = data['entries']
    
    # Load existing processed entries
    existing_entries = load_existing_entries()
    
    print(f"Found {len(existing_entries)} existing processed entries")
    print(f"Total entries to check: {len(entries)}")
    
    # Identify entries that need processing
    entries_to_process = []
    for entry in entries:
        entry_id = entry.get('id')
        existing = existing_entries.get(entry_id)
        
        # Process if entry doesn't exist or has low/empty confidence
        if not existing:
            entries_to_process.append(entry)
        else:
            confidence = existing.get('categoryConfidence')
            if confidence is None or confidence == '' or confidence < 75:
                entries_to_process.append(entry)
            else:
                # Copy existing data to this entry
                entry['summary'] = existing.get('summary', '')
                entry['category'] = existing.get('category', 'Other')
                entry['categoryConfidence'] = existing.get('categoryConfidence', 0)
    
    print(f"Entries requiring processing: {len(entries_to_process)}")
    print("\nThis is a placeholder script.")
    print("For accurate AI-powered categorization, each entry should be")
    print("analyzed individually with proper AI context.")
    print("\nPlease run this with AI agent to process entries properly.")
    
    # Process each entry that needs it (basic version)
    for i, entry in enumerate(entries_to_process):
        if (i + 1) % 50 == 0:
            print(f"Processed {i+1}/{len(entries_to_process)} entries...")
        
        result = analyze_entry(entry)
        entry['summary'] = result['summary']
        entry['category'] = result['category']
        entry['categoryConfidence'] = result['categoryConfidence']
    
    # Save results
    save_entries(data)
    
    # Statistics
    agentic_count = sum(1 for e in entries if e.get('category') == 'Agentic AI')
    other_count = len(entries) - agentic_count
    avg_confidence = sum(e.get('categoryConfidence', 0) for e in entries) / len(entries)
    
    print(f"\nComplete! Processed {len(entries_to_process)} entries.")
    print(f"\nStatistics:")
    print(f"  Total entries: {len(entries)}")
    print(f"  Agentic AI: {agentic_count}")
    print(f"  Other: {other_count}")
    print(f"  Average Confidence: {avg_confidence:.1f}%")

if __name__ == "__main__":
    main()
