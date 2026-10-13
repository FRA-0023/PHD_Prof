/**
 * PHD Prof Cockpit — Client-Side Controller (app.js)
 * High-performance Vanilla ES6 controller.
 * Manages reactive state, SSE telemetry streaming, keyboard shortcuts, and UI updates.
 * # ARCHITETTURA: Controller client-side zero-build disaccoppiato dal backend,
 *   con gestione deterministica degli stati asincroni (coda FIFO serializzata per grafi)
 *   e reattività istantanea su eventi SSE del dominio.
 */

(() => {
  // Global Application State
  const state = {
    profiles: [],
    activeProfile: null,
    files: [],
    selectedFiles: new Set(),
    isBatchRunning: false,
    quota: { remaining: 0, model: "gemini-2.5-flash" },
    autoscroll: true,
  };

  // DOM Elements
  const el = {
    profileList: document.getElementById("profile-list"),
    specSubject: document.getElementById("spec-subject"),
    specProf: document.getElementById("spec-prof"),
    specDocType: document.getElementById("spec-doctype"),
    specNotion: document.getElementById("spec-notion"),
    activeCourseTitle: document.getElementById("active-course-title"),
    activeCoursePath: document.getElementById("active-course-path"),
    activeCourseCount: document.getElementById("active-course-count"),
    heroStudyCard: document.getElementById("hero-study-card"),
    heroCourseTitle: document.getElementById("hero-course-title"),
    heroProfDesc: document.getElementById("hero-prof-desc"),
    heroDocTypeBadge: document.getElementById("hero-doctype-badge"),
    heroTargetBadge: document.getElementById("hero-target-badge"),
    heroQuotaStatus: document.getElementById("hero-quota-status"),
    heroProgressText: document.getElementById("hero-progress-text"),
    heroProgressBar: document.getElementById("hero-progress-bar"),
    activityDrawer: document.getElementById("activity-drawer"),
    drawerHeader: document.getElementById("drawer-header"),
    drawerTeaser: document.getElementById("drawer-teaser"),
    btnToggleDrawer: document.getElementById("btn-toggle-drawer"),
    fileTableBody: document.getElementById("file-table-body"),
    masterCheckbox: document.getElementById("master-checkbox"),
    emptyState: document.getElementById("empty-state"),
    btnSelectAll: document.getElementById("btn-select-all"),
    btnRefreshFiles: document.getElementById("btn-refresh-files"),
    btnRunBatch: document.getElementById("btn-run-batch"),
    btnStopBatch: document.getElementById("btn-stop-batch"),
    batchSelectedCount: document.getElementById("batch-selected-count"),
    selectGenerationMode: document.getElementById("select-generation-mode"),
    logPane: document.getElementById("log-pane"),
    autoscrollToggle: document.getElementById("autoscroll-toggle"),
    btnCopyLog: document.getElementById("btn-copy-log"),
    btnClearLog: document.getElementById("btn-clear-log"),
    quotaDisplay: document.getElementById("quota-display"),
    statusDot: document.getElementById("system-status-dot"),
    statusText: document.getElementById("system-status-text"),
    btnAddProfile: document.getElementById("btn-add-profile"),
    btnEditProfile: document.getElementById("btn-edit-profile"),
    profileModal: document.getElementById("profile-modal"),
    modalClose: document.getElementById("modal-close"),
    modalCancel: document.getElementById("modal-cancel"),
    profileForm: document.getElementById("profile-form"),
    formSubject: document.getElementById("form-subject"),
    formProf: document.getElementById("form-prof"),
    formDocType: document.getElementById("form-doctype"),
    formFolder: document.getElementById("form-folder"),
    formDbId: document.getElementById("form-db-id"),
    formCourseName: document.getElementById("form-course-name"),
    btnThemeToggle: document.getElementById("btn-theme-toggle"),
    themeToggleIcon: document.getElementById("theme-toggle-icon"),
    themeToggleLabel: document.getElementById("theme-toggle-label"),
  };

  // Utility helpers
  const escapeHtml = (str) => {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  // --- 1. Profiles & Navigation ---
  async function loadProfiles(preferredKey = null) {
    try {
      const res = await fetch("/api/profiles");
      if (!res.ok) {
        let errMsg = "Errore recupero profili";
        try {
          const errData = await res.json();
          if (errData && errData.detail) errMsg = errData.detail;
        } catch (_) {}
        throw new Error(errMsg);
      }
      state.profiles = await res.json();
      renderProfiles();

      if (state.profiles.length > 0) {
        const target = preferredKey
          ? state.profiles.find((p) => p.key === preferredKey)
          : state.profiles[0];
        selectProfile(target || state.profiles[0]);
      } else {
        appendLog("sys", "Nessun profilo corso configurato. Clicca su '+ Nuovo' per aggiungere il tuo primo corso.", "warn");
      }
    } catch (err) {
      appendLog("sys", `Impossibile caricare i profili: ${err.message}`, "error");
    }
  }

  function renderProfiles() {
    el.profileList.innerHTML = "";
    state.profiles.forEach((p, idx) => {
      const item = document.createElement("div");
      item.className = `profile-item ${state.activeProfile?.key === p.key ? "active" : ""}`;
      item.dataset.key = p.key;

      const badgeTypeClass = p.doc_type === "slides" ? "badge-slides" : "badge-paper";
      const filesBadge = p.folder_exists !== false
        ? `<span class="badge badge-count">${p.files_count || 0} file</span>`
        : `<span class="badge badge-warn" title="Cartella non trovata su disco: ${escapeHtml(p.folder_path)}">Cartella assente</span>`;

      item.innerHTML = `
        <div class="profile-info">
          <div class="profile-name">
            ${escapeHtml(p.subject)}
          </div>
          <div class="profile-meta">
            <span class="badge ${badgeTypeClass}">${escapeHtml(p.doc_type)}</span>
            ${filesBadge}
          </div>
        </div>
      `;

      item.addEventListener("click", () => selectProfile(p));
      el.profileList.appendChild(item);
    });
  }

  // # ARCHITETTURA: Calcolo metrico reattivo per l'avanzamento didattico del corso.
  // Aggiorna simultaneamente la progress bar, la percentuale e il contatore file.
  function updateHeroProgress() {
    const total = state.files.length;
    const synced = state.files.filter((f) => f.status === "SYNCED").length;
    const percent = total > 0 ? Math.round((synced / total) * 100) : 0;

    if (el.heroProgressBar) {
      el.heroProgressBar.style.width = `${percent}%`;
      const track = el.heroProgressBar.parentElement;
      if (track) {
        track.setAttribute("aria-valuenow", percent);
      }
    }
    if (el.heroProgressText) {
      el.heroProgressText.textContent = `${percent}% completato (${synced}/${total})`;
    }
    if (el.activeCourseCount) {
      el.activeCourseCount.textContent = `${total} lezioni`;
    }
  }

  function selectProfile(profile) {
    state.activeProfile = profile;

    // Highlight sidebar active item
    document.querySelectorAll(".profile-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.key === profile.key);
    });

    // Update Course Spec Inspector
    if (el.specSubject) el.specSubject.textContent = profile.subject || "--";
    if (el.specProf) el.specProf.textContent = profile.professor_type || "--";
    if (el.specDocType) el.specDocType.textContent = (profile.doc_type || "SLIDES").toUpperCase();
    if (el.specNotion) el.specNotion.textContent = `${profile.target?.course_name || ""} > ${profile.target?.database_title || "Notes"}`;

    // # ARCHITETTURA: Aggiornamento pulito della testata corso integrata (no banner giganti)
    if (el.activeCourseTitle) {
      el.activeCourseTitle.textContent = profile.subject || "Seleziona un corso";
    }
    if (el.heroProfDesc) {
      el.heroProfDesc.textContent = profile.professor_type || "Ambiente di studio per sintesi accademiche rigorose e mappe concettuali";
    }
    if (el.activeCoursePath) {
      el.activeCoursePath.textContent = profile.folder_path || "--";
      el.activeCoursePath.title = profile.folder_path || "";
    }

    loadFiles(profile.key);
  }

  // --- 2. Files Queue ---
  async function loadFiles(profileKey) {
    el.fileTableBody.innerHTML = `
      <div class="syllabus-loading">
        Scansione materiali didattici in corso...
      </div>
    `;
    el.emptyState.style.display = "none";

    try {
      const res = await fetch(`/api/profiles/${encodeURIComponent(profileKey)}/files`);
      if (!res.ok) throw new Error("Errore recupero file");
      const data = await res.json();
      state.files = data.files || [];
      state.selectedFiles.clear();

      if (data.error) {
        appendLog(
          "sys",
          `Cartella materiali non accessibile per '${state.activeProfile?.subject || profileKey}': ${data.error}. Usa 'Modifica' per aggiornare il percorso.`,
          "warn"
        );
      }

      // By default, select files that are NOT yet synced
      state.files.forEach((f) => {
        if (f.status !== "SYNCED") {
          state.selectedFiles.add(f.name);
        }
      });

      renderFiles();
      updateHeroProgress();
    } catch (err) {
      appendLog("sys", `Errore scansione file per ${profileKey}: ${err.message}`, "error");
      el.fileTableBody.innerHTML = `
        <div class="syllabus-error">
          Errore caricamento cartella: ${escapeHtml(err.message)}
        </div>
      `;
      updateHeroProgress();
    }
  }

  // --- 2.1 Sequential Graph Append Queue ---
  // # ARCHITETTURA: Coda FIFO serializzata per l'azione on-demand '+ Grafo'.
  // Previene sovrapposizioni e timeout generati da dispatch multipli
  // concorrenti a LLM e Notion API, garantendo feedback visivo reattivo 'In coda (N)'.
  const graphQueue = {
    items: [],
    activeHash: null,

    isQueued(hash) {
      return this.items.some((item) => item.file_hash === hash);
    },

    isActive(hash) {
      return this.activeHash === hash;
    },

    enqueue(file) {
      if (state.isBatchRunning) {
        appendLog("sys", "Impossibile avviare Append Grafo mentre è attivo un batch di sincronizzazione.", "warn");
        return;
      }

      if (this.isActive(file.file_hash)) {
        appendLog("sys", `Append Grafo già in esecuzione per ${file.name}.`, "warn");
        return;
      }

      if (this.isQueued(file.file_hash)) {
        appendLog("sys", `Il file ${file.name} è già presente nella coda di attesa.`, "warn");
        return;
      }

      this.items.push(file);
      const position = this.items.length;
      appendLog("sys", `File ${file.name} aggiunto alla coda Append Grafo (in attesa: ${position}).`);
      this.updateUI();

      if (!this.activeHash) {
        this.processNext();
      }
    },

    updateUI() {
      document.querySelectorAll(".btn-append-graph").forEach((btn) => {
        const hash = btn.dataset.hash;
        if (this.isActive(hash)) {
          btn.disabled = true;
          btn.innerHTML = `<span class="status-dot syncing" style="width: 5px; height: 5px;"></span> Grafo...`;
          btn.style.color = "#7c3aed";
          btn.style.borderColor = "rgba(124, 58, 237, 0.4)";
        } else if (this.isQueued(hash)) {
          const index = this.items.findIndex((item) => item.file_hash === hash) + 1;
          btn.disabled = true;
          btn.innerHTML = `<span class="status-dot" style="width: 5px; height: 5px; background-color: var(--status-warning-fg);"></span> Coda (${index})`;
          btn.style.color = "var(--status-warning-fg)";
          btn.style.borderColor = "rgba(251, 191, 36, 0.4)";
        }
      });
    },

    async processNext() {
      if (this.items.length === 0) {
        this.activeHash = null;
        this.updateUI();
        return;
      }

      const file = this.items.shift();
      this.activeHash = file.file_hash;
      this.updateUI();

      appendLog("sys", `Append Grafo concettuale avviato per ${file.name}...`);

      try {
        const res = await fetch(`/api/documents/${file.file_hash}/append-graph`, {
          method: "POST",
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Errore durante l'append del grafo");
        }
        appendLog("notion", `Grafo aggiunto con successo alla pagina Notion per ${file.name} (${data.blocks_count} blocchi)!`);

        const btn = document.querySelector(`.btn-append-graph[data-hash="${file.file_hash}"]`);
        if (btn) {
          btn.innerHTML = `✓ Grafo`;
          btn.style.color = "var(--status-synced-fg)";
          btn.style.borderColor = "rgba(5, 150, 105, 0.4)";
          setTimeout(() => {
            btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg> + Grafo`;
            btn.disabled = false;
            btn.style.color = "#7c3aed";
            btn.style.borderColor = "rgba(124, 58, 237, 0.25)";
          }, 3000);
        }
      } catch (err) {
        appendLog("sys", `Fallito append grafo per ${file.name}: ${err.message}`, "error");
        const btn = document.querySelector(`.btn-append-graph[data-hash="${file.file_hash}"]`);
        if (btn) {
          btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg> + Grafo`;
          btn.disabled = false;
          btn.style.color = "#7c3aed";
          btn.style.borderColor = "rgba(124, 58, 237, 0.25)";
        }
      } finally {
        this.activeHash = null;
        setTimeout(() => this.processNext(), 400);
      }
    }
  };

  function renderFiles() {
    el.fileTableBody.innerHTML = "";

    if (state.files.length === 0) {
      el.emptyState.style.display = "flex";
      updateBatchButton();
      updateHeroProgress();
      return;
    }

    el.emptyState.style.display = "none";

    state.files.forEach((file) => {
      // # ARCHITETTURA: Creazione della card a isola Syllabus con elevazione 3D e hover-lift
      const card = document.createElement("div");
      card.id = `row-${file.name.replace(/[^a-zA-Z0-9_-]/g, "_")}`;

      const isChecked = state.selectedFiles.has(file.name);
      card.className = `syllabus-card-row ${isChecked ? "selected" : ""}`;

      const statusClass = (file.status || "idle").toLowerCase();
      const cleanExt = (file.extension || "").replace(".", "").toUpperCase();

      let appendGraphHtml = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg> + Grafo`;
      let appendGraphDisabled = false;

      if (graphQueue.isActive(file.file_hash)) {
        appendGraphHtml = `<span class="status-dot syncing" style="width: 5px; height: 5px;"></span> Grafo...`;
        appendGraphDisabled = true;
      } else if (graphQueue.isQueued(file.file_hash)) {
        const pos = graphQueue.items.findIndex((item) => item.file_hash === file.file_hash) + 1;
        appendGraphHtml = `<span class="status-dot" style="width: 5px; height: 5px; background-color: var(--status-warning-fg);"></span> Coda (${pos})`;
        appendGraphDisabled = true;
      }

      let statusLabel = "Da sincronizzare";
      if (file.status === "SYNCED") statusLabel = "Sincronizzato";
      else if (file.status === "SYNCING") statusLabel = "In corso...";
      else if (file.status === "FAILED") statusLabel = "Errore";

      card.innerHTML = `
        <div class="col-check">
          <input type="checkbox" class="file-checkbox" data-filename="${escapeHtml(file.name)}" ${isChecked ? "checked" : ""}>
        </div>
        <div class="col-name file-name-cell" title="File: ${escapeHtml(file.name)}">
          <span class="file-badge-format ${cleanExt.toLowerCase()}">${escapeHtml(cleanExt)}</span>
          <span class="file-title-text">${escapeHtml(file.name)}</span>
        </div>
        <div class="col-type"><span class="badge badge-format">${escapeHtml(file.extension)}</span></div>
        <div class="col-size">${escapeHtml(file.size_formatted)}</div>
        <div class="col-status">
          <span class="status-badge ${statusClass}">
            <span class="status-dot ${statusClass === 'syncing' ? 'syncing' : ''}"></span>
            ${escapeHtml(statusLabel)}
          </span>
        </div>
        <div class="col-actions">
          ${
            file.status === "SYNCED" && file.page_id
              ? `<div class="action-buttons-group">
                  <a href="/api/study-schema/${file.file_hash}/opml" download="${encodeURIComponent(file.name.replace(/\.[^/.]+$/, ""))}.opml" class="btn-action btn-opml" title="Scarica Mappa Mentale OPML (EdrawMind / XMind / MindNode)">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Mappa OPML
                  </a>
                  <button class="btn-action btn-append-graph" data-hash="${escapeHtml(file.file_hash)}" data-filename="${escapeHtml(file.name)}" title="Aggiungi schema concettuale Mermaid alla pagina Notion" ${appendGraphDisabled ? "disabled" : ""}>
                    ${appendGraphHtml}
                  </button>
                  <a href="https://www.notion.so/${file.page_id.replace(/-/g, '')}" target="_blank" rel="noopener noreferrer" class="btn-action btn-notion" title="Apri appunti su Notion">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    Notion
                  </a>
                  <button class="btn-action btn-single-sync" data-filename="${escapeHtml(file.name)}" title="Riprocessa questo documento">
                    Sync
                  </button>
                </div>`
              : `<div class="action-buttons-group">
                  <button class="btn-action btn-primary-sync btn-single-sync" data-filename="${escapeHtml(file.name)}" title="Sincronizza ora questa lezione su Notion">
                    Sincronizza
                  </button>
                </div>`
          }
        </div>
      `;

      // Checkbox listener
      const cb = card.querySelector(".file-checkbox");
      if (cb) {
        cb.addEventListener("change", (e) => {
          if (e.target.checked) {
            state.selectedFiles.add(file.name);
            card.classList.add("selected");
          } else {
            state.selectedFiles.delete(file.name);
            card.classList.remove("selected");
          }
          updateBatchButton();
        });
      }

      // Append graph button listener
      const btnAppendGraph = card.querySelector(".btn-append-graph");
      if (btnAppendGraph) {
        btnAppendGraph.addEventListener("click", () => {
          graphQueue.enqueue(file);
        });
      }

      // Single sync button listener
      const btnSync = card.querySelector(".btn-single-sync");
      if (btnSync) {
        btnSync.addEventListener("click", () => {
          startBatch([file.name]);
        });
      }

      el.fileTableBody.appendChild(card);
    });

    updateBatchButton();
    updateHeroProgress();
  }

  function updateBatchButton() {
    const count = state.selectedFiles.size;
    if (el.batchSelectedCount) el.batchSelectedCount.textContent = count;
    if (el.btnRunBatch) el.btnRunBatch.disabled = count === 0 || state.isBatchRunning;
    if (el.masterCheckbox) el.masterCheckbox.checked = count === state.files.length && state.files.length > 0;
  }

  // --- 3. Batch ETL Execution ---
  async function startBatch(customFileList = null) {
    if (state.isBatchRunning || !state.activeProfile) return;

    if (graphQueue.activeHash || graphQueue.items.length > 0) {
      appendLog("sys", "Attendere il completamento della coda Append Grafo prima di avviare la sincronizzazione.", "warn");
      return;
    }

    const filesToRun = customFileList || Array.from(state.selectedFiles);
    if (filesToRun.length === 0) {
      appendLog("sys", "Nessun file selezionato per l'elaborazione didattica.", "warn");
      return;
    }

    try {
      const mode = el.selectGenerationMode ? el.selectGenerationMode.value : "both";
      const res = await fetch("/api/batch/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile_key: state.activeProfile.key,
          file_names: filesToRun,
          mode: mode,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Impossibile avviare la sincronizzazione");
      }

      setBatchRunningState(true);
    } catch (err) {
      appendLog("sys", `Errore avvio sincronizzazione: ${err.message}`, "error");
    }
  }

  async function stopBatch() {
    try {
      const res = await fetch("/api/batch/stop", { method: "POST" });
      if (res.ok) {
        appendLog("sys", "Arresto richiesto. Il processo si fermerà al termine del file corrente.", "warn");
      }
    } catch (err) {
      appendLog("sys", `Errore richiesta arresto: ${err.message}`, "error");
    }
  }

  function setBatchRunningState(running) {
    state.isBatchRunning = running;
    if (el.btnRunBatch) el.btnRunBatch.disabled = running || state.selectedFiles.size === 0;
    if (el.btnStopBatch) el.btnStopBatch.style.display = running ? "inline-flex" : "none";
    if (el.statusDot) el.statusDot.classList.toggle("syncing", running);
    if (el.statusText) el.statusText.textContent = running ? "Sincronizzazione in corso..." : "Notion Pronto";
  }

  // --- 4. Real-time Telemetry & SSE Streaming ---
  function initEventSource() {
    const sse = new EventSource("/api/events");

    sse.addEventListener("log", (evt) => {
      try {
        const item = JSON.parse(evt.data);
        const data = item.data;
        appendLog(data.source, data.message, data.level, item.timestamp);
      } catch (e) {
        console.error("SSE parse error", e);
      }
    });

    sse.addEventListener("file_progress", (evt) => {
      try {
        const item = JSON.parse(evt.data);
        const data = item.data;
        updateFileRowStatus(data.file_name, data.status);
      } catch (e) {
        console.error("file_progress parse error", e);
      }
    });

    sse.addEventListener("quota_update", (evt) => {
      try {
        const item = JSON.parse(evt.data);
        updateQuotaDisplay(item.data.remaining);
      } catch (e) {
        console.error("quota_update parse error", e);
      }
    });

    sse.addEventListener("batch_state", (evt) => {
      try {
        const item = JSON.parse(evt.data);
        const data = item.data;
        setBatchRunningState(data.running);
        if (!data.running) {
          // Refresh file table on batch completion
          if (state.activeProfile) {
            loadFiles(state.activeProfile.key);
          }
          fetchQuota();
        }
      } catch (e) {
        console.error("batch_state parse error", e);
      }
    });

    sse.onerror = () => {
      if (el.statusDot) el.statusDot.style.backgroundColor = "var(--status-warning-fg)";
      if (el.statusText) el.statusText.textContent = "Riconnessione...";
    };

    sse.onopen = () => {
      if (el.statusDot) el.statusDot.style.backgroundColor = "var(--status-synced-fg)";
      if (el.statusText) el.statusText.textContent = "Notion Pronto";
    };
  }

  function appendLog(source, message, level = "info", timestamp = null) {
    const time = timestamp || new Date().toTimeString().split(" ")[0];
    const line = document.createElement("div");
    line.className = "log-line";

    const cleanSrc = (source || "sys").toLowerCase();
    const isError = level === "error";
    const isWarn = level === "warn";

    line.innerHTML = `
      <span class="log-time">[${time}]</span>
      <span class="log-src ${cleanSrc}">${cleanSrc}</span>
      <span class="log-text ${isError ? 'error' : ''} ${isWarn ? 'warn' : ''}">${escapeHtml(message)}</span>
    `;

    el.logPane.appendChild(line);

    if (state.autoscroll) {
      el.logPane.scrollTop = el.logPane.scrollHeight;
    }

    // # ARCHITETTURA: Aggiornamento contestuale del teaser preview nello Study Activity Drawer
    if (el.drawerTeaser) {
      el.drawerTeaser.textContent = message;
      el.drawerTeaser.title = message;
    }
  }

  function updateFileRowStatus(fileName, newStatus) {
    const safeId = `row-${fileName.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
    const row = document.getElementById(safeId);
    if (!row) return;

    // # ARCHITETTURA: Sincronizzazione stato in-memory per ricalcolo istantaneo del progresso
    const fileObj = state.files.find((f) => f.name === fileName);
    if (fileObj) {
      fileObj.status = newStatus;
      updateHeroProgress();
    }

    const badge = row.querySelector(".status-badge");
    if (badge) {
      const lower = (newStatus || "idle").toLowerCase();
      badge.className = `status-badge ${lower}`;

      let label = "Da sincronizzare";
      if (newStatus === "SYNCED") label = "Sincronizzato";
      else if (newStatus === "SYNCING") label = "In corso...";
      else if (newStatus === "FAILED") label = "Errore";

      badge.innerHTML = `
        <span class="status-dot ${lower === 'syncing' ? 'syncing' : ''}"></span>
        ${escapeHtml(label)}
      `;
    }
  }

  async function fetchQuota() {
    try {
      const res = await fetch("/api/quota");
      if (res.ok) {
        const data = await res.json();
        state.quota = data;
        updateQuotaDisplay(data.remaining);
      }
    } catch (err) {
      console.warn("Quota fetch failed", err);
    }
  }

  function updateQuotaDisplay(remaining) {
    if (el.quotaDisplay) {
      el.quotaDisplay.textContent = `${remaining} RPD`;
      el.quotaDisplay.classList.remove("warning", "danger");

      if (remaining <= 0) {
        el.quotaDisplay.classList.add("danger");
      } else if (remaining <= 5) {
        el.quotaDisplay.classList.add("warning");
      }
    }
  }

  // --- 5. Modal: Create & Edit Profile ---
  function openProfileModal(profileToEdit = null) {
    if (profileToEdit) {
      document.getElementById("modal-title").textContent = "Modifica Corso";
      el.formSubject.value = profileToEdit.subject;
      el.formProf.value = profileToEdit.professor_type || "";
      el.formDocType.value = profileToEdit.doc_type || "slides";
      el.formFolder.value = profileToEdit.folder_path;
      el.formDbId.value = profileToEdit.target?.database_id || "";
      el.formCourseName.value = profileToEdit.target?.course_name || profileToEdit.subject;
    } else {
      document.getElementById("modal-title").textContent = "Nuovo Corso";
      el.profileForm.reset();
      el.formDocType.value = "slides";
    }
    el.profileModal.classList.add("open");
    el.formSubject.focus();
  }

  function closeProfileModal() {
    el.profileModal.classList.remove("open");
  }

  async function saveProfileForm(e) {
    e.preventDefault();
    const payload = {
      subject: el.formSubject.value.trim(),
      professor_type: el.formProf.value.trim(),
      doc_type: el.formDocType.value,
      folder_path: el.formFolder.value.trim(),
      target: {
        database_id: el.formDbId.value.trim(),
        course_name: el.formCourseName.value.trim() || el.formSubject.value.trim(),
        database_title: "Notes",
      },
    };

    try {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Errore nel salvataggio");
      }

      const resData = await res.json();
      closeProfileModal();
      await loadProfiles(resData.key);
      appendLog("sys", `Profilo salvato: ${payload.subject}`);
    } catch (err) {
      alert(`Errore: ${err.message}`);
    }
  }

  // --- 6. Event Listeners & Keyboard Shortcuts ---
  function setupListeners() {
    // Master checkbox
    el.masterCheckbox.addEventListener("change", (e) => {
      const checked = e.target.checked;
      state.selectedFiles.clear();
      if (checked) {
        state.files.forEach((f) => state.selectedFiles.add(f.name));
      }
      renderFiles();
    });

    // Select all button toggle
    el.btnSelectAll.addEventListener("click", () => {
      if (state.selectedFiles.size === state.files.length) {
        state.selectedFiles.clear();
      } else {
        state.files.forEach((f) => state.selectedFiles.add(f.name));
      }
      renderFiles();
    });

    el.btnRefreshFiles.addEventListener("click", () => {
      if (state.activeProfile) loadFiles(state.activeProfile.key);
    });

    el.btnRunBatch.addEventListener("click", () => startBatch());
    el.btnStopBatch.addEventListener("click", () => stopBatch());

    // Autoscroll toggle
    el.autoscrollToggle.addEventListener("change", (e) => {
      state.autoscroll = e.target.checked;
    });

    // Clear logs
    el.btnClearLog.addEventListener("click", () => {
      el.logPane.innerHTML = "";
    });

    // Copy logs
    el.btnCopyLog.addEventListener("click", () => {
      const lines = Array.from(el.logPane.querySelectorAll(".log-line"))
        .map((l) => l.innerText)
        .join("\n");
      navigator.clipboard.writeText(lines);
      appendLog("sys", "Registro attività copiato negli appunti.");
    });

    // Profile Modal
    el.btnAddProfile.addEventListener("click", () => openProfileModal(null));
    el.btnEditProfile.addEventListener("click", () => openProfileModal(state.activeProfile));
    el.modalClose.addEventListener("click", closeProfileModal);
    el.modalCancel.addEventListener("click", closeProfileModal);
    el.profileForm.addEventListener("submit", saveProfileForm);

    // Theme Toggle Control
    if (el.btnThemeToggle) {
      el.btnThemeToggle.addEventListener("click", toggleTheme);
    }

    // Study Activity Drawer Collapsible Logic
    // # ARCHITETTURA: Transizione fluida e collassabilità a 38px dello Study Activity Drawer
    function toggleDrawer() {
      if (el.activityDrawer) {
        el.activityDrawer.classList.toggle("collapsed");
      }
    }

    if (el.drawerHeader) {
      el.drawerHeader.addEventListener("click", (e) => {
        if (e.target.closest("button") || e.target.closest("input") || e.target.closest("label")) {
          return;
        }
        toggleDrawer();
      });
    }

    if (el.btnToggleDrawer) {
      el.btnToggleDrawer.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleDrawer();
      });
    }

    // Segmented Output Mode Selector
    document.querySelectorAll(".mode-segment-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".mode-segment-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        if (el.selectGenerationMode) {
          el.selectGenerationMode.value = btn.dataset.mode;
        }
      });
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", (e) => {
      // If modal open, Esc closes it
      if (el.profileModal.classList.contains("open")) {
        if (e.key === "Escape") closeProfileModal();
        return;
      }

      // Hotkeys: 1-9 to select profiles
      if (!e.ctrlKey && !e.altKey && !e.metaKey && e.key >= "1" && e.key <= "9") {
        const idx = parseInt(e.key, 10) - 1;
        if (idx < state.profiles.length) {
          selectProfile(state.profiles[idx]);
        }
      }

      // Alt + T to toggle theme (Dark <-> Light)
      if (e.altKey && (e.key === "t" || e.key === "T")) {
        e.preventDefault();
        toggleTheme();
      }

      // Ctrl + Enter to run batch
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        startBatch();
      }

      // Escape to stop batch if running
      if (e.key === "Escape" && state.isBatchRunning) {
        stopBatch();
      }
    });
  }

  // --- 7. Watchdog Heartbeat ---
  function initHeartbeat() {
    // Send immediate heartbeat on startup
    fetch("/api/heartbeat", { method: "POST" }).catch(() => {});

    // Periodic heartbeat every 3 seconds to keep backend alive
    setInterval(() => {
      fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
    }, 3000);

    // Refresh heartbeat immediately when switching back to tab
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        fetch("/api/heartbeat", { method: "POST" }).catch(() => {});
      }
    });

    // Notify backend when browser is closing or navigating away
    window.addEventListener("beforeunload", () => {
      try {
        if (navigator.sendBeacon) {
          navigator.sendBeacon("/api/unload");
        } else {
          fetch("/api/unload", { method: "POST", keepalive: true }).catch(() => {});
        }
      } catch (e) {}
    });
  }

  // --- 8. Theme Management (Dark / Light) ---
  // # ARCHITETTURA: Gestione deterministica del tema con default Light (richiesta utente)
  // e memorizzazione in localStorage per latenza zero.
  const THEME_STORAGE_KEY = "phd_cockpit_theme";

  const SUN_ICON_SVG = `
    <circle cx="12" cy="12" r="5"></circle>
    <line x1="12" y1="1" x2="12" y2="3"></line>
    <line x1="12" y1="21" x2="12" y2="23"></line>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
    <line x1="1" y1="12" x2="3" y2="12"></line>
    <line x1="21" y1="12" x2="23" y2="12"></line>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
  `;

  const MOON_ICON_SVG = `
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
  `;

  function getSystemPreferredTheme() {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  function getActiveTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function applyTheme(theme, save = true) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      if (el.btnThemeToggle) {
        el.btnThemeToggle.title = "Passa a tema scuro (Alt+T)";
        el.btnThemeToggle.setAttribute("aria-label", "Passa a tema scuro");
      }
      if (el.themeToggleIcon) {
        el.themeToggleIcon.innerHTML = MOON_ICON_SVG;
      }
      if (el.themeToggleLabel) {
        el.themeToggleLabel.textContent = "Scuro";
      }
    } else {
      document.documentElement.removeAttribute("data-theme");
      if (el.btnThemeToggle) {
        el.btnThemeToggle.title = "Passa a tema chiaro (Alt+T)";
        el.btnThemeToggle.setAttribute("aria-label", "Passa a tema chiaro");
      }
      if (el.themeToggleIcon) {
        el.themeToggleIcon.innerHTML = SUN_ICON_SVG;
      }
      if (el.themeToggleLabel) {
        el.themeToggleLabel.textContent = "Chiaro";
      }
    }

    if (save) {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
      } catch (err) {
        // Fallback per ambienti con storage disabilitato
      }
    }
  }

  function toggleTheme() {
    const current = getActiveTheme();
    const nextTheme = current === "light" ? "dark" : "light";
    applyTheme(nextTheme, true);
  }

  function initTheme() {
    let savedTheme = null;
    try {
      savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    } catch (err) {}

    const initialTheme = savedTheme || "light"; // Default to Light theme as requested
    applyTheme(initialTheme, false);

    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        try {
          if (!localStorage.getItem(THEME_STORAGE_KEY)) {
            applyTheme(e.matches ? "dark" : "light", false);
          }
        } catch (err) {}
      });
    }
  }

  // Initialization
  async function init() {
    initTheme();
    setupListeners();
    initHeartbeat();
    initEventSource();
    await fetchQuota();
    await loadProfiles();
  }

  init();
})();
