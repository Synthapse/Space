import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse
import time

from document.generic_plan_generator import GenericDocumentGenerator
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



##


# -> Initial Requirements



# -> Summarization of Something

# -> Marketing strategy of Initial Requirements
# 1. Project Overview: Title, timeline, and purpose.
# 2. Goals & KPIs: What success looks like (and doesn’t).
# 3. Audience Details: Personas, needs, and tone.
# 4. Key Messaging: Your story, themes, and takeaways.
# 5. Deliverables & Roles: Who owns what.
# 6. Distribution Plan: Channels, tactics, and optimization.
# 7. Sales Enablement: Tools and strategies to support your sales team.

@app.post("/generateDocument")
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
    #return FileResponse(doc, media_type="application/pdf", filename="{title}.pdf")

@app.post("/generateSummarization")
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
