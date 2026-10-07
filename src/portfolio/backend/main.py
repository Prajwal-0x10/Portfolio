from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from portfolio.backend.read_resume_from_pdf import read_pdf_text
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from glob import glob
import json

app = FastAPI(title="Prajwal Gawande | AI Candidate Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=my_api_key) if my_api_key else None
model = "openai/gpt-oss-120b"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESUME_PATH = BASE_DIR / "Prajwal_Gawande_Resume_0726.pdf"

_cached_resume = None

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
        You are an AI Assistant representing job candidate Prajwal Gawande.
        Use the following resume details to answer interviewer questions accurately, professionally, and naturally.

        {resume.model_dump_json(indent=2)}
         
        Rules:
        1) Never hallucinate facts outside the provided resume.
        2) If information cannot be answered from the resume, state politely: "That information isn't covered in my current resume, but I'd be happy to share more details directly!"
        3) Be concise, confident, and direct.
        4) Limit answers to 3-4 clear sentences.
        5) Respond in first person ("I have worked on...", "My background includes...").
    """
    response = client.chat.completions.create(
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

def resume_parser(resume_text: str) -> Resume:
    schema = Resume.model_json_schema()
    response_format = {"type":"json_object"}
    system_prompt=f"""
    Act as an expert resume parser.
    Return JSON strictly matching schema: {schema} after extracting information from the resume text.
    Do not invent information.
    """

    user_prompt = f'''   
    Analyse the following resume text:
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
    return Resume(**data)

def get_parsed_resume() -> Resume:
    global _cached_resume
    if _cached_resume is None:
        resume_text = read_pdf_text(DEFAULT_RESUME_PATH)
        _cached_resume = resume_parser(resume_text)
    return _cached_resume

def pdf_extaction(file_path:str):
    resume_text = read_pdf_text(file_path)
    return resume_text

@app.get("/")
@app.get("/api/health")
def home():
    return {"status": "online", "message": "Prajwal Gawande AI Candidate Assistant API is running"}

@app.post("/chat")
@app.post("/api/chat")
def chat(request: ChatRequest):
    if not client:
        return {"error": "GROQ_API_KEY is not configured in environment variables."}
    
    try:
        resume = get_parsed_resume()
        answer = ask_candidate(request.question, resume)
        return {"answer": answer}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}



