import json
import asyncio
import os
from pathlib import Path
from copilot import CopilotClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables being set externally

async def categorize_and_summarize_entry(entry, session):
    """
    Analyze an entry and return:
    - A concise summary
    - Category (Agentic AI or Other)
    - Confidence level (0-100)
    """
    
    # Prepare the prompt
    prompt = f"""Analyze this AI news entry and provide:
1. A concise 1-2 sentence summary of the content
2. Choose the best category: "Agentic AI" or "Other"
   - "Agentic AI" = AI systems that can take actions, make decisions, use tools, plan, or operate autonomously
   - "Other" = General AI models, applications, partnerships, policy, infrastructure, etc.
3. Your confidence level (0-100) in the category choice

Entry:
Title: {entry.get('title', '')}
Source: {entry.get('source', '')}
Content: {entry.get('content', '')}

Respond in this exact JSON format:
{{
  "summary": "your summary here",
  "category": "Agentic AI" or "Other",
  "confidence": 85
}}"""

    try:
        response = await session.send_and_wait({"prompt": prompt})
        
        # Parse the response
        response_text = response.data.content
        
        # Extract JSON from the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            print(f"Warning: Could not parse response for entry {entry.get('id')}")
            return {
                "summary": entry.get('content', '')[:200],
                "category": "Other",
                "confidence": 50
            }
            
    except Exception as e:
        print(f"Error processing entry {entry.get('id')}: {e}")
        return {
            "summary": entry.get('content', '')[:200],
            "category": "Other",
            "confidence": 0
        }

async def process_entries():
    """Process all entries in the raw JSON file"""
    
    # Initialize Copilot client
    client = CopilotClient()
    await client.start()
    session = await client.create_session({"model": "gpt-4.1"})
    
    try:
        # Read the input file — paths are read from environment variables
        input_path = Path(os.environ.get('DATA_INPUT_PATH', 'site/data/entries raw.json'))
        output_path = Path(os.environ.get('DATA_OUTPUT_PATH', 'site/data/entries.json'))
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load existing processed entries if they exist
        existing_entries = {}
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # Create a lookup dictionary by entry ID
                for entry in existing_data.get('entries', []):
                    entry_id = entry.get('id')
                    if entry_id:
                        existing_entries[entry_id] = entry
        
        print(f"Found {len(existing_entries)} existing processed entries")
        print(f"Total entries to check: {len(data['entries'])}")
        
        entries_to_process = []
        for entry in data['entries']:
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
        
        # Process each entry that needs it
        for i, entry in enumerate(entries_to_process):
            print(f"Processing entry {i+1}/{len(entries_to_process)}: {entry.get('title', 'Untitled')}")
            
            result = await categorize_and_summarize_entry(entry, session)
            
            # Update the entry
            entry['summary'] = result['summary']
            entry['category'] = result['category']
            entry['categoryConfidence'] = result['confidence']
            
            # Progress indicator every 10 entries
            if (i + 1) % 10 == 0:
                print(f"  ... {i+1} entries processed")
        
        # Write back to the file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nComplete! Processed {len(entries_to_process)} entries.")
        print(f"Output saved to: {output_path}")
        
        # Print statistics
        agentic_count = sum(1 for e in data['entries'] if e.get('category') == 'Agentic AI')
        other_count = len(data['entries']) - agentic_count
        avg_confidence = sum(e.get('categoryConfidence', 0) for e in data['entries']) / len(data['entries'])
        
        print(f"\nStatistics:")
        print(f"  Agentic AI: {agentic_count}")
        print(f"  Other: {other_count}")
        print(f"  Average Confidence: {avg_confidence:.1f}")
    
    finally:
        # Clean up Copilot client
        await client.stop()

if __name__ == "__main__":
    asyncio.run(process_entries())
