"""Mini-API locale qui sert les livraisons en JSON (simule une vraie API d'entreprise).

Lancer :  python data_generation/mock_api/app.py
Puis :    http://localhost:8000/deliveries?lot=2026-10-01&page=1&page_size=500
"""
import json
from pathlib import Path

from flask import Flask, abort, jsonify, request

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
app = Flask(__name__)
_cache = {}


def _lots():
    return sorted(p.parent.name for p in RAW_DIR.glob("*/deliveries.json"))


def _load(lot):
    if lot not in _cache:
        path = RAW_DIR / lot / "deliveries.json"
        if not path.exists():
            abort(404, description=f"Lot inconnu : {lot}")
        _cache[lot] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[lot]


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/lots")
def lots():
    return jsonify(lots=_lots())


@app.get("/deliveries")
def deliveries():
    available = _lots()
    lot = request.args.get("lot") or (available[0] if available else abort(404))
    page = max(int(request.args.get("page", 1)), 1)
    size = min(max(int(request.args.get("page_size", 500)), 1), 5000)
    data = _load(lot)
    return jsonify(lot=lot, page=page, page_size=size, total=len(data),
                   items=data[(page - 1) * size: page * size])


if __name__ == "__main__":
    app.run(port=8000)
