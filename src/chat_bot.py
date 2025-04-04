from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.memory import ConversationBufferMemory

import streamlit as st

# Load the LLM
def load_llms(model_name, base_url):
    return OllamaLLM(
        model=model_name,
        base_url=base_url,
        max_tokens=1024,
        temperature=0.1    
        )





# Load vector database with error handling
def read_vector_db():
    try:
        embedding_model = GPT4AllEmbeddings(model_file="models/all-MiniLM-L12-v2.F16.gguf")
        return FAISS.load_local(vector_db_path, embeddings=embedding_model, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f" Error loading vector database: {str(e)}")
        return None



def create_prompt(template):
    return PromptTemplate(
        input_variables=["chat_history", "context", "question"],
        template=template
    )

# Create chatbot chain with manual retrieval
def create_chat_bot_chain(prompt, llm, memory, db):
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    def custom_invoke(inputs):
        question = inputs["query"]
        
        # Retrieve chat history and context
        chat_history = memory.load_memory_variables({}).get("chat_history", [])
        chat_history_str = "\n".join(
            [f"{msg['type']}: {msg['content']}" for msg in chat_history]
        ) if chat_history else "No previous conversation."
        
        # Retrieve relevant context for the current query (e.g., using the vector database)
        docs = db.as_retriever(search_kwargs={"k": 3}).invoke(question) if db else []
        context = "\n".join([doc.page_content for doc in docs]) if docs else "No relevant information found."

        # Prepare input for LLM, including chat history and question
        full_input = {
            "chat_history": chat_history_str,
            "context": context,  # Ensure context is included here
            "question": question
        }

        # Run the LLM chain to get the response
        response = llm_chain.invoke(full_input)["text"].strip()

        # Save context for the next round of questions
        chat_history.extend([
            {"type": "user", "content": question},
            {"type": "assistant", "content": response}
        ])

        # Save to LangChain memory
        memory.save_context(
            inputs={"input": question},
            outputs={"output": response}
        )
        return {"result": response}

    class CustomChain:
        def invoke(self, inputs):
            return custom_invoke(inputs)

    return CustomChain()


vector_db_path = 'vector_db_news'

# Create prompt template
template = """<|begin_of_text|>system
You are an AI assistant specialized in providing context-aware news updates.
Previous conversation history:
{chat_history}
Retrieved news data:
{context}
<|EOT|>
<|begin_of_text|>user
{question}
<|EOT|>
<|begin_of_text|>assistant
"""

# Initialize memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Streamlit UI for the chatbot
st.title("AI News Chatbot")
st.write("Chat with an AI-powered news assistant!")

# Model and prompt setup

model_name = "deepseek-r1:8b"
base_url = "http://localhost:11435"
llm = load_llms(model_name, base_url)
prompt=create_prompt(template)
# Initialize chatbot chain
llm_chain = create_chat_bot_chain(prompt, llm, memory,read_vector_db())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Input field for user query
user_input = st.text_input("You:", "")

# Button for sending the query
if st.button("Send") and user_input:
    # Process the user input and get the response
    response = llm_chain.invoke({"query": user_input})
    
    # Extract response result
    raw_result = response["result"].strip()
    final_answer = raw_result.split("</think>")[-1].strip()
    # Store both user query and chatbot's response in the session state (chat history)
    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Chatbot", final_answer))

# Display conversation history
st.write("### Conversation History")
for speaker, text in st.session_state.chat_history:
    st.write(f"**{speaker}:** {text}")
    