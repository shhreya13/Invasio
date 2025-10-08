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

# ---------------- Load species data ----------------
with open("data/invasive_species.json") as f:
    invasive_species = json.load(f)["species"]

with open("data/species_database.json") as f:
    all_species = json.load(f)

# ---------------- General Q&A ----------------
general_qa = {
    "what is edna": "Environmental DNA (eDNA) is genetic material shed by organisms into their environment (water, soil, or air). It allows monitoring species without capturing them.",
    "how can edna help monitor invasive species": "eDNA helps detect invasive species in water bodies early by analyzing genetic traces left in the environment.",
    "what are invasive fish species": "Invasive fish species in freshwater lakes include Micropterus salmoides (Largemouth bass), Oreochromis niloticus (Nile tilapia), and Clarias gariepinus (African catfish).",
    "how do invasive species affect native fish": "Invasive species compete with native fish for resources, sometimes causing population declines or local extinctions.",
    "difference between invasive and native species": "Invasive species are non-native and can cause ecological or economic harm, whereas native species naturally occur in the ecosystem.",
    "how is dna extracted from water samples": "DNA is extracted from water samples using filtration, cell lysis, and purification methods to isolate genetic material for analysis.",
    "can edna detect rare species": "Yes, eDNA can detect rare or elusive species because even small traces of DNA are sufficient for detection.",
    "how reliable is edna analysis": "eDNA analysis is generally reliable but can be affected by DNA degradation, contamination, or sampling errors.",
    "methods to control invasive fish": "Common methods include physical removal, biological control, habitat management, and public awareness campaigns.",
    "why is biodiversity important": "Biodiversity ensures ecosystem stability, resilience, and provides resources for humans and other organisms."
}

# ---------------- Helper Functions ----------------
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
    """Mock species identification from DNA sequences"""
    species_list = random.choices(list(all_species.keys()), k=len(sequences))
    return species_list

def classify_species(species_list):
    """Split species into invasive and native"""
    invasive_found = [s for s in species_list if s in invasive_species]
    native_found = [s for s in species_list if all_species.get(s) == "Native fish"]
    return invasive_found, native_found

def answer_query_rule_based(query, invasive_found=None, native_found=None):
    """Return answer using rule-based matching"""
    q = query.lower()
    species_info = ""
    if invasive_found:
        species_info = f"Invasive species in this sample: {', '.join(invasive_found)}. "
    if native_found:
        species_info += f"Native species: {', '.join(native_found)}."

    for key, answer in general_qa.items():
        if key in q:
            return species_info + " " + answer if species_info else answer

    return "Sorry, I can only answer questions about eDNA, biology, or invasive/native fish species."

# ---------------- Routes ----------------
@app.route("/chat", methods=["POST"])
def chat():
    file = request.files.get("file")
    query = request.form.get("query")

    # ----- File Analysis -----
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        try:
            sequences = parse_sequences(filepath)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        identified_species = identify_species(sequences)
        invasive_found, native_found = classify_species(identified_species)
        risk_score = round((len(invasive_found) / len(identified_species)) * 100, 2) if identified_species else 0

        result = {
            "file": file.filename,
            "total_species": len(identified_species),
            "identified_species": identified_species,
            "invasive_species_found": invasive_found,
            "native_species_found": native_found,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat()
        }

        if query:
            response = answer_query_rule_based(query, invasive_found, native_found)
            result["response"] = response

        return jsonify(result)

    # ----- Text Question Only -----
    elif query:
        response = answer_query_rule_based(query)
        return jsonify({"response": response})

    else:
        return jsonify({"error": "No file or query provided"}), 400

@app.route("/")
def home():
    return "INVASIO Chatbot Backend running 🚀"

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
