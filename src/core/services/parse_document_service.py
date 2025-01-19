import re
import logging
from pypdf import PdfReader
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ParseDocumentService:
    def __init__(self):
        pass

    def parse_document(self, file_path: str, is_interviewer: bool) -> None:
        """Index documents (including PDF) into the vector store."""

        if file_path.lower().endswith(".pdf"):
            logger.debug(f"Extracting text from PDF: {file_path}")
            content = self._extract_pdf_text(file_path, is_interviewer)
        else:
            # Attempt reading as a plain text file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

            content = content.strip() if isinstance(content, str) else ""
            
            if not content:
                logger.warning(f"No text extracted or readable from: {file_path}. Skipping.")
        
        return content
    
    def _extract_pdf_text(self, file_path: str, is_interviewer: bool) -> str:
        """Extract text from a PDF using pypdf."""
        text = ""
        with open(file_path, "rb") as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                if (is_interviewer):
                    logger.info(f"Extracting questions from {text}")
                    content = self.parse_form_questions(text)
                    logger.info(f"Questions: {content}")
                    return self.questions_to_text(content)
                else:
                    return text
    
    def parse_form_questions(self, raw_text: str):
        """
        Given a string containing lines like:
            Question ID: q1
            Question: What is your company's mission?
            Answer Type: text
            Required: Yes
        returns a list of dicts:
        [
        {
            "id": "q1",
            "question": "What is your company's mission?",
            "answer_type": "text",
            "required": True
        },
        ...
        ]
        """
        lines = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]

        questions = []
        current = {}

        re_id = re.compile(r"^Question\s*ID:\s*(.*)$", re.IGNORECASE)
        re_q  = re.compile(r"^Question:\s*(.*)$", re.IGNORECASE)
        re_at = re.compile(r"^Answer\s*Type:\s*(.*)$", re.IGNORECASE)
        re_req = re.compile(r"^Required:\s*(.*)$", re.IGNORECASE)

        for line in lines:
            if re_id.match(line):
                # If we were already building a question, store it
                if current:
                    questions.append(current)
                    current = {}
                current['id'] = re_id.match(line).group(1).strip()

            elif re_q.match(line):
                current['question'] = re_q.match(line).group(1).strip()

            elif re_at.match(line):
                current['answer_type'] = re_at.match(line).group(1).strip()

            elif re_req.match(line):
                val = re_req.match(line).group(1).strip().lower()
                current['required'] = (val == 'yes')

        # If there's a leftover question
        if current:
            questions.append(current)

        return questions
    
    def questions_to_text(self, questions: List[Dict[str, Any]]) -> str:
        """Convert questions list to formatted text"""
        # Build a text block, e.g.:
        # "Question ID: q1\nQuestion: ...\nAnswer Type: text\nRequired: yes\n\nQuestion ID: q2..."
        lines = []
        for q in questions:
            lines.append(f"Question ID: {q['id']}")
            lines.append(f"Question: {q['question']}")
            lines.append(f"Answer Type: {q['answer_type']}")
            lines.append(f"Required: {'Yes' if q.get('required') else 'No'}\n")
        return "\n".join(lines)