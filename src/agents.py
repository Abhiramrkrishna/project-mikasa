import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from memory import get_retriever
from tools import search_jobs
from templates import LATEX_COVER_LETTER # Import the template

load_dotenv()

class MikasaAgent:
    def __init__(self):
        # Temp 0 for Logic, Temp 0.6 for Writing (Natural but not hallucinating)
        self.llm_logic = ChatOpenAI(model="gpt-4o", temperature=0)
        self.llm_scribe = ChatOpenAI(model="gpt-4o", temperature=0.6)
        self.retriever = get_retriever()
        
        # --- 1. COMPLIANCE & STRATEGY PROMPT ---
        self.analysis_prompt = PromptTemplate.from_template(
            """
            You are Mikasa. Analyze this PhD/Job posting with extreme scrutiny.
            
            JOB: {job_str}
            CANDIDATE: {resume_context}
            
            TASK:
            1. Extract Application Requirements (ECTS, specific docs, reference letters, merging rules).
            2. Check for "Red Flags" (e.g., Requires fluent German, Requires 300 ECTS, Requires C++ expert).
            3. Formulate the "Hook" (How his thesis/projects solve their specific problem).
            
            OUTPUT JSON:
            {{
                "score": 88,
                "university": "University Name",
                "department": "Department Name",
                "winning_factor": "...",
                "red_flags": ["Requires C2 German", "Needs 300 ECTS"],
                "requirements_checklist": [
                    "Merge CV and Letter into one PDF",
                    "Include 2 Reference contacts",
                    "Mention Supervisor Name"
                ]
            }}
            """
        )

        # --- 2. HUMANE SCRIBE PROMPT ---
        self.scribe_prompt = PromptTemplate.from_template(
            """
            Write the BODY CONTENT for a cover letter. 
            Do NOT write the header, date, or signature (these are in LaTeX).
            
            TONE: "Humane," academic, humble but confident. 
            STYLE: Use the user's preferred structure:
            1. Paragraph 1: Hook based on Master's Thesis (Hardware Security/PINNs) matching their topic.
            2. Paragraph 2: Technical depth (Digital Twins/ROS/Optimization).
            3. Paragraph 3: Why THIS lab/professor? (Connect to their recent work).
            4. Conclusion: Eagerness for interview.
            
            CONTEXT:
            - Job: {job_title} at {university}
            - Winning Factor: {winning_factor}
            - Resume Context: {resume_context}
            
            Write ONLY the body paragraphs (LaTeX formatted text). 
            Use \\par between paragraphs. 
            """
        )

    def analyze_job(self, job):
        relevant_docs = self.retriever.invoke(job['content'])
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        chain = self.analysis_prompt | self.llm_logic | StrOutputParser()
        
        try:
            response = chain.invoke({
                "job_str": str(job),
                "resume_context": context_text
            })
            clean_json = response.replace("```json", "").replace("```", "")
            return json.loads(clean_json), context_text
        except Exception as e:
            return {"score": 0, "requirements_checklist": [], "red_flags": ["Error"]}, ""

    def start_mission(self, query):
        raw_jobs = search_jobs(query, max_results=5)
        targets = []
        for job in raw_jobs:
            analysis, context = self.analyze_job(job)
            full_report = {**job, **analysis, "resume_context": context}
            targets.append(full_report)
        targets.sort(key=lambda x: x.get('score', 0), reverse=True)
        return targets

    def generate_latex_letter(self, target):
        """Generates the full .tex file content"""
        chain = self.scribe_prompt | self.llm_scribe | StrOutputParser()
        
        body = chain.invoke({
            "job_title": target['title'],
            "university": target.get('university', 'the University'),
            "winning_factor": target.get('winning_factor', 'Strong Research Fit'),
            "resume_context": target['resume_context']
        })
        
        # Fill the Template
        full_latex = LATEX_COVER_LETTER.format(
            university_name=target.get('university', 'University Name'),
            department_name=target.get('department', ''),
            job_title=target['title'],
            body_content=body
        )
        return full_latex

    def generate_proposal_skeleton(self, target):
        """Creates a Research Proposal Outline"""
        prompt = PromptTemplate.from_template(
            """
            Draft a Research Proposal SKELETON for this PhD.
            Title: Create a novel title combining "{job_title}" and "Physics-Informed Digital Twins".
            
            Structure:
            1. Abstract (100 words)
            2. Research Gap (Why their current methods are slow/inaccurate)
            3. Proposed Methodology (How Abhiram will use GNNs/PINNs to fix it)
            4. Timeline (Year 1-3)
            
            Return in Markdown format.
            """
        )
        chain = prompt | self.llm_scribe | StrOutputParser()
        return chain.invoke({"job_title": target['title']})