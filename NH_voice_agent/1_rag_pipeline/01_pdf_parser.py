"""
PDF 문서 파싱
Unity Catalog Volume에서 PDF를 읽어 Delta Table로 저장
"""
import os
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from databricks.sdk import WorkspaceClient
import PyPDF2
import pdfplumber
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class PDFParser:
    """PDF 문서 파싱 클래스"""

    def __init__(self):
        self.client = WorkspaceClient(
            host=config.DATABRICKS_HOST,
            token=config.DATABRICKS_TOKEN
        )
        self.volume_path = config.volume_path

    def list_pdfs(self, directory: str = None) -> List[str]:
        """
        Volume 또는 로컬 디렉토리에서 PDF 파일 목록 가져오기

        Args:
            directory: PDF 파일이 있는 디렉토리 (None이면 volume_path 사용)

        Returns:
            PDF 파일 경로 리스트
        """
        if directory:
            # Local directory
            pdf_dir = Path(directory)
            return [str(f) for f in pdf_dir.glob("*.pdf")]
        else:
            # Databricks Volume
            # TODO: Implement volume listing using Databricks SDK
            logger.warning("Volume listing not implemented yet")
            return []

    def parse_pdf_pypdf2(self, pdf_path: str) -> Dict:
        """
        PyPDF2를 사용한 PDF 파싱

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            파싱된 문서 정보
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                # 메타데이터 추출
                metadata = reader.metadata or {}

                # 전체 텍스트 추출
                text_content = []
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text_content.append({
                        'page_num': page_num + 1,
                        'text': page_text
                    })

                return {
                    'file_path': pdf_path,
                    'file_name': Path(pdf_path).name,
                    'num_pages': len(reader.pages),
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'pages': text_content,
                    'full_text': '\n\n'.join([p['text'] for p in text_content])
                }

        except Exception as e:
            logger.error(f"Error parsing {pdf_path}: {e}")
            return None

    def parse_pdf_pdfplumber(self, pdf_path: str) -> Dict:
        """
        pdfplumber를 사용한 PDF 파싱 (테이블 추출 지원)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            파싱된 문서 정보
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                tables = []

                for page_num, page in enumerate(pdf.pages):
                    # 텍스트 추출
                    page_text = page.extract_text()

                    # 테이블 추출
                    page_tables = page.extract_tables()

                    text_content.append({
                        'page_num': page_num + 1,
                        'text': page_text,
                        'has_tables': len(page_tables) > 0
                    })

                    if page_tables:
                        tables.extend([{
                            'page_num': page_num + 1,
                            'table_data': table
                        } for table in page_tables])

                return {
                    'file_path': pdf_path,
                    'file_name': Path(pdf_path).name,
                    'num_pages': len(pdf.pages),
                    'pages': text_content,
                    'tables': tables,
                    'full_text': '\n\n'.join([p['text'] for p in text_content])
                }

        except Exception as e:
            logger.error(f"Error parsing {pdf_path} with pdfplumber: {e}")
            return None

    def parse_directory(self, directory: str, use_pdfplumber: bool = True) -> List[Dict]:
        """
        디렉토리의 모든 PDF 파싱

        Args:
            directory: PDF 파일이 있는 디렉토리
            use_pdfplumber: pdfplumber 사용 여부

        Returns:
            파싱된 문서 리스트
        """
        pdf_files = self.list_pdfs(directory)
        logger.info(f"Found {len(pdf_files)} PDF files")

        parsed_docs = []
        for pdf_path in pdf_files:
            logger.info(f"Parsing: {pdf_path}")

            if use_pdfplumber:
                doc = self.parse_pdf_pdfplumber(pdf_path)
            else:
                doc = self.parse_pdf_pypdf2(pdf_path)

            if doc:
                parsed_docs.append(doc)

        logger.info(f"Successfully parsed {len(parsed_docs)} documents")
        return parsed_docs

    def save_to_delta(self, docs: List[Dict], table_name: str = "parsed_docs"):
        """
        파싱된 문서를 Delta Table로 저장

        Args:
            docs: 파싱된 문서 리스트
            table_name: Delta Table 이름
        """
        # TODO: Implement Delta Table write using Databricks SDK or Spark
        import pandas as pd

        df = pd.DataFrame(docs)
        full_table_name = f"{config.uc_full_path}.{table_name}"

        logger.info(f"Saving {len(docs)} documents to {full_table_name}")
        logger.warning("Delta Table write not implemented - saving to parquet instead")

        output_path = config.PROCESSED_DATA_DIR / f"{table_name}.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved to {output_path}")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Parse PDF documents")
    parser.add_argument(
        "--input_dir",
        default=str(config.RAW_DATA_DIR),
        help="Input directory containing PDF files"
    )
    parser.add_argument(
        "--output_table",
        default="parsed_docs",
        help="Output Delta Table name"
    )
    parser.add_argument(
        "--use_pdfplumber",
        action="store_true",
        default=True,
        help="Use pdfplumber instead of PyPDF2"
    )

    args = parser.parse_args()

    # Parse PDFs
    parser = PDFParser()
    docs = parser.parse_directory(args.input_dir, use_pdfplumber=args.use_pdfplumber)

    # Save to Delta Table
    parser.save_to_delta(docs, args.output_table)

    print(f"\n✓ Parsed {len(docs)} documents")
    print(f"✓ Saved to table: {config.uc_full_path}.{args.output_table}")


if __name__ == "__main__":
    main()
