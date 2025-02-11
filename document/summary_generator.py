import google.generativeai as genai
from fastapi import FastAPI
import uuid
import time
import os
import re
from fastapi.responses import FileResponse

app = FastAPI()


# Gemini limits:
# 15 RPM (requests per minute)
# 1 million TPM (tokens per minute)
# 1.5K RPD (requests per day)

class SummaryDocumentGenerator:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_api_key = "AIzaSyCOOnCXXPIaG1mJ0TLjgoZHQt7JZ4y-gn0"

    def configure_model(self):
        genai.configure(api_key=self.gemini_api_key)
        return genai.GenerativeModel('gemini-pro'), genai.GenerativeModel('gemini-pro-vision')

    def generate_summary(self, doc_prompts):
        text_model, image_model = self.configure_model()

        for prompt in doc_prompts:
            title = prompt["title"]

            # Step 1: Generate Summary Overview
            response = text_model.generate_content(prompt["strategic_prompt"])
            summary_overview = response.text[:300]  # Shortened initial overview

            print(f"Overview: {summary_overview}")

            # Step 2: Extract Key Themes
            print("Extracting Key Themes...")
            key_themes = self.extract_key_themes(title, summary_overview, text_model)
            print("Key Themes Extracted.")

            # Step 3: Identify Important Insights
            print("Identifying Important Insights...")
            insights = self.extract_insights(title, summary_overview, text_model)
            print("Insights Identified.")

            # Step 4: Determine Actionable Takeaways
            print("Generating Actionable Takeaways...")
            takeaways = self.extract_takeaways(title, summary_overview, text_model)
            print("Takeaways Generated.")

            # Step 5: Gather Supporting Evidence (Optional)
            print("Extracting Supporting Evidence...")
            supporting_evidence = self.extract_evidence(title, summary_overview, text_model)
            print("Supporting Evidence Extracted.")

            # Organize into structured output
            summary_content = {
                "overview": summary_overview,
                "key_themes": key_themes,
                "important_insights": insights,
                "actionable_takeaways": takeaways,
                "supporting_evidence": supporting_evidence
            }

            # Generate final summary PDF
            # doc = self.generate_pdf(title, summary_content)
            return null
            # return doc

    def extract_key_themes(self, title, summary_overview, text_model):
        prompt = f"""
            This is a summary of a document related to {title}:
            "{summary_overview}"

            Identify the key themes or topics discussed in the document.
            Return a list of main themes without excessive details.
        """

        response = text_model.generate_content(prompt)
        return self.parse_list(response.text)  # Convert to structured list

    def extract_insights(self, title, summary_overview, text_model):
        prompt = f"""
            This is a summary of a document related to {title}:
            "{summary_overview}"

            Extract the most important insights from the document.
            Focus on key learnings, statistics, or conclusions.
        """

        response = text_model.generate_content(prompt)
        return self.parse_list(response.text)  # Convert to structured list

    def extract_takeaways(self, title, summary_overview, text_model):
        prompt = f"""
            This is a summary of a document related to {title}:
            "{summary_overview}"

            Provide the most actionable takeaways from the document.
            These should be recommendations or practical applications.
        """

        response = text_model.generate_content(prompt)
        return self.parse_list(response.text)  # Convert to structured list

    def extract_evidence(self, title, summary_overview, text_model):
        prompt = f"""
            This is a summary of a document related to {title}:
            "{summary_overview}"

            Identify any supporting evidence or references mentioned in the document.
            This can include key statistics, studies, quotes, or expert opinions.
        """

        response = text_model.generate_content(prompt)
        return self.parse_list(response.text)  # Convert to structured list

    def parse_list(self, text):
        # Splitting into list format (Assuming AI returns comma or newline-separated values)
        items = [line.strip("-• ") for line in text.split("\n") if line.strip()]
        return items


