const apiBase = `http://127.0.0.1:${window.MT17_CONFIG.apiPort}`;
const webBase = "";

let presets = [];
let selectedFile = "";
let busy = false;
let waitTimer = null;

const statusEl = document.getElementById("status");
const presetList = document.getElementById("presetList");
const presetName = document.getElementById("presetName");
const settingsDialog = document.getElementById("settingsDialog");
const viewDialog = document.getElementById("viewDialog");
const viewDialogBody = document.getElementById("viewDialogBody");
const viewDialogTitle = document.getElementById("viewDialogTitle");
const monitorSelect = document.getElementById("monitorSelect");
const wallpaperPathInfo = document.getElementById("wallpaperPathInfo");
const installedWallpaperPath = document.getElementById("installedWallpaperPath");
const savedataDir = document.getElementById("savedataDir");
const wallpaperPathOverride = document.getElementById("wallpaperPathOverride");
const downloadPreset = document.getElementById("downloadPreset");
const downloadPresetZip = document.getElementById("downloadPresetZip");
const downloadBackup = document.getElementById("downloadBackup");
const downloadBackupZip = document.getElementById("downloadBackupZip");
const exportBlankApi = document.getElementById("exportBlankApi");
const exportRandomLocation = document.getElementById("exportRandomLocation");
const wallpaperThumb = document.getElementById("wallpaperThumb");
const wallpaperThumbFallback = document.getElementById("wallpaperThumbFallback");
const slideshowEnabled = document.getElementById("slideshowEnabled");
const slideshowInterval = document.getElementById("slideshowInterval");
const slideshowCrossfade = document.getElementById("slideshowCrossfade");
const slideshowOrder = document.getElementById("slideshowOrder");
const slideshowPlaylist = document.getElementById("slideshowPlaylist");
const slideshowStatus = document.getElementById("slideshowStatus");
const slideshowSaveBtn = document.getElementById("slideshowSaveBtn");

const actionButtons = [
  "applyBtn",
  "saveBtn",
  "viewBtn",
  "renameBtn",
  "deleteBtn",
  "duplicateBtn",
  "backupBtn",
  "uploadBtn",
  "restoreBtn",
  "downloadBackup",
  "downloadBackupZip",
  "downloadPreset",
  "downloadPresetZip",
  "slideshowSaveBtn",
  "slideshowAddBtn",
  "slideshowRemoveBtn",
  "slideshowUpBtn",
  "slideshowDownBtn",
].map((id) => document.getElementById(id));

function setStatus(message, ok = true) {
  statusEl.textContent = message;
  statusEl.classList.toggle("ok", ok);
  statusEl.classList.toggle("error", !ok);
}

function setBusy(nextBusy) {
  busy = nextBusy;
  actionButtons.forEach((button) => {
    if (!button) return;
    if (button.tagName === "A") {
      button.classList.toggle("disabled", nextBusy);
    } else {
      button.disabled = nextBusy;
    }
  });
  document.querySelector(".file-label")?.classList.toggle("disabled", nextBusy);
}

async function webJson(path, options = {}) {
  const response = await fetch(`${webBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

function selectPresetByFile(file) {
  if (!file || !presets.some((preset) => preset.file === file)) {
    return false;
  }

  selectedFile = file;
  presetList.value = file;
  const preset = presets.find((item) => item.file === file);
  if (preset) {
    presetName.value = preset.name;
    updatePresetDownloadLink();
  }
  return true;
}

function exportOptionsQuery() {
  const params = new URLSearchParams();
  if (exportBlankApi?.checked) {
    params.set("blankApiKey", "true");
  }
  if (exportRandomLocation?.checked) {
    params.set("randomizeLocation", "true");
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

function updateExportDownloadLinks() {
  const options = exportOptionsQuery();
  if (downloadBackupZip) {
    downloadBackupZip.href = `/api/backup/download-zip${options}`;
  }
  updatePresetDownloadLink();
}

function updatePresetDownloadLink() {
  if (!selectedFile) {
    downloadPreset.href = "#";
    downloadPreset.classList.add("disabled");
    if (downloadPresetZip) {
      downloadPresetZip.href = "#";
      downloadPresetZip.classList.add("disabled");
    }
    return;
  }

  const options = exportOptionsQuery();
  const encoded = encodeURIComponent(selectedFile);
  downloadPreset.href = `/api/preset/${encoded}/download`;
  downloadPreset.classList.remove("disabled");
  if (downloadPresetZip) {
    downloadPresetZip.href = `/api/preset/${encoded}/download-zip${options}`;
    downloadPresetZip.classList.remove("disabled");
  }
}

let targetMonitor = "1";

function getSelectedMonitor() {
  return monitorSelect.value || targetMonitor || "1";
}

async function loadMonitors() {
  try {
    const data = await webJson("/api/lively/monitors");
    const monitors = data.monitors || [];
    monitorSelect.innerHTML = "";
    if (monitors.length === 0) {
      const option = document.createElement("option");
      option.value = "1";
      option.textContent = "Monitor 1";
      monitorSelect.appendChild(option);
    } else {
      monitors.forEach((monitor) => {
        const option = document.createElement("option");
        option.value = monitor.id;
        option.textContent = monitor.label;
        monitorSelect.appendChild(option);
      });
    }

    const settings = await webJson("/api/settings");
    targetMonitor = settings.targetMonitor || monitors[0]?.id || "1";
    monitorSelect.value = targetMonitor;
    wallpaperPathInfo.textContent = settings.installedWallpaperPath
      ? `Wallpaper folder (${settings.pathSource === "override" ? "override" : "auto from script"}): ${settings.installedWallpaperPath}`
      : "";
  } catch (error) {
    wallpaperPathInfo.textContent = "";
  }
}

async function saveTargetMonitor(monitor) {
  targetMonitor = monitor;
  await webJson("/api/settings", {
    method: "POST",
    body: JSON.stringify({ targetMonitor: monitor }),
  });
}

monitorSelect.addEventListener("change", () => {
  saveTargetMonitor(getSelectedMonitor()).catch((error) => setStatus(error.message, false));
});

async function loadPresets(options = {}) {
  const selectFile = options.selectFile || "";
  const selectName = options.selectName || "";
  const keepFile = options.keepFile || selectedFile;

  const data = await webJson("/api/presets");
  presets = data.presets || [];
  presetList.innerHTML = "";

  presets.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.file;
    option.textContent = preset.name;
    presetList.appendChild(option);
  });

  if (selectFile && selectPresetByFile(selectFile)) {
    // Selected by file.
  } else if (selectName) {
    const match = presets.find(
      (preset) => preset.name.toLowerCase() === selectName.toLowerCase()
    );
    if (match) {
      selectPresetByFile(match.file);
    } else if (!selectPresetByFile(keepFile) && presets.length > 0) {
      selectPresetByFile(presets[0].file);
    }
  } else if (!selectPresetByFile(keepFile) && presets.length > 0) {
    selectPresetByFile(presets[0].file);
  } else {
    updatePresetDownloadLink();
  }

  if (!busy) {
    setStatus(`${presets.length} preset(s) ready`);
  }
}

function selectedPreset() {
  return presets.find((preset) => preset.file === selectedFile) || null;
}

presetList.addEventListener("change", () => {
  selectPresetByFile(presetList.value);
});

function beginWait(action, label, context = {}) {
  const waitFile = context.file || selectedFile;
  const waitName = context.name || "";

  setBusy(true);
  setStatus(`${label}... waiting for wallpaper`);
  const deadline = Date.now() + 15000;

  const poll = async () => {
    if (Date.now() > deadline) {
      setBusy(false);
      selectPresetByFile(waitFile);
      setStatus(`${label} timed out. Reload the wallpaper in Lively once.`, false);
      return;
    }

    try {
      const response = await fetch(`${apiBase}/api/status`);
      const status = await response.json();
      if (status.action !== action) {
        waitTimer = window.setTimeout(poll, 250);
        return;
      }

      if (status.ok === true) {
        await loadPresets({
          selectFile: status.file || waitFile,
          selectName: status.name || waitName,
          keepFile: waitFile,
        });
        setBusy(false);
        setStatus(status.message || `${label} done`);
        return;
      }

      if (status.ok === false) {
        setBusy(false);
        selectPresetByFile(waitFile);
        setStatus(status.message || `${label} failed`, false);
        return;
      }
    } catch (error) {
      // Wallpaper API may be offline briefly.
    }

    waitTimer = window.setTimeout(poll, 250);
  };

  poll();
}

async function loadThumbnail() {
  wallpaperThumb.hidden = true;
  wallpaperThumbFallback.hidden = false;

  try {
    const response = await fetch("/api/wallpaper/thumbnail");
    if (!response.ok) {
      return;
    }
    wallpaperThumb.src = `/api/wallpaper/thumbnail?ts=${Date.now()}`;
    wallpaperThumb.hidden = false;
    wallpaperThumbFallback.hidden = true;
  } catch (error) {
    // Keep fallback visible.
  }
}

let slideshowPlaylistFiles = [];

function presetLabelMap(extraItems = []) {
  const map = {};
  presets.forEach((preset) => {
    map[preset.file] = preset.name;
  });
  extraItems.forEach((item) => {
    map[item.file] = item.name;
  });
  return map;
}

function renderSlideshowPlaylist(items = []) {
  const labels = presetLabelMap(items);
  slideshowPlaylist.innerHTML = "";
  slideshowPlaylistFiles.forEach((file) => {
    const option = document.createElement("option");
    option.value = file;
    option.textContent = labels[file] || file;
    slideshowPlaylist.appendChild(option);
  });
}

function updateSlideshowStatus(data) {
  if (!data?.enabled) {
    slideshowStatus.textContent = "Slideshow is off.";
    return;
  }
  if (data.pausedUntilManualResume) {
    slideshowStatus.textContent =
      "Slideshow paused after manual apply. Save with Enable checked to resume.";
    return;
  }
  const count = slideshowPlaylistFiles.length;
  const minutes = (data.intervalSeconds || 300) / 60;
  const crossfade = data.crossfadeSeconds ?? 1.2;
  const fadeLabel = crossfade > 0 ? `, ${crossfade}s cross-fade` : "";
  slideshowStatus.textContent =
    count > 0
      ? `Active — ${count} preset(s), every ${minutes} min (${data.order})${fadeLabel}.`
      : "Enabled but playlist is empty.";
}

async function loadSlideshow() {
  const data = await webJson("/api/slideshow");
  slideshowEnabled.checked = !!data.enabled;
  slideshowInterval.value = String((data.intervalSeconds || 300) / 60);
  slideshowCrossfade.value = String(data.crossfadeSeconds ?? 1.2);
  slideshowOrder.value = data.order || "sequential";
  slideshowPlaylistFiles = Array.isArray(data.playlist) ? [...data.playlist] : [];
  renderSlideshowPlaylist(data.playlistItems || []);
  updateSlideshowStatus(data);
}

async function saveSlideshow() {
  const minutes = Number.parseFloat(slideshowInterval.value);
  const intervalSeconds = Math.max(30, Math.round((Number.isFinite(minutes) ? minutes : 5) * 60));
  const crossfadeSeconds = Math.max(
    0,
    Math.min(10, Number.parseFloat(slideshowCrossfade.value) || 0),
  );

  const data = await webJson("/api/slideshow", {
    method: "POST",
    body: JSON.stringify({
      enabled: slideshowEnabled.checked,
      intervalSeconds,
      crossfadeSeconds,
      order: slideshowOrder.value,
      playlist: slideshowPlaylistFiles,
      pausedUntilManualResume: false,
    }),
  });
  slideshowPlaylistFiles = [...(data.slideshow?.playlist || [])];
  renderSlideshowPlaylist(data.slideshow?.playlistItems || []);
  updateSlideshowStatus(data.slideshow);
  setStatus("Slideshow saved");
}

function moveSlideshowItem(offset) {
  const selected = Array.from(slideshowPlaylist.selectedOptions).map((opt) => opt.value);
  if (selected.length !== 1) {
    setStatus("Select one playlist item to move", false);
    return;
  }
  const file = selected[0];
  const index = slideshowPlaylistFiles.indexOf(file);
  if (index < 0) return;
  const target = index + offset;
  if (target < 0 || target >= slideshowPlaylistFiles.length) return;
  slideshowPlaylistFiles.splice(index, 1);
  slideshowPlaylistFiles.splice(target, 0, file);
  renderSlideshowPlaylist();
  slideshowPlaylist.value = file;
}

document.getElementById("slideshowAddBtn").addEventListener("click", () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset to add to the slideshow", false);
    return;
  }
  if (slideshowPlaylistFiles.includes(preset.file)) {
    setStatus("Preset is already in the slideshow", false);
    return;
  }
  slideshowPlaylistFiles.push(preset.file);
  renderSlideshowPlaylist();
  slideshowPlaylist.value = preset.file;
});

document.getElementById("slideshowRemoveBtn").addEventListener("click", () => {
  const selected = Array.from(slideshowPlaylist.selectedOptions).map((opt) => opt.value);
  if (!selected.length) {
    setStatus("Select playlist item(s) to remove", false);
    return;
  }
  slideshowPlaylistFiles = slideshowPlaylistFiles.filter((file) => !selected.includes(file));
  renderSlideshowPlaylist();
});

document.getElementById("slideshowUpBtn").addEventListener("click", () => moveSlideshowItem(-1));
document.getElementById("slideshowDownBtn").addEventListener("click", () => moveSlideshowItem(1));
slideshowSaveBtn.addEventListener("click", () => {
  saveSlideshow().catch((error) => setStatus(error.message, false));
});

function renderPresetView(groups) {
  viewDialogBody.innerHTML = "";

  groups.forEach((group) => {
    const section = document.createElement("section");
    section.className = "view-group";

    const heading = document.createElement("h3");
    heading.textContent = group.group;
    section.appendChild(heading);

    const table = document.createElement("table");
    table.className = "view-table";

    group.items.forEach((item) => {
      const row = document.createElement("tr");
      const labelCell = document.createElement("td");
      const valueCell = document.createElement("td");
      labelCell.textContent = item.label;
      valueCell.textContent = item.value;
      row.appendChild(labelCell);
      row.appendChild(valueCell);
      table.appendChild(row);
    });

    section.appendChild(table);
    viewDialogBody.appendChild(section);
  });
}

document.getElementById("applyBtn").addEventListener("click", async () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset first", false);
    return;
  }

  try {
    const applyResult = await webJson("/api/command/apply", {
      method: "POST",
      body: JSON.stringify({
        name: preset.name,
        file: preset.file,
        monitor: getSelectedMonitor(),
      }),
    });
    const monitor = applyResult.monitor || getSelectedMonitor();
    let label = `Applying '${preset.name}' on monitor ${monitor}`;
    const livelySaved = applyResult.livelySavedataFiles || [];
    if (livelySaved.length) {
      label += ` (+ Lively saved for ${livelySaved.length} monitor(s))`;
    }
    beginWait("apply", label, {
      file: preset.file,
      name: preset.name,
    });
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("saveBtn").addEventListener("click", async () => {
  const name = presetName.value.trim();
  if (!name) {
    setStatus("Enter a preset name first", false);
    return;
  }

  const preset = selectedPreset();
  const existingFile = preset && preset.name === name ? preset.file : null;

  try {
    await webJson("/api/command/capture", {
      method: "POST",
      body: JSON.stringify({
        name,
        file: existingFile,
        monitor: getSelectedMonitor(),
      }),
    });
    beginWait("capture", `Saving '${name}' (monitor ${getSelectedMonitor()})`, { name, file: existingFile });
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("viewBtn").addEventListener("click", async () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset first", false);
    return;
  }

  try {
    const data = await webJson(`/api/preset/${encodeURIComponent(preset.file)}`);
    viewDialogTitle.textContent = `${data.preset.name} settings`;
    renderPresetView(data.groups || []);
    viewDialog.showModal();
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("viewClose").addEventListener("click", () => {
  viewDialog.close();
});

document.getElementById("renameBtn").addEventListener("click", async () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset first", false);
    return;
  }

  const newName = presetName.value.trim();
  if (!newName) {
    setStatus("Enter a preset name first", false);
    return;
  }

  if (newName === preset.name) {
    setStatus("Change the name in the text box first", false);
    return;
  }

  try {
    const data = await webJson("/api/preset/rename", {
      method: "POST",
      body: JSON.stringify({ file: preset.file, name: newName }),
    });
    await loadPresets({ selectFile: data.preset.file, keepFile: data.preset.file });
    await loadSlideshow();
    setStatus(`Renamed to '${data.preset.name}'`);
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("deleteBtn").addEventListener("click", async () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset first", false);
    return;
  }

  if (!window.confirm(`Delete '${preset.name}'?`)) return;

  try {
    await webJson("/api/preset/delete", {
      method: "POST",
      body: JSON.stringify({ file: preset.file }),
    });
    selectedFile = "";
    presetName.value = "";
    await loadPresets();
    await loadSlideshow();
    setStatus(`Deleted '${preset.name}'`);
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("duplicateBtn").addEventListener("click", async () => {
  const preset = selectedPreset();
  if (!preset) {
    setStatus("Select a preset first", false);
    return;
  }

  try {
    const data = await webJson("/api/preset/duplicate", {
      method: "POST",
      body: JSON.stringify({ file: preset.file }),
    });
    await loadPresets({ selectFile: data.preset.file });
    setStatus(`Created '${data.preset.name}'`);
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("uploadPresetFile").addEventListener("change", async (event) => {
  const fileInput = event.target;
  if (!fileInput.files || !fileInput.files[0]) {
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const importName = presetName.value.trim();
  if (importName) {
    formData.append("name", importName);
  }

  try {
    const response = await fetch("/api/preset/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Upload failed");
    }
    fileInput.value = "";
    await loadPresets({ selectFile: data.preset.file });
    setStatus(data.message || "Preset uploaded");
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("uploadPresetZipFile").addEventListener("change", async (event) => {
  const fileInput = event.target;
  if (!fileInput.files || !fileInput.files[0]) {
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const response = await fetch("/api/preset/upload-zip", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Upload failed");
    }
    fileInput.value = "";
    await loadPresets({ selectFile: data.preset.file });
    await loadSlideshow();
    setStatus(data.message || "Preset ZIP imported");
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("backupBtn").addEventListener("click", async () => {
  try {
    const data = await webJson("/api/backup", { method: "POST", body: "{}" });
    setStatus(`Local backup saved to ${data.backup}`);
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("restoreBtn").addEventListener("click", async () => {
  if (!window.confirm("Restore the latest local backup into your presets folder?")) {
    return;
  }

  try {
    await webJson("/api/restore", { method: "POST", body: "{}" });
    await loadPresets();
    setStatus("Restored latest local backup");
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("uploadFile");
  if (!fileInput.files || !fileInput.files[0]) {
    setStatus("Choose a backup JSON file first", false);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const response = await fetch("/api/backup/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Upload failed");
    }
    fileInput.value = "";
    await loadPresets();
    setStatus(data.message || "Backup uploaded");
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("uploadZipBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("uploadZipFile");
  if (!fileInput.files || !fileInput.files[0]) {
    setStatus("Choose a full backup ZIP file first", false);
    return;
  }

  if (
    !window.confirm(
      "Import full backup ZIP? This replaces your current presets and restores slideshow settings from the package."
    )
  ) {
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const response = await fetch("/api/backup/upload-zip", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Upload failed");
    }
    fileInput.value = "";
    await loadPresets();
    await loadSlideshow();
    setStatus(data.message || "Full backup ZIP imported");
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("settingsBtn").addEventListener("click", async () => {
  try {
    const data = await webJson("/api/settings");
    installedWallpaperPath.value = data.installedWallpaperPath || "";
    savedataDir.value = data.savedataDir || "";
    wallpaperPathOverride.value = data.wallpaperPathOverride || "";
    settingsDialog.showModal();
  } catch (error) {
    setStatus(error.message, false);
  }
});

document.getElementById("settingsCancel").addEventListener("click", () => {
  settingsDialog.close();
});

document.getElementById("settingsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await webJson("/api/settings", {
      method: "POST",
      body: JSON.stringify({
        wallpaperPathOverride: wallpaperPathOverride.value.trim(),
        targetMonitor: getSelectedMonitor(),
      }),
    });
    settingsDialog.close();
    await loadMonitors();
    await loadPresets();
    await loadThumbnail();
    setStatus("Settings saved");
  } catch (error) {
    setStatus(error.message, false);
  }
});

async function pollHealth() {
  if (!busy) {
    try {
      await fetch(`${apiBase}/api/health`);
    } catch (error) {
      setStatus("Web UI running. Start the mt17 wallpaper in Lively.", false);
    }
  }
  window.setTimeout(pollHealth, 5000);
}

exportBlankApi?.addEventListener("change", updateExportDownloadLinks);
exportRandomLocation?.addEventListener("change", updateExportDownloadLinks);

loadMonitors()
  .then(() => loadPresets())
  .then(() => loadSlideshow())
  .then(() => updateExportDownloadLinks())
  .catch((error) => setStatus(error.message, false));
loadThumbnail();
pollHealth();
