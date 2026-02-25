# RAG 파이프라인

PDF 문서를 파싱하고 청킹하여 Vector Search 인덱스를 생성하는 파이프라인

## 구성 요소

1. **01_pdf_parser.py**: PDF 문서 파싱
2. **02_chunking.py**: 텍스트 청킹 및 전처리
3. **03_vector_index.py**: Vector Search 인덱스 생성
4. **pipeline.py**: 전체 파이프라인 실행

## 사용법

### 개별 실행

```bash
# 1. PDF 파싱
python 01_pdf_parser.py --input_dir ../data/raw --output_table parsed_docs

# 2. 청킹
python 02_chunking.py --input_table parsed_docs --output_table chunked_docs

# 3. 벡터 인덱스 생성
python 03_vector_index.py --table chunked_docs --index_name pdf_embeddings_index
```

### 전체 파이프라인 실행

```bash
python pipeline.py --input_dir ../data/raw
```

## 출력

- Delta Table: `{catalog}.{schema}.parsed_docs`
- Delta Table: `{catalog}.{schema}.chunked_docs`
- Vector Index: `{catalog}.{schema}.pdf_embeddings_index`
