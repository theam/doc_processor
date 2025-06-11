"""
Streamlit application for analyzing documents.
Allows user to enter a prompt and upload a document (PDF or Word),
then applies the prompt to each paragraph and displays a diff of suggested changes.
"""
import io
import os
import re
import difflib

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI
import streamlit as st
from PyPDF2 import PdfReader
from docx import Document

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not set. Please set the environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_chunks.append(page_text)
    return "\n".join(text_chunks)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)

def analyze_paragraph(instructions: str, paragraph: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant that revises text based on the user's instructions."},
        {"role": "user", "content": f"Instructions: {instructions}\n\nParagraph:\n{paragraph}"},
    ]
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
    )
    return response.choices[0].message.content.strip()


def group_lines_into_paragraphs(text: str) -> list[str]:
    """
    Group raw text lines into coherent paragraphs and clean up line breaks using the LLM.
    Returns a list of cleaned paragraphs.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that groups lines of text into paragraphs and cleans up line breaks "
                "to restore proper paragraph structure."
            ),
        },
        {
            "role": "user",
            "content": (
                "Please group the following lines into paragraphs. Each line is separated by a newline character. "
                "Output the paragraphs separated by a blank line without line numbers or bullet points, preserving the original words.\n\n"
                f"{text}"
            ),
        },
    ]
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
    )
    grouped = response.choices[0].message.content.strip()
    return [p.strip() for p in re.split(r"\n\s*\n", grouped) if p.strip()]

def main():
    st.title("Document Analyzer")
    st.write(
        "Enter a prompt and upload a PDF or Word document. The app will apply your prompt to each paragraph "
        "and display a diff of the suggested changes."
    )

    with st.form("analysis_form"):
        instructions = st.text_area("Prompt", height=150)
        uploaded_file = st.file_uploader("Upload document (PDF or Word)", type=["pdf", "docx", "doc"])
        submitted = st.form_submit_button("Analyze Document")

    if not submitted:
        return

    if not instructions:
        st.warning("Please enter a prompt.")
        return

    if not uploaded_file:
        st.warning("Please upload a document.")
        return

    file_bytes = uploaded_file.read()
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif file_name.endswith(".docx") or file_name.endswith(".doc"):
        text = extract_text_from_docx(file_bytes)
    else:
        st.error("Unsupported file type.")
        return

    with st.spinner("Grouping lines into paragraphs..."):
        paragraphs = group_lines_into_paragraphs(text)
    if not paragraphs:
        st.warning("No paragraphs found in the document.")
        return

    st.info(f"Found {len(paragraphs)} paragraphs. Processing...")
    responses = []
    progress_bar = st.progress(0)
    for i, paragraph in enumerate(paragraphs):
        with st.spinner(f"Processing paragraph {i+1}/{len(paragraphs)}"):
            modified = analyze_paragraph(instructions, paragraph)
            responses.append((paragraph, modified))
        progress_bar.progress((i + 1) / len(paragraphs))
    progress_bar.empty()

    st.header("Results")
    for idx, (orig, mod) in enumerate(responses, start=1):
        st.subheader(f"Paragraph {idx}")
        diff = difflib.unified_diff(
            orig.splitlines(),
            mod.splitlines(),
            lineterm="",
            fromfile="Original",
            tofile="Modified",
        )
        st.code("\n".join(diff), language="diff")

if __name__ == "__main__":
    main()
