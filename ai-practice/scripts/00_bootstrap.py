import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

def main():
    # Get the script's directory
    script_dir = Path(__file__).parent.parent
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Check if assistant already exists
    assistant_file = script_dir / "assistant_id.json"
    
    if assistant_file.exists():
        with open(assistant_file, 'r') as f:
            data = json.load(f)
            assistant_id = data.get("assistant_id")
            
        print(f"Using existing assistant: {assistant_id}")
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            print(f"Error retrieving assistant: {e}")
            print("Creating new assistant...")
            assistant_file.unlink()  # Remove invalid assistant file
            assistant = None
    else:
        assistant = None
    
    if not assistant:
        # Upload PDF file(s) from data directory first
        data_dir = script_dir / "data"
        pdf_files = list(data_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found in data/ directory")
            return
        
        # Upload files for assistants
        file_ids = []
        for pdf_file in pdf_files:
            print(f"Uploading {pdf_file.name}...")
            
            with open(pdf_file, "rb") as f:
                file_obj = client.files.create(
                    purpose="assistants",
                    file=f
                )
            file_ids.append(file_obj.id)
            print(f"Uploaded file ID: {file_obj.id}")
        
        # Create new assistant with file attachments
        assistant = client.beta.assistants.create(
            name="Study Q&A Assistant",
            instructions=(
                "You are a helpful tutor. "
                "Use the knowledge in the attached files to answer questions. "
                "Cite sources where possible."
            ),
            model="gpt-3.5-turbo-1106",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_stores": [{
                        "file_ids": file_ids
                    }]
                }
            }
        )
        
        # Save assistant ID for reuse
        with open(assistant_file, 'w') as f:
            json.dump({"assistant_id": assistant.id}, f)
            
        print(f"Created new assistant: {assistant.id}")
        print(f"Assistant created with {len(file_ids)} file(s)")
    
    print("Bootstrap complete!")

if __name__ == "__main__":
    main() 