# 🏥 DME - Dossiers Médicaux Électroniques

Application web de gestion de dossiers médicaux développée avec Flask.

## 🚀 Fonctionnalités

### 👥 Gestion des patients
- Ajout, modification, suppression de patients
- Informations complètes (nom, prénom, âge, sexe, contact)
- Validation des données intégrée

### 🩺 Gestion des consultations
- Création et suivi des consultations médicales
- Symptômes, diagnostic, traitement
- Historique complet par patient

### 👤 Gestion des utilisateurs
- Authentification JWT sécurisée
- Rôles : Administrateur / Médecin
- Interface d'administration

### 📊 Statistiques et rapports
- Tableau de bord en temps réel
- Graphiques des consultations mensuelles
- Répartition par sexe
- Top patients les plus consultés

### 🔐 Sécurité
- Tokens JWT avec expiration
- Rate limiting anti-abus
- Validation des entrées
- Logging des actions

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip

### Configuration
1. Cloner le dépôt :
```bash
git clone https://github.com/Nojo25-Sys/DME_Project.git
cd dme_project
```

2. Créer l'environnement virtuel :
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos clés secrètes
```

## 🚀 Lancement

### Développement
```bash
python app.py
```

### Production
```bash
python run.py
```

L'application sera accessible sur `http://localhost:5000`

## 📱 Accès

### Interface web
- URL : `http://localhost:5000/interface`
- Admin par défaut : `admin` / `DME_Admin_2026!`

### API REST
- Documentation Swagger : `http://localhost:5000/docs`
- Endpoint API : `http://localhost:5000/`

## 🏗️ Architecture

```
dme_project/
├── app.py              # Application Flask principale
├── config.py           # Configuration avec variables d'environnement
├── models.py           # Modèles de données SQLAlchemy
├── run.py              # Serveur de production (Waitress)
├── requirements.txt    # Dépendances Python
├── .env               # Variables d'environnement (à créer)
├── .gitignore         # Fichiers ignorés par Git
├── static/            # Fichiers statiques (CSS, JS)
│   ├── css/
│   └── js/
└── templates/         # Templates HTML
    └── index.html
```

## 🔧 Technologies

- **Backend** : Flask 3.1.3
- **Base de données** : SQLite avec SQLAlchemy 2.0.46
- **Authentification** : JWT avec Flask-JWT-Extended
- **Sécurité** : Bcrypt, Flask-Limiter, CORS
- **Frontend** : HTML5, CSS3, JavaScript vanilla
- **Documentation** : Swagger UI
- **Déploiement** : Waitress (production)

## 📝 API Endpoints

### Authentification
- `POST /auth/login` - Connexion
- `POST /auth/register` - Création utilisateur (admin seulement)

### Patients
- `GET /patients` - Lister tous les patients
- `POST /patients` - Ajouter un patient
- `GET /patients/{id}` - Voir un patient
- `PUT /patients/{id}` - Modifier un patient
- `DELETE /patients/{id}` - Supprimer un patient

### Consultations
- `GET /patients/{id}/consultations` - Voir consultations patient
- `POST /patients/{id}/consultations` - Ajouter consultation
- `PUT /consultations/{id}` - Modifier consultation
- `DELETE /consultations/{id}` - Supprimer consultation

### Utilisateurs (admin seulement)
- `GET /users` - Lister utilisateurs
- `PUT /users/{id}/role` - Modifier rôle
- `DELETE /users/{id}` - Supprimer utilisateur

### Statistiques
- `GET /stats` - Statistiques générales

## 🛡️ Sécurité

- Mots de passe hashés avec Bcrypt
- Tokens JWT avec expiration (3h)
- Rate limiting (200/jour, 50/heure)
- Validation des entrées utilisateur
- Logging des actions sensibles

## 📝 Notes

- Base de données SQLite créée automatiquement au premier lancement
- Compte admin créé automatiquement si aucun utilisateur n'existe
- Interface responsive pour mobile et desktop
- Support multilingue (français)

## 🤝 Contribuer

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Pusher la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.
