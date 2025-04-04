from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import GPT4AllEmbeddings
import os
def create_db_from_txt_folder(txt_folder_path, vector_db_path):
    all_chunks = []

    for txt_filename in os.listdir(txt_folder_path):
        if txt_filename.endswith(".txt"):
            txt_data_path = os.path.join(txt_folder_path, txt_filename)
            
            with open(txt_data_path, "r", encoding="utf-8") as file:
                text_data = file.read()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
            chunks = text_splitter.split_text(text_data)
            all_chunks.extend(chunks)

    embedding_model = GPT4AllEmbeddings(model_file="mmodels/mxbai-embed-large-v1-f16.gguf")
    db = FAISS.from_texts(all_chunks, embedding_model)

    db.save_local(vector_db_path)
    
    return db

db = create_db_from_txt_folder("cnn_articles", "vector_db_news")
