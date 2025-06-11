# Document Analyzer

This is a Streamlit application for analyzing documents. You can enter a prompt and upload a PDF or Word document, and the app will apply your prompt to each paragraph and display a diff of suggested changes.

## Setup

1. Copy `.env.example` to `.env` and set your OpenAI API key:

   ```bash
   cp .env.example .env
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   streamlit run doc_analyzer.py
   ```

## Usage

- Enter a prompt describing how you want to revise the document.
- Upload a PDF or Word document.
- The app will process each paragraph using OpenAI and show a unified diff of the changes.