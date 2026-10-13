import os, time
from flask import Flask, jsonify, request
app = Flask(__name__)
DATA_FILE = "data.txt"
def read_legacy_records():
    records = []
    if not os.path.exists(DATA_FILE):
        return records
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            c = line.strip()
            if c:
                fl = c.split("|")
                if len(fl) == 4:
                    records.append({"id": fl[0], "nama": fl[1], "jurusan": fl[2], "status": fl[3]})
    return records
def append_legacy_record(r):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{r['id']}|{r['nama']}|{r['jurusan']}|{r['status']}\n")
@app.route("/api/v1/students", methods=["GET"])
def get_all_students():
    records = read_legacy_records()
    return jsonify({"metadata": {"service": "Legacy-Integrated API Gateway", "format": "JSON", "total_records": len(records), "timestamp": int(time.time())}, "data": records}), 200
@app.route("/api/v1/students", methods=["POST"])
def create_student():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Bad Request", "message": "Body payload JSON wajib disertakan"}), 400
    req = ["id", "nama", "jurusan", "status"]
    miss = [k for k in req if k not in payload or not str(payload[k]).strip()]
    if miss:
        return jsonify({"error": "Unprocessable Entity", "message": f"Kunci data berikut tidak boleh kosong: {', '.join(miss)}"}), 422
    if any(r["id"] == str(payload["id"]) for r in read_legacy_records()):
        return jsonify({"error": "Conflict", "message": f"Data dengan ID {payload['id']} sudah ada di sistem legacy"}), 409
    s = {k: str(payload[k]).replace("|", "") for k in req}
    append_legacy_record(s)
    return jsonify({"status": "success", "message": "Data berhasil disimpan ke sistem legacy", "created_item": s}), 201
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
