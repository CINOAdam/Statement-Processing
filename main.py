# coding=utf-8
from typing import List
import pdfplumber
import re
import os
from openai import OpenAI
from logger import SessionLogger
from datetime import datetime
import uuid
import instructor
from pydantic import BaseModel
from pprint import pprint as ppr
from settings import OPENAI_API_KEY


class Statement(BaseModel):
    Date: str
    Description: str
    Amount: float
    Category: str
    Subcategory: str
    Analysis: str


class Response(BaseModel):
    data: List[Statement]





def create_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    sessions_dir = os.path.join(os.path.dirname(__file__), "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    return sessions_dir

def extract_data_with_openai(text, statement_type="bank", logger=None):
    client = OpenAI(api_key=OPENAI_API_KEY)
    client = instructor.from_openai(client)
    """
    Extract structured data from bank statement text using OpenAI API.
    """
    if logger:
        logger.logger.info("Starting OpenAI API call for data extraction", extra={"prefix": "🤖 OpenAI"})

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured data from text.",
                },
                {
                    "role": "user",
                    "content": f"""
                    Extract the structured data from the following {statement_type} statement text. Categories should include any 
                    common descriptions useful for financial analysis and personal financial management.
                    Provide the data in this JSON format:
                    
                    [
                        {{
                            "Date": "01/02/22",
                            "Description": "INSTACART HTTPSINSTACAR CA",
                            "Amount": 183.53,
                            "Category": "Debit",
                            "Subcategory": "Groceries",
                            "Analysis": "Household Expense"
                        }},
                        {{
                            "Date": "12/28/21",
                            "Description": "Payment Thank You - Web",
                            "Amount": -15925.89,
                            "Category": "Credit",
                            "Subcategory": "Payment",
                            "Analysis": "Credit Card Payment"
                        }},
                        {{
                            "Date": "01/10/22",
                            "Description": "DOORDASH*TROPICAL SMOO WWW.DOORDASH. CA",
                            "Amount": 72.19,
                            "Category": "Debit",
                            "Subcategory": "Food",
                            "Analysis": "Dining In"
                        }}
                        
                        ...
                    ]

                    Text:
                    {text}
                    """
                }
            ],
            model="gpt-4-0125-preview",
            response_model=Response,
        )

        if logger:
            # With instructor, we can access the raw response through _raw_response
            if hasattr(chat_completion, '_raw_response'):
                usage = chat_completion._raw_response.usage
                logger.update_token_usage(
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens
                )
                logger.logger.info(
                    f"API call completed. Prompt tokens: {usage.prompt_tokens}, "
                    f"Completion tokens: {usage.completion_tokens}",
                    extra={"prefix": "🤖 OpenAI"}
                )
            else:
                logger.logger.warning(
                    "Could not access token usage information from the API response",
                    extra={"prefix": "⚠️ OpenAI"}
                )

        return chat_completion

    except Exception as e:
        if logger:
            logger.logger.error(f"Error in OpenAI API call: {str(e)}", extra={"prefix": "❌ OpenAI"})
        raise

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text

def parse_chase_statement(text):
    """
    Parse Chase statement transactions based on MM/DD format.
    """
    transactions = []
    pattern = r"(\d{2}/\d{2})\s+(.+?)\s+(\d+\.\d{2})$"

    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            date, description, amount = match.groups()
            transactions.append({
                "Date": date,
                "Description": description.strip(),
                "Amount": float(amount)
            })
    return transactions

def main():
    sessions_dir = create_sessions_dir()
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    logger = SessionLogger(session_id, sessions_dir)

    try:
        logger.logger.info("Starting statement processing", extra={"prefix": "🏁 Start"})

        extracted = extract_text_from_pdf("data/Card/20220118-statements-6813-.pdf")
        logger.logger.info("Processing PDF file", extra={"prefix": "📄 PDF"})

        result = parse_chase_statement(extracted)
        logger.logger.info("PDF conversion completed", extra={"prefix": "📄 PDF"})

        process = extract_data_with_openai(
            result,
            statement_type="Credit Card",
            logger=logger
        )

        logger.logger.info("Processing completed successfully", extra={"prefix": "✅ Success"})
        ppr(process.model_dump())  # Using pprint for better formatted output

    except Exception as e:
        logger.logger.error(f"Error during processing: {str(e)}", extra={"prefix": "❌ Error"})
        raise

    finally:
        logger.log_total_cost()

if __name__ == "__main__":
    main()

