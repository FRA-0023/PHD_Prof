"""
i18n.py
-------
Presentation layer localization module for CLIAdapter.
Encapsulates human-facing terminal UI strings in Italian and English without impacting
internal ETL domain logic, document ingestion, or LLM inference.
"""
from typing import Dict, Any

class I18n:
    """
    Lightweight string catalog for bilingual interaction (IT vs EN).
    Maintains zero overhead and decouples presentation language from core pipelines.
    """
    SUPPORTED_LANGUAGES = {"IT", "EN"}

    MESSAGES: Dict[str, Dict[str, str]] = {
        "IT": {
            # Quota & Startup
            "remaining_calls": "Chiamate disponibili oggi: {count}",
            "quota_exceeded": "Limite giornaliero raggiunto. Riprova domani.",
            "banner_title": "PHD PROF: THE ANTIFRAGILE DOCUMENT ETL",
            "banner_subtitle": "Hexagonal Architecture & Crash-Only Pipeline",
            # Profile & Setup
            "config_header": "CONFIGURAZIONE PROMPT & DOCUMENTO",
            "saved_profiles_title": "Profili memorizzati (invarianti corso salvati):",
            "new_course_option": "Nuovo corso / Inserimento manuale",
            "folder_not_found": "cartella non trovata",
            "file_count": "{count} file",
            "choice_prompt": "Scelta [1-{total} o +, default: 1]: ",
            "profile_selected": "Profilo selezionato: \"{subject}\"",
            "label_subject": "Materia",
            "label_professor": "Professore",
            "label_doc_type": "Tipo Doc",
            "label_folder": "Cartella",
            "label_notion_course": "Corso Notion",
            "label_database": "Database",
            "label_files_found": "File trovati",
            "confirm_profile": "Usare questa configurazione? [Invio=Sì / m=Modifica / n=Nuovo]: ",
            # Modify Profile
            "modify_header": "[Modifica Profilo Corso]",
            "modify_subject": "Materia [{default}]: ",
            "modify_professor": "Tipo professore [{default}]: ",
            "doc_type_header": "Tipologia di documento:",
            "doc_type_slides": "Slide di lezione (Visual/Multimodale per PDF e PPTX — Gemini File API)",
            "doc_type_paper": "Paper / Libro / Dispensa (Estrazione analitica locale — sintesi rigorosa, dimostrazioni)",
            "doc_type_choice": "Scelta [1/2, default: {default}]: ",
            "modify_folder": "Cartella [{default}]: ",
            "reconfigure_notion": "Vuoi riconfigurare la destinazione Notion? [s/N]: ",
            "save_modifications": "Salvare le modifiche nel profilo '{subject}'? [S/n]: ",
            "profile_updated": "[OK] Profilo '{subject}' aggiornato.",
            # Manual Setup
            "prompt_subject": "Materia del corso (es. Statistical Modelling): ",
            "required_field": "Campo obbligatorio.",
            "professor_desc": "Tipo di professore — descrive il ruolo accademico del modello.",
            "professor_default_hint": "Lascia vuoto per usare il default: 'PhD Professor in {subject}'",
            "prompt_professor": "Tipo professore: ",
            "folder_header": "CARTELLA DOCUMENTI (PDF / PPTX)",
            "prompt_folder": "Percorso (supporta ~): ",
            "folder_not_found_err": "Cartella '{folder}' non trovata.",
            "folder_reenter": "Inserisci nuovo percorso cartella: ",
            "no_supported_files": "Nessun file supportato (.pdf / .pptx) in '{folder}'.",
            "folder_reenter_other": "Inserisci un'altra cartella: ",
            "save_new_profile": "Salvare questo profilo come predefinito per '{subject}'? [S/n]: ",
            "profile_saved": "[OK] Profilo '{subject}' memorizzato con successo.",
            # Notion Navigation
            "notion_nav_header": "SELEZIONE CORSO E DATABASE NOTION",
            "fetching_courses": "Recupero corsi...",
            "no_courses_found": "Nessun corso trovato nel database Courses. Controlla che l'integrazione abbia accesso alla pagina.",
            "auto_matched_course": "Corso selezionato automaticamente: \"{title}\"",
            "available_courses": "CORSI DISPONIBILI",
            "fetching_sections": "Recupero sezioni in '{title}'...",
            "no_sections_found": "Nessuna sezione trovata in '{title}'.",
            "pick_another_course": "Scegli un altro corso? [s/n]: ",
            "op_cancelled": "Nessuna sezione trovata. Operazione annullata.",
            "auto_matched_section": "Sezione selezionata automaticamente: \"{title}\"",
            "sections_in_course": "SEZIONI IN '{course}'",
            "invalid_choice": "Valore non valido.",
            "number_prompt": "Numero [1-{total}]: ",
            # Batch Execution
            "batch_header": "ELABORAZIONE: {total} file  |  {course} > {db}",
            "first_file_done": "Primo file completato. Controlla la pagina su Notion.",
            "remaining_files": "Rimangono {count} file da elaborare.",
            "continue_prompt": "Continuare con gli altri? [s/n]: ",
            "aborted_by_user": "Elaborazione interrotta dall'utente.",
            "pause_seconds": "Pausa {seconds}s...",
            "batch_summary": "Risultato: {success}/{total} file archiviati su Notion.",
            "process_another_course": "Elaborare un altro corso? [s/n]: ",
            "session_terminated": "Sessione terminata.",
            "session_archived": "File archiviati     : {success}/{total}",
            "session_remaining_calls": "Chiamate residue    : {remaining}",
            "setup_cancelled": "Setup annullato: {err}",
            "quota_warning": "Attenzione: {count} file ma solo {remaining} chiamate disponibili oggi. Lo script si fermerà al raggiungimento del limite.",
        },
        "EN": {
            # Quota & Startup
            "remaining_calls": "Available API calls today: {count}",
            "quota_exceeded": "Daily quota limit reached. Please try again tomorrow.",
            "banner_title": "PHD PROF: THE ANTIFRAGILE DOCUMENT ETL",
            "banner_subtitle": "Hexagonal Architecture & Crash-Only Pipeline",
            # Profile & Setup
            "config_header": "PROMPT & DOCUMENT CONFIGURATION",
            "saved_profiles_title": "Saved course profiles (invariant course parameters):",
            "new_course_option": "New course / Manual setup",
            "folder_not_found": "folder not found",
            "file_count": "{count} files",
            "choice_prompt": "Choice [1-{total} or +, default: 1]: ",
            "profile_selected": "Selected Profile: \"{subject}\"",
            "label_subject": "Subject",
            "label_professor": "Professor",
            "label_doc_type": "Doc Type",
            "label_folder": "Folder",
            "label_notion_course": "Notion Course",
            "label_database": "Database",
            "label_files_found": "Files found",
            "confirm_profile": "Use this configuration? [Enter=Yes / m=Modify / n=New]: ",
            # Modify Profile
            "modify_header": "[Edit Course Profile]",
            "modify_subject": "Subject [{default}]: ",
            "modify_professor": "Professor persona [{default}]: ",
            "doc_type_header": "Document type:",
            "doc_type_slides": "Lecture slides (Visual/Multimodal for PDF and PPTX — Gemini File API)",
            "doc_type_paper": "Paper / Book / Handout (Local analytical extraction — rigorous proofs & synthesis)",
            "doc_type_choice": "Choice [1/2, default: {default}]: ",
            "modify_folder": "Folder path [{default}]: ",
            "reconfigure_notion": "Reconfigure Notion target? [y/N]: ",
            "save_modifications": "Save changes to profile '{subject}'? [Y/n]: ",
            "profile_updated": "[OK] Profile '{subject}' updated.",
            # Manual Setup
            "prompt_subject": "Course subject (e.g. Statistical Modelling): ",
            "required_field": "Required field.",
            "professor_desc": "Professor persona — defines the academic role of the model.",
            "professor_default_hint": "Leave empty for default: 'PhD Professor in {subject}'",
            "prompt_professor": "Professor persona: ",
            "folder_header": "DOCUMENT FOLDER (PDF / PPTX)",
            "prompt_folder": "Folder path (supports ~): ",
            "folder_not_found_err": "Folder '{folder}' not found.",
            "folder_reenter": "Enter new folder path: ",
            "no_supported_files": "No supported files (.pdf / .pptx) found in '{folder}'.",
            "folder_reenter_other": "Enter another folder path: ",
            "save_new_profile": "Save this profile as default for '{subject}'? [Y/n]: ",
            "profile_saved": "[OK] Profile '{subject}' successfully saved.",
            # Notion Navigation
            "notion_nav_header": "NOTION COURSE & DATABASE SELECTION",
            "fetching_courses": "Fetching courses...",
            "no_courses_found": "No courses found in Courses database. Check integration permissions.",
            "auto_matched_course": "Course automatically matched: \"{title}\"",
            "available_courses": "AVAILABLE COURSES",
            "fetching_sections": "Fetching sections in '{title}'...",
            "no_sections_found": "No sections found in '{title}'.",
            "pick_another_course": "Choose another course? [y/n]: ",
            "op_cancelled": "No sections found. Operation cancelled.",
            "auto_matched_section": "Section automatically matched: \"{title}\"",
            "sections_in_course": "SECTIONS IN '{course}'",
            "invalid_choice": "Invalid value.",
            "number_prompt": "Number [1-{total}]: ",
            # Batch Execution
            "batch_header": "PROCESSING: {total} files  |  {course} > {db}",
            "first_file_done": "First file completed. Check the page on Notion.",
            "remaining_files": "{count} files remaining to process.",
            "continue_prompt": "Continue with remaining files? [y/n]: ",
            "aborted_by_user": "Batch processing aborted by user.",
            "pause_seconds": "Pausing {seconds}s...",
            "batch_summary": "Result: {success}/{total} files archived to Notion.",
            "process_another_course": "Process another course? [y/n]: ",
            "session_terminated": "Session terminated.",
            "session_archived": "Files archived      : {success}/{total}",
            "session_remaining_calls": "Remaining API calls : {remaining}",
            "setup_cancelled": "Setup cancelled: {err}",
            "quota_warning": "Warning: {count} files queued but only {remaining} API calls remaining today. Script will halt at quota limit.",
        }
    }

    def __init__(self, lang: str = "EN"):
        normalized = lang.strip().upper() if lang else "EN"
        self.lang = normalized if normalized in self.SUPPORTED_LANGUAGES else "EN"

    def t(self, key: str, **kwargs: Any) -> str:
        # Fallback cascade: requested language -> EN default -> IT fallback -> raw key string
        msg = self.MESSAGES.get(self.lang, {}).get(key)
        if msg is None:
            msg = self.MESSAGES.get("EN", {}).get(key)
        if msg is None:
            msg = self.MESSAGES.get("IT", {}).get(key, key)
        if kwargs:
            return msg.format(**kwargs)
        return msg
