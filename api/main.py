from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile
import google.generativeai as genai

gemini_api_key = "gemini api"
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-pro')

def send_to_gemini(question, text):
    try: 
        text = question + ". this is the question, answer in one line. and answer from the contents of the following texts - \n " + text
        response = model.generate_content(text)
        if response:
            return response.candidates[0].content.parts[0].text
        else:
            return f"Error1"
    except Exception as e:
        return f"Error2: {type(e).__name__} - {e}"

# Set root_path to /api/v1
app = FastAPI(root_path="/api/v1")

class RunRequest(BaseModel):
    documents: HttpUrl
    questions: List[str]

@app.post("/hackrx/run")
def run_endpoint(
    request: RunRequest,
    authorization: Optional[str] = Header(None)
):
    if authorization != "Bearer b70940bab4e0bf6f1edb9d469c7804d6f0a03b4804697738d2195df3f70ff5a6":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    
    pdf_url = request.documents
    response = requests.get(pdf_url)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(response.content)
        pdf_path = temp_pdf.name

    # Step 2: Extract all text (including OCR)
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        # Extract selectable text
        text = page.get_text()
        all_text += text
        
        # Extract OCR text from image (if necessary)
        if not text.strip():  # no real text, likely image-based
            pix = page.get_pixmap(dpi=300)
            img = Image.open(BytesIO(pix.tobytes()))
            ocr_text = pytesseract.image_to_string(img)
            all_text += ocr_text

    ans = []
    for i in range(len(request.questions)):
        ans.append(send_to_gemini(request.questions[i],all_text))

    return {
        "answers": ans
    }
