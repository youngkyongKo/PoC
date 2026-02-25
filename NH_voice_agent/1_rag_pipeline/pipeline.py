"""
전체 RAG 파이프라인 실행
PDF 파싱 → 청킹 → Vector Search 인덱스 생성
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import config

# Import pipeline modules
from pdf_parser import PDFParser
from chunking import TextChunker
from vector_index import VectorIndexBuilder

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """전체 RAG 파이프라인"""

    def __init__(
        self,
        input_dir: str = None,
        parsed_table: str = "parsed_docs",
        chunked_table: str = "chunked_docs",
        index_name: str = None
    ):
        """
        Args:
            input_dir: PDF 파일 입력 디렉토리
            parsed_table: 파싱된 문서 테이블 이름
            chunked_table: 청킹된 문서 테이블 이름
            index_name: Vector Search 인덱스 이름
        """
        self.input_dir = input_dir or str(config.RAW_DATA_DIR)
        self.parsed_table = parsed_table
        self.chunked_table = chunked_table
        self.index_name = index_name or config.VECTOR_INDEX_NAME

        # Initialize components
        self.pdf_parser = PDFParser()
        self.text_chunker = TextChunker()
        self.vector_builder = VectorIndexBuilder()

    def run(self):
        """전체 파이프라인 실행"""
        logger.info("=" * 60)
        logger.info("Starting RAG Pipeline")
        logger.info("=" * 60)

        # Step 1: Parse PDFs
        logger.info("\n[1/4] Parsing PDF documents...")
        parsed_docs = self.pdf_parser.parse_directory(self.input_dir)

        if not parsed_docs:
            logger.error("No documents parsed. Exiting.")
            return False

        logger.info(f"✓ Parsed {len(parsed_docs)} documents")

        # Save parsed documents
        self.pdf_parser.save_to_delta(parsed_docs, self.parsed_table)

        # Step 2: Chunk documents
        logger.info("\n[2/4] Chunking documents...")
        chunks = self.text_chunker.process_documents(parsed_docs)

        if not chunks:
            logger.error("No chunks created. Exiting.")
            return False

        logger.info(f"✓ Created {len(chunks)} chunks")

        # Save chunks
        import pandas as pd
        df = pd.DataFrame(chunks)
        output_path = config.PROCESSED_DATA_DIR / f"{self.chunked_table}.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"✓ Saved chunks to {output_path}")

        # Step 3: Create Vector Search endpoint
        logger.info("\n[3/4] Creating Vector Search endpoint...")
        self.vector_builder.create_vector_search_endpoint()
        logger.info("✓ Vector Search endpoint ready")

        # Step 4: Create Vector Index
        logger.info("\n[4/4] Creating Vector Search index...")
        source_table = f"{config.uc_full_path}.{self.chunked_table}"

        self.vector_builder.create_delta_sync_index(
            source_table=source_table,
            index_name=self.index_name
        )

        logger.info("\n" + "=" * 60)
        logger.info("RAG Pipeline completed!")
        logger.info("=" * 60)

        # Print summary
        print("\n📊 Pipeline Summary:")
        print(f"  - Input directory: {self.input_dir}")
        print(f"  - Documents parsed: {len(parsed_docs)}")
        print(f"  - Chunks created: {len(chunks)}")
        print(f"  - Parsed table: {config.uc_full_path}.{self.parsed_table}")
        print(f"  - Chunked table: {config.uc_full_path}.{self.chunked_table}")
        print(f"  - Vector index: {self.index_name}")

        print("\n⚠️  Next steps:")
        print("  1. Complete Vector Index creation in Databricks UI")
        print("  2. Wait for index sync to complete")
        print("  3. Test the index with sample queries")

        return True


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Run RAG pipeline")
    parser.add_argument(
        "--input_dir",
        default=str(config.RAW_DATA_DIR),
        help="Input directory containing PDF files"
    )
    parser.add_argument(
        "--parsed_table",
        default="parsed_docs",
        help="Parsed documents table name"
    )
    parser.add_argument(
        "--chunked_table",
        default="chunked_docs",
        help="Chunked documents table name"
    )
    parser.add_argument(
        "--index_name",
        default=config.VECTOR_INDEX_NAME,
        help="Vector Search index name"
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = RAGPipeline(
        input_dir=args.input_dir,
        parsed_table=args.parsed_table,
        chunked_table=args.chunked_table,
        index_name=args.index_name
    )

    success = pipeline.run()

    if success:
        print("\n✅ Pipeline completed successfully!")
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
