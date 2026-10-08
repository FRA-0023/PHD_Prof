/**
 * PHD Prof Cockpit — Client-Side Controller (app.js)
 * High-performance Vanilla ES6 controller.
 * Manages reactive state, SSE telemetry streaming, keyboard shortcuts, and UI updates.
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
      if (!res.ok) throw new Error("Errore recupero profili");
      state.profiles = await res.json();
      renderProfiles();

      if (state.profiles.length > 0) {
        const target = preferredKey
          ? state.profiles.find((p) => p.key === preferredKey)
          : state.profiles[0];
        selectProfile(target || state.profiles[0]);
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

      item.innerHTML = `
        <div class="profile-info">
          <div class="profile-name">
            <span style="font-family: var(--font-mono); color: var(--text-tertiary); margin-right: 4px;">[${idx + 1}]</span>
            ${escapeHtml(p.subject)}
          </div>
          <div class="profile-meta">
            <span class="badge ${badgeTypeClass}">${escapeHtml(p.doc_type)}</span>
            <span class="badge badge-count">${p.files_count || 0} file</span>
          </div>
        </div>
      `;

      item.addEventListener("click", () => selectProfile(p));
      el.profileList.appendChild(item);
    });
  }

  function selectProfile(profile) {
    state.activeProfile = profile;

    // Highlight sidebar active item
    document.querySelectorAll(".profile-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.key === profile.key);
    });

    // Update Course Spec Inspector
    el.specSubject.textContent = profile.subject;
    el.specProf.textContent = profile.professor_type || "--";
    el.specDocType.textContent = (profile.doc_type || "SLIDES").toUpperCase();
    el.specNotion.textContent = `${profile.target?.course_name || ""} > ${profile.target?.database_title || "Notes"}`;

    // Update Toolbar Header
    el.activeCourseTitle.textContent = profile.subject;
    el.activeCoursePath.textContent = profile.folder_path;
    el.activeCoursePath.title = profile.folder_path;

    loadFiles(profile.key);
  }

  // --- 2. Files Queue ---
  async function loadFiles(profileKey) {
    el.fileTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 24px; color: var(--text-tertiary);">
          Scansione file su disco in corso...
        </td>
      </tr>
    `;
    el.emptyState.style.display = "none";

    try {
      const res = await fetch(`/api/profiles/${encodeURIComponent(profileKey)}/files`);
      if (!res.ok) throw new Error("Errore recupero file");
      const data = await res.json();
      state.files = data.files || [];
      state.selectedFiles.clear();

      // By default, select files that are NOT yet synced
      state.files.forEach((f) => {
        if (f.status !== "SYNCED") {
          state.selectedFiles.add(f.name);
        }
      });

      renderFiles();
    } catch (err) {
      appendLog("sys", `Errore scansione file per ${profileKey}: ${err.message}`, "error");
      el.fileTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 24px; color: var(--status-failed-fg);">
            Errore caricamento cartella: ${escapeHtml(err.message)}
          </td>
        </tr>
      `;
    }
  }

  function renderFiles() {
    el.fileTableBody.innerHTML = "";

    if (state.files.length === 0) {
      el.emptyState.style.display = "block";
      updateBatchButton();
      return;
    }

    el.emptyState.style.display = "none";

    state.files.forEach((file) => {
      const tr = document.createElement("tr");
      tr.id = `row-${file.name.replace(/[^a-zA-Z0-9_-]/g, "_")}`;

      const isChecked = state.selectedFiles.has(file.name);
      const shortHash = file.file_hash ? file.file_hash.substring(0, 8) : "--";
      const statusClass = (file.status || "idle").toLowerCase();

      tr.innerHTML = `
        <td>
          <input type="checkbox" class="file-checkbox" data-filename="${escapeHtml(file.name)}" ${isChecked ? "checked" : ""}>
        </td>
        <td>
          <div class="file-name-cell">
            <span class="file-icon">${escapeHtml(file.extension.replace(".", "").toUpperCase())}</span>
            <span>${escapeHtml(file.name)}</span>
          </div>
        </td>
        <td><span class="badge badge-count">${escapeHtml(file.extension)}</span></td>
        <td>${escapeHtml(file.size_formatted)}</td>
        <td>
          <span class="hash-cell" title="Clicca per copiare l'hash SHA-256 completo: ${escapeHtml(file.file_hash)}">
            ${shortHash}
          </span>
        </td>
        <td>
          <span class="status-badge ${statusClass}">
            <span class="pulse-dot ${statusClass === 'syncing' ? 'syncing' : ''}" style="width: 5px; height: 5px;"></span>
            ${escapeHtml(file.status)}
          </span>
        </td>
        <td style="text-align: right;">
          ${
            file.status === "SYNCED" && file.page_id
              ? `<div style="display: flex; gap: 6px; justify-content: flex-end; align-items: center;">
                  <a href="/api/study-schema/${file.file_hash}/opml" download="${encodeURIComponent(file.name.replace(/\.[^/.]+$/, ""))}.opml" class="btn-secondary" title="Scarica Mappa Mentale OPML (EdrawMind / XMind)" style="padding: 2px 7px; font-size: 10px; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; color: #10b981; border-color: rgba(16, 185, 129, 0.3);">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    OPML
                  </a>
                  <a href="https://www.notion.so/${file.page_id.replace(/-/g, '')}" target="_blank" rel="noopener noreferrer" class="btn-secondary btn-notion-link" title="Apri nota su Notion" style="padding: 2px 8px; font-size: 11px; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; color: var(--accent-primary);">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    Notion
                  </a>
                  <button class="btn-secondary btn-single-sync" data-filename="${escapeHtml(file.name)}" title="Riprocessa file" style="padding: 2px 6px; font-size: 10px;">
                    Sync
                  </button>
                </div>`
              : `<button class="btn-secondary btn-single-sync" data-filename="${escapeHtml(file.name)}" style="padding: 2px 6px; font-size: 10px;">
                  Sync
                </button>`
          }
        </td>
      `;

      // Copy hash on click
      const hashSpan = tr.querySelector(".hash-cell");
      hashSpan.addEventListener("click", () => {
        if (file.file_hash) {
          navigator.clipboard.writeText(file.file_hash);
          appendLog("local", `SHA-256 copiato negli appunti: ${file.file_hash}`);
        }
      });

      // Checkbox listener
      const cb = tr.querySelector(".file-checkbox");
      cb.addEventListener("change", (e) => {
        if (e.target.checked) {
          state.selectedFiles.add(file.name);
        } else {
          state.selectedFiles.delete(file.name);
        }
        updateBatchButton();
      });

      // Single sync button listener
      const btnSync = tr.querySelector(".btn-single-sync");
      btnSync.addEventListener("click", () => {
        startBatch([file.name]);
      });

      el.fileTableBody.appendChild(tr);
    });

    updateBatchButton();
  }

  function updateBatchButton() {
    const count = state.selectedFiles.size;
    el.batchSelectedCount.textContent = count;
    el.btnRunBatch.disabled = count === 0 || state.isBatchRunning;
    el.masterCheckbox.checked = count === state.files.length && state.files.length > 0;
  }

  // --- 3. Batch ETL Execution ---
  async function startBatch(customFileList = null) {
    if (state.isBatchRunning || !state.activeProfile) return;

    const filesToRun = customFileList || Array.from(state.selectedFiles);
    if (filesToRun.length === 0) {
      appendLog("sys", "Nessun file selezionato per l'elaborazione.", "warn");
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
        throw new Error(errData.detail || "Impossibile avviare il batch");
      }

      setBatchRunningState(true);
    } catch (err) {
      appendLog("sys", `Errore avvio batch: ${err.message}`, "error");
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
    el.btnRunBatch.disabled = running || state.selectedFiles.size === 0;
    el.btnStopBatch.style.display = running ? "inline-flex" : "none";
    el.statusDot.classList.toggle("syncing", running);
    el.statusText.textContent = running ? "ETL IN CORSO" : "ONLINE";
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
      el.statusDot.style.backgroundColor = "var(--status-warning-fg)";
      el.statusText.textContent = "RICONNESSIONE SSE...";
    };

    sse.onopen = () => {
      el.statusDot.style.backgroundColor = "var(--status-synced-fg)";
      el.statusText.textContent = "ONLINE";
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
  }

  function updateFileRowStatus(fileName, newStatus) {
    const safeId = `row-${fileName.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
    const row = document.getElementById(safeId);
    if (!row) return;

    const badge = row.querySelector(".status-badge");
    if (badge) {
      const lower = (newStatus || "idle").toLowerCase();
      badge.className = `status-badge ${lower}`;
      badge.innerHTML = `
        <span class="pulse-dot ${lower === 'syncing' ? 'syncing' : ''}" style="width: 5px; height: 5px;"></span>
        ${escapeHtml(newStatus)}
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
    el.quotaDisplay.textContent = `${remaining} RPD`;
    el.quotaDisplay.classList.remove("warning", "danger");

    if (remaining <= 0) {
      el.quotaDisplay.classList.add("danger");
    } else if (remaining <= 5) {
      el.quotaDisplay.classList.add("warning");
    }
  }

  // --- 5. Modal: Create & Edit Profile ---
  function openProfileModal(profileToEdit = null) {
    if (profileToEdit) {
      document.getElementById("modal-title").textContent = "Modifica Profilo Corso";
      el.formSubject.value = profileToEdit.subject;
      el.formProf.value = profileToEdit.professor_type || "";
      el.formDocType.value = profileToEdit.doc_type || "slides";
      el.formFolder.value = profileToEdit.folder_path;
      el.formDbId.value = profileToEdit.target?.database_id || "";
      el.formCourseName.value = profileToEdit.target?.course_name || profileToEdit.subject;
    } else {
      document.getElementById("modal-title").textContent = "Nuovo Profilo Corso";
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
      appendLog("sys", "Log copiati negli appunti.");
    });

    // Profile Modal
    el.btnAddProfile.addEventListener("click", () => openProfileModal(null));
    el.btnEditProfile.addEventListener("click", () => openProfileModal(state.activeProfile));
    el.modalClose.addEventListener("click", closeProfileModal);
    el.modalCancel.addEventListener("click", closeProfileModal);
    el.profileForm.addEventListener("submit", saveProfileForm);

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

  // Initialization
  async function init() {
    setupListeners();
    initHeartbeat();
    initEventSource();
    await fetchQuota();
    await loadProfiles();
  }

  init();
})();
