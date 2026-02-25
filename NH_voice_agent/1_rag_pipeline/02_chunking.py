"""
텍스트 청킹 및 전처리
파싱된 문서를 적절한 크기의 청크로 분할
"""
import sys
from pathlib import Path
from typing import List, Dict
import logging
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TextChunker:
    """텍스트 청킹 클래스"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50
    ):
        """
        Args:
            chunk_size: 청크 최대 크기 (토큰/문자 수)
            chunk_overlap: 청크 간 오버랩 크기
            min_chunk_size: 청크 최소 크기
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def clean_text(self, text: str) -> str:
        """
        텍스트 정제

        Args:
            text: 원본 텍스트

        Returns:
            정제된 텍스트
        """
        if not text:
            return ""

        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)

        # 특수 문자 정제
        text = text.replace('\x00', '')

        # 앞뒤 공백 제거
        text = text.strip()

        return text

    def split_by_sentences(self, text: str) -> List[str]:
        """
        문장 단위로 텍스트 분할

        Args:
            text: 원본 텍스트

        Returns:
            문장 리스트
        """
        # 한국어와 영어 문장 분리 패턴
        # 마침표, 물음표, 느낌표 뒤에 공백이나 줄바꿈이 오는 경우
        sentences = re.split(r'(?<=[.!?])\s+', text)

        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        텍스트를 청크로 분할

        Args:
            text: 원본 텍스트
            metadata: 문서 메타데이터

        Returns:
            청크 리스트
        """
        # 텍스트 정제
        clean_text = self.clean_text(text)

        if len(clean_text) < self.min_chunk_size:
            return []

        # 문장 단위로 분할
        sentences = self.split_by_sentences(clean_text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # 현재 청크에 추가 가능한지 확인
            if current_size + sentence_size <= self.chunk_size:
                current_chunk.append(sentence)
                current_size += sentence_size
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append({
                            'text': chunk_text,
                            'chunk_size': len(chunk_text),
                            **(metadata or {})
                        })

                # 오버랩을 위해 마지막 몇 문장 유지
                overlap_sentences = []
                overlap_size = 0
                for sent in reversed(current_chunk):
                    if overlap_size + len(sent) <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_size += len(sent)
                    else:
                        break

                # 새 청크 시작
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)

        # 마지막 청크 추가
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'chunk_size': len(chunk_text),
                    **(metadata or {})
                })

        return chunks

    def chunk_document(self, doc: Dict) -> List[Dict]:
        """
        문서 전체를 청크로 분할

        Args:
            doc: 파싱된 문서

        Returns:
            청크 리스트
        """
        metadata = {
            'file_name': doc.get('file_name', ''),
            'file_path': doc.get('file_path', ''),
            'num_pages': doc.get('num_pages', 0)
        }

        # 전체 텍스트로 청킹
        full_text = doc.get('full_text', '')
        chunks = self.chunk_text(full_text, metadata)

        # 청크 ID 추가
        for idx, chunk in enumerate(chunks):
            chunk['chunk_id'] = f"{doc.get('file_name', 'unknown')}_{idx}"

        logger.info(
            f"Document '{doc.get('file_name')}' split into {len(chunks)} chunks"
        )

        return chunks

    def process_documents(self, docs: List[Dict]) -> List[Dict]:
        """
        여러 문서 청킹

        Args:
            docs: 파싱된 문서 리스트

        Returns:
            모든 청크 리스트
        """
        all_chunks = []

        for doc in docs:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"Total {len(all_chunks)} chunks created from {len(docs)} documents")

        return all_chunks


def main():
    """메인 실행 함수"""
    import argparse
    import pandas as pd

    parser = argparse.ArgumentParser(description="Chunk parsed documents")
    parser.add_argument(
        "--input_table",
        default="parsed_docs",
        help="Input Delta Table name"
    )
    parser.add_argument(
        "--output_table",
        default="chunked_docs",
        help="Output Delta Table name"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=512,
        help="Maximum chunk size"
    )
    parser.add_argument(
        "--chunk_overlap",
        type=int,
        default=50,
        help="Chunk overlap size"
    )

    args = parser.parse_args()

    # Load parsed documents
    input_path = config.PROCESSED_DATA_DIR / f"{args.input_table}.parquet"
    logger.info(f"Loading documents from {input_path}")

    docs = pd.read_parquet(input_path).to_dict('records')

    # Chunk documents
    chunker = TextChunker(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    chunks = chunker.process_documents(docs)

    # Save chunks
    df = pd.DataFrame(chunks)
    output_path = config.PROCESSED_DATA_DIR / f"{args.output_table}.parquet"
    df.to_parquet(output_path, index=False)

    logger.info(f"Saved {len(chunks)} chunks to {output_path}")

    print(f"\n✓ Created {len(chunks)} chunks from {len(docs)} documents")
    print(f"✓ Saved to: {output_path}")


if __name__ == "__main__":
    main()
