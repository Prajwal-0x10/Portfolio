from fastapi import FastAPI
from portfolio.backend.read_resume_from_pdf import read_pdf_text
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from glob import glob
import json

app = FastAPI()

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=my_api_key) if my_api_key else None
model = "openai/gpt-oss-120b"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESUME_PATH = BASE_DIR / "Prajwal_Gawande_Resume_0726.pdf"

class Experience(BaseModel):
    company : str | None
    role : str | None
    duration : str | None
    responsibilities : str | None

class Resume(BaseModel):
    summary :str | None
    skills : list[str] | None
    projects: list[str] | None
    experience: list[Experience] | None
    education: list[str]

class ChatRequest(BaseModel):
    question : str

def ask_candidate(question:str, resume: Resume):
    system_prompt = f"""
        You are and AI Assistant representing a job candidate.
        Use the following resume to answer questions

        {resume.model_dump_json(indent=2)}
         
        Rules:
        1) Never Hallucinate
        2) If cannot answer say i dont know
        3) Be concise and direct
        4) Answer in 3-4 sentences max
        5) Answer only with given resume
        6) Answer as fif hr is interviewing Candidate.
    """
    response=client.chat.completions.create(
        model=model,
        messages=[{
            "role":"system",
            "content":system_prompt
        },
        {
            "role":"user",
            "content":question
        }]
    )

    return response.choices[0].message.content

def resume_parser(resume_text: str) -> dict:
    schema = Resume.model_json_schema()
    response_format = {"type":"json_object"}
    system_prompt=f"""
    Act as a expert resume parser
    Return json matching {schema} after extracting necessary information from the job description

    Do not invent information.
    """

    user_prompt = f'''   
    Analyse the following resume:
    {resume_text}
    '''
    message_system = {
        "role": "system",
        "content": system_prompt
    }
    messages = {
        "role":"user",
        "content":user_prompt
    }
    
    messages = [message_system, messages]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format = response_format
    )
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume 

def pdf_extaction(file_path:str):
    resume_text = read_pdf_text(file_path)
    return resume_text

@app.get("/")
def home():
    return {"message":"Hello"}

@app.post("/chat")
def chat(request: ChatRequest):
    if not client:
        return {"error": "GROQ_API_KEY is not configured in environment variables."}
    resume_text = read_pdf_text(DEFAULT_RESUME_PATH)   
    resume = resume_parser(resume_text)
    answer = ask_candidate(request.question, resume)
    return {"answer": answer}


