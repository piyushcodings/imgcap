from flask import Flask, request, jsonify
import base64
import re
import pytesseract
from PIL import Image

app = Flask(__name__)

@app.route("/solve", methods=["GET"])
def solve():

    try:
        base64_data = request.args.get("base64", "")

        if not base64_data:
            return jsonify({
                "success": False,
                "message": "base64 parameter missing"
            })

        # Fix escaped slashes
        base64_data = base64_data.replace("\\/", "/")

        # Remove data:image/png;base64,
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        # Decode image
        image_bytes = base64.b64decode(base64_data)

        # Save image
        with open("captcha.png", "wb") as f:
            f.write(image_bytes)

        # OCR
        text = pytesseract.image_to_string(Image.open("captcha.png")).strip()

        print("Detected:", text)

        # Extract math expression
        match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', text)

        if not match:
            return jsonify({
                "success": False,
                "text": text,
                "message": "Math expression not found"
            })

        a = int(match.group(1))
        op = match.group(2)
        b = int(match.group(3))

        # Solve
        if op == "+":
            answer = a + b
        elif op == "-":
            answer = a - b
        elif op == "*":
            answer = a * b
        elif op == "/":
            answer = a / b
        else:
            return jsonify({
                "success": False,
                "message": "Invalid operator"
            })

        return jsonify({
            "success": True,
            "text": text,
            "answer": answer
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route("/")
def home():
    return "Captcha Solver API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
