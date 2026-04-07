from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role     = db.Column(db.String(20), default="medecin")

    def __repr__(self):
        return f"<User {self.username} - {self.role}>"


class Patient(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    prenom        = db.Column(db.String(100), nullable=False)
    age           = db.Column(db.Integer, nullable=False)
    sexe          = db.Column(db.String(10))
    contact       = db.Column(db.String(20))
    consultations = db.relationship(
        "Consultation", backref="patient",
        lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id, "nom": self.nom, "prenom": self.prenom,
            "age": self.age, "sexe": self.sexe, "contact": self.contact
        }

    def __repr__(self):
        return f"<Patient {self.nom} {self.prenom}>"


class Consultation(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    date       = db.Column(db.DateTime, default=datetime.utcnow)
    symptomes  = db.Column(db.Text)
    diagnostic = db.Column(db.Text)
    traitement = db.Column(db.Text)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d %H:%M"),
            "symptomes": self.symptomes,
            "diagnostic": self.diagnostic,
            "traitement": self.traitement,
            "patient_id": self.patient_id
        }

    def __repr__(self):
        return f"<Consultation {self.id} - Patient {self.patient_id}>"