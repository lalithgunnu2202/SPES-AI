from src.read_scripts import *

def read_pdf_format(filepath,chunks_filename,collection_name,model_name="BAAI/bge-small-en-v1.5"):
    content=load_pdf_content(filepath)
    content=format_text(content)
    sections = make_sections(content)
    chunks = make_chunks(sections)
    embeddings = encod_chunks(model_name,chunks)
    add_to_index_storage(embeddings, chunks, collection_name)
    export_chunks(chunks, chunks_filename)