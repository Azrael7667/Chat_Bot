from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
import requests
import json
import fitz  # PyMuPDF for better PDF text extraction
import re  # For cleaning noisy text
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator
import re


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up folders
UPLOAD_FOLDER = "./uploads"
VECTORSTORE_FOLDER = "./vectorstore"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTORSTORE_FOLDER, exist_ok=True)

# FAISS Vector Database
db = None

@app.get("/")
async def root():
    return {"message": "Welcome to GuffSpace AI Backend!"}

# ---------------------- PDF UPLOAD API ---------------------- #
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Handles PDF uploads, processes text, and stores in FAISS."""
    global db
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        print(f"✅ File saved at: {file_path}")

        # Extract text using PyMuPDF (fitz)
        extracted_text = []
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text = page.get_text("text")
                if text:
                    extracted_text.append(text)

        if not extracted_text:
            raise ValueError("❌ Failed to extract text from PDF. Try another file.")

        full_text = "\n".join(extracted_text).strip()

        # Clean extracted text (Remove special characters & repetitive symbols)
        full_text = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()  # Normalize spaces

        # Split text into smaller chunks for better embeddings
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = text_splitter.split_text(full_text)
        print(f"🔹 Text split into {len(texts)} chunks")

        # Use a multilingual embeddings model
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        # Store embeddings in FAISS
        db = FAISS.from_texts(texts, embeddings)
        db.save_local(VECTORSTORE_FOLDER)
        print("✅ FAISS database saved successfully.")

        return {"message": "PDF uploaded and processed successfully.", "file_name": file.filename}

    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return {"error": f"Error processing PDF: {str(e)}"}

# ---------------------- CHAT API ---------------------- #
class ChatRequest(BaseModel):
    query: str
    response_language: str = "en"

def query_openrouter(text):
    """Helper function to call OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="❌ Missing OpenRouter API Key. Set it in .env")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Ensure text does not exceed 5000 characters
    truncated_text = text[:4900]

    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": "Summarize the following text in a clear and concise manner."},
            {"role": "user", "content": truncated_text}
        ],
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    try:
        response_data = response.json()
        if response.status_code == 200 and "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        else:
            return "⚠️ AI response was empty. Try refining your query."
    except Exception as e:
        print(f"❌ API Parsing Error: {str(e)}")
        return "⚠️ AI encountered an issue while processing your request."


@app.post("/chat")
async def chat(request: ChatRequest):
    """Handles user queries, translates if needed, and returns AI-generated responses."""
    try:
        global db
        if db is None:
            # Load FAISS database if it's not already loaded
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            db = FAISS.load_local(VECTORSTORE_FOLDER, embeddings)
            print("✅ FAISS database loaded from storage.")

        # Translate query to Nepali for better retrieval
        translated_query = GoogleTranslator(source="en", target="ne").translate(request.query)
        print(f"📝 Translated Query (English -> Nepali): {translated_query}")

        # Retrieve relevant text from FAISS
        relevant_texts = db.similarity_search(translated_query, k=3)
        retrieved_text = " ".join([doc.page_content for doc in relevant_texts])

        if not retrieved_text.strip():
            return {"error": "❌ No relevant text found in the PDF for this query."}

        # **Clean retrieved text**
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', retrieved_text)  # Remove special symbols
        cleaned_text = cleaned_text[:4900]  # Keep within API limits

        print(f"🔹 Cleaned Retrieved Text: {cleaned_text[:500]}...")

        # **Get AI response**
        ai_response = query_openrouter(cleaned_text)

        # **If AI response is empty, retry with English query**
        if not ai_response or ai_response.strip() == "":
            print("⚠️ AI Response was empty. Retrying with English query...")
            ai_response = query_openrouter(request.query)

        # **Final check: If no response, return an error**
        if not ai_response or ai_response.strip() == "":
            return {"error": "❌ AI did not return a valid response."}

        print(f"✅ AI Response (English): {ai_response}")

        # **Translate AI response to Nepali if requested**
        if request.response_language == "ne":
            try:
                translated_response = GoogleTranslator(source="en", target="ne").translate(ai_response)

                # **Check if the translated response is corrupted**
                if not translated_response.strip() or any(char in translated_response for char in ["@", "*", "!", "?", "/"]):
                    print("⚠️ Nepali translation failed or has formatting issues. Retrying...")
                    translated_response = GoogleTranslator(source="en", target="ne").translate(ai_response)

                # **Fallback to English if translation is still corrupted**
                if not translated_response.strip():
                    print("⚠️ Translation failed again. Showing response in English.")
                    return {"response": ai_response}  # Fallback to English

                print(f"🔹 Translated Response (English -> Nepali): {translated_response}")
                return {"response": translated_response}

            except Exception as e:
                print(f"❌ Translation error: {str(e)}. Showing response in English.")
                return {"response": ai_response}  # Fallback to English if translation errors occur

        return {"response": ai_response}

    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return {"error": f"Chat error: {str(e)}"}


# ---------------------- RUN SERVER ---------------------- #
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
