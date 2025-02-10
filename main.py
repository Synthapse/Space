import uvicorn
from fastapi import FastAPI

from document.generic_plan_generator import GenericDocumentGenerator
from document.space_engineering.plan_generator import DocumentGenerator
from document.summary_generator import SummaryDocumentGenerator

app = FastAPI()


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
            "mission_name": title,
            "objectives": objective,
            "strategic_prompt": strategic_prompt,
        }
    ]

    c = GenericDocumentGenerator()
    doc = c.generate_plan(prompts)
    return doc

@app.get("/generateSummarization")
async def generateDocSummary():

    sd = SummaryDocumentGenerator()
    doc = sd.generate_summary()
    return doc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
