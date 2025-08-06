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

gemini_api_key = "AIzaSyBe34XDH5tiA1cqL5NgK5KhinJ-kNw35Z0"
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-pro')

def send_to_gemini(question, text):
    try: 
        text = question + ". this are the question, no question are dependent on each other so the asnwers should not infulence on other answers, answer in one line, so for example 10 question each line one question so 10 lines of answer each answer is one line. give me only the lines of answer . and answer should be form the contents of the following texts. dont generate, take the answer line form the following text with out any changes  - \n " + text
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

    question = ""
    for i in range(len(request.questions)):
        question += (request.questions[i]+'\n')

    print(question)
    ans = send_to_gemini(question, all_text)
    print(ans)
    ans = ans.split('\n')
    print(ans)

    return {
        "answers": ans
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
