import google.generativeai as genai
from fastapi import FastAPI
from fpdf import FPDF
import uuid
import time
import os
import re

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


    def generate_strategic_prompt(self, prompts):

        # This prompt is different per different products like:
        # Space Hackhathon -> Different
        # Authentic Scope -> Different
        # Quality Care -> Different

        for prompt in prompts:
            strategic_overview_prompt = f"""
                    Generate a high-level overview and strategic preplan for the space mission with the following details:
                    Mission Name: {prompt.mission_name}
                    Objectives: {prompt.objectives}
    
                    The overview should provide a cohesive, strategic narrative that includes:
                    - A summary of the mission's overarching goals and purpose.
                    - An explanation of the major challenges the mission seeks to address and the broader vision it supports.
                    - Insight into the key strategies and innovations being employed to achieve success.
                    - A bird's-eye view of the mission's scope, touching on the scientific, technological, or societal impact it aims to have.
                    - A discussion on how the mission contributes to humanity's progress in space exploration, highlighting the mission’s long-term importance and strategic value.
    
                    The tone should be visionary, emphasizing the mission's impact, importance, and broader goals.
                """

            prompt['strategic_prompt'] = strategic_overview_prompt

        return prompts

    def generate_plan(self, doc_prompts):

        text_model, image_model = self.configure_model()
        for prompt in doc_prompts:

            mission_name = prompt["mission_name"]
            objectives = prompt["objectives"]

            response = text_model.generate_content(prompt["strategic_prompt"])
            strategic_overview = response.text

            print(f"Overview: {strategic_overview}")
            summarization_strategic_overview = strategic_overview[:300]

            # Step 2: Generate Phases
            print("Phases Generating...")
            phases_num, phases_content = self.generate_phases(mission_name, summarization_strategic_overview, text_model)

            print("Phases Generated")
            phases = []

            #for i in range(phases_num):
            for i in range(1):

                print(f"Objectives in Phase {i} Generating...")
                time.sleep(5)
                phase = phases_content[i]
                objectives = self.generate_objectives(mission_name, phase, objectives, text_model)

                print(f"Objectives in Phase {i} Generated")

                phase_objectives = []

                for objective in objectives:
                    resources = []

                    print(f"Resources in Objective {objective} in Phase {i} Generating...")
                    time.sleep(5)
                    resource = self.generate_resources(mission_name, phase, objective, text_model)
                    print(f"Resources in Objective {objective} in Phase {i} Generated...")
                    resources.append(resource)

                    phase_objectives.append({
                        "objective": objective,
                        "resources": resources
                    })

                phase_data = {
                    "phase": phases_content[i],
                    "objectives": phase_objectives
                }

                phases.append(phase_data)

            # Objectives per phase & resources per objective in phase!

            plan_content = {
                "mission_overview": strategic_overview,
                "phases": phases
            }
            self.generate_pdf(mission_name, plan_content)

    def generate_phases(self, mission_name, strategic_overview, text_model):
        prompt = f"""
            This is mission: {mission_name}
            This is strategic overview: {strategic_overview}
            
            Include a timeline and brief description for each phase.
            Phases should cover all stages of the mission, from preparation to completion.
        """

        response = text_model.generate_content(prompt)
        # Parse and structure the response (you may need additional parsing logic here)
        return self.parse_phases(response.text)

    import re

    def generate_objectives(self, mission_name, phase, objectives, text_model):
        prompt = f"""
            For the mission '{mission_name}' with main objectives '{objectives}', 
            during the phase '{phase}',

            Generate detailed and specific objectives. 
            Each objective should include a short title, followed by 2-4 detailed sub-points explaining the objective.

            Format them like this:
            1. Objective Title
               - Sub-point 1
               - Sub-point 2
               - Sub-point 3
        """

        response = text_model.generate_content(prompt)

        # Debugging: Print AI Response
        print("AI Response:\n", response.text)

        objectives_text = response.text.strip()

        if not objectives_text:
            return []  # Return empty list if AI fails to generate content

        objectives_list = []
        current_objective = None

        for line in objectives_text.split("\n"):
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            # Detect numbered objectives (e.g., "**1. Objective Name**")
            match = re.match(r"\*\*(\d+)\.\s(.+?)\*\*", line)
            if match:
                if current_objective:
                    objectives_list.append(current_objective)  # Save previous objective

                current_objective = {
                    "objective": match.group(2).strip(),  # Extract objective name
                    "sub_points": []
                }
            elif line.startswith("-") and current_objective:  # Detect sub-points
                current_objective["sub_points"].append(line.lstrip("-").strip())

        if current_objective:  # Add last objective
            objectives_list.append(current_objective)

        return objectives_list

    import re
    

    def generate_resources(self, mission_name, phase, objective, text_model):
        prompt = f"""
            For the mission '{mission_name}', in the phase '{phase}', for the objective '{objective}',

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


    def generate_pdf(self, mission_name, plan_content):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", style="B", size=16)
        pdf.cell(200, 10, f"Mission Plan: {mission_name}", ln=True, align='C')
        pdf.ln(10)

        # Mission Overview
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Mission Overview', ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, plan_content.get("mission_overview", "No overview provided."))
        pdf.ln(5)

        # Phases Section
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, 'Phases', ln=True)
        pdf.ln(5)

        for i, phase in enumerate(plan_content["phases"], start=1):
            pdf.set_font("Arial", style="B", size=24)
            pdf.multi_cell(0, 10, f"Phase {i}: {phase['phase']}")

        pdf.set_font("Arial", size=12)
        for i, phase in enumerate(plan_content["phases"], start=1):
            pdf.set_font("Arial", style="B", size=24)
            pdf.multi_cell(0, 10, f"Phase {i}: {phase['phase']}")
            pdf.ln(3)

            pdf.cell(0, 10, 'Objectives', ln=True)
            pdf.set_font("Arial", size=12)
            for j, objective_data in enumerate(phase["objectives"], start=1):
                pdf.multi_cell(0, 8, f"{j}. {objective_data['objective']}")
                pdf.ln(2)  # Space between objectives

                # Print sub-points under each objective
                for sub_point in objective_data.get("sub_points", []):
                    pdf.multi_cell(0, 8, f"   - {sub_point}")  # Indented sub-points
                pdf.ln(3)  # Extra spacing after sub-points

            pdf.set_font("Arial", size=12)
            for j, objective_data in enumerate(phase["objectives"], start=1):
                pdf.set_font("Arial", style="B", size=18)
                pdf.multi_cell(0, 10, f"Objective {j}: {objective_data['objective']}")
                pdf.ln(2)

                # Format lists properly
                pdf.set_font("Arial", style="B", size=14)
                pdf.multi_cell(0, 10, "Resources:")  # Category title
                pdf.ln(1)

                pdf.set_font("Arial", size=12)  # Regular font for list items
                for resource in objective_data["resources"]:
                    pdf.multi_cell(0, 8, f" - {resource}")  # Bullet point
                pdf.ln(4)  # Extra spacing after list

        # Generate unique file name
        file_name = f"{mission_name.replace(' ', '_')}.pdf"
        file_path = os.path.join("pdfs", file_name)

        # Create the pdfs directory if it doesn't exist
        os.makedirs("pdfs", exist_ok=True)

        # Output the PDF
        pdf.output(file_path)

        return {"message": "Mission plan PDF generated successfully", "file_path": file_path}


