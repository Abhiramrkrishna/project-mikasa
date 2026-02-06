import json
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from memory import get_retriever
from tools import search_jobs
from templates import LATEX_COVER_LETTER

load_dotenv()

class MikasaAgent:
    def __init__(self):
        # Temp 0 for logic (Precision), Temp 0.6 for writing (Flow)
        self.llm_logic = ChatOpenAI(model="gpt-4o", temperature=0)
        self.llm_scribe = ChatOpenAI(model="gpt-4o", temperature=0.6)
        self.retriever = get_retriever()
        
        # --- STRATEGY PROMPT ---
        self.analysis_prompt = PromptTemplate.from_template(
            """
            You are Mikasa. Analyze this PhD/Job posting.
            
            JOB: {job_str}
            CANDIDATE: {resume_context}
            
            TASK:
            1. Extract Requirements (ECTS, docs, rules).
            2. Check for Red Flags (Language, ECTS).
            3. Formulate the "Hook".
            
            OUTPUT JSON ONLY (No markdown, no conversation):
            {{
                "score": 88,
                "university": "University Name",
                "department": "Department Name",
                "winning_factor": "...",
                "red_flags": ["Requires C2 German"],
                "requirements_checklist": ["Merge CV", "2 References"]
            }}
            """
        )

        # --- SCRIBE PROMPT ---
        self.scribe_prompt = PromptTemplate.from_template(
            """
            Write the BODY CONTENT for a cover letter.
            
            TONE: Academic, humble but confident.
            STRUCTURE:
            1. Hook: Connect Master's Thesis (Hardware Security/PINNs) to their topic.
            2. Tech: Digital Twins/ROS/Optimization.
            3. Lab Fit: Why this specific lab?
            4. Closing.
            
            CONTEXT:
            - Job: {job_title} at {university}
            - Winning Factor: {winning_factor}
            - Resume Context: {resume_context}
            
            IMPORTANT: Return ONLY the raw body text. Do NOT use markdown code blocks. Do NOT say "Here is the letter".
            Use \\par between paragraphs.
            """
        )

    def extract_json(self, text):
        """
        Robustly extracts JSON object from LLM response, handling markdown wrapping.
        """
        try:
            # Try parsing directly first
            return json.loads(text)
        except:
            # If that fails, look for { ... } pattern
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return None

    def clean_latex_output(self, text):
        """
        Removes conversational filler and markdown blocks from the Scribe output.
        """
        # Remove ```latex ... ``` blocks
        text = re.sub(r'```latex', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```', '', text)
        
        # Remove conversational intros (basic heuristic)
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            if "certainly" in line.lower() or "here is" in line.lower():
                continue
            clean_lines.append(line)
            
        return "\n".join(clean_lines).strip()

    def analyze_job(self, job):
        relevant_docs = self.retriever.invoke(job['content'])
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        chain = self.analysis_prompt | self.llm_logic | StrOutputParser()
        
        try:
            response = chain.invoke({
                "job_str": str(job),
                "resume_context": context_text
            })
            
            analysis = self.extract_json(response)
            
            if not analysis:
                raise ValueError("Could not parse JSON")

            # --- SANITIZATION LAYER ---
            bad_titles = ["portal", "search", "jobs", "careers", "home", "welcome"]
            if any(x in job['title'].lower() for x in bad_titles):
                job['title'] = f"PhD Position at {analysis.get('university', 'University')}"
            
            return analysis, context_text
            
        except Exception as e:
            # Graceful Fallback
            return {
                "score": 0, 
                "university": "Unknown", 
                "red_flags": [f"Analysis Error: {str(e)[:50]}"], 
                "winning_factor": "N/A"
            }, ""

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
        chain = self.scribe_prompt | self.llm_scribe | StrOutputParser()
        
        raw_body = chain.invoke({
            "job_title": target['title'],
            "university": target.get('university', 'the University'),
            "winning_factor": target.get('winning_factor', 'Strong Research Fit'),
            "resume_context": target['resume_context']
        })
        
        # Clean the output
        clean_body = self.clean_latex_output(raw_body)
        
        full_latex = LATEX_COVER_LETTER.format(
            university_name=target.get('university', 'University Name'),
            department_name=target.get('department', ''),
            job_title=target['title'],
            body_content=clean_body
        )
        return full_latex

    def generate_proposal_skeleton(self, target):
        prompt = PromptTemplate.from_template("Draft Proposal Skeleton for {job_title}")
        chain = prompt | self.llm_scribe | StrOutputParser()
        return chain.invoke({"job_title": target['title']})