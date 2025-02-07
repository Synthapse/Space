import google.generativeai as genai
from fastapi import FastAPI
from fpdf import FPDF
import uuid
import os

app = FastAPI()


# Gemini limits:
# 15 RPM (requests per minute)
# 1 million TPM (tokens per minute)
# 1.5K RPD (requests per day)

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
          # {
          #   "mission_name": "Autonomous Space Debris Removal",
          #   "objectives": "Develop an AI-controlled satellite capable of identifying, capturing, and safely disposing of space debris to reduce orbital clutter."
          # },
          # {
          #   "mission_name": "Exoplanet Data Analysis AI",
          #   "objectives": "Use AI to process and analyze vast amounts of data from space telescopes, identifying Earth-like planets and potential biosignatures."
          # },
          # {
          #   "mission_name": "AI-Powered Martian Colony Optimization",
          #   "objectives": "Implement AI systems to optimize resource distribution, habitat sustainability, and communication for future Mars colonists."
          # },
          # {
          #   "mission_name": "Deep Space AI Navigation System",
          #   "objectives": "Design an AI-driven navigation system that enables autonomous spacecraft travel between planets, reducing reliance on ground-based mission control."
          # }
        ]

        text_model, image_model = self.configure_model()

        for prompt in space_prompts:

            # 07.02.2025 -> It may be some kind of title of generated raport
            mission_name = prompt["mission_name"]
            objectives = prompt["objectives"]

            prompt = f"""
                Generate a structured plan for the space mission with the following details:
                Mission Name: {mission_name}
                Objectives: {objectives}

                Please include:
                1. Phases: Break the mission into distinct phases with detailed descriptions (timeline, actions, and goals).
                2. Resources: List all the resources required (AI systems, equipment, personnel, etc.) and their roles in the mission.
            """

            response = text_model.generate_content(prompt)
            plan_text = response.text

            # Step 1: Generate Objectives (if not already provided)
            objectives_content = self.generate_objectives(mission_name, objectives, text_model)

            # Step 2: Generate Phases
            phases_content = self.generate_phases(mission_name, text_model)

            # Step 3: Generate Resources
            resources_content = self.generate_resources(mission_name, text_model)

            # Combine everything into the final structured plan
            plan_content = {
                "mission_overview": f"Mission Name: {mission_name}\nObjectives: {objectives_content}",
                "objectives": [objectives_content],
                "phases": phases_content,
                "resources": resources_content
            }


            self.generate_pdf(mission_name, plan_content)

    def generate_objectives(self, mission_name, objectives, text_model):
        prompt = f"""
            For the mission '{mission_name}', generate detailed and specific objectives. 
            The mission aims to: {objectives}
            Please list 3-5 clear and actionable objectives.
        """

        response = text_model.generate_content(prompt)
        return response.text.strip()

    def generate_phases(self, mission_name, text_model):
        prompt = f"""
            For the mission '{mission_name}', generate a list of mission phases.
            Include a timeline and brief description for each phase.
            Phases should cover all stages of the mission, from preparation to completion.
        """

        response = text_model.generate_content(prompt)
        # Parse and structure the response (you may need additional parsing logic here)
        return self.parse_phases(response.text)

    def generate_resources(self, mission_name, text_model):
        prompt = f"""
            For the mission '{mission_name}', generate a list of all required resources.
            List the key resources (AI systems, personnel, equipment, etc.) and their role in the mission.
        """

        response = text_model.generate_content(prompt)
        # Parse and structure the response (you may need additional parsing logic here)
        return self.parse_resources(response.text)

    def parse_phases(self, phases_text):
        # Parse the text response into a structured format (you can customize this as needed)
        phases = []
        for line in phases_text.split("\n"):
            if line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    phase_title, phase_details = parts
                    phases.append({"title": phase_title.strip(), "description": phase_details.strip()})
        return phases

    def parse_resources(self, resources_text):
        # Parse the text response into a structured format (you can customize this as needed)
        resources = []
        for line in resources_text.split("\n"):
            if line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    resource_name, resource_description = parts
                    resources.append({"name": resource_name.strip(), "description": resource_description.strip()})
        return resources

    def generate_pdf(self, mission_name, plan_content):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", style="B", size=16)
        pdf.cell(200, 10, f"Mission Plan {mission_name}", ln=True, align='C')
        pdf.ln(10)

        # Mission Overview
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Mission Overview', ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, plan_content["mission_overview"])
        pdf.ln(5)

        # Objectives Section
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Objectives', ln=True)
        pdf.set_font("Arial", size=12)
        for objective in plan_content["objectives"]:
            pdf.multi_cell(0, 10, f"- {objective}")
        pdf.ln(5)

        # Phases Section
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Phases', ln=True)
        pdf.set_font("Arial", size=12)
        for phase in plan_content["phases"]:
            pdf.multi_cell(0, 10, f"{phase['title']}: {phase['description']}")
            pdf.ln(5)

        # Resources Section
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Resources', ln=True)
        pdf.set_font("Arial", size=12)
        for resource in plan_content["resources"]:
            pdf.multi_cell(0, 10, f"{resource['name']}: {resource['description']}")
        pdf.ln(5)

        # Generate unique file name
        file_name = f"{mission_name}.pdf"
        file_path = os.path.join("pdfs", file_name)

        # Create the pdfs directory if it doesn't exist
        os.makedirs("pdfs", exist_ok=True)

        # Output the PDF
        pdf.output(file_path)

        return {"message": "Mission plan PDF generated successfully", "file_path": file_path}

