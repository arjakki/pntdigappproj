import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ed_database.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mrn             TEXT UNIQUE NOT NULL,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            dob             TEXT NOT NULL,
            age             INTEGER,
            biological_sex  TEXT,
            phone           TEXT,
            address         TEXT,
            language        TEXT DEFAULT 'English',
            ssn_last4       TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS triage_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER REFERENCES patients(id),
            mrn             TEXT,
            arrival_date    TEXT,
            arrival_time    TEXT,
            arrival_mode    TEXT,
            chief_complaint TEXT,
            esi_level       INTEGER,
            disposition     TEXT,
            triage_nurse    TEXT,
            triage_note     TEXT,
            isolation_type  TEXT DEFAULT 'None',
            fall_risk       TEXT DEFAULT 'Low',
            code_status     TEXT DEFAULT 'Full Code',
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS vital_signs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            triage_id           INTEGER REFERENCES triage_records(id),
            patient_id          INTEGER REFERENCES patients(id),
            reading_number      INTEGER DEFAULT 1,
            reading_time        TEXT,
            blood_pressure      TEXT,
            heart_rate          INTEGER,
            respiratory_rate    INTEGER,
            temperature         REAL,
            spo2                INTEGER,
            o2_source           TEXT DEFAULT 'RA',
            glucose             INTEGER,
            gcs                 INTEGER DEFAULT 15,
            recorded_at         TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS allergies (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER REFERENCES patients(id),
            allergen        TEXT NOT NULL,
            reaction_type   TEXT,
            severity        TEXT,
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS medications (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id          INTEGER REFERENCES patients(id),
            medication_name     TEXT NOT NULL,
            dose                TEXT,
            frequency           TEXT,
            route               TEXT DEFAULT 'PO',
            last_taken          TEXT
        );

        CREATE TABLE IF NOT EXISTS medical_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER REFERENCES patients(id),
            condition_name  TEXT NOT NULL,
            category        TEXT DEFAULT 'PMH',
            year_diagnosed  INTEGER
        );

        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER REFERENCES patients(id),
            name            TEXT NOT NULL,
            relationship    TEXT,
            phone           TEXT
        );
    """)

    cur.execute("SELECT COUNT(*) FROM patients")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    patients = [
        ("MRN-2024-001","James","Hartford","1965-03-15",59,"Male","(617) 555-0142","24 Elm Street, Boston, MA 02134","English","4521"),
        ("MRN-2024-002","Maria","Gonzalez","1989-07-22",35,"Female","(617) 555-0287","89 Oak Ave, Cambridge, MA 02139","Spanish","7823"),
        ("MRN-2024-003","David","Chen","1978-11-04",46,"Male","(617) 555-0391","12 Maple Dr, Somerville, MA 02143","Mandarin","3156"),
        ("MRN-2024-004","Patricia","Williams","1943-05-30",81,"Female","(617) 555-0456","567 Pine Rd, Brookline, MA 02446","English","9012"),
        ("MRN-2024-005","Marcus","Thompson","2001-09-18",23,"Male","(617) 555-0523","334 Cedar Ln, Quincy, MA 02169","English","5678"),
        ("MRN-2024-006","Sarah","Johnson","1955-12-01",69,"Female","(617) 555-0614","78 Birch Blvd, Newton, MA 02458","English","2345"),
        ("MRN-2024-007","Robert","Kim","1982-04-14",42,"Male","(617) 555-0729","456 Walnut St, Malden, MA 02148","Korean","8901"),
        ("MRN-2024-008","Aisha","Patel","1997-08-25",27,"Female","(617) 555-0834","23 Chestnut Ave, Medford, MA 02155","English","4567"),
        ("MRN-2024-009","Thomas","OBrien","1938-02-11",86,"Male","(617) 555-0947","901 Spruce St, Watertown, MA 02472","English","1234"),
        ("MRN-2024-010","Lisa","Anderson","1971-06-07",53,"Female","(617) 555-1052","145 Dogwood Dr, Arlington, MA 02474","English","6789"),
    ]
    cur.executemany(
        "INSERT INTO patients (mrn,first_name,last_name,dob,age,biological_sex,phone,address,language,ssn_last4) VALUES (?,?,?,?,?,?,?,?,?,?)",
        patients,
    )

    triage = [
        (1,"MRN-2024-001","2025-04-28","08:15","EMS — Ground Ambulance","Chest pain, crushing, started 1 hour ago. Radiating to left arm.",2,"Resuscitation Room","RN Martinez","59M presenting with acute onset crushing chest pain x1hr, radiation to L arm. ST elevation on field 12-lead by EMS. Immediate cath lab activation. STEMI protocol initiated.","None","Low","Full Code"),
        (2,"MRN-2024-002","2025-04-28","09:30","Walk-in / Ambulatory","Severe abdominal pain, right lower quadrant, nausea, vomiting for 12 hours.",3,"Main ED — Bay assignment","RN Johnson","35F c/o severe RLQ pain x12h with N/V. Rebound tenderness on exam. Concern for appendicitis. CT abdomen/pelvis ordered. Surgery consult placed.","None","Low","Full Code"),
        (3,"MRN-2024-003","2025-04-28","10:45","Private Vehicle","Laceration to right hand, 3cm, from kitchen knife. No numbness.",4,"Fast Track","RN Garcia","46M with 3cm laceration R hand from kitchen accident. Bleeding controlled with pressure. Sensation intact distally. Wound irrigation and repair in fast track.","None","Low","Full Code"),
        (4,"MRN-2024-004","2025-04-28","11:00","EMS — Ground Ambulance","Found unresponsive at home by family. History of diabetes and hypertension.",1,"Resuscitation Room","RN Thompson","81F found unresponsive, GCS 8 on arrival. FSBS 38 mg/dL — severe hypoglycemia. D50 administered by EMS x1. History of T2DM on insulin. Airway maintained, monitoring closely.","None","High","DNR — No CPR, no intubation"),
        (5,"MRN-2024-005","2025-04-28","12:20","Walk-in / Ambulatory","Left ankle pain after twisting during basketball. Cannot bear weight.",4,"Fast Track","RN Patel","23M with acute L ankle injury playing basketball. Ottawa criteria positive. XR ordered. No neurovascular compromise. Pain managed with ice and elevation.","None","Low","Full Code"),
        (6,"MRN-2024-006","2025-04-28","13:15","Private Vehicle","Shortness of breath, worse over 3 days. History of COPD.",2,"Main ED — Bay assignment","RN Williams","69F with known COPD presenting with progressive dyspnea x3d. Wheezing on auscultation. SpO2 88% on RA. Placed on 2L NC with improvement to 94%. Nebulizer treatment initiated.","None","Moderate","Full Code"),
        (7,"MRN-2024-007","2025-04-28","14:30","Walk-in / Ambulatory","Severe headache, worst of my life, sudden onset 2 hours ago.",2,"Main ED — Bay assignment","RN Chen","42M thunderclap headache onset 2h ago, 10/10 pain. No prior hx. CT head ordered STAT. Neurology consulted. Concern for SAH. Patient lying still in dark room.","None","Low","Full Code"),
        (8,"MRN-2024-008","2025-04-28","15:45","Walk-in / Ambulatory","Fever 102F, sore throat, difficulty swallowing for 2 days.",4,"Fast Track","RN Davis","27F with 2d hx of fever, pharyngitis, odynophagia. Tonsillar exudates noted. Rapid strep pending. Mononucleosis in differential given LAD.","Droplet","Low","Full Code"),
        (9,"MRN-2024-009","2025-04-28","16:00","EMS — Ground Ambulance","Fall from standing, hit head. Anticoagulated on Coumadin.",2,"Main ED — Bay assignment","RN Robinson","86M fall from standing, head strike. On warfarin for AF. CT head ordered urgently. GCS 14 on arrival. Significant head laceration. INR pending.","None","High","Full Code"),
        (10,"MRN-2024-010","2025-04-28","17:30","Walk-in / Ambulatory","Urinary burning, frequency for 3 days. Possible UTI.",5,"Fast Track","RN Taylor","53F presenting with classic UTI symptoms x3d. UA ordered. No flank pain, no fever. Low complexity visit. Empiric antibiotic likely if UA positive.","None","Low","Full Code"),
        (1,"MRN-2024-001","2025-03-15","22:00","EMS — Ground Ambulance","Chest pressure, similar to previous MI. Diaphoresis.",2,"Resuscitation Room","RN Adams","Prior STEMI patient returning with recurrent chest pressure. EKG shows new changes. Cardiology at bedside.","None","Low","Full Code"),
        (6,"MRN-2024-006","2025-02-20","14:00","Private Vehicle","COPD exacerbation, worse today. Using rescue inhaler every hour.",3,"Main ED — Bay assignment","RN Lee","Known COPD, 3rd ED visit this month. SpO2 85% on RA. Systemic steroids, nebulizers, and BiPAP initiated.","None","Moderate","Full Code"),
    ]
    cur.executemany(
        "INSERT INTO triage_records (patient_id,mrn,arrival_date,arrival_time,arrival_mode,chief_complaint,esi_level,disposition,triage_nurse,triage_note,isolation_type,fall_risk,code_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        triage,
    )

    vitals = [
        (1,1,1,"08:18","88/60",118,24,99.1,92,"NRB",142,14),
        (2,2,1,"09:35","126/82",96,18,100.2,98,"RA",95,15),
        (3,3,1,"10:50","128/78",88,16,98.6,99,"RA",110,15),
        (4,4,1,"11:05","84/52",104,20,98.9,96,"RA",38,8),
        (5,5,1,"12:25","124/80",92,16,98.4,99,"RA",102,15),
        (6,6,1,"13:20","148/92",102,22,99.8,88,"RA",108,15),
        (7,7,1,"14:35","162/94",88,16,98.7,99,"RA",98,15),
        (8,8,1,"15:50","102/66",94,16,102.4,99,"RA",95,15),
        (9,9,1,"16:05","156/94",82,18,98.6,97,"RA",115,14),
        (10,10,1,"17:35","118/74",78,14,98.5,99,"RA",100,15),
        (11,1,1,"22:05","90/58",122,22,99.0,93,"NRB",138,14),
        (12,6,1,"14:05","142/88",108,24,99.6,85,"NC",105,15),
    ]
    cur.executemany(
        "INSERT INTO vital_signs (triage_id,patient_id,reading_number,reading_time,blood_pressure,heart_rate,respiratory_rate,temperature,spo2,o2_source,glucose,gcs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        vitals,
    )

    allergies = [
        (1,"Penicillin","Anaphylaxis","Severe","Carries EpiPen"),
        (1,"Contrast dye","Urticaria","Moderate","Pre-medicate with Benadryl"),
        (2,"Sulfa drugs","Rash","Mild",None),
        (4,"Codeine","Nausea/Vomiting","Mild",None),
        (6,"Aspirin","Bronchospasm","Severe","NSAIDs also avoided"),
        (7,"Latex","Contact dermatitis","Moderate","Use latex-free gloves"),
        (9,"Morphine","Paradoxical agitation","Moderate","Use hydromorphone instead"),
        (10,"Metronidazole","Severe nausea","Mild",None),
    ]
    cur.executemany(
        "INSERT INTO allergies (patient_id,allergen,reaction_type,severity,notes) VALUES (?,?,?,?,?)",
        allergies,
    )

    meds = [
        (1,"Metoprolol","50mg","BID","PO","This morning"),
        (1,"Lisinopril","10mg","Daily","PO","This morning"),
        (1,"Atorvastatin","40mg","Nightly","PO","Last night"),
        (1,"Aspirin","81mg","Daily","PO","This morning"),
        (2,"Oral Contraceptives","1 tablet","Daily","PO","This morning"),
        (2,"Ibuprofen","400mg","PRN","PO","12h ago"),
        (4,"Metformin","1000mg","BID","PO","Breakfast"),
        (4,"Insulin Glargine","20 units","Nightly","SubQ","Last night"),
        (4,"Amlodipine","5mg","Daily","PO","This morning"),
        (4,"Furosemide","20mg","Daily","PO","This morning"),
        (6,"Tiotropium","18mcg","Daily","Inhaled","This morning"),
        (6,"Albuterol","2 puffs","Q4h PRN","Inhaled","30 min ago"),
        (6,"Prednisone","10mg","Daily","PO","This morning"),
        (7,"Sumatriptan","100mg","PRN","PO","2 days ago"),
        (9,"Warfarin","5mg","Daily","PO","This morning"),
        (9,"Metoprolol","25mg","BID","PO","This morning"),
        (9,"Digoxin","0.125mg","Daily","PO","This morning"),
        (10,"Lisinopril","5mg","Daily","PO","This morning"),
        (10,"Levothyroxine","75mcg","Daily","PO","This morning"),
    ]
    cur.executemany(
        "INSERT INTO medications (patient_id,medication_name,dose,frequency,route,last_taken) VALUES (?,?,?,?,?,?)",
        meds,
    )

    history = [
        (1,"Hypertension","PMH",2010),(1,"CAD / MI","PMH",2022),(1,"Hyperlipidemia","PMH",2012),
        (2,"GERD","PMH",2018),(2,"Appendectomy","PSH",2020),
        (4,"Diabetes — Type 2","PMH",2005),(4,"Hypertension","PMH",2008),(4,"CHF","PMH",2018),(4,"CKD Stage 3","PMH",2019),
        (6,"COPD","PMH",2015),(6,"Hypertension","PMH",2010),(6,"Breast cancer — in remission","PMH",2017),
        (7,"Migraine disorder","PMH",2005),(7,"Hypertension","PMH",2019),
        (9,"Atrial fibrillation","PMH",2015),(9,"Hypertension","PMH",2000),(9,"Prostate cancer — treated","PMH",2018),
        (10,"Hypothyroidism","PMH",2010),(10,"Hypertension","PMH",2020),
    ]
    cur.executemany(
        "INSERT INTO medical_history (patient_id,condition_name,category,year_diagnosed) VALUES (?,?,?,?)",
        history,
    )

    contacts = [
        (1,"Helen Hartford","Spouse","(617) 555-0143"),
        (2,"Carlos Gonzalez","Spouse","(617) 555-0288"),
        (3,"Wei Chen","Spouse","(617) 555-0392"),
        (4,"Michael Williams Jr.","Son","(617) 555-0457"),
        (5,"Angela Thompson","Mother","(617) 555-0524"),
        (6,"David Johnson","Husband","(617) 555-0615"),
        (7,"Jenny Kim","Spouse","(617) 555-0730"),
        (8,"Ravi Patel","Father","(617) 555-0835"),
        (9,"Mary O'Brien","Daughter","(617) 555-0948"),
        (10,"Brian Anderson","Spouse","(617) 555-1053"),
    ]
    cur.executemany(
        "INSERT INTO emergency_contacts (patient_id,name,relationship,phone) VALUES (?,?,?,?)",
        contacts,
    )

    conn.commit()
    conn.close()
    print("Database initialized with 10 patients and sample ED records")
