import pdfplumber
import io


async def extract_text(file):
    """Extract text from uploaded PDF or image files."""
    content = await file.read()

    if file.filename.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if not text.strip():
                return "[PDF appears to be scanned/image-based. Text extraction returned empty. Please upload a text-based PDF.]"
            
            return text.strip()
        except Exception as e:
            return f"[Error reading PDF: {str(e)}]"
    
    elif file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        # Try OCR if pytesseract is available
        try:
            from PIL import Image
            import pytesseract
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            if not text.strip():
                return "[Could not extract text from image. Please upload a clearer image.]"
            return text.strip()
        except ImportError:
            return "[Image OCR not available. Please install pytesseract and Tesseract OCR, or upload a PDF instead.]"
        except Exception as e:
            return f"[Error reading image: {str(e)}]"
    
    else:
        # Try reading as plain text
        try:
            return content.decode("utf-8").strip()
        except Exception:
            return "[Unsupported file format. Please upload a PDF, JPG, or PNG file.]"