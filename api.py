from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
import pytesseract
import requests

app = Flask(__name__)

# Optional: set tesseract path (Windows users only)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def process_image_for_ocr(img: Image.Image) -> Image.Image:
    """Preprocess image to improve OCR accuracy."""
    img = img.convert("L")  # grayscale
    img = ImageEnhance.Contrast(img).enhance(2.0)  # boost contrast
    img = img.point(lambda x: 0 if x < 140 else 255, "1")  # threshold
    img = img.filter(ImageFilter.MedianFilter(size=3))  # smooth edges
    return img

@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Simple OCR API",
        "usage": "/ocr?url=<image_url>"
    })

@app.route("/ocr", methods=["GET"])
def ocr_from_url():
    image_url = request.args.get("url")
    if not image_url:
        return jsonify({"error": "Please provide ?url=<image_url>"}), 400

    try:
        # Download the image
        headers = {"User-Agent": "ocr-flask-api"}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        img = process_image_for_ocr(img)

        # Run OCR
        text = pytesseract.image_to_string(
            img,
            config="--psm 8 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ).strip()

        return jsonify({
            "success": True,
            "image_url": image_url,
            "extracted_text": text or "[No text detected]"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
