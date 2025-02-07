import google.generativeai as genai
from fastapi import FastAPI
from fpdf import FPDF
import uuid
import os

app = FastAPI()


class DocumentGenerator:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_api_key = "AIzaSyCOOnCXXPIaG1mJ0TLjgoZHQt7JZ4y-gn0"

    def configure_model(self):
        genai.configure(api_key=self.gemini_api_key)
        return genai.GenerativeModel('gemini-pro'), genai.GenerativeModel('gemini-pro-vision')

    def generate_plan(self):

        space_prompts = [
          {
            "mission_name": "Lunar AI Research Assistant",
            "objectives": "Deploy an AI-powered rover on the Moon to autonomously analyze soil composition, detect water ice, and map geological structures."
          },
          {
            "mission_name": "Autonomous Space Debris Removal",
            "objectives": "Develop an AI-controlled satellite capable of identifying, capturing, and safely disposing of space debris to reduce orbital clutter."
          },
          {
            "mission_name": "Exoplanet Data Analysis AI",
            "objectives": "Use AI to process and analyze vast amounts of data from space telescopes, identifying Earth-like planets and potential biosignatures."
          },
          {
            "mission_name": "AI-Powered Martian Colony Optimization",
            "objectives": "Implement AI systems to optimize resource distribution, habitat sustainability, and communication for future Mars colonists."
          },
          {
            "mission_name": "Deep Space AI Navigation System",
            "objectives": "Design an AI-driven navigation system that enables autonomous spacecraft travel between planets, reducing reliance on ground-based mission control."
          }
        ]

        text_model, image_model = self.configure_model()

        for prompt in space_prompts:

            # 07.02.2025 -> It may be some kind of title of generated raport
            mission_name = prompt["mission_name"]

            prompt = f"""
                Generate a structured plan for a space AI mission with the following details:
                Mission Name: {mission_name}
                Objectives: {prompt["objectives"]}
                """

            response = text_model.generate_content(prompt)
            plan_text = response.text
            self.generate_pdf(mission_name, plan_text)



    def generate_pdf(self, title, content):

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=16)
        pdf.cell(200, 10, title, ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)

        file_name = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join("pdfs", file_name)

        os.makedirs("pdfs", exist_ok=True)
        pdf.output(file_path)

        return {"message": "Mission plan PDF generated successfully", "file_path": file_path}
