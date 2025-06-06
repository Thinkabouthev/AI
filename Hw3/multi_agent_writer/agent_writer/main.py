from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
import requests
import os
import google.generativeai as genai

load_dotenv()
app = FastAPI()

class Topic(BaseModel):
    topic: str

@app.post("/write")
def write_article(data: Topic):
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        prompt = f"Write a short informative article on the topic: {data.topic}"
        response = llm([HumanMessage(content=prompt)])
        return {"text": response.content}
    except Exception as e:
        return {"error": f"Writer error: {str(e)}"}