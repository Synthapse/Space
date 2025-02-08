import uvicorn
from fastapi import FastAPI

from document.generator import DocumentGenerator

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/generateDocument")
async def generateDoc():
    space_prompts = [
        {
            "mission_name": "Lunar mining",
            "objectives": "Land and start minning the key resources (Helium-3) and Earth Rare Resources on moon, with detecting water ice and mapping geological structures",
        }
    ]

    c = DocumentGenerator()
    prompts = c.generate_strategic_prompt(space_prompts)
    doc = c.generate_plan(prompts)
    return doc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
