import uvicorn
from fastapi import FastAPI

from document.generator import DocumentGenerator

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/generateDocument")
async def generateDoc():

    c = DocumentGenerator()
    doc = c.generate_plan()
    return doc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

