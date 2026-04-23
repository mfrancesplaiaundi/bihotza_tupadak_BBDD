from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_code = Column(String, unique=True, index=True)
    pin_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    questionnaires = relationship("Questionnaire", back_populates="patient")
    biomarkers = relationship("Biomarker", back_populates="patient")

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    answers = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="questionnaires")

class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    il6_value = Column(Float)
    dental_plaque = Column(Float)
    tooth_count = Column(Integer)
    ph_value = Column(Float)
    observations = Column(String)
    measured_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="biomarkers")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"), nullable=False)

    score = Column(Float, nullable=False)
    nivel = Column(String, nullable=False)
    factores = Column(JSON, nullable=False)
    mensaje_general = Column(JSON, nullable=False)

    ia_texto = Column(JSON, nullable=True)
    ia_links = Column(JSON, nullable=True)
    ia_sources = Column(JSON, nullable=True)
    ia_mode = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")
    questionnaire = relationship("Questionnaire")
    biomarker = relationship("Biomarker")