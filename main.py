import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import time

from document.generic_plan_generator import GenericDocumentGenerator
from document.space_engineering.plan_generator import DocumentGenerator
from document.summary_generator import SummaryDocumentGenerator

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8081",
    "https://storage.googleapis.com",
    "https://storage.googleapis.com/voicesense",
    "https://storage.googleapis.com/voicesense/index.html"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessionid = os.getsid(0)
print("Session ID: ", sessionid)
sessionid2 = int(time.time())

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/generateDocument")
async def generateDoc(title, objective, strategic_prompt):

    space_prompts = [
        {
            "mission_name": "Lunar mining",
            "objectives": "Land and start minning the key resources (Helium-3) and Earth Rare Resources on moon, with detecting water ice and mapping geological structures",
        }
    ]

    prompts = [
        {
            "title": title,
            "objectives": objective,
            "strategic_prompt": strategic_prompt,
        }
    ]

    c = GenericDocumentGenerator()
    doc = c.generate_plan(prompts)
    return doc

@app.get("/generateSummarization")
async def generateDocSummary(title, strategic_prompt):


    prompts = [
        {
            "title": title,
            "strategic_prompt": strategic_prompt,
        }
    ]

    sd = SummaryDocumentGenerator()
    doc = sd.generate_summary(prompts)
    return doc
