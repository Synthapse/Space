import google.generativeai as genai
from fastapi import FastAPI
from fpdf import FPDF
from fastapi.responses import FileResponse
import time
import os
import re

app = FastAPI()


# Gemini limits:
# 15 RPM (requests per minute)
# 1 million TPM (tokens per minute)
# 1.5K RPD (requests per day)

class GenericDocumentGenerator:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_api_key = "AIzaSyCOOnCXXPIaG1mJ0TLjgoZHQt7JZ4y-gn0"

    def configure_model(self):
        genai.configure(api_key=self.gemini_api_key)
        return genai.GenerativeModel('gemini-pro'), genai.GenerativeModel('gemini-pro-vision')

    def generate_plan(self, doc_prompts):

        text_model, image_model = self.configure_model()
        for prompt in doc_prompts:

            title = prompt["title"]
            objectives = prompt["objectives"]

            response = text_model.generate_content(prompt["strategic_prompt"])
            strategic_overview = response.text

            print(f"Overview: {strategic_overview}")
            summarization_strategic_overview = strategic_overview[:300]

            # Step 2: Generate Phases
            print("Phases Generating...")
            phases_num, phases_content = self.generate_phases(title, summarization_strategic_overview, text_model)

            print("Phases Generated")
            phases = []

            for i in range(phases_num):

                print(f"Objectives in Phase {i} Generating...")
                time.sleep(5)
                phase = phases_content[i]
                objectives = self.generate_objectives(title, phase, objectives, text_model)

                print(f"Objectives in Phase {i} Generated")
                print(f"Resources in Phase {i} Generating...")
                time.sleep(5)
                resources = self.generate_resources(title, phase, text_model)
                print(f"Resources in Phase {i} Generated...")


                phase_data = {
                    "phase": phases_content[i],
                    "objectives": objectives,
                    "resources": resources
                }

                phases.append(phase_data)

            # Objectives per phase & resources per objective in phase!

            plan_content = {
                "mission_overview": strategic_overview,
                "phases": phases
            }
            doc = self.generate_pdf(title, plan_content)
            return doc

    def generate_phases(self, title, strategic_overview, text_model):
        prompt = f"""
            This is title: {title}
            This is strategic overview: {strategic_overview}
            
            Include a timeline and brief description for each phase.
            Phases should cover all stages of the project, from preparation to completion.
        """

        response = text_model.generate_content(prompt)
        # Parse and structure the response (you may need additional parsing logic here)
        return self.parse_phases(response.text)

    def generate_objectives(self, title, phase, objectives, text_model):
        prompt = f"""
            For the title '{title}' with main objectives '{objectives}', 
            during the phase '{phase}',

            Generate detailed and specific objectives. 
            Each objective should include a short title, followed by 5 detailed sub-points explaining the objective.

            Format them like this:
            1. Objective Title
               - Sub-point 1
               - Sub-point 2
               - Sub-point 3
               - Sub-point 4
               - Sub-point 5
        """

        response = text_model.generate_content(prompt)

        # Debugging: Print AI Response
        print("AI Response:\n", response.text)

        objectives_text = response.text.strip()

        if not objectives_text:
            return []  # Return empty list if AI fails to generate content

        objectives_list = []
        current_objective = None

        # Split response into lines and process each line
        for line in objectives_text.split("\n"):
            line = line.strip()
            if not line:
                continue  # Skip empty lines


            match = re.match(r"\*\*(\d+)\.\s(.+?)\*\*|(\d+)\.\s\*\*(.+?)\*\*", line)
            if match:
                # If an objective is found, save the previous one
                if current_objective:
                    objectives_list.append(current_objective)

                # Capture the objective name based on the match
                objective_name = match.group(2) or match.group(4)

                current_objective = {
                    "objective": objective_name.strip(),
                    "sub_points": []
                }
            elif line.startswith("-") and current_objective:  # Detect sub-points
                sub_point = line.lstrip("-").strip()
                current_objective["sub_points"].append(sub_point)

        # Add the last objective if it's valid
        if current_objective:
            objectives_list.append(current_objective)

        return objectives_list

    def generate_resources(self, title, phase, text_model):
        prompt = f"""
            For the mission '{title}', in the phase '{phase}'.',

            Generate a structured list of all required resources.  
            Include key resource categories such as **Hardware, Personnel, Equipment, Money, Minerals, etc.**  
            Provide a brief description for each resource, explaining its role in the mission.

            Format them like this:
            **Category Name**
            - Resource 1: Description
            - Resource 2: Description
        """

        response = text_model.generate_content(prompt)

        # Debugging: Print AI Response to verify formatting
        print("AI Response:\n", response.text)

        resources_text = response.text.strip()

        if not resources_text:
            return {}  # Return empty dict if AI fails to generate content

        structured_resources = {}
        current_category = None

        for line in resources_text.split("\n"):
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            # Detect category (e.g., "**Hardware**")
            category_match = re.match(r"\*\*(.+?)\*\*", line)
            if category_match:
                current_category = category_match.group(1).strip()
                structured_resources[current_category] = []
            elif line.startswith("-") and current_category:  # Detect resource items
                parts = line.lstrip("-").split(":", 1)
                resource_name = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else "No description provided."
                structured_resources[current_category].append({"name": resource_name, "description": description})

        return structured_resources

    def parse_phases(self, phases_text):
        # Parse the text response into a structured format (you can customize this as needed)
        phases_num = 0
        phases = []
        for line in phases_text.split("\n"):
            if line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    phases_num = phases_num + 1
                    phase_title, phase_details = parts
                    phases.append({phase_title.strip() + phase_details.strip()})
        return phases_num, phases


    def generate_pdf(self, title, plan_content):
        pdf = FPDF("P", "mm", "A4")
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=20)  # Automatic page breaks

        # Title Page
        pdf.add_page()
        pdf.set_font("Arial", style="B",size=36)
        pdf.cell(0, 20, f"{title}", 0, 1, "C")
        pdf.set_font("Arial", size=16)
        pdf.cell(0, 10, "Generated by Gemini", 0, 1, "C") # Add a small note
        pdf.ln(20) # Add more space before the overview

        # Mission Overview
        pdf.set_font("Arial", style="B", size=20)
        pdf.set_font("Arial", size=14)
        pdf.multi_cell(0, 10, plan_content.get("mission_overview", "No overview provided."))
        pdf.add_page()

        for i, phase in enumerate(plan_content["phases"], start=1):
            pdf.set_font("Arial", style="B", size=24)
            pdf.multi_cell(0, 10, f"Phase {i}: {phase['phase']}")

        pdf.add_page()
        pdf.ln(15)

        # Phases
        for i, phase in enumerate(plan_content["phases"]):
            pdf.set_font("Arial", style="B", size=24)
            pdf.cell(0, 15, f"Phase {i+1}: {phase['phase']}", 0, 1)
            pdf.ln(10)

            # Objectives
            for j, objective_data in enumerate(phase["objectives"]):
                pdf.set_font("Arial",style="B", size=18)
                pdf.cell(0, 12, f"{j+1}. {objective_data['objective']}", 0, 1)
                pdf.set_font("Arial", size=14)
                for sub_point in objective_data['sub_points']:
                    pdf.multi_cell(0, 8, "- " + sub_point, 0, 1)  # Increased indent
                pdf.ln(8)

            # Resources
            pdf.set_font("Arial", style="B", size=18)
            pdf.cell(0, 12, "Resources", 0, 1)
            pdf.set_font("Arial", size=14)

            for category, items in phase["resources"].items():
                pdf.set_font("Arial", style="B", size=14)
                pdf.cell(0, 10, category, 0, 1)
                pdf.set_font("Arial", size=14) # Consistent font size
                for item in items:
                    pdf.multi_cell(0, 8, "- " + item['name'] + ": " + item['description'], 0, 1) # Increased indent
                pdf.ln(5)

            if i < len(plan_content["phases"]) - 1: # Add page break between phases if not the last phase
                pdf.add_page()


        file_name = f"{title.replace(' ', '_')}.pdf"
        file_path = os.path.join("pdfs", file_name)
        os.makedirs("pdfs", exist_ok=True)
        pdf.output(file_path)
        return FileResponse(file_path, media_type="application/pdf", filename=file_name)


