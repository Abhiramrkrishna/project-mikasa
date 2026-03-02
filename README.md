# ⚔️ Mikasa V2: AI Job Scout & Application Agent

An end-to-end, agentic Retrieval-Augmented Generation (RAG) system designed to automate the discovery, analysis, and application process for highly technical academic (PhD) and industry positions.

Mikasa acts as an intelligent career proxy: it scouts the web for hidden job postings, cross-references the requirements against your personal resume using a vector database, flags compliance risks, and dynamically generates compilation-ready LaTeX cover letters and research proposal skeletons.

## ✨ Key Features

* **Intelligent Web Scouting (Bypassing Aggregators):** Uses the Tavily API combined with custom heuristic filtering and domain blacklists to ignore generic job boards (LinkedIn, Indeed, etc.) and find direct, high-quality job postings.
* **RAG-Powered Profile Matching:** Ingests your personal resume (PDF) into a ChromaDB vector store using OpenAI's `text-embedding-3-small`. The agent uses this context to deeply understand your background (e.g., Mechatronics, PINNs, Machine Learning).
* **Dual-LLM Orchestration:** Utilizes GPT-4o with distinct temperature settings:
    * *Logic Agent (Temp 0.0):* Analyzes job requirements, extracts ECTS/language compliance, and flags potential red flags.
    * *Scribe Agent (Temp 0.6):* Drafts highly tailored, academic-toned text based on the logical analysis and RAG context.
* **Automated Document Generation:** Generates customized, compilation-ready LaTeX cover letters and research proposal skeletons directly in the chat interface.
* **Interactive UI:** Built with Chainlit for a responsive, real-time conversational experience with color-coded job scoring and downloadable artifacts.

## 🛠️ Tech Stack

* **LLM & Orchestration:** OpenAI (GPT-4o), LangChain
* **Vector Database & RAG:** ChromaDB, PyPDFLoader, OpenAI Embeddings
* **Web Search API:** Tavily
* **Frontend UI:** Chainlit
* **Formatting:** LaTeX (Automated Document Generation)

## 📂 Project Structure

* `app.py`: Main Chainlit application and chat interface logic.
* `agents.py`: Contains the `MikasaAgent` class, handling the LangChain prompts, LLM invocations, and JSON parsing.
* `memory.py`: Handles the ingestion, chunking, and ChromaDB vectorization of the user's resume.
* `tools.py`: Manages the Tavily search integration, query formulation, and aggressive filtering of generic job portals.
* `templates.py`: Stores the raw LaTeX template used for dynamic cover letter generation.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/mikasa-job-scout.git](https://github.com/yourusername/mikasa-job-scout.git)
   cd mikasa-job-scout
   ```
   
