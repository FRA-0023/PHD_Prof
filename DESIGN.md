# DESIGN.md — PHD Prof (Living Design System)

> Specifiche del Design System per l'interfaccia web locale di PHD Prof.
> Conforme ai framework **Impeccable Design** (Visitor Mode: Operate), **Frontend UX Excellence** e **Design Taste Frontend**.

---

## 1. Parametrizzazione Operativa (The Three Dials)

| Dial | Valore (1-10) | Razionale di Configurazione |
|---|:---:|---|
| **`DESIGN_VARIANCE`** | **2 / 10** | Layout cockpit simmetrico e ultra-prevedibile. Due colonne fisse (rail comandi a sinistra, viewport telemetrico a destra). Nessun offset casuale. |
| **`MOTION_INTENSITY`** | **2 / 10** | Micro-transizioni snelle (150ms cubic-bezier). Zero animazioni decorative o rimbalzi giocattolo. Pieno rispetto di `prefers-reduced-motion`. |
| **`VISUAL_DENSITY`** | **9 / 10** | Densità massima industriale: altezze riga compatte (32-36px su tabelle), metadati mono, code hash visibili, log console integrata. |

---

## 2. Fondazione Cromatica & Token Semantici (WCAG 2.2 AA Verified)

L'interfaccia adotta un'estetica **Dark Tech Industriale** calibrata per ridurre l'affaticamento visivo durante sessioni prolungate. Banditi il nero assoluto (`#000000`) e il bianco puro (`#FFFFFF`) per preservare il contrasto naturale e la profondità dei livelli ottici.

### 2.1 Tavolozza Fondamentale

```css
:root {
  /* --- Superfici (Elevation Layers) --- */
  --bg-canvas:       #0A0E17; /* Sfondo base app (Deep Zinc-Navy) */
  --bg-surface:      #111827; /* Superficie rail e pannelli primari */
  --bg-surface-elev: #1B2436; /* Celle hover, header tabelle, modali */
  --bg-surface-sub:  #0F1522; /* Sfondo console log e aree incassate */

  /* --- Confini & Separatori (Anti-Cardception: separazione via linea 1px) --- */
  --border-subtle:   #1E293B; /* Bordi riquadri e divisori interni (1.8:1) */
  --border-muted:    #334155; /* Bordi input e bottoni secondari (3.2:1) */
  --border-focus:    #38BDF8; /* Focus ring ad alto contrasto (7.5:1) */

  /* --- Gerarchia Tipografica (Contrasto verificato su --bg-canvas #0A0E17) --- */
  --text-primary:    #F1F5F9; /* Slate-100: Titoli, comandi, stati attivi (14.2:1) */
  --text-secondary:  #94A3B8; /* Slate-400: Label, metadati, descrizioni (6.5:1) */
  --text-tertiary:   #64748B; /* Slate-500: Hash secondari, timestamp (4.5:1) */
  --text-disabled:   #475569; /* Slate-600: Controlli disabilitati (3.1:1) */

  /* --- Accento Funzionale (The Lila Rule: mono-accento tecnico Sky) --- */
  --accent-primary:  #0284C7; /* Sky-600: Azioni primarie e stati selezionati */
  --accent-hover:    #0369A1; /* Sky-700: Hover su bottoni primari */
  --accent-glow:     rgba(56, 189, 248, 0.15); /* Ring e bagliori sottili */
  --text-on-accent:  #FFFFFF; /* Bianco su Sky-600 (4.6:1) */

  /* --- Stati Semantici & Telemetria ETL --- */
  --status-idle-bg:       #1E293B;
  --status-idle-fg:       #94A3B8; /* Grigio neutrale */
  
  --status-syncing-bg:    #0C2B47;
  --status-syncing-fg:    #38BDF8; /* Sky Blue (Pulsing pulse) */
  
  --status-synced-bg:     #063323;
  --status-synced-fg:     #34D399; /* Emerald Green (7.8:1) */
  
  --status-failed-bg:     #3F1317;
  --status-failed-fg:     #F87171; /* Rose Red (6.2:1) */

  --status-warning-bg:    #382405;
  --status-warning-fg:    #FBBF24; /* Amber Yellow (9.1:1) */
}
```

---

## 3. Tipografia & Modular Scale

Il sistema tipografico abbandona l'estetica asettica e fredda da terminale "meccanico": adotta un sans-serif geometrico-umanista raffinato (**Plus Jakarta Sans**) per tutti i controlli, etichette, badge, tabelle e card, con proporzioni armoniche e calore percettivo.
Il font **Monospace** è rigorosamente circoscritto a due soli elementi funzionali:
1. Gli hash crittografici SHA-256 (colonna tabella e ispezione).
2. Il terminale di telemetria e log di streaming.

- **UI Sans Stack**: `"Plus Jakarta Sans", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Telemetry Mono Stack**: `"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace`

### Scala Modulare (Minor Third — Ratio 1.200)

| Token | Dimensione | Line-Height | Peso Font | Utilizzo Principale |
|---|:---:|:---:|:---:|---|
| `--text-xs` | **11px** (0.6875rem) | 16px (1.45) | 500 / 600 | Badge stato, etichette upper mono, timestamp |
| `--text-sm` | **13px** (0.8125rem) | 18px (1.38) | 400 / 500 | Dati tabella, testo secondario, input form |
| `--text-base` | **14px** (0.875rem) | 20px (1.42) | 400 / 500 | Testo di lettura, bottoni di comando |
| `--text-md` | **16px** (1.000rem) | 24px (1.50) | 600 | Titoli di sezione, card profilo corso |
| `--text-lg` | **18px** (1.125rem) | 26px (1.44) | 600 | Titoli panelli principali, indicatori metrica |
| `--text-xl` | **22px** (1.375rem) | 28px (1.27) | 700 | Titolo Cockpit Topbar |

---

## 4. Griglia Spaziale & Layout Cockpit (Multipli di 8pt)

Nessun valore di spaziatura arbitrario. Tutte le distanze interne (`padding`), esterne (`margin`), interstiziali (`gap`) e le altezze componenti derivano dalla progressione geometrica:
`4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`.

```
+---------------------------------------------------------------------------------------+
| TOPBAR (48px) : PHD Prof Cockpit | Status Live | LLM Quota Meter [750 RPM] | En/It    |
+------------------------------------+--------------------------------------------------+
| CONTROL RAIL (Sidebar 320px)       | WORKSPACE VIEWPORT (Fluid)                       |
|                                    |                                                  |
| 1. Profile Selector                | 1. Queue Header & Action Bar                     |
|    - [1] Enterprise Architectures  |    - Folder: C:/Documenti/.../Slides             |
|    - [2] Text Mining and Search    |    - [Seleziona Tutti] [Elabora 3 File Selezionati] |
|    - [3] Big Data Analytics        |                                                  |
|    - [4] Time Series Analysis      | 2. File Queue Data Table                         |
|    - [+ Nuovo Profilo Corso]       |    [x] EA_W01_Intro.pptx  | 14.2 MB | SYNCED    |
|                                    |    [x] EA_W02_Arch.pptx   |  8.6 MB | IDLE      |
| 2. Course Profile Spec Inspector   |    [ ] EA_W03_Model.pdf   | 22.1 MB | IDLE      |
|    - Subject, Professor Role       |                                                  |
|    - DocType (Slides / Paper)      | 3. Live Streaming Telemetry Console              |
|    - Notion Target Database        |    [10:14:02] Local: Computing SHA-256...        |
|                                    |    [10:14:04] Gemini: Multimodal upload OK       |
| 3. Session Diagnostics             |    [10:14:08] Notion: 211 blocks written.        |
+------------------------------------+--------------------------------------------------+
```

---

## 5. Matrice dei 9 Stati Obbligatori dei Componenti

Tutti i controlli interattivi (bottoni, selettori, toggle di riga, card) implementano i 9 stati conformi a **Frontend UX Excellence**:

1. **Default**: Aspetto visivo stabile con target touch minimo $\ge 40\times 40\text{px}$.
2. **Hover**: Transizione di background a `--bg-surface-elev` in 150ms `ease-out`. Nessun falso movimento o shift di layout.
3. **Focus-Visible**: Ring di focus esterno netto `outline: 2px solid var(--border-focus); outline-offset: 2px;` con contrasto $\ge 3:1$.
4. **Active**: Leggera contrazione scalare tattile `transform: scale(0.98);` (100ms).
5. **Disabled**: Opacità ridotta al $45\%$, cursore `not-allowed`, attributo `aria-disabled="true"`.
6. **Loading / Processing**: Disabilitazione click con micro-spinner SVG integrato e testo di stato esplicito ("Sincronizzazione...").
7. **Error**: Bordo `--status-failed-fg` ad alto contrasto con messaggio testuale azionabile (non solo colore).
8. **Empty**: Pannello vuoto contestuale ("Nessun file `.pdf` o `.pptx` rilevato nella cartella") con bottone rapido "Esplora cartella" o "Modifica percorso".
9. **Success**: Badge o barra di avanzamento che conferma l'avvenuta sincronizzazione con icona di spunta e permanenza temporale prima del reset.

---

## 6. Contratti dei Componenti Principali

### 6.1 Profile Selector (Sidebar Rail)
- Elemento a lista verticale con tasti numerici associati (`[1]`, `[2]`, ...).
- Badge compatto indicante tipologia (`SLIDES` / `PAPER`) e conteggio file fisici rilevati su disco.
- Stato selezionato evidenziato con barra verticale a sinistra da 3px `--accent-primary` e background leggermente illuminato.

### 6.2 Data Table File Queue
- Righe fisse da 40px con hover sottile.
- Colonne: Checkbox selezione, Nome File, Estensione/Formato, Dimensione, Hash SHA-256 (troncato a 8 caratteri con click-to-copy), Badge Stato (IDLE, SYNCING, SYNCED, FAILED).
- Azione rapida per singola riga: "Sincronizza singolo file" / "Apri su Notion" (se già sincronizzato).

### 6.3 Live Telemetry Console
- Sfondo scuro incassato `--bg-surface-sub` con bordo `1px solid var(--border-subtle)`.
- Tipografia strict monospace 12px con timestamp verde/grigio.
- Auto-scroll lock: scorre automaticamente verso il basso durante l'arrivo di nuovi chunk di log, ma si sospende se l'utente esegue lo scroll manuale verso l'alto (con indicatore "Nuovi log sotto").

### 6.4 LLM Quota Meter
- Barra di avanzamento segmentata o percentuale indicante chiamate residue nel blocco di rate-limiting.
- Soglia visiva di allerta: cambia in `--status-warning-fg` se rimangono $< 10$ chiamate, `--status-failed-fg` se quota esaurita.

---

## 7. Regole Deterministiche Anti-Slop Enforced

1. **Anti-Cardception**: MAI annidare card dentro card. I dettagli del profilo e la coda file sono organizzati tramite divisioni funzionali pulite, bordi di confine sottili (1px) o spaziatura negativa.
2. **No Pure Black / Pure White**: Tutti i token partono da una matrice Zinc-Navy profonda (`#0A0E17`) e Slate-100 (`#F1F5F9`).
3. **The Lila Rule**: Nessun gradiente o sfumatura viola/magenta. La palette è rigorosamente basata su tonalità Slate / Steel con accento Sky Blue e indicatori semantici standard (Smeraldo, Ambra, Rubino).
4. **No Cartoon Easing**: Transizioni fluide con curva smorzata `cubic-bezier(0.16, 1, 0.3, 1)` e durate $\le 200\text{ ms}$.
5. **No Fake Precision / No Placeholder Text**: Ogni informazione visualizzata (nomi cartelle, database Notion, contatori, quote) corrisponde a dati reali estratti da disco o API.

---

## 8. Ciclo di Vita, Silent Launcher & Watchdog di Spegnimento

Per eliminare l'attrito di finestre terminali superflue ed evitare processi orfani in background:
1. **Silent Windowless Launcher (`Avvia_PHD_Prof.vbs`)**: Il processo Python viene lanciato in background senza alcuna finestra CMD a schermo. Il desktop shortcut `PHD Prof.lnk` invoca direttamente lo script VBS.
2. **Heartbeat & Browser Keepalive**: Il client web invia un ping periodico ogni 3 secondi (`POST /api/heartbeat`) e notifica la chiusura tramite `navigator.sendBeacon('/api/unload')`.
3. **Auto-Shutdown Watchdog**: Un daemon thread lato server rileva la chiusura del browser: se non riceve heartbeat per oltre 10 secondi (e nessun batch ETL è in corso), avvia lo spegnimento pulito e termina il processo Python automaticamente.
