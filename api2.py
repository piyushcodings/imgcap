from flask import Flask, request, jsonify
import base64
import re
import pytesseract
from PIL import Image
from io import BytesIO
import urllib.parse

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

        # URL decode
        base64_data = urllib.parse.unquote(base64_data)

        # Fix spaces back to +
        base64_data = base64_data.replace(" ", "+")

        # Remove data:image/png;base64,
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        # Decode image
        image_bytes = base64.b64decode(base64_data)

        # Open image directly from memory
        img = Image.open(BytesIO(image_bytes))

        # OCR
        text = pytesseract.image_to_string(img).strip()

        print("Detected:", text)

        # Extract expression
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

        if op == "+":
            answer = a + b
        elif op == "-":
            answer = a - b
        elif op == "*":
            answer = a * b
        elif op == "/":
            answer = a / b

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
