from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from flask_swagger_ui import get_swaggerui_blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config import Config
from models import db, User, Patient, Consultation
from datetime import datetime
import logging, re, os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
jwt    = JWTManager(app)
CORS(app)

limiter = Limiter(get_remote_address, app=app,
                  default_limits=["200 per day", "50 per hour"])

logging.basicConfig(filename="dme.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def log(msg): logging.info(msg)

def valider_chaine(v, n=100):
    return bool(v and isinstance(v, str) and 0 < len(v.strip()) <= n)

def valider_age(age):
    try: return 0 < int(age) < 150
    except: return False

def valider_contact(c):
    if not c: return True
    return bool(re.match(r'^[\d\s\+\-]{6,20}$', c))

def is_admin():
    return get_jwt().get("role") == "admin"

# ===================== SWAGGER =====================
SWAGGER_URL = "/docs"
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, "/swagger.json",
                                               config={"app_name": "API DME"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route("/swagger.json")
def swagger_json():
    return jsonify({
        "swagger": "2.0",
        "info": {"title": "API DME", "version": "1.0.0"},
        "basePath": "/",
        "securityDefinitions": {"Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}},
        "tags": [
            {"name": "Auth"}, {"name": "Patients"},
            {"name": "Consultations"}, {"name": "Users"},
            {"name": "Stats"}
        ],
        "paths": {
            "/auth/login":   {"post": {"tags": ["Auth"], "summary": "Connexion",
                "parameters": [{"in":"body","name":"body","required":True,"schema":{"type":"object","properties":{
                    "username":{"type":"string","example":"admin"},
                    "password":{"type":"string","example":"admin123"}}}}],
                "responses": {"200":{"description":"Token JWT"},"401":{"description":"Erreur"}}}},
            "/auth/register":{"post": {"tags": ["Auth"], "summary": "Créer utilisateur",
                "security":[{"Bearer":[]}],
                "parameters": [{"in":"body","name":"body","required":True,"schema":{"type":"object","properties":{
                    "username":{"type":"string"},"password":{"type":"string"},"role":{"type":"string"}}}}],
                "responses": {"201":{"description":"Créé"}}}},
            "/patients":     {
                "get":  {"tags":["Patients"],"summary":"Voir tous","security":[{"Bearer":[]}],
                         "responses":{"200":{"description":"OK"}}},
                "post": {"tags":["Patients"],"summary":"Ajouter","security":[{"Bearer":[]}],
                         "parameters":[{"in":"body","name":"body","required":True,"schema":{"type":"object","properties":{
                             "nom":{"type":"string","example":"Mensah"},
                             "prenom":{"type":"string","example":"Kossi"},
                             "age":{"type":"integer","example":28},
                             "sexe":{"type":"string","example":"M"},
                             "contact":{"type":"string","example":"0909090909"}}}}],
                         "responses":{"201":{"description":"Ajouté"}}}},
            "/patients/{id}": {
                "get":    {"tags":["Patients"],"summary":"Voir un patient","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"}],
                           "responses":{"200":{"description":"OK"}}},
                "put":    {"tags":["Patients"],"summary":"Modifier","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"},
                               {"in":"body","name":"body","schema":{"type":"object"}}],
                           "responses":{"200":{"description":"OK"}}},
                "delete": {"tags":["Patients"],"summary":"Supprimer","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"}],
                           "responses":{"200":{"description":"OK"}}}},
            "/patients/{id}/consultations": {
                "get":  {"tags":["Consultations"],"summary":"Voir consultations","security":[{"Bearer":[]}],
                         "parameters":[{"name":"id","in":"path","required":True,"type":"integer"}],
                         "responses":{"200":{"description":"OK"}}},
                "post": {"tags":["Consultations"],"summary":"Ajouter","security":[{"Bearer":[]}],
                         "parameters":[{"name":"id","in":"path","required":True,"type":"integer"},
                             {"in":"body","name":"body","required":True,"schema":{"type":"object","properties":{
                                 "symptomes":{"type":"string"},"diagnostic":{"type":"string"},
                                 "traitement":{"type":"string"}}}}],
                         "responses":{"201":{"description":"OK"}}}},
            "/consultations/{id}": {
                "put":    {"tags":["Consultations"],"summary":"Modifier","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"},
                               {"in":"body","name":"body","schema":{"type":"object"}}],
                           "responses":{"200":{"description":"OK"}}},
                "delete": {"tags":["Consultations"],"summary":"Supprimer","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"}],
                           "responses":{"200":{"description":"OK"}}}},
            "/users":        {"get": {"tags":["Users"],"summary":"Voir utilisateurs","security":[{"Bearer":[]}],
                              "responses":{"200":{"description":"OK"}}}},
            "/users/{id}":   {
                "delete": {"tags":["Users"],"summary":"Supprimer","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"}],
                           "responses":{"200":{"description":"OK"}}},
                "put":    {"tags":["Users"],"summary":"Changer rôle","security":[{"Bearer":[]}],
                           "parameters":[{"name":"id","in":"path","required":True,"type":"integer"},
                               {"in":"body","name":"body","schema":{"type":"object","properties":{
                                   "role":{"type":"string"}}}}],
                           "responses":{"200":{"description":"OK"}}}},
            "/stats":        {"get": {"tags":["Stats"],"summary":"Statistiques","security":[{"Bearer":[]}],
                              "responses":{"200":{"description":"OK"}}}}
        }
    })

# ===================== INIT DB =====================
with app.app_context():
    db.create_all()
    if not User.query.first():
        mdp = bcrypt.generate_password_hash("DME_Admin_2026!").decode("utf-8")
        db.session.add(User(username="admin", password=mdp, role="admin"))
        db.session.commit()
        print("✅ Admin créé : admin / DME_Admin_2026!")

# ===================== ROUTES =====================

@app.route("/")
def home():
    return jsonify({"message": "API DME opérationnelle ✅"})

@app.route("/interface")
def interface():
    return render_template("index.html")

# ---- AUTH ----

@app.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"erreur": "Champs obligatoires"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        log(f"Connexion échouée : {username}")
        return jsonify({"erreur": "Identifiants incorrects"}), 401
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "username": user.username}
    )
    log(f"Connexion réussie : {username}")
    return jsonify({"token": token, "role": user.role, "username": user.username, "message": "Connexion réussie ✅"})

@app.route("/auth/register", methods=["POST"])
@jwt_required()
def register():
    if not is_admin():
        return jsonify({"erreur": "Accès refusé"}), 403
    data = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role     = data.get("role", "medecin")
    if not valider_chaine(username, 80) or not password:
        return jsonify({"erreur": "Données invalides"}), 400
    if len(password) < 6:
        return jsonify({"erreur": "Mot de passe trop court (min 6 caractères)"}), 400
    if role not in ["admin", "medecin"]:
        return jsonify({"erreur": "Rôle invalide"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"erreur": "Utilisateur existe déjà"}), 400
    mdp  = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=mdp, role=role)
    db.session.add(user)
    db.session.commit()
    log(f"Utilisateur créé : {username} ({role})")
    return jsonify({"message": "Utilisateur créé ✅"}), 201

# ---- PATIENTS ----

@app.route("/patients", methods=["POST"])
@jwt_required()
def add_patient():
    data = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    nom     = data.get("nom", "").strip()
    prenom  = data.get("prenom", "").strip()
    age     = data.get("age")
    sexe    = data.get("sexe", "")
    contact = data.get("contact", "").strip()
    if not valider_chaine(nom) or not valider_chaine(prenom):
        return jsonify({"erreur": "Nom et prénom invalides"}), 400
    if not valider_age(age):
        return jsonify({"erreur": "Âge invalide (1-150)"}), 400
    if sexe and sexe not in ["M", "F"]:
        return jsonify({"erreur": "Sexe invalide"}), 400
    if contact and not valider_contact(contact):
        return jsonify({"erreur": "Contact invalide"}), 400
    patient = Patient(nom=nom, prenom=prenom, age=int(age), sexe=sexe, contact=contact)
    db.session.add(patient)
    db.session.commit()
    log(f"Patient ajouté : {nom} {prenom}")
    return jsonify({"message": "Patient ajouté ✅", "id": patient.id}), 201

@app.route("/patients", methods=["GET"])
@jwt_required()
def get_patients():
    try:
        return jsonify([p.to_dict() for p in Patient.query.all()])
    except Exception as e:
        log(f"Erreur get_patients: {str(e)}")
        return jsonify({"erreur": "Erreur interne"}), 500

@app.route("/patients/<int:id>", methods=["GET"])
@jwt_required()
def get_patient(id):
    p = Patient.query.get(id)
    if not p:
        return jsonify({"erreur": "Patient introuvable"}), 404
    data = p.to_dict()
    data["consultations"] = [c.to_dict() for c in p.consultations]
    return jsonify(data)

@app.route("/patients/<int:id>", methods=["PUT"])
@jwt_required()
def update_patient(id):
    p = Patient.query.get(id)
    if not p:
        return jsonify({"erreur": "Patient introuvable"}), 404
    data    = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    nom     = data.get("nom",     p.nom).strip()
    prenom  = data.get("prenom",  p.prenom).strip()
    age     = data.get("age",     p.age)
    if not valider_chaine(nom) or not valider_chaine(prenom):
        return jsonify({"erreur": "Nom ou prénom invalide"}), 400
    if not valider_age(age):
        return jsonify({"erreur": "Âge invalide"}), 400
    p.nom = nom; p.prenom = prenom; p.age = int(age)
    p.sexe = data.get("sexe", p.sexe)
    p.contact = data.get("contact", p.contact)
    db.session.commit()
    log(f"Patient modifié : ID {id}")
    return jsonify({"message": "Patient modifié ✅"})

@app.route("/patients/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_patient(id):
    p = Patient.query.get(id)
    if not p:
        return jsonify({"erreur": "Patient introuvable"}), 404
    db.session.delete(p)
    db.session.commit()
    log(f"Patient supprimé : ID {id}")
    return jsonify({"message": "Patient supprimé ✅"})

# ---- CONSULTATIONS ----

@app.route("/patients/<int:id>/consultations", methods=["POST"])
@jwt_required()
def add_consultation(id):
    p = Patient.query.get(id)
    if not p:
        return jsonify({"erreur": "Patient introuvable"}), 404
    data = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    symptomes  = data.get("symptomes",  "").strip()
    diagnostic = data.get("diagnostic", "").strip()
    traitement = data.get("traitement", "").strip()
    if not symptomes and not diagnostic:
        return jsonify({"erreur": "Symptômes ou diagnostic requis"}), 400
    c = Consultation(symptomes=symptomes, diagnostic=diagnostic,
                     traitement=traitement, patient_id=id)
    db.session.add(c)
    db.session.commit()
    log(f"Consultation ajoutée : patient ID {id}")
    return jsonify({"message": "Consultation ajoutée ✅", "id": c.id}), 201

@app.route("/patients/<int:id>/consultations", methods=["GET"])
@jwt_required()
def get_consultations(id):
    p = Patient.query.get(id)
    if not p:
        return jsonify({"erreur": "Patient introuvable"}), 404
    return jsonify([c.to_dict() for c in p.consultations])

@app.route("/consultations/<int:id>", methods=["PUT"])
@jwt_required()
def update_consultation(id):
    c = Consultation.query.get(id)
    if not c:
        return jsonify({"erreur": "Consultation introuvable"}), 404
    data = request.json
    if not data:
        return jsonify({"erreur": "Données manquantes"}), 400
    c.symptomes  = data.get("symptomes",  c.symptomes)
    c.diagnostic = data.get("diagnostic", c.diagnostic)
    c.traitement = data.get("traitement", c.traitement)
    db.session.commit()
    log(f"Consultation modifiée : ID {id}")
    return jsonify({"message": "Consultation modifiée ✅"})

@app.route("/consultations/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_consultation(id):
    c = Consultation.query.get(id)
    if not c:
        return jsonify({"erreur": "Consultation introuvable"}), 404
    db.session.delete(c)
    db.session.commit()
    log(f"Consultation supprimée : ID {id}")
    return jsonify({"message": "Consultation supprimée ✅"})

# ---- USERS ----

@app.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    if not is_admin():
        return jsonify({"erreur": "Accès refusé"}), 403
    return jsonify([{"id": u.id, "username": u.username, "role": u.role}
                    for u in User.query.all()])

@app.route("/users/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    if not is_admin():
        return jsonify({"erreur": "Accès refusé"}), 403
    u = User.query.get(id)
    if not u:
        return jsonify({"erreur": "Utilisateur introuvable"}), 404
    if u.username == "admin":
        return jsonify({"erreur": "Impossible de supprimer l'admin principal"}), 400
    db.session.delete(u)
    db.session.commit()
    log(f"Utilisateur supprimé : ID {id}")
    return jsonify({"message": "Utilisateur supprimé ✅"})

@app.route("/users/<int:id>/role", methods=["PUT"])
@jwt_required()
def update_role(id):
    if not is_admin():
        return jsonify({"erreur": "Accès refusé"}), 403
    u = User.query.get(id)
    if not u:
        return jsonify({"erreur": "Utilisateur introuvable"}), 404
    data = request.json
    role = data.get("role")
    if role not in ["admin", "medecin"]:
        return jsonify({"erreur": "Rôle invalide"}), 400
    u.role = role
    db.session.commit()
    log(f"Rôle modifié : {u.username} → {role}")
    return jsonify({"message": "Rôle modifié ✅"})

# ---- STATS ----

@app.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    try:
        patients      = Patient.query.all()
        consultations = Consultation.query.all()

        # Consultations par mois (12 derniers mois)
        mois_labels = []
        mois_data   = []
        now = datetime.utcnow()
        for i in range(11, -1, -1):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)
            label = f"{y}-{m:02d}"
            count = sum(1 for c in consultations
                        if c.date.month == m and c.date.year == y)
            mois_labels.append(f"{m:02d}/{y}")
            mois_data.append(count)

        # Répartition par sexe
        hommes = sum(1 for p in patients if p.sexe == "M")
        femmes = sum(1 for p in patients if p.sexe == "F")
        autres = len(patients) - hommes - femmes

        # Top 5 patients les plus consultés
        top_patients = sorted(patients, key=lambda p: len(p.consultations), reverse=True)[:5]
        top_data = [{"nom": f"{p.nom} {p.prenom}", "nb": len(p.consultations)}
                    for p in top_patients]

        return jsonify({
            "total_patients":      len(patients),
            "total_consultations": len(consultations),
            "mois_labels":         mois_labels,
            "mois_data":           mois_data,
            "sexe":                {"hommes": hommes, "femmes": femmes, "autres": autres},
            "top_patients":        top_data
        })
    except Exception as e:
        log(f"Erreur get_stats: {str(e)}")
        return jsonify({"erreur": "Erreur interne"}), 500

# ===================== LANCEMENT =====================
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)