import streamlit as st
from groq import Groq
from docx import Document
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import difflib
import re

client = Groq(api_key="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")

# --- SESSION STATE INITIALISIEREN ---
if "anzeige" not in st.session_state:
    st.session_state.anzeige = None
if "historie" not in st.session_state:
    st.session_state.historie = []
if "hr_status" not in st.session_state:
    st.session_state.hr_status = None
if "hr_kommentar" not in st.session_state:
    st.session_state.hr_kommentar = ""
if "job_titel_gespeichert" not in st.session_state:
    st.session_state.job_titel_gespeichert = ""
if "compliance" not in st.session_state:
    st.session_state.compliance = None
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = 0

# --- HILFSFUNKTIONEN ---
def formatiere_ueberschriften(text):
    zeilen = text.split("\n")
    ergebnis = []
    for zeile in zeilen:
        if zeile.startswith("# "):
            ergebnis.append("### " + zeile.lstrip("#").strip().upper())
        elif zeile.startswith("## "):
            ergebnis.append("#### " + zeile.lstrip("#").strip().upper())
        else:
            ergebnis.append(zeile)
    return "\n".join(ergebnis)

def hole_wissen_aus_archiv(job_titel):
    try:
        with open("archiv.txt", "r", encoding="utf-8") as f:
            alle_anzeigen = f.read().split("---")
            treffer = [a.strip() for a in alle_anzeigen if any(wort.lower() in a.lower() for wort in job_titel.split())]
            if treffer:
                return "\n---\n".join(treffer[:2])
            else:
                return alle_anzeigen[6].strip()
    except:
        return "Nutze einen modernen IT-Stil."

def fuehre_compliance_loop_durch(anzeige_text):
    aktuelle_anzeige = anzeige_text
    for versuch in range(1, 4):
        compliance_prompt = f"""
        Du bist ein Experte für deutsches Arbeitsrecht und diskriminierungsfreie Sprache.
        
        Analysiere diese Stellenanzeige auf problematische Formulierungen:
        {aktuelle_anzeige}
        
        Prüfe auf folgende Probleme:
        - Altersdiskriminierung (z.B. "jung", "junges Team", "Young Professional")
        - Geschlechterdiskriminierung (fehlende Genderung, ausschließlich männliche Form)
        - Sprachdiskriminierung (z.B. "Muttersprache Deutsch")
        - Überforderungs-Begriffe (z.B. "belastbar", "stressresistent")
        - Unrealistische Anforderungen
        - Versteckte Diskriminierung (z.B. "kulturelle Passung")
        
        Antworte NUR in diesem Format:
        STATUS: [BESTANDEN oder PROBLEME GEFUNDEN]
        PROBLEME:
        - [Problem 1 mit Erklärung]
        EMPFEHLUNG:
        - [Konkrete Verbesserung 1]
        
        Falls keine Probleme: schreibe bei PROBLEME: "Keine gefunden ✅"
        """
        check_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": compliance_prompt}]
        )
        ergebnis = check_response.choices[0].message.content

        if "BESTANDEN" in ergebnis:
            return aktuelle_anzeige

        if versuch < 3:
            korrektur_prompt = f"""
            Diese Stellenanzeige hat Compliance-Probleme:
            {ergebnis}
            
            Aktuelle Anzeige:
            {aktuelle_anzeige}
            
            Korrigiere NUR die problematischen Stellen.
            Schreibe die vollständige korrigierte Anzeige zurück.
            """
            korrektur_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": korrektur_prompt}]
            )
            aktuelle_anzeige = formatiere_ueberschriften(
                korrektur_response.choices[0].message.content
            )

    return aktuelle_anzeige

def erstelle_word_dokument(anzeige_text):
    doc = Document()
    titel = doc.add_heading("Stellenanzeige", 0)
    titel.alignment = 1
    for zeile in anzeige_text.split("\n"):
        zeile = zeile.strip()
        if not zeile:
            doc.add_paragraph("")
        elif zeile.startswith("## "):
            doc.add_heading(zeile.replace("## ", ""), level=2)
        elif zeile.startswith("# "):
            doc.add_heading(zeile.replace("# ", ""), level=1)
        elif zeile.startswith("- "):
            doc.add_paragraph(zeile.replace("- ", ""), style="List Bullet")
        else:
            absatz = doc.add_paragraph()
            teile = re.split(r'(\*\*.*?\*\*)', zeile)
            for teil in teile:
                if teil.startswith("**") and teil.endswith("**"):
                    lauf = absatz.add_run(teil[2:-2])
                    lauf.bold = True
                else:
                    absatz.add_run(teil)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def erstelle_pdf_dokument(anzeige_text, job_titel):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    links = 15
    pdf.set_left_margin(links)
    nutzbare_breite = pdf.w - (2 * links)

    def clean(text):
        if not text: return ""
        t = text.replace('•', '-').replace('€', 'Euro').replace('–', '-')
        return t.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_x(links)
    pdf.cell(nutzbare_breite, 10, clean(f"Stellenanzeige: {job_titel}"), ln=True, align="C")
    pdf.ln(5)

    for zeile in anzeige_text.split("\n"):
        zeile = zeile.strip()
        if not zeile:
            pdf.ln(4)
            continue
        pdf.set_x(links)
        if zeile.startswith("#"):
            saubere_zeile = clean(zeile.lstrip("#").strip())
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(nutzbare_breite, 8, saubere_zeile)
            pdf.ln(2)
        elif zeile.startswith("- "):
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(nutzbare_breite, 6, clean(f"- {zeile[2:]}"))
        else:
            saubere_zeile = clean(re.sub(r'\*\*(.*?)\*\*', r'\1', zeile))
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(nutzbare_breite, 6, saubere_zeile)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def zeige_diff_wortweise(alt_zeile, neu_zeile):
    alt_woerter = alt_zeile.split()
    neu_woerter = neu_zeile.split()
    matcher = difflib.SequenceMatcher(None, alt_woerter, neu_woerter)
    ergebnis = []
    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            ergebnis.append(" ".join(neu_woerter[b0:b1]))
        elif opcode == "insert":
            woerter = " ".join(neu_woerter[b0:b1])
            ergebnis.append(f"<span style='background-color:#00cc44;color:white;padding:2px 4px;border-radius:4px'>{woerter}</span>")
        elif opcode == "delete":
            woerter = " ".join(alt_woerter[a0:a1])
            ergebnis.append(f"<span style='background-color:#ff4444;color:white;padding:2px 4px;border-radius:4px;text-decoration:line-through'>{woerter}</span>")
        elif opcode == "replace":
            alt_w = " ".join(alt_woerter[a0:a1])
            neu_w = " ".join(neu_woerter[b0:b1])
            ergebnis.append(f"<span style='background-color:#ff4444;color:white;padding:2px 4px;border-radius:4px;text-decoration:line-through'>{alt_w}</span> <span style='background-color:#00cc44;color:white;padding:2px 4px;border-radius:4px'>{neu_w}</span>")
    return " ".join(ergebnis)

# --- FIRMEN-STECKBRIEF ---
FIRMEN_NAME = "Alwina Digital"
ANREDE = "Du"
GENDER_STIL = "Gender-Sternchen (z.B. Mitarbeiter*innen)"
HIGHLIGHT = "Dachterrasse in Wiesbaden"
SENIOR_MIN_GEHALT = 80000
JUNIOR_MAX_ERFAHRUNG = 2

def pruefe_ausschreibung(daten):
    berichte = []
    level = daten["level"].lower()
    if level == "senior" and daten["gehalt"] < SENIOR_MIN_GEHALT and daten["gehalt"] > 0:
        berichte.append(f"❌ Gehalt ({daten['gehalt']}€) ist zu niedrig für ein Senior-Level (Min: {SENIOR_MIN_GEHALT}€).")
    if level == "junior" and daten["erfahrung"] > JUNIOR_MAX_ERFAHRUNG:
        berichte.append(f"❌ Ein Junior sollte nicht {daten['erfahrung']} Jahre Erfahrung haben (Max: {JUNIOR_MAX_ERFAHRUNG}).")
    if daten["ort"].lower() == "remote" and not daten["homeoffice"]:
        berichte.append("❌ Widerspruch: 'Remote' gewählt, aber Homeoffice ist deaktiviert!")
    return berichte

# --- WEB-OBERFLÄCHE ---
st.set_page_config(page_title="Recruitment-Check", page_icon="🏢")

col_titel, col_reset = st.columns([5, 1])
with col_titel:
    st.title("Recruitment-Check Tool 🚀")
    st.markdown("Nutze dieses Tool, um Stellenanzeigen vor der Veröffentlichung zu prüfen.")
with col_reset:
    st.write("")
    st.write("")
    if st.button("🔄 Neu"):
        trigger = st.session_state.get("reset_trigger", 0) + 1
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.reset_trigger = trigger
        st.rerun()

col1, col2 = st.columns(2)
with col1:
    job_titel = st.text_input(
        "Titel der Stelle",
        placeholder="z.B. IT Consultant",
        key=f"job_titel_{st.session_state.reset_trigger}")
    level = st.selectbox(
        "Erfahrungslevel", ["Junior", "Senior", "Lead"],
        key=f"level_{st.session_state.reset_trigger}")
    gehalt = st.number_input(
        "Gehalt pro Jahr (in €)", min_value=0, value=0, step=1000,
        key=f"gehalt_{st.session_state.reset_trigger}")
with col2:
    erfahrung = st.number_input(
        "Berufserfahrung (Jahre)", min_value=0, value=0,
        key=f"erfahrung_{st.session_state.reset_trigger}")
    ort = st.selectbox(
        "Arbeitsmodell", ["On-site", "Remote", "Hybrid"],
        key=f"ort_{st.session_state.reset_trigger}")
    homeoffice = st.checkbox(
        "Homeoffice-Option verfügbar?", value=True,
        key=f"homeoffice_{st.session_state.reset_trigger}")
    aufgaben = st.text_area(
        "Was sind die Hauptaufgaben?",
        placeholder="z.B. - Einkauf von IT-Hardware\n- Verhandlung mit Lieferanten",
        key=f"aufgaben_{st.session_state.reset_trigger}")

# --- SCHRITT 1: ANALYSE STARTEN ---
if st.button("Analyse starten"):
    if not job_titel:
        st.warning("⚠️ Bitte gib mindestens einen Jobtitel ein.")
    elif gehalt == 0:
        st.warning("⚠️ Bitte gib ein Gehalt ein.")
    else:
        aktuelle_daten = {
            "titel": job_titel,
            "level": level,
            "gehalt": gehalt,
            "erfahrung": erfahrung,
            "ort": ort,
            "homeoffice": homeoffice
        }
        ergebnisse = pruefe_ausschreibung(aktuelle_daten)

        if ergebnisse:
            st.error("Folgende Probleme wurden gefunden:")
            for fehler in ergebnisse:
                st.write(fehler)
        else:
            st.session_state.job_titel_gespeichert = job_titel
            relevantes_wissen = hole_wissen_aus_archiv(job_titel)
            system_prompt = f"""
            Du bist ein HR-Experte für Alwina Digital in Wiesbaden.
            
            STIL-VORLAGE AUS UNSEREM ARCHIV (Nutze diesen Stil!):
            {relevantes_wissen}
            
            AUFTRAG:
            Schreibe eine neue, begeisternde Stellenanzeige für die Position: {job_titel}.
            Nutze die Tonalität und Struktur der Vorlage (Impact, Aufgaben, Profil).
            
            WICHTIGE REGEL ZU GEHALT:
            Erwähne die konkrete Zahl ({gehalt}) auf keinen Fall.
            Nutze stattdessen elegante Formulierungen wie: 'Dich erwartet ein attraktives Vergütungspaket'.
            
            INPUT-DETAILS:
            - Aufgaben: {aufgaben}
            - Highlight: {HIGHLIGHT}
            
            Schreibe die Anzeige in schönem Markdown-Format.
            Alle Überschriften NUR in Großbuchstaben.
            """
            with st.spinner("✍️ Anzeige wird erstellt..."):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": system_prompt}]
                    )
                    st.session_state.anzeige = formatiere_ueberschriften(
                        response.choices[0].message.content
                    )
                    st.session_state.historie.append({
                        "version": len(st.session_state.historie) + 1,
                        "inhalt": st.session_state.anzeige,
                        "typ": "Erste Version",
                        "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "bearbeiter": "KI"
                    })
                except Exception as e:
                    st.error(f"Fehler bei der Generierung: {e}")

            st.divider()
            st.markdown(st.session_state.anzeige)
            st.info("💡 Möchtest du etwas ändern? Nutze das Feedback-Feld unten. Wenn alles passt, klicke auf '📤 An HR senden'.")

# --- SCHRITT 2: FEEDBACK VOM TEAMLEITER ---
if st.session_state.anzeige:
    st.divider()
    st.subheader("💬 Feedback vom Teamleiter")
    feedback = st.text_area(
        "Was soll geändert werden?",
        placeholder="z.B. 'Nimm das Studium raus' oder 'Füge Team Events hinzu'..."
    )
    if st.button("Änderungen übernehmen"):
        if feedback:
            refinement_prompt = f"""
            Du hast bereits diese Anzeige erstellt:
            {st.session_state.anzeige}
            
            Der Teamleiter hat nun folgendes Feedback gegeben:
            "{feedback}"
            
            Bitte überarbeite NUR den Inhalt der Anzeige.
            Behalte die Struktur und alle Überschriften exakt bei.
            WICHTIG: Das Feedback des Teamleiters steht ÜBER dem Wissen aus dem Archiv.
            """
            with st.spinner("✍️ Anzeige wird angepasst..."):
                try:
                    new_response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": refinement_prompt}]
                    )
                    st.session_state.anzeige = formatiere_ueberschriften(
                        new_response.choices[0].message.content
                    )
                    st.session_state.historie.append({
                        "version": len(st.session_state.historie) + 1,
                        "inhalt": st.session_state.anzeige,
                        "typ": f"Feedback: {feedback[:50]}",
                        "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "bearbeiter": "Teamleiter"
                    })
                    st.success("✅ Anzeige wurde aktualisiert!")
                    st.markdown(st.session_state.anzeige)
                    st.info("💡 Weitere Änderungen gewünscht? Einfach neues Feedback oben eingeben und erneut auf 'Änderungen übernehmen' klicken. Wenn alles passt, unten auf '📤 An HR senden' klicken.")
                except Exception as e:
                    st.error(f"Fehler: {e}")
        else:
            st.info("Bitte gib erst ein Feedback ein.")

# --- SCHRITT 3: VERSIONS-HISTORIE ---
if st.session_state.historie:
    st.divider()
    st.subheader("📋 Versions-Historie")

    for i, version in enumerate(reversed(st.session_state.historie)):
        idx = len(st.session_state.historie) - 1 - i
        with st.expander(
            f"v{version['version']} | {version['datum']} | {version['bearbeiter']} | {version['typ']}",
            expanded=False
        ):
            if idx > 0:
                st.caption("🟢 Hinzugefügt   🔴 Entfernt")

                alt_zeilen = st.session_state.historie[idx - 1]["inhalt"].split("\n")
                neu_zeilen = version["inhalt"].split("\n")

                for neu_zeile in neu_zeilen:
                    if not neu_zeile.strip():
                        st.markdown("")
                        continue

                    beste_alte = None
                    beste_ratio = 0
                    for alt_zeile in alt_zeilen:
                        ratio = difflib.SequenceMatcher(None, alt_zeile, neu_zeile).ratio()
                        if ratio > beste_ratio:
                            beste_ratio = ratio
                            beste_alte = alt_zeile

                    if beste_ratio > 0.8:
                        diff_zeile = zeige_diff_wortweise(beste_alte, neu_zeile)
                        if neu_zeile.startswith("###") or neu_zeile.startswith("####"):
                            st.markdown(f"<div style='font-size:16px;font-weight:bold;margin-top:12px'>{diff_zeile}</div>", unsafe_allow_html=True)
                        elif neu_zeile.startswith("- "):
                            st.markdown(f"<div style='margin-left:16px'>• {diff_zeile}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='font-size:14px'>{diff_zeile}</div>", unsafe_allow_html=True)
                    elif beste_ratio < 0.3:
                        if neu_zeile.startswith("###") or neu_zeile.startswith("####"):
                            st.markdown(f"<div style='font-size:16px;font-weight:bold;margin-top:12px;background-color:#00cc4422;border-left:3px solid #00cc44;padding:4px 8px'>{neu_zeile.lstrip('#').strip()}</div>", unsafe_allow_html=True)
                        elif neu_zeile.startswith("- "):
                            st.markdown(f"<div style='margin-left:16px;background-color:#00cc4422;border-left:3px solid #00cc44;padding:4px 8px'>• {neu_zeile[2:]}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='font-size:14px;background-color:#00cc4422;border-left:3px solid #00cc44;padding:4px 8px'>{neu_zeile}</div>", unsafe_allow_html=True)
                    else:
                        diff_zeile = zeige_diff_wortweise(beste_alte, neu_zeile)
                        st.markdown(f"<div style='font-size:14px'>{diff_zeile}</div>", unsafe_allow_html=True)

                for alt_zeile in alt_zeilen:
                    if not alt_zeile.strip():
                        continue
                    in_neu = any(
                        difflib.SequenceMatcher(None, alt_zeile, n).ratio() > 0.8
                        for n in neu_zeilen
                    )
                    if not in_neu:
                        st.markdown(f"<div style='font-size:14px;background-color:#ff444422;border-left:3px solid #ff4444;padding:4px 8px;text-decoration:line-through'>{alt_zeile.strip()}</div>", unsafe_allow_html=True)

            else:
                st.caption("Erste Version")
                st.markdown(version["inhalt"])

# --- SCHRITT 4: HR FREIGABE ---
if st.session_state.anzeige:
    st.divider()
    st.subheader("📤 HR Freigabe")

    if st.session_state.hr_status is None:
        if st.button("📤 An HR senden"):
            with st.spinner("⚖️ Finale Prüfung läuft..."):
                st.session_state.anzeige = fuehre_compliance_loop_durch(
                    st.session_state.anzeige
                )
            st.session_state.hr_status = "wartend"
            st.success("✅ Anzeige wurde geprüft und an HR weitergeleitet!")
            st.rerun()

    elif st.session_state.hr_status == "wartend":
        st.info("⏳ Wartet auf HR-Freigabe...")
        st.markdown("---")
        st.markdown("**HR-Bereich – Finale Anzeige:**")
        st.markdown(st.session_state.anzeige)
        st.divider()

        hr_kommentar = st.text_area(
            "Kommentar für Teamleiter (optional):",
            placeholder="z.B. 'Bitte Anforderungen anpassen...'"
        )
        if hr_kommentar:
            st.session_state.hr_kommentar = hr_kommentar

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Freigeben"):
                st.session_state.hr_status = "freigegeben"
                st.rerun()
        with col2:
            if st.button("❌ Ablehnen"):
                st.session_state.hr_status = "abgelehnt"
                st.rerun()

    elif st.session_state.hr_status == "freigegeben":
        st.success("✅ Anzeige wurde von HR freigegeben!")
        if st.session_state.hr_kommentar:
            st.info(f"💬 Kommentar HR: {st.session_state.hr_kommentar}")

    elif st.session_state.hr_status == "abgelehnt":
        st.error("❌ Anzeige wurde von HR abgelehnt!")
        if st.session_state.hr_kommentar:
            st.info(f"💬 Begründung HR: {st.session_state.hr_kommentar}")
        if st.button("🔄 Überarbeiten"):
            st.session_state.hr_status = None
            st.rerun()

# --- SCHRITT 5: EXPORT ---
if st.session_state.hr_status == "freigegeben":
    st.divider()
    st.subheader("📥 Export")
    dateiname_basis = st.session_state.job_titel_gespeichert.replace(' ', '_')
    col1, col2 = st.columns(2)
    with col1:
        word_buffer = erstelle_word_dokument(st.session_state.anzeige)
        st.download_button(
            label="📄 Als Word herunterladen",
            data=word_buffer,
            file_name=f"stellenanzeige_{dateiname_basis}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="btn_download_word"
        )
    with col2:
        pdf_buffer = erstelle_pdf_dokument(
            st.session_state.anzeige,
            st.session_state.job_titel_gespeichert
        )
        st.download_button(
            label="📑 Als PDF herunterladen",
            data=pdf_buffer,
            file_name=f"stellenanzeige_{dateiname_basis}.pdf",
            mime="application/pdf",
            key="btn_download_pdf"
        )