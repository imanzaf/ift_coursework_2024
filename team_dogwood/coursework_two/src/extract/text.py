"""
Methods for text extraction from PDF documents.

# TODO - implement vector store for querying (targeted searches of specific figures)
# TODO - implement async calls (for extracting from multiple documents at once)

# TODO - maybe configure data source (minio) with llama client?
# TODO - maybe configure data sink (postgres) to automate upload of extracted text?
"""
import os
import sys
from typing import Optional, List
from loguru import logger

from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader, Document

from pydantic import BaseModel, Field, PrivateAttr

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from config.models import model_settings


class LLamaTextExtractor(BaseModel):
    """
    Class for extracting text from PDF documents using LlamaParse.
    """

    # pdf document path
    pdf_path: str = Field(
        ...,
        description="Path to the PDF document to extract text from.",
    )

    # parsed documents
    documents: Optional[List[Document]] = Field(
        None,
        description="List of extracted documents.",
    )

    # LlamaParse API key
    _llama_api_key: str = PrivateAttr(model_settings.LLAMACLOUD_API_KEY)

    def extract_document_pages(self) -> List[Document]:
        """
        Extract text from the PDF document using LlamaParse.

        Returns:
            list[Document]: per page extracted text from the PDF document.
                text can be accessed via documents[0].text
        """
        # Initialize LlamaParse with the API key
        parser = LlamaParse(
            api_key=self._llama_api_key,
            result_type="markdown",
            language="en",
            table_extraction_mode="full",
            system_prompt_append="You extract text, metrics, and figures from company sustainability reports.",
            user_prompt="""\
Extract all text, metrics, and figures from the PDF document.
Return a summary of the extracted text. Return metrics and figures in a table format where possible.
\
""")

        # Use SimpleDirectoryReader to read the PDF document
        file_extractor = {".pdf": parser}
        reader = SimpleDirectoryReader(input_files=[self.pdf_path], file_extractor=file_extractor)
        documents = reader.load_data()

        self.documents = documents
        return documents


if __name__ == "__main__":
    # Sample Usage
    pdf_path = f"{os.getcwd()}/data/sample-reports/2023-sustainability-report.pdf"
    logger.info(f"Extracting text from PDF document: {pdf_path}")
    # Extract text
    extractor = LLamaTextExtractor(pdf_path=pdf_path)
    extractor.extract_document_pages()
    logger.info(f"Snippet of Extracted Text: {extractor.documents[5].text}")  # Print the extracted text from a single page
    # write to a markdown file
    logger.info(f"Writing extracted text to markdown file...")
    with open(f"{os.getcwd()}/data/sample-outputs/test.md", "w") as f:
        f.write(extractor.documents[5].text)
        # for doc in extractor.documents:
        #     f.write(doc.text)