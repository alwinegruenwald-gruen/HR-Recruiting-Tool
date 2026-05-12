# HR Recruiting Tool

KI-gestütztes Tool zur automatischen Generierung von Stellenanzeigen mit RAG, Compliance-Check, HR-Workflow und einem KI Agenten.

🔗 **Live Demo:** [https://hr-recruiting-tool.onrender.com](https://hr-recruiting-tool.onrender.com)

---

## Was ist das?

Ein vollständiges HR-Tool das den gesamten Prozess der Stellenanzeigen-Erstellung automatisiert: von der Eingabe bis zur finalen Freigabe durch HR.

Der Teamleiter beschreibt die Stelle, die KI schreibt die Anzeige, HR gibt frei.

---

## Features

### KI-Agent
- Teamleiter beschreibt die Stelle in Freitext
- Agent analysiert den Text und stellt gezielte Rückfragen
- Generiert automatisch eine professionelle Stellenanzeige

### Formular-Modus
- Strukturierte Eingabe für erfahrene Nutzer
- Direkte Anzeigen-Generierung ohne Rückfragen

### RAG-System (Retrieval-Augmented Generation)
- Liest echte Stellenanzeigen aus einem PDF-Archiv
- Nutzt den Stil vorhandener Anzeigen als Vorlage
- Jede generierte Anzeige klingt wie das Unternehmen

### Compliance-Check
- Automatische Prüfung auf diskriminierende Formulierungen
- Prüft auf Altersdiskriminierung, Geschlechterdiskriminierung, Sprachdiskriminierung u.v.m.
- KI korrigiert Probleme automatisch (bis zu 3 Versuche)

### Teamleiter-Feedback
- Iterative Überarbeitung der Anzeige
- Versions-Historie mit farbigem Diff (was wurde geändert?)
- Klare Schritt-für-Schritt Navigation

### HR Freigabe-Workflow
- Anzeige wird an HR weitergeleitet
- HR kann freigeben oder ablehnen mit Kommentar
- Bei Ablehnung geht es zurück zur Überarbeitung

### Export
- Download als Word
- Download als PDF
- Dateiname enthält automatisch den Jobtitel

### HR-Einstellungen (Sidebar)
- Firmenname, Anrede, Gender-Stil, Highlight
- Konfigurierbare Erfahrungsstufen mit Gehalts- und Erfahrungsgrenzen
- Einstellungen werden lokal gespeichert (persistent mit Datenbank geplant)

---

## Tech-Stack

| Technologie | Verwendung |
|-------------|------------|
| Python | Hauptsprache |
| Streamlit | Web-Interface |
| Groq API | LLM (llama-3.3-70b-versatile) |
| PyMuPDF | PDF-Archiv lesen (RAG) |
| python-docx | Word-Export |
| fpdf2 | PDF-Export |
| python-dotenv | API-Key Management |
| Render | Cloud Deployment |
| GitHub | Versionskontrolle |

---

## Workflow

```
Teamleiter gibt Stelle ein (Formular oder Agent)
        ↓
KI generiert Stellenanzeige (mit RAG-Archiv)
        ↓
Compliance-Check läuft automatisch
        ↓
Teamleiter prüft & gibt Feedback
        ↓
"An HR senden" → Finale Compliance-Prüfung
        ↓
HR liest Anzeige → Freigeben oder Ablehnen
        ↓
Export als Word / PDF ✅
```

---

## Lokale Installation

### Voraussetzungen
- Python 3.9+
- Groq API Key

### Setup

```bash
# Repository klonen
git clone https://github.com/alwinegruenwald-gruen/HR-Recruiting-Tool.git
cd HR-Recruiting-Tool

# Libraries installieren
pip install -r requirements.txt

# API Key einrichten
echo "GROQ_API_KEY=dein_key_hier" > .env

# App starten
streamlit run app.py
```

### Archiv einrichten (optional)
Lege Stellenanzeigen als PDF-Dateien in den `archiv/` Ordner – die KI nutzt diese als Stil-Vorlage.

---

## Projektstruktur

```
HR-Recruiting-Tool/
├── app.py                  # Hauptanwendung
├── requirements.txt        # Python Libraries
├── .env                    # API Keys (nicht auf GitHub)
├── hr_einstellungen.json   # HR-Konfiguration
└── archiv/                 # PDF-Archiv für RAG
    ├── stellenanzeige1.pdf
    └── stellenanzeige2.pdf
```

---

## Geplante Features

- [ ] Docker-Containerisierung
- [ ] CI/CD mit GitHub Actions
- [ ] Kubernetes Deployment
- [ ] Datenbank für persistente Speicherung
- [ ] E-Mail-Benachrichtigung bei HR-Freigabe
- [ ] Mehrsprachigkeit (DE/EN)
- [ ] Duplikat-Erkennung im Archiv

---

## Entwickelt von

**Alwine Grünwald**
Junior Developer | KI & Cloud Enthusiast
[GitHub](https://github.com/alwinegruenwald-gruen)

---

## Lizenz

Dieses Projekt ist für Lern- und Portfolio-Zwecke erstellt.
