#!/usr/bin/env python3

import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

def get_assistant_id():
    # Get the script's directory and go up one level to project root
    script_dir = Path(__file__).parent.parent
    assistant_file = script_dir / "assistant_id.json"
    
    if not assistant_file.exists():
        print("Assistant not found. Please run 00_bootstrap.py first.")
        return None
    
    with open(assistant_file, 'r') as f:
        data = json.load(f)
        return data.get("assistant_id")

def ask_question(client, assistant_id, question):
    print(f"Question: {question}")
    print("=" * 60)
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add the message to the thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )
    
    print("Assistant is thinking...\n")
    
    try:
        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Poll for the run to complete
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
                return
            time.sleep(1)  # Wait 1 second between checks
        
        # Get the messages after run completes
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Get the last assistant message
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == 'text':
                        print(content.text.value)
                        
                        # Print citations if any
                        if hasattr(content.text, 'annotations') and content.text.annotations:
                            print("\nCitations:")
                            for i, annotation in enumerate(content.text.annotations, 1):
                                if hasattr(annotation, 'file_citation'):
                                    file_citation = annotation.file_citation
                                    print(f"  [{i}] Quote: {file_citation.quote[:100]}...")
                break
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print()  # Add blank line after response

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    assistant_id = get_assistant_id()
    if not assistant_id:
        return
    
    print(f"Using assistant: {assistant_id}")
    
    test_questions = [
        "Explain the difference between linearly independent and dependent vectors.",
        "What is a basis of a vector space? Give an example.",
        "How do you compute the inverse of a 2x2 matrix?",
        "What is the rank of a matrix and what does it tell us?",
    ]
    
    print("\nStudy Q&A Assistant")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Ask a question")
        print("2. Try example questions")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == "1":
            question = input("\nEnter your question: ").strip()
            if question:
                ask_question(client, assistant_id, question)
        
        elif choice == "2":
            print("Testing example questions...")
            for i, question in enumerate(test_questions, 1):
                print(f"\n--- Example {i} ---")
                ask_question(client, assistant_id, question)
                
                if i < len(test_questions):
                    input("\nPress Enter to continue to next question...")
        
        elif choice == "3":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()