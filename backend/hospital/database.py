import os
import sqlite3
from typing import Optional
from backend.hospital.seed_data import (
    SEED_PATIENTS,
    SEED_ALLERGIES,
    SEED_DIAGNOSES,
    SEED_PRESCRIPTIONS,
    SEED_PRESCRIPTION_MEDICATIONS,
)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_sim.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite hospital database.
    Configures row factory to sqlite3.Row for dictionary-like access.
    """
    path = db_path or os.getenv("HOSPITAL_DB_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_hospital_db(db_path: Optional[str] = None, force_reseed: bool = False) -> None:
    """
    Initializes SQLite tables and seeds them with realistic test data.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Create Tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            date_of_birth TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS allergies (
            allergy_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            allergen TEXT NOT NULL,
            category TEXT NOT NULL,
            reaction TEXT NOT NULL,
            severity TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        );

        CREATE TABLE IF NOT EXISTS diagnoses (
            diagnosis_id TEXT PRIMARY KEY,
            icd10_code TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            diagnosis_id TEXT NOT NULL,
            prescribed_date TEXT NOT NULL,
            prescriber_name TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
            FOREIGN KEY (diagnosis_id) REFERENCES diagnoses (diagnosis_id)
        );

        CREATE TABLE IF NOT EXISTS prescription_medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            route TEXT NOT NULL,
            frequency TEXT NOT NULL,
            duration TEXT NOT NULL,
            instructions TEXT NOT NULL,
            FOREIGN KEY (prescription_id) REFERENCES prescriptions (prescription_id)
        );
    """)

    # Check if seeding is needed
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    count = cursor.fetchone()["count"]

    if count == 0 or force_reseed:
        if force_reseed:
            cursor.execute("DELETE FROM prescription_medications")
            cursor.execute("DELETE FROM prescriptions")
            cursor.execute("DELETE FROM allergies")
            cursor.execute("DELETE FROM diagnoses")
            cursor.execute("DELETE FROM patients")

        # Insert Seed Patients
        for p in SEED_PATIENTS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO patients (patient_id, first_name, last_name, age, gender, date_of_birth)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (p["patient_id"], p["first_name"], p["last_name"], p["age"], p["gender"], p["date_of_birth"])
            )

        # Insert Seed Allergies
        for a in SEED_ALLERGIES:
            cursor.execute(
                """
                INSERT OR REPLACE INTO allergies (allergy_id, patient_id, allergen, category, reaction, severity)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (a["allergy_id"], a["patient_id"], a["allergen"], a["category"], a["reaction"], a["severity"])
            )

        # Insert Seed Diagnoses
        for d in SEED_DIAGNOSES:
            cursor.execute(
                """
                INSERT OR REPLACE INTO diagnoses (diagnosis_id, icd10_code, description)
                VALUES (?, ?, ?)
                """,
                (d["diagnosis_id"], d["icd10_code"], d["description"])
            )

        # Insert Seed Prescriptions
        for rx in SEED_PRESCRIPTIONS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO prescriptions (prescription_id, patient_id, diagnosis_id, prescribed_date, prescriber_name, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (rx["prescription_id"], rx["patient_id"], rx["diagnosis_id"], rx["prescribed_date"], rx["prescriber_name"], rx["status"], rx.get("notes"))
            )

        # Insert Seed Medications
        for m in SEED_PRESCRIPTION_MEDICATIONS:
            cursor.execute(
                """
                INSERT INTO prescription_medications (prescription_id, medication_name, generic_name, dosage, route, frequency, duration, instructions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (m["prescription_id"], m["medication_name"], m["generic_name"], m["dosage"], m["route"], m["frequency"], m["duration"], m["instructions"])
            )

        conn.commit()

    conn.close()
