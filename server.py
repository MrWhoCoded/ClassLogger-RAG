"""
ClassLogger AI — Flask server.

Wraps main.answer_query() behind a POST /api/query endpoint
and serves the frontend/ static files on /.

Run:
    python server.py

Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from main import answer_query
import os

# ── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend", static_url_path="")


# ── CORS (needed when frontend is hosted on GitHub Pages) ────────────────────
@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


# ── Static file serving ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)


# ── API ──────────────────────────────────────────────────────────────────────
@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json(silent=True)

    if not data or not data.get("query", "").strip():
        return jsonify({"answer": "No query provided.", "is_error": True}), 400

    user_query = data["query"].strip()

    try:
        response = answer_query(user_query)

        if response is None:
            return jsonify(
                {
                    "answer": "Failed to get a response. Check server logs for details.",
                    "is_error": True,
                }
            )

        answer_text = response["choices"][0]["message"]["content"]

        return jsonify({"answer": answer_text, "is_error": False})

    except Exception as e:
        print(f"[server] Error: {e}")
        return (
            jsonify({"answer": f"Server error: {e}", "is_error": True}),
            500,
        )


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  ClassLogger AI server")
    print("  http://localhost:5000\n")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
