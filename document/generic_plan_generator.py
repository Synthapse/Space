import google.generativeai as genai
from fastapi import FastAPI

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate

from fastapi.responses import FileResponse
import time
import os
import re
from datetime import datetime

app = FastAPI()


# Gemini limits:
# 15 RPM (requests per minute)
# 1 million TPM (tokens per minute)
# 1.5K RPD (requests per day)

class GenericDocumentGenerator:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_api_key = "AIzaSyCOOnCXXPIaG1mJ0TLjgoZHQt7JZ4y-gn0"
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

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

            if len(phases_content) > 0:
                for i in range(1):
                #for i in range(phases_num):

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
            
            Include a timeline and brief description for each phase. This should contains 3-5 phases.
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

    def _add_custom_styles(self):
        # Adding custom styles to enhance aesthetics
        self.styles.add(ParagraphStyle(name="CHeading1", fontSize=40, alignment=1, textColor=colors.darkblue, fontName="Helvetica-Bold", leading=48))
        self.styles.add(ParagraphStyle(name="CHeading2", fontSize=20, alignment=0, textColor=colors.navy, fontName="Helvetica-Bold", leading=24))
        self.styles.add(ParagraphStyle(name="CHighNormal", fontSize=16, alignment=0, textColor=colors.black, fontName="Helvetica", spaceAfter=16))
        self.styles.add(ParagraphStyle(name="CNormal", fontSize=12, alignment=0, textColor=colors.gray, fontName="Helvetica", spaceAfter=12))
        self.styles.add(ParagraphStyle(name="CSubtitle", fontSize=14, alignment=1, textColor=colors.gray, fontName="Helvetica-Oblique"))
        self.styles.add(ParagraphStyle(name="CListItem", fontSize=12, bulletFontName="Helvetica", bulletFontSize=12, leftIndent=20, spaceAfter=6))

    def generate_pdf(self, title, plan_content):
        # Set up the PDF document
        file_name = f"{title.replace(' ', '_')}.pdf"
        file_path = os.path.join("pdfs", file_name)
        os.makedirs("pdfs", exist_ok=True)
        
        document = SimpleDocTemplate(file_path, pagesize=A4)
        document.title = title

        width, height = A4
        frame = Frame(0, 0, width, height - 100, id='normal')  # Leave space for the title page

        # Create the custom page template with navy background on the first page
        custom_page_template = PageTemplate(id='title', onPage=self.add_title_page, frames=[frame])
        document.addPageTemplates([custom_page_template])
        elements = []

        elements.append(PageBreak())
        # Mission Overview
        self.parse_and_add_content(elements, plan_content["mission_overview"])
        # Phases
        self.add_phases(elements, plan_content)
        # Build PDF
        document.build(elements)

        return FileResponse(file_path, media_type="application/pdf", filename=file_name)

    def add_title_page(self, canvas, doc):
        # Get page dimensions
        width, height = A4
        
        # Set navy blue background
        canvas.setFillColor(colors.navy)
        canvas.rect(0, 0, width, height, fill=True, stroke=False)

        # Set text properties
        canvas.setFillColor(colors.white)  # White text for contrast
        canvas.setFont("Helvetica-Bold", 24)

        # Add Title (Centered at the top)
        title = doc.title
        canvas.drawCentredString(width / 2, height - 100, title)

        # Add Date (Below title)
        canvas.setFont("Helvetica", 14)
        current_date = datetime.now().strftime("%B %d, %Y")  # Format: February 11, 2025
        canvas.drawCentredString(width / 2, height - 140, f"Date: {current_date}")

        # Add Generation Info (Below date)
        canvas.setFont("Helvetica-Oblique", 12)
        canvas.drawCentredString(width / 2, height - 170, "Generated by Authentic Scope / Gemini")


    ## 11.02.2025 -> It's depends on the "*" sugn
    def parse_and_add_content(self, elements, content):
        # Get the standard styles
        styles = getSampleStyleSheet()
        normal_style = self.styles["CNormal"]
        bold_style = self.styles["CHeading2"]
        bullet_style = self.styles["CListItem"]
        
        # Split the content into lines (assuming paragraphs are separated by newlines)
        lines = content.split('\n')
        
        # Process each line
        for i, line in enumerate(lines):
            # Make the first line in the section a header (if not already bolded)
            if i == 0:
                header_paragraph = Paragraph(f"<b>{line.strip()}</b>", bold_style)
                elements.append(header_paragraph)
                elements.append(Spacer(1, 12))
                continue
            
            # Check if it's a bullet point (starts with '*')
            if line.strip().startswith('*'):
                # Remove the '*' and any extra spaces
                bullet_point = line.strip()[1:].strip()
                
                # Bold the text before the colon
                bullet_point = re.sub(r'^(.*?)(:)', r'<b>\1</b>\2', bullet_point)
                
                bullet_paragraph = Paragraph(f"• {bullet_point}", bullet_style)
                elements.append(bullet_paragraph)
                elements.append(Spacer(1, 6))
            
            # Check if it has bold text (surrounded by '**')
            elif '**' in line:
                # Replace '**' with <b> for HTML-like formatting
                formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                bold_paragraph = Paragraph(formatted_text, bold_style)
                elements.append(bold_paragraph)
                elements.append(Spacer(1, 6))
            
            # If it's normal text (neither bold nor a bullet point)
            else:
                formatted_text = line.strip()
                normal_paragraph = Paragraph(formatted_text, normal_style)
                elements.append(normal_paragraph)
                elements.append(Spacer(1, 6))

        elements.append(PageBreak())  # Optionally, you can add a page break after content


    def parse_phase(self, phase_string):
        # If phase_string is a set, extract its single value
        if isinstance(phase_string, set):
            if len(phase_string) == 1:  # Ensure it's not an empty or multi-value set
                phase_string = next(iter(phase_string))  # Extract the single element
            else:
                raise ValueError(f"Expected a set with one element, but got: {phase_string}")

        if not isinstance(phase_string, str):
            raise TypeError(f"Expected a string, but got {type(phase_string).__name__}")

        # Debugging: Print the phase_string before processing
        print(f"Parsing phase string: {phase_string}")

        # Adjusted regex pattern for flexibility
        match = re.search(r'Phase\s*\d+\s*[:-]?\s*(.*)', phase_string, re.IGNORECASE)

        if match:
            result = match.group(1).strip()  # Return the phase name without leading/trailing spaces
            print(f"Extracted Phase Name: {result}")  # Debugging output
            return result
        
        print("No match found!")  # Debugging output
        return phase_string

    def add_phases(self, elements, plan_content):
        for i, phase in enumerate(plan_content["phases"], start=1):
            # Phase Title
            self.add_phase_title(elements, phase, i)

            # Objectives and Sub-Points
            self.add_objectives_and_subpoints(elements, phase)

            # Resources
            self.add_resources(elements, phase)

            if i < len(plan_content["phases"]) - 1:  # Add page break between phases if not the last
                elements.append(PageBreak())

    def add_phase_title(self, elements, phase, phase_number):
        phase_title_style = self.styles["CHeading2"]

        parsed_phase = self.parse_phase(phase['phase'])

        phase_title = Paragraph(f"<b>Phase {phase_number}: {parsed_phase}</b>", phase_title_style)
        elements.append(phase_title)
        elements.append(Spacer(1, 16))

    def add_objectives_and_subpoints(self, elements, phase):
        for j, objective_data in enumerate(phase["objectives"]):
            objective_style = self.styles["CHighNormal"]
            objective_title = Paragraph(f"<b>{j+1}. {objective_data['objective']}</b>", objective_style)
            elements.append(objective_title)
            elements.append(Spacer(1, 8))
            
            for sub_point in objective_data['sub_points']:
                sub_point_style = self.styles["CNormal"]
                sub_point_para = Paragraph(f"- {sub_point}", sub_point_style)
                elements.append(sub_point_para)
                elements.append(Spacer(1, 2))

    def add_resources(self, elements, phase):
        resources_title_style = self.styles["CHeading2"]
        resources_title = Paragraph("<b>Resources</b>", resources_title_style)
        elements.append(resources_title)
        elements.append(Spacer(1, 16))

        for category, items in phase["resources"].items():
            self.add_resource_category(elements, category, items)

    def add_resource_category(self, elements, category, items):
        resources_category_style = self.styles["CHighNormal"]
        category_title = Paragraph(f"<b>{category}:</b>", resources_category_style)
        elements.append(category_title)
        elements.append(Spacer(1, 8))
        
        for item in items:
            resource_item_style = self.styles["CNormal"]
            resource_item = Paragraph(f"- {item['name']}: {item['description']}", resource_item_style)
            elements.append(resource_item)
            elements.append(Spacer(1, 4))