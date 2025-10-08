from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from datetime import datetime
from Bio import SeqIO
import random

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load species data
with open("data/invasive_species.json") as f:
    invasive_species = json.load(f)["species"]

with open("data/species_database.json") as f:
    all_species = json.load(f)

# ----- Helper Functions -----
def parse_sequences(filepath):
    """Parse DNA sequences from FASTA or FASTQ file"""
    sequences = []
    ext = filepath.split(".")[-1].lower()
    if ext in ["fasta", "fa"]:
        seq_iter = SeqIO.parse(filepath, "fasta")
    elif ext in ["fastq", "fq"]:
        seq_iter = SeqIO.parse(filepath, "fastq")
    else:
        raise ValueError("Unsupported file type")
    for record in seq_iter:
        sequences.append(str(record.seq))
    return sequences

def identify_species(sequences):
    """
    Map sequences to species (mock demo)
    Replace with Kraken/BLAST for real DNA mapping
    """
    species_list = random.choices(list(all_species.keys()), k=len(sequences))
    return species_list

# ----- Routes -----
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        sequences = parse_sequences(filepath)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    identified_species = identify_species(sequences)
    invasive_found = [s for s in identified_species if s in invasive_species]

    risk_score = round((len(invasive_found) / len(identified_species)) * 100, 2) if identified_species else 0

    result = {
        "file": file.filename,
        "total_species": len(identified_species),
        "identified_species": identified_species,
        "invasive_species_found": invasive_found,
        "risk_score": risk_score,
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(result)

@app.route("/")
def home():
    return "INVASIO backend running 🚀"

if __name__ == "__main__":
    app.run(debug=True)
