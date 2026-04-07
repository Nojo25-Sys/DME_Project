from waitress import serve
from app import app

print("🚀 Serveur DME démarré sur http://0.0.0.0:5000")
serve(app, host="0.0.0.0", port=5000)