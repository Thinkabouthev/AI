import json
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Note(BaseModel):
    id: int = Field(..., ge=1, le=10)
    heading: str = Field(..., min_length=1)
    summary: str = Field(..., max_length=150, min_length=1)
    page_ref: Optional[int] = Field(None, description="Page number in source PDF", ge=1)

def get_assistant_id():
    script_dir = Path(__file__).parent.parent
    assistant_file = script_dir / "assistant_id.json"
    
    if not assistant_file.exists():
        print("Assistant not found. Please run 00_bootstrap.py first.")
        return None
    
    with open(assistant_file, 'r') as f:
        data = json.load(f)
        return data.get("assistant_id")

def main():
    # Create OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get assistant ID
    assistant_id = get_assistant_id()
    if not assistant_id:
        print("Please run 00_bootstrap.py first to set up the assistant.")
        exit(1)
    
    print(f"Using assistant: {assistant_id}")
    print("Generating study notes...\n")
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add the instruction message
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=(
            "Generate 10 study notes from the Linear Algebra textbook in JSON format. "
            "IMPORTANT: Each summary MUST be 150 characters or less!\n\n"
            "The response must be valid JSON that matches this schema:\n"
            "{\n"
            '  "notes": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "heading": "Example Heading",\n'
            '      "summary": "Very short summary under 150 chars",\n'
            '      "page_ref": 42  // Must be a number, or null if unknown\n'
            "    },\n"
            "    ...\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "1. Generate exactly 10 notes\n"
            "2. Each note must have id (1-10), heading, and summary\n"
            "3. page_ref must be a number (like 42) or null if unknown\n"
            "4. CRITICAL: Summary MUST be under 150 characters - longer summaries will cause errors\n"
            "5. Focus on key concepts and theorems from the textbook\n"
            "6. Response must be pure JSON (no markdown or other text)\n"
            "7. Be very concise in summaries to stay under the 150 character limit\n"
            "8. For page_ref, use actual page numbers from the textbook, or null if not found"
        )
    )
    
    try:
        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Wait for run to complete
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == 'completed':
                break
            elif run.status in ['failed', 'cancelled', 'expired']:
                print(f"\n❌ Run failed with status: {run.status}")
                if hasattr(run, 'last_error'):
                    print(f"Error: {run.last_error}")
                exit(1)
            time.sleep(1)  # Wait between checks
        
        # Get the messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        # Get the last assistant message
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == 'text':
                        # Try to extract JSON from the response
                        try:
                            # Find JSON content between triple backticks if present
                            text = content.text.value
                            if '```json' in text:
                                text = text.split('```json')[1].split('```')[0].strip()
                            elif '```' in text:
                                text = text.split('```')[1].split('```')[0].strip()
                            
                            data = json.loads(text)
                            
                            # Validate the notes
                            if "notes" not in data:
                                data = {"notes": data}  # Try to fix missing wrapper
                            notes: List[Note] = [Note(**item) for item in data["notes"]]
                            
                            # Pretty print
                            print("Generated Study Notes:")
                            print("=" * 40 + "\n")
                            for note in notes:
                                print(f"{note.id}. {note.heading}")
                                print(f"   Page: {note.page_ref or '–'}")
                                print(f"   {note.summary}\n")
                            
                            # Save to file
                            script_dir = Path(__file__).parent.parent
                            output_file = script_dir / "exam_notes.json"
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump([note.model_dump() for note in notes], f, indent=2, ensure_ascii=False)
                            
                            print(f"Notes saved to {output_file.absolute()}")
                            return
                            
                        except (json.JSONDecodeError, ValidationError) as e:
                            print(f"\n⚠️ Failed to parse response as valid notes: {str(e)}")
                            print("\nRaw response:")
                            print(content.text.value)
                break
        
        print("No valid response found in assistant's message")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
