from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI

load_dotenv()
app = FastAPI()

class Text(BaseModel):
    text: str

@app.post("/critique")
def critique_text(data: Text):
    try:
        llm = OpenAI(model="gpt-3.5-turbo")
        prompt = f"You are a critic. Give constructive feedback for the following text:\n\n{data.text}"
        feedback = llm.complete(prompt).text
        return {"feedback": feedback}
    except Exception as e:
        return {"error": f"Critic error: {str(e)}"}