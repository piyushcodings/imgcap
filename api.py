from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
import pytesseract
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
# If you are on Windows, uncomment and set the path to your Tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# The URL of the page where the CAPTCHA is displayed. This is crucial for the session.
SESSION_URL = "https://savastan0.tools/login"
# --- END CONFIGURATION ---

def process_image_for_ocr(img: Image.Image) -> Image.Image:
    """Preprocess image to improve OCR accuracy."""
    img = img.convert("L")  # Convert to grayscale
    img = ImageEnhance.Contrast(img).enhance(2.0) # Increase contrast
    # Binarize the image. This threshold is a key parameter to tune.
    # All pixels darker than 140 will become black, all others white.
    img = img.point(lambda x: 0 if x < 140 else 255, "1")
    return img

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Simple OCR API",
        "usage": "/ocr?captcha_url=<full_url_to_captcha_image>"
    })

@app.route("/ocr", methods=["GET"])
def ocr_from_url():
    captcha_url = request.args.get("captcha_url")
    if not captcha_url:
        return jsonify({"error": "Please provide ?captcha_url=<image_url>"}), 400

    try:
        # Use a realistic User-Agent to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Use a 'with' statement for the session to ensure it's properly closed
        with requests.Session() as s:
            # 1. Make a request to the login page to establish a session and get cookies.
            # We don't need the content, just the act of visiting is important.
            s.get(SESSION_URL, headers=headers, timeout=10)

            # 2. Now, request the CAPTCHA image using the SAME session.
            # The session will automatically send the necessary cookies.
            response = s.get(captcha_url, headers=headers, timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes (like 403 Forbidden)

            # Check if the server actually sent back an image
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                return jsonify({
                    "success": False,
                    "error": f"Content is not an image. Received content-type: {content_type}",
                    "response": response.text,
                }), 415 # Unsupported Media Type

            # Open the image from the response content
            img = Image.open(BytesIO(response.content))

            # Preprocess the image to make it clearer for Tesseract
            processed_img = process_image_for_ocr(img)
            
            # Use Tesseract to extract text
            # --psm 7: Treat the image as a single text line.
            # tessedit_char_whitelist: Restricts Tesseract to only recognize these characters.
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(
                processed_img,
                config=custom_config
            ).strip()

            return jsonify({
                "success": True,
                "captcha_url": captcha_url,
                "extracted_text": text or "[No text detected]"
            })

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Network or HTTP error: {e}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
