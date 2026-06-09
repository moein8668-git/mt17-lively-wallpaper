// Canvas and context
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

var show_weather = true;
var show_visualizer = true;
var show_cover = true;
var show_song_name = true;
var show_singer = true;
var show_sys_info = true;
var show_cpu = true;
var show_gpu = true;
var show_mem = true;
var show_animated_background = true;
var show_clock1 = true;
let showAllDays = true; // Set to false to display only the current day

// Default position values
let weatherbottom = 30; // Default top position in pixels
let weatherLeft = 20; // Default left position in pixels
let systemUsageTop = 20;
let systemUsageRight = 20;
let weatherTempColor = "#ffffff";
let weatherDescriptionColor = "#cccccc";
let weatherBackground = "rgba(0, 0, 0, 0.7)";
let weatherIconSize = 40;
let weatherFontSize = 14;
let weatherTempFontSize = 18;
let systemUsageColor = "#ffffff";
let systemUsageBackground = "#000000";
let systemUsageFontSize = 14;
let mediaColor = "#cccccc";
let mediaTitleColor = "#ffffff";

//clock1 settings
let clock1TimeColor = "#afeeee";
let clock1TodayColor = "#afeeee";
let clock1OtherDaysColor = "#cccccc";
let clock1DateColor = "#afeeee";
let clock1TimeBottom = 110; // px
let clock1TimeFontSize = 24; // px
let clock1TimeGap = 5; // px
let clock1AmPmFontSize = 16; // px
let clock1DaysBottom = 80; // px
let clock1DaysGap = 0.7; // rem
let clock1DaysFontSize = 18; // px
let clock1DateBottom = 50; // px
let clock1DateGap = 0.5; // rem
let clock1DateFontSize = 16; // px
let clock1Left = 50;//problem 
let clock1Top = 30;

// Visualizer settings
let visualizerWidth = 100; // Width of the visualizer//controllable
let visualizerHeight = 30; // Height of the visualizer//controllable
let backgroundColor = "rgba(0, 0, 0, 0)"; // Fully transparent //controllable
let linesColor = "#7B00FF"; //controllable
let square = true; //no need to change
//"rgba(119, 0, 255, 0)"
// Visualizer position settings
let visualizerLeft = 130; // Horizontal position in pixels//controllable
let visualizerTop = 100; // Vertical position in pixels//controllable

// Album cover and song data settings
let albumArtSize = 120; // Size of the album art (width and height)//controllable
let titleFontSize = 20; // Font size for the song title//controllable
let artistFontSize = 15; // Font size for the artist name//controllable
let songNameLimit = 20; // Maximum characters for song name before wrapping//controllable
let visualizerMargin = 0; // Space between song data and visualizer//controllable
let contentTop = 20; // in pixel
let contentLeft = 20; // in pixel
//let visualizerTop = 100; // Default top position

var BackgroundSource = 'media/bmw.webm';//controllable
var BackgroundImageSource = 'images/background.jpg';//not controllable in js but still could be changed by  lively or css file

var cpuDecimalnumber = 2;//controllable
var gpuDecimalnumber = 2;//controllable
var memDecimalnumber = 2;//controllable
// OpenWeather API settings (defaults match LivelyProperties.json)
let apiKey = "";
let city = "Tehran";
let units = "metric";
var UseCity = false;
var Lat = 30.77;
var Lon = 40.77;
var update_interval = 180; // in seconds

let show_weatherFeelsLike = false;
let show_weatherHumidity = false;
let show_weatherWind = false;
let weatherExtraColor = "#cccccc";
let weatherExtraFontSize = 13;

let show_network = true;
let networkBottom = 20;
let networkRight = 20;
let networkColor = "#ffffff";
let networkFontSize = 12;
let networkBackground = "rgba(0, 0, 0, 0.7)";
let networkUseMegabits = true;

let visualizerGlow = true;
let clock24Hour = false;
let wallpaperPaused = false;
let clockTimer = null;

const DEFAULT_ALBUM_ART = "res/da.png";
const IDLE_MEDIA_TITLE = "Nothing playing";

let weatherRefreshTimer = null;
const PRESET_API = "http://127.0.0.1:8766";
let presetBridgeBusy = false;

const PRESET_VERSION = 1;

const BUNDLED_FONTS = [
  "mediaFont.otf",
  "weatherFont.ttf",
  "systemFont.ttf",
  "clock1Font.ttf",
  "clock1DateFont.ttf",
];

const fontSlots = {
  mediaTitleFont: { family: "livelyMediaTitle", cssVar: "--media-title-font", defaultFile: "mediaFont.otf" },
  mediaArtistFont: { family: "livelyMediaArtist", cssVar: "--media-artist-font", defaultFile: "mediaFont.otf" },
  weatherFont: { family: "livelyWeather", cssVar: "--weather-font-family", defaultFile: "weatherFont.ttf" },
  systemUsageFont: { family: "livelySystemUsage", cssVar: "--systemUsage-font-family", defaultFile: "systemFont.ttf" },
  clock1TimeFont: { family: "livelyClockTime", cssVar: "--clock1-time-font", defaultFile: "clock1Font.ttf" },
  clock1DaysFont: { family: "livelyClockDays", cssVar: "--clock1-days-font", defaultFile: "clock1DateFont.ttf" },
  clock1DateFont: { family: "livelyClockDate", cssVar: "--clock1-date-font", defaultFile: "clock1DateFont.ttf" },
};

const fontFiles = {
  mediaTitleFont: "mediaFont.otf",
  mediaArtistFont: "mediaFont.otf",
  weatherFont: "weatherFont.ttf",
  systemUsageFont: "systemFont.ttf",
  clock1TimeFont: "clock1Font.ttf",
  clock1DaysFont: "clock1DateFont.ttf",
  clock1DateFont: "clock1DateFont.ttf",
};

function sanitizeFontFilename(filename) {
  if (filename == null || filename === "") {
    return null;
  }

  let name = String(filename).replace(/\\/g, "/");
  if (name.includes("/")) {
    name = name.split("/").pop();
  }

  if (/\.(ttf|otf|woff2?)$/i.test(name)) {
    return name;
  }

  return null;
}

function resolveFontSelection(val, slotKey) {
  if (typeof val === "number" || (typeof val === "string" && /^\d+$/.test(val.trim()))) {
    const index = Number(val);
    return BUNDLED_FONTS[index] || fontSlots[slotKey].defaultFile;
  }

  const cleaned = sanitizeFontFilename(val);
  return cleaned || fontSlots[slotKey].defaultFile;
}

function applyClockFont(filename) {
  applyCustomFont("clock1TimeFont", filename);
  applyCustomFont("clock1DaysFont", filename);
  applyCustomFont("clock1DateFont", filename);
}

function getFontFormat(extension) {
  switch (extension) {
    case "otf":
      return "opentype";
    case "woff":
      return "woff";
    case "woff2":
      return "woff2";
    default:
      return "truetype";
  }
}

function applyCustomFont(slotKey, filename) {
  const slot = fontSlots[slotKey];
  if (!slot || filename == null || filename === "") {
    return;
  }

  const resolvedName = resolveFontSelection(filename, slotKey);
  let path = resolvedName.replace(/\\/g, "/");
  if (!path.startsWith("fonts/")) {
    path = `fonts/${path}`;
  }

  const extension = path.split(".").pop().toLowerCase();
  const format = getFontFormat(extension);

  let styleEl = document.getElementById(`font-face-${slotKey}`);
  if (!styleEl) {
    styleEl = document.createElement("style");
    styleEl.id = `font-face-${slotKey}`;
    document.head.appendChild(styleEl);
  }

  styleEl.textContent = `@font-face {
    font-family: '${slot.family}';
    src: url('${path}') format('${format}');
  }`;

  document.documentElement.style.setProperty(slot.cssVar, `'${slot.family}', sans-serif`);
  fontFiles[slotKey] = resolvedName;
}

function initializeFonts() {
  Object.keys(fontSlots).forEach((slotKey) => {
    applyCustomFont(slotKey, fontFiles[slotKey] || fontSlots[slotKey].defaultFile);
  });
}

function getPresetState() {
  return {
    version: PRESET_VERSION,
    show_weather,
    show_visualizer,
    show_cover,
    show_song_name,
    show_singer,
    show_sys_info,
    show_cpu,
    show_gpu,
    show_mem,
    show_animated_background,
    show_clock1,
    showAllDays,
    weatherbottom,
    weatherLeft,
    systemUsageTop,
    systemUsageRight,
    weatherTempColor,
    weatherDescriptionColor,
    weatherBackground,
    weatherIconSize,
    weatherFontSize,
    weatherTempFontSize,
    systemUsageColor,
    systemUsageBackground,
    systemUsageFontSize,
    mediaColor,
    mediaTitleColor,
    clock1TimeColor,
    clock1TodayColor,
    clock1OtherDaysColor,
    clock1DateColor,
    clock1TimeBottom,
    clock1TimeFontSize,
    clock1TimeGap,
    clock1AmPmFontSize,
    clock1DaysBottom,
    clock1DaysGap,
    clock1DaysFontSize,
    clock1DateBottom,
    clock1DateGap,
    clock1DateFontSize,
    clock1Left,
    clock1Top,
    visualizerWidth,
    visualizerHeight,
    backgroundColor,
    linesColor,
    square,
    visualizerLeft,
    visualizerTop,
    albumArtSize,
    titleFontSize,
    artistFontSize,
    songNameLimit,
    visualizerMargin,
    contentTop,
    contentLeft,
    BackgroundSource,
    BackgroundImageSource,
    cpuDecimalnumber,
    gpuDecimalnumber,
    memDecimalnumber,
    apiKey,
    city,
    units,
    UseCity,
    Lat,
    Lon,
    update_interval,
    show_weatherFeelsLike,
    show_weatherHumidity,
    show_weatherWind,
    weatherExtraColor,
    weatherExtraFontSize,
    show_network,
    networkBottom,
    networkRight,
    networkColor,
    networkFontSize,
    networkBackground,
    networkUseMegabits,
    visualizerGlow,
    clock24Hour,
    fontFiles: { ...fontFiles },
  };
}

function getActiveBgLayer() {
  return document.querySelector(".bg-layer.is-visible") || document.getElementById("bg-layer-a");
}

function getInactiveBgLayer() {
  const layerA = document.getElementById("bg-layer-a");
  const layerB = document.getElementById("bg-layer-b");
  if (!layerA || !layerB) {
    return null;
  }
  return layerA.classList.contains("is-visible") ? layerB : layerA;
}

function getBackgroundImage() {
  return getActiveBgLayer()?.querySelector(".bg-image");
}

function getBackgroundVideo() {
  return getActiveBgLayer()?.querySelector(".bg-video");
}

function resolveImagePath(staticWallpaper) {
  let path = staticWallpaper.replace(/\\/g, "/");
  if (!path.startsWith("images/")) {
    path = `images/${path}`;
  }
  return path;
}

function resolveVideoPath(newSrc) {
  let path = newSrc.replace(/\\/g, "/");
  if (!path.startsWith("media/")) {
    path = `media/${path}`;
  }
  return path;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function preloadImageElement(img, src) {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      img.onload = null;
      img.onerror = null;
    };
    img.onload = () => {
      cleanup();
      resolve();
    };
    img.onerror = () => {
      cleanup();
      reject(new Error(`Failed to load image: ${src}`));
    };
    img.src = src;
  });
}

function preloadVideoElement(video, src) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      video.removeEventListener("loadeddata", onReady);
      video.removeEventListener("error", onReady);
      clearTimeout(timer);
      resolve();
    };
    const onReady = () => finish();
    const timer = setTimeout(finish, 4000);
    video.addEventListener("loadeddata", onReady);
    video.addEventListener("error", onReady);
    video.src = src;
    video.load();
    video.play().catch(() => {});
  });
}

function getSlideshowCrossfadeMs() {
  const seconds = Number(slideshowConfig?.crossfadeSeconds);
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return 0;
  }
  return Math.round(Math.min(10, Math.max(0.3, seconds)) * 1000);
}

function setCrossfadeDurationCss(ms) {
  const seconds = ms > 0 ? ms / 1000 : 1.2;
  document.documentElement.style.setProperty("--crossfade-duration", `${seconds}s`);
}

async function applyPresetWithCrossfade(state) {
  const durationMs = getSlideshowCrossfadeMs();
  if (!durationMs) {
    return applyPresetState(state);
  }

  setCrossfadeDurationCss(durationMs);
  const uiLayer = document.getElementById("ui-layer");
  const inactiveLayer = getInactiveBgLayer();
  if (!uiLayer || !inactiveLayer) {
    return applyPresetState(state);
  }

  const inactiveImage = inactiveLayer.querySelector(".bg-image");
  const inactiveVideo = inactiveLayer.querySelector(".bg-video");
  const imagePath = resolveImagePath(state.BackgroundImageSource || BackgroundImageSource);
  const videoPath = resolveVideoPath(state.BackgroundSource || BackgroundSource);

  try {
    await Promise.all([
      preloadImageElement(inactiveImage, imagePath),
      preloadVideoElement(inactiveVideo, videoPath),
    ]);
  } catch (error) {
    console.warn("Crossfade preload issue:", error);
  }

  inactiveVideo.style.visibility = state.show_animated_background !== false ? "visible" : "hidden";

  const uiHalf = Math.max(150, Math.round(durationMs / 2));
  uiLayer.classList.add("is-fading");
  await sleep(uiHalf);

  const activeLayer = getActiveBgLayer();
  inactiveLayer.classList.add("is-visible");
  if (activeLayer) {
    activeLayer.classList.remove("is-visible");
  }
  await sleep(durationMs);

  const applied = applyPresetState(state, { skipBackgrounds: true });
  if (!applied) {
    if (activeLayer) {
      activeLayer.classList.add("is-visible");
    }
    inactiveLayer.classList.remove("is-visible");
    uiLayer.classList.remove("is-fading");
    return false;
  }

  uiLayer.classList.remove("is-fading");
  await sleep(uiHalf);
  return true;
}

function applyPresetState(state, options = {}) {
  if (!state) {
    return false;
  }

  show_weather = state.show_weather;
  show_visualizer = state.show_visualizer;
  show_cover = state.show_cover;
  show_song_name = state.show_song_name;
  show_singer = state.show_singer;
  show_sys_info = state.show_sys_info;
  show_cpu = state.show_cpu;
  show_gpu = state.show_gpu;
  show_mem = state.show_mem;
  show_animated_background = state.show_animated_background;
  show_clock1 = state.show_clock1;
  showAllDays = state.showAllDays;
  weatherbottom = state.weatherbottom;
  weatherLeft = state.weatherLeft;
  systemUsageTop = state.systemUsageTop;
  systemUsageRight = state.systemUsageRight;
  weatherTempColor = state.weatherTempColor;
  weatherDescriptionColor = state.weatherDescriptionColor;
  weatherBackground = state.weatherBackground;
  weatherIconSize = state.weatherIconSize;
  weatherFontSize = state.weatherFontSize;
  weatherTempFontSize = state.weatherTempFontSize;
  systemUsageColor = state.systemUsageColor;
  systemUsageBackground = state.systemUsageBackground;
  systemUsageFontSize = state.systemUsageFontSize;
  mediaColor = state.mediaColor;
  mediaTitleColor = state.mediaTitleColor;
  clock1TimeColor = state.clock1TimeColor;
  clock1TodayColor = state.clock1TodayColor;
  clock1OtherDaysColor = state.clock1OtherDaysColor;
  clock1DateColor = state.clock1DateColor;
  clock1TimeBottom = state.clock1TimeBottom;
  clock1TimeFontSize = state.clock1TimeFontSize;
  clock1TimeGap = state.clock1TimeGap;
  clock1AmPmFontSize = state.clock1AmPmFontSize;
  clock1DaysBottom = state.clock1DaysBottom;
  clock1DaysGap = state.clock1DaysGap;
  clock1DaysFontSize = state.clock1DaysFontSize;
  clock1DateBottom = state.clock1DateBottom;
  clock1DateGap = state.clock1DateGap;
  clock1DateFontSize = state.clock1DateFontSize;
  clock1Left = state.clock1Left;
  clock1Top = state.clock1Top;
  visualizerWidth = state.visualizerWidth;
  visualizerHeight = state.visualizerHeight;
  backgroundColor = state.backgroundColor;
  linesColor = state.linesColor;
  square = state.square;
  visualizerLeft = state.visualizerLeft;
  visualizerTop = state.visualizerTop;
  albumArtSize = state.albumArtSize;
  titleFontSize = state.titleFontSize;
  artistFontSize = state.artistFontSize;
  songNameLimit = state.songNameLimit;
  visualizerMargin = state.visualizerMargin;
  contentTop = state.contentTop ?? 20;
  contentLeft = state.contentLeft ?? 20;
  BackgroundSource = state.BackgroundSource;
  BackgroundImageSource = state.BackgroundImageSource;
  cpuDecimalnumber = state.cpuDecimalnumber;
  gpuDecimalnumber = state.gpuDecimalnumber;
  memDecimalnumber = state.memDecimalnumber;
  apiKey = state.apiKey ?? "";
  city = state.city ?? "Tehran";
  units = state.units ?? "metric";
  UseCity = state.UseCity ?? false;
  Lat = state.Lat ?? 30.77;
  Lon = state.Lon ?? 40.77;
  update_interval = state.update_interval ?? 180;
  show_weatherFeelsLike = state.show_weatherFeelsLike ?? false;
  show_weatherHumidity = state.show_weatherHumidity ?? false;
  show_weatherWind = state.show_weatherWind ?? false;
  weatherExtraColor = state.weatherExtraColor ?? "#cccccc";
  weatherExtraFontSize = state.weatherExtraFontSize ?? 13;
  show_network = state.show_network ?? true;
  networkBottom = state.networkBottom ?? 20;
  networkRight = state.networkRight ?? 20;
  networkColor = state.networkColor ?? "#ffffff";
  networkFontSize = state.networkFontSize ?? 12;
  networkBackground = state.networkBackground ?? "rgba(0, 0, 0, 0.7)";
  networkUseMegabits = state.networkUseMegabits ?? true;
  visualizerGlow = state.visualizerGlow ?? true;
  clock24Hour = state.clock24Hour ?? false;

  if (state.fontFiles) {
    Object.keys(fontSlots).forEach((slotKey) => {
      applyCustomFont(slotKey, state.fontFiles[slotKey] || fontSlots[slotKey].defaultFile);
    });
  }

  if (!options.skipBackgrounds) {
    changeVideoSource(BackgroundSource);
    updateStaticWallpaper(BackgroundImageSource);
  }
  setSize();
  updateStyles();
  updateVisualizerPosition();
  toggleVisibility();
  updateWeatherPosition();
  updateClock();
  startWeatherRefresh();
  fetchWeather();
  return true;
}

async function savePresetViaApp(name, existingFile) {
  const presetName = (name || "").trim();
  if (!presetName) {
    return false;
  }

  try {
    const response = await fetch(`${PRESET_API}/api/preset/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: presetName,
        file: existingFile || undefined,
        data: getPresetState(),
      }),
    });
    const result = await response.json();
    return response.ok && result.ok;
  } catch (error) {
    console.error("Preset Manager is not running.", error);
    return false;
  }
}

async function loadPresetFromFile(filename, options = {}) {
  if (!filename) {
    return false;
  }

  let path = filename.replace(/\\/g, "/");
  if (!path.startsWith("presets/")) {
    path = `presets/${path}`;
  }

  try {
    const response = await fetch(`${path}`, { cache: "no-store" });
    if (!response.ok) {
      return false;
    }
    const data = await response.json();
    if (options.crossfade) {
      return applyPresetWithCrossfade(data);
    }
    return applyPresetState(data);
  } catch (error) {
    console.error("Failed to load preset:", error);
    return false;
  }
}

async function notifyPresetApp(payload) {
  try {
    await fetch(`${PRESET_API}/api/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    // Preset app may be closed.
  }
}

async function finishPresetCommand() {
  try {
    await fetch(`${PRESET_API}/api/command/done`, { method: "POST" });
  } catch (error) {
    // Preset app may be closed.
  }
}

async function handlePresetCommand(command) {
  if (!command || !command.action) {
    return;
  }

  if (command.action === "apply") {
    pauseSlideshowForManualApply();
    const ok = await loadPresetFromFile(command.file);
    await notifyPresetApp({
      ok,
      action: "apply",
      message: ok ? `Applied '${command.name || command.file}'` : "Apply failed",
      name: command.name || command.file,
      file: command.file,
    });
  } else if (command.action === "capture") {
    const ok = await savePresetViaApp(command.name, command.file);
    await notifyPresetApp({
      ok,
      action: "capture",
      message: ok ? `Saved '${command.name}'` : "Save failed — is Preset Manager running?",
      name: command.name,
      file: command.file || null,
    });
  }

  await finishPresetCommand();
}

async function checkPresetCommand() {
  if (presetBridgeBusy) {
    return;
  }

  presetBridgeBusy = true;
  try {
    const response = await fetch("presets/_command.json", { cache: "no-store" });
    if (!response.ok) {
      return;
    }
    const command = await response.json();
    await handlePresetCommand(command);
  } catch (error) {
    // No command file yet.
  } finally {
    presetBridgeBusy = false;
  }
}

setInterval(checkPresetCommand, 1500);

const SLIDESHOW_STORAGE_KEY = "mt17_slideshow_state";
const SLIDESHOW_POLL_MS = 5000;

let slideshowConfig = null;
let slideshowConfigSignature = "";
let slideshowBusy = false;

function loadSlideshowState() {
  try {
    const raw = localStorage.getItem(SLIDESHOW_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (error) {
    return {};
  }
}

function saveSlideshowState(patch) {
  const next = { ...loadSlideshowState(), ...patch };
  localStorage.setItem(SLIDESHOW_STORAGE_KEY, JSON.stringify(next));
  return next;
}

function pauseSlideshowForManualApply() {
  saveSlideshowState({ paused: true });
}

function buildSlideshowSignature(config) {
  if (!config) {
    return "";
  }
  return JSON.stringify({
    enabled: !!config.enabled,
    intervalSeconds: config.intervalSeconds,
    crossfadeSeconds: config.crossfadeSeconds,
    order: config.order,
    playlist: config.playlist || [],
    pausedUntilManualResume: !!config.pausedUntilManualResume,
  });
}

async function fetchSlideshowConfig() {
  try {
    const response = await fetch("presets/slideshow.json", { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    return null;
  }
}

function getSlideshowPlaylist(config) {
  return (config?.playlist || []).filter(
    (file) => typeof file === "string" && file.endsWith(".preset.json")
  );
}

function pickNextSlideshowFile(config) {
  const playlist = getSlideshowPlaylist(config);
  if (!playlist.length) {
    return null;
  }

  const order = config.order || "sequential";
  const state = loadSlideshowState();

  if (order === "random") {
    return playlist[Math.floor(Math.random() * playlist.length)];
  }

  if (order === "shuffle") {
    let bag = Array.isArray(state.shuffleBag)
      ? state.shuffleBag.filter((file) => playlist.includes(file))
      : [];
    if (!bag.length) {
      bag = [...playlist];
      for (let i = bag.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [bag[i], bag[j]] = [bag[j], bag[i]];
      }
    }
    const next = bag.shift();
    saveSlideshowState({ shuffleBag: bag });
    return next || playlist[0];
  }

  let index = Number.isFinite(state.index) ? state.index : 0;
  if (index < 0 || index >= playlist.length) {
    index = 0;
  }
  const file = playlist[index];
  saveSlideshowState({ index: (index + 1) % playlist.length });
  return file;
}

async function refreshSlideshowConfig() {
  const config = await fetchSlideshowConfig();
  const signature = buildSlideshowSignature(config);
  if (signature === slideshowConfigSignature) {
    return;
  }

  const previous = slideshowConfig;
  slideshowConfig = config;
  slideshowConfigSignature = signature;

  if (!config) {
    return;
  }

  const wasActive = previous?.enabled && !previous?.pausedUntilManualResume;
  const isActive = config.enabled && !config.pausedUntilManualResume;
  const playlistChanged =
    JSON.stringify(previous?.playlist || []) !== JSON.stringify(config.playlist || []);

  if (isActive && (!wasActive || playlistChanged)) {
    saveSlideshowState({
      paused: false,
      nextAt: 0,
      index: 0,
      shuffleBag: [],
    });
  }

  if (config.pausedUntilManualResume) {
    saveSlideshowState({ paused: true });
  } else if (isActive && loadSlideshowState().paused) {
    saveSlideshowState({ paused: false, nextAt: 0 });
  }
}

async function tickSlideshow() {
  if (slideshowBusy || presetBridgeBusy) {
    return;
  }

  const config = slideshowConfig;
  if (!config?.enabled || config.pausedUntilManualResume) {
    return;
  }

  const state = loadSlideshowState();
  if (state.paused) {
    return;
  }

  const playlist = getSlideshowPlaylist(config);
  if (!playlist.length) {
    console.warn("Slideshow enabled but playlist is empty");
    return;
  }

  const now = Date.now();
  const intervalMs = Math.max(30000, (Number(config.intervalSeconds) || 300) * 1000);

  if (state.nextAt && now < state.nextAt) {
    return;
  }

  slideshowBusy = true;
  try {
    const file = pickNextSlideshowFile(config);
    if (!file) {
      return;
    }
    const ok = await loadPresetFromFile(file, { crossfade: getSlideshowCrossfadeMs() > 0 });
    if (ok) {
      saveSlideshowState({ nextAt: now + intervalMs });
    }
  } finally {
    slideshowBusy = false;
  }
}

async function slideshowLoop() {
  await refreshSlideshowConfig();
  await tickSlideshow();
}

setInterval(slideshowLoop, SLIDESHOW_POLL_MS);
slideshowLoop();

// Function to set canvas size and visualizer parameters
function setSize() {
  canvas.width = visualizerWidth;
  canvas.height = visualizerHeight;
  canvas.style.width = `${visualizerWidth}px`;
  canvas.style.height = `${visualizerHeight}px`;
}

// Function to change the video source
function changeVideoSource(newSrc) {
  const video = getBackgroundVideo();
  if (!video) {
    return;
  }
  video.src = resolveVideoPath(newSrc);
  video.load();
  if (!wallpaperPaused && show_animated_background) {
    video.play().catch(() => {});
  }
}
changeVideoSource(BackgroundSource);

function updateStaticWallpaper(staticWallpaper) {
  const image = getBackgroundImage();
  if (!image) {
    return;
  }
  image.src = resolveImagePath(staticWallpaper);
}
updateStaticWallpaper(BackgroundImageSource);


function setIdleMediaState() {
  document.getElementById("title").innerText = IDLE_MEDIA_TITLE;
  document.getElementById("artist").innerText = "";
  document.getElementById("albumart").src = DEFAULT_ALBUM_ART;
}

function isTrackEmpty(obj) {
  if (!obj) {
    return true;
  }
  const title = (obj.Title || "").trim();
  const artist = (obj.Artist || "").trim();
  return !title && !artist && !obj.Thumbnail;
}

function formatNetworkSpeed(bytesPerSec) {
  const bytes = Number(bytesPerSec) || 0;
  if (networkUseMegabits) {
    return `${((bytes * 8) / (1024 * 1024)).toFixed(2)} Mb/s`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`;
}

function updateNetworkDisplay(downBytes, upBytes) {
  document.getElementById("netDown").innerText = `↓ ${formatNetworkSpeed(downBytes)}`;
  document.getElementById("netUp").innerText = `↑ ${formatNetworkSpeed(upBytes)}`;
}

function toggleVisibility() {
  // Weather
  document.getElementById("weather").style.visibility = show_weather ? "visible" : "hidden";

  document.getElementById("networkStats").style.display = show_network ? "block" : "none";

  // Visualizer
  document.getElementById("canvas").style.visibility = show_visualizer ? "visible" : "hidden";

  // Album Cover
  document.getElementById("albumart").style.display = show_cover ? "block" : "none";

  // Song Name
  document.getElementById("title").style.display = show_song_name ? "block" : "none";

  // Singer
  document.getElementById("artist").style.visibility = show_singer ? "visible" : "hidden";

  // System Info
  document.getElementById("systemUsage").style.display = show_sys_info ? "block" : "none";

  // CPU
  document.getElementById("cpuUsage").style.display = show_cpu ? "block" : "none";

  // GPU
  document.getElementById("gpuUsage").style.display = show_gpu ? "block" : "none";

  // Memory (RAM)
  document.getElementById("ramUsage").style.display = show_mem ? "block" : "none";

  document.querySelectorAll(".bg-video").forEach((videoEl) => {
    videoEl.style.visibility = show_animated_background ? "visible" : "hidden";
  });
  document.getElementById("clocknum1").style.visibility = show_clock1 ? "visible" : "hidden";


}
//document.getElementById("animated-background").style.display = "block";


// Function to update system usage display
function updateSystemUsage(cpu, ram, gpu) {
  document.getElementById("cpuUsage").innerText = `CPU: ${cpu}%`;
  document.getElementById("ramUsage").innerText = `RAM: ${ram}%`;
  document.getElementById("gpuUsage").innerText = `GPU: ${gpu}%`;
}

// Clock functionality

function updateClock() {
  const now = new Date(); // Get the current time
  const date = new Date();
  let hours = now.getHours(); // Get hours (0-23)
  const minutes = String(now.getMinutes()).padStart(2, '0'); // Format minutes
  const seconds = String(now.getSeconds()).padStart(2, '0'); // Format seconds
  const ampmEl = document.getElementById('ampm');

  if (clock24Hour) {
    document.getElementById('time').textContent = `${String(hours).padStart(2, '0')}:${minutes}:${seconds}`;
    ampmEl.textContent = '';
    ampmEl.style.display = 'none';
  } else {
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    document.getElementById('time').textContent = `${String(hours).padStart(2, '0')}:${minutes}:${seconds}`;
    ampmEl.textContent = ampm;
    ampmEl.style.display = '';
  }

  // Get day, date, month, and year
  let day = date.getDay(); // 0 (Sunday) to 6 (Saturday)
  const currDate = date.getDate();
  const year = date.getFullYear();
  const month = date.getMonth();
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  // Update the full date (separate spans so date gap flex setting works)
  document.getElementById('day-name').textContent = monthNames[month];
  document.getElementById('month-date').textContent = String(currDate);
  document.getElementById('year').textContent = String(year);

  // Adjust the day order to start from Monday
  day = day === 0 ? 6 : day - 1; // Convert Sunday (0) to 6, and shift other days back by 1

  // Get all day elements
  const days = document.querySelectorAll(".day");

  if (showAllDays) {
    // Show all days and highlight the current day
    days.forEach((dayElement, index) => {
      dayElement.style.display = "inline"; // Show all days
      dayElement.style.color = index === day ? "var(--clock1-today-color)" : "var(--clock1-otherdays-color)";
    });
  } else {
    // Show only the current day in the center
    days.forEach((dayElement, index) => {
      if (index === day) {
        dayElement.style.display = "inline"; // Show the current day
        dayElement.style.color = "var(--clock1-today-color)";
      } else {
        dayElement.style.display = "none"; // Hide other days
      }
    });
  }
}

// Example: Toggle between showing all days and only the current day
// showAllDays = false; // Uncomment this line to display only the current day

function startClockTimer() {
  if (clockTimer) {
    clearInterval(clockTimer);
  }
  clockTimer = setInterval(() => {
    if (!wallpaperPaused) {
      updateClock();
    }
  }, 1000);
}

startClockTimer();

function updateWeatherPosition() {
  document.documentElement.style.setProperty("--weather-bottom", `${weatherbottom}px`);
  document.documentElement.style.setProperty("--weather-left", `${weatherLeft}px`);
}

function getWeatherUrl() {
  if (!apiKey) {
    return null;
  }
  if (UseCity) {
    return `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=${units}&appid=${apiKey}`;
  }
  return `https://api.openweathermap.org/data/2.5/weather?lat=${Lat}&lon=${Lon}&units=${units}&appid=${apiKey}`;
}

function showWeatherError(message) {
  document.getElementById("weatherIcon").innerHTML = "";
  document.getElementById("weatherTemp").innerText = "";
  document.getElementById("weatherDescription").innerText = message;
  updateWeatherExtra(null);
}

function updateWeatherExtra(data) {
  const extraEl = document.getElementById("weatherExtra");
  if (!data || (!show_weatherFeelsLike && !show_weatherHumidity && !show_weatherWind)) {
    extraEl.style.display = "none";
    extraEl.innerText = "";
    return;
  }

  const parts = [];
  const tempUnit = units === "imperial" ? "°F" : "°C";
  const windUnit = units === "imperial" ? "mph" : "m/s";

  if (show_weatherFeelsLike && data.main?.feels_like != null) {
    parts.push(`Feels ${Math.round(data.main.feels_like)}${tempUnit}`);
  }
  if (show_weatherHumidity && data.main?.humidity != null) {
    parts.push(`Humidity ${data.main.humidity}%`);
  }
  if (show_weatherWind && data.wind?.speed != null) {
    parts.push(`Wind ${data.wind.speed} ${windUnit}`);
  }

  if (parts.length === 0) {
    extraEl.style.display = "none";
    extraEl.innerText = "";
    return;
  }

  extraEl.style.display = "block";
  extraEl.innerText = parts.join(" · ");
}

// Function to fetch weather data
async function fetchWeather() {
  if (!show_weather) {
    return;
  }

  if (!apiKey || !apiKey.trim()) {
    showWeatherError("Weather: API key required");
    return;
  }

  const weatherUrl = getWeatherUrl();
  if (!weatherUrl) {
    showWeatherError("Weather: invalid location settings");
    return;
  }

  try {
    const response = await fetch(weatherUrl);
    const data = await response.json();

    if (!response.ok || data.cod !== 200) {
      const message = data.message || `HTTP ${response.status}`;
      showWeatherError(`Weather unavailable: ${message}`);
      console.error("Error fetching weather data:", message);
      return;
    }

    const temp = Math.round(data.main.temp);
    const description = data.weather[0].description;
    const iconCode = data.weather[0].icon;
    const tempUnit = units === "imperial" ? "°F" : "°C";

    document.getElementById("weatherTemp").innerText = `${temp}${tempUnit}`;
    document.getElementById("weatherDescription").innerText = description;

    const iconUrl = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
    document.getElementById("weatherIcon").innerHTML = `<img src="${iconUrl}" alt="${description}">`;
    updateWeatherExtra(data);
  } catch (error) {
    showWeatherError("Weather unavailable: network error");
    console.error("Error fetching weather data:", error);
  }
}

function startWeatherRefresh() {
  if (weatherRefreshTimer) {
    clearInterval(weatherRefreshTimer);
  }
  weatherRefreshTimer = setInterval(fetchWeather, update_interval * 1000);
}

function livelySystemInformation(data) {
  const obj = JSON.parse(data);
  const memTotal = obj.TotalRam;
  const memUsed = memTotal - obj.CurrentRamAvail;
  const mempercent = memTotal > 0 ? (memUsed / memTotal) * 100 : 0;
  const cpuUsage = obj.CurrentCpu.toFixed(cpuDecimalnumber);
  const ramUsage = mempercent.toFixed(memDecimalnumber);
  const gpuUsage = obj.CurrentGpu3D.toFixed(gpuDecimalnumber);
  updateSystemUsage(cpuUsage, ramUsage, gpuUsage);

  if (show_network) {
    updateNetworkDisplay(obj.CurrentNetDown, obj.CurrentNetUp);
  }
}

function livelyWallpaperPlaybackChanged(data) {
  const obj = JSON.parse(data);
  wallpaperPaused = !!obj.IsPaused;
  if (wallpaperPaused) {
    document.querySelectorAll(".bg-video").forEach((videoEl) => videoEl.pause());
  } else if (show_animated_background) {
    getBackgroundVideo()?.play().catch(() => {});
  }
}

// Initialize on load
window.onload = () => {
  initializeFonts();
  setIdleMediaState();
  setSize();
  updateStyles();
  updateVisualizerPosition(); // Set initial visualizer position
  fetchWeather();
  startWeatherRefresh();
  toggleVisibility();
  updateWeatherPosition();
  updateClock();
};

// Adjust on resize
window.onresize = () => {
  setSize();
};

// Update styles
function updateStyles() {
  const albumart = document.getElementById("albumart");
  const title = document.getElementById("title");
  const artist = document.getElementById("artist");
  const canvasElement = document.querySelector("canvas");
  const content = document.getElementById("content");
  const systemUsage = document.getElementById("systemUsage");

  content.style.top = `${contentTop}px`;
  content.style.left = `${contentLeft}px`;

  systemUsage.style.top = `${systemUsageTop}px`;
  systemUsage.style.right = `${systemUsageRight}px`;

  // Update CSS custom properties using the variables
  document.documentElement.style.setProperty("--weather-temp-color", weatherTempColor);
  document.documentElement.style.setProperty("--weatherDescription-color", weatherDescriptionColor);
  document.documentElement.style.setProperty("--weather-background", weatherBackground);
  document.documentElement.style.setProperty("--weatherIcon-size", `${weatherIconSize}px`);
  document.documentElement.style.setProperty("--weather-font-size", `${weatherFontSize}px`);
  document.documentElement.style.setProperty("--weather-temp-font-size", `${weatherTempFontSize}px`);
  document.documentElement.style.setProperty("--weather-extra-color", weatherExtraColor);
  document.documentElement.style.setProperty("--weather-extra-font-size", `${weatherExtraFontSize}px`);
  document.documentElement.style.setProperty("--network-bottom", `${networkBottom}px`);
  document.documentElement.style.setProperty("--network-right", `${networkRight}px`);
  document.documentElement.style.setProperty("--network-color", networkColor);
  document.documentElement.style.setProperty("--network-font-size", `${networkFontSize}px`);
  document.documentElement.style.setProperty("--network-background", networkBackground);
  document.documentElement.style.setProperty("--systemUsage-color", systemUsageColor);
  document.documentElement.style.setProperty("--systemUsage-background", systemUsageBackground);
  document.documentElement.style.setProperty("--systemUsage-font-size", `${systemUsageFontSize}px`);
  document.documentElement.style.setProperty("--media-color", mediaColor);
  document.documentElement.style.setProperty("--media-title-color", mediaTitleColor);

  //clock1 properties   
  document.documentElement.style.setProperty("--clock1-time-color", clock1TimeColor);
  document.documentElement.style.setProperty("--clock1-today-color", clock1TodayColor);
  document.documentElement.style.setProperty("--clock1-otherdays-color", clock1OtherDaysColor);
  document.documentElement.style.setProperty("--clock1-date-color", clock1DateColor);
  document.documentElement.style.setProperty("--clock1-time-bottom", `${clock1TimeBottom}px`);
  document.documentElement.style.setProperty("--clock1-time-font-size", `${clock1TimeFontSize}px`);
  document.documentElement.style.setProperty("--clock1-time-gap", `${clock1TimeGap}px`);
  document.documentElement.style.setProperty("--clock1-ampm-font-size", `${clock1AmPmFontSize}px`);
  document.documentElement.style.setProperty("--clock1-days-bottom", `${clock1DaysBottom}px`);
  document.documentElement.style.setProperty("--clock1-days-gap", `${clock1DaysGap}rem`);
  document.documentElement.style.setProperty("--clock1-days-font-size", `${clock1DaysFontSize}px`);
  document.documentElement.style.setProperty("--clock1-date-bottom", `${clock1DateBottom}px`);
  document.documentElement.style.setProperty("--clock1-date-gap", `${clock1DateGap}rem`);
  document.documentElement.style.setProperty("--clock1-date-font-size", `${clock1DateFontSize}px`);
  document.documentElement.style.setProperty("--clock1-left", `${clock1Left}%`);
  document.documentElement.style.setProperty("--clock1-top", `${clock1Top}`);
  document.documentElement.style.setProperty("--clock1-vertical-shift", `calc((100 - ${clock1Top}) * (100vh - 200px) / 100)`);




  // Apply styles
  albumart.style.width = `${albumArtSize}px`;
  albumart.style.height = `${albumArtSize}px`;

  title.style.fontSize = `${titleFontSize}px`;
  artist.style.fontSize = `${artistFontSize}px`;

  canvasElement.style.marginLeft = `${visualizerMargin}px`;

  canvasElement.style.top = `${visualizerTop}px`;


  updateWeatherPosition();
}

function updateVisualizerPosition() {
  const canvasElement = document.querySelector("canvas");
  canvasElement.style.left = `${visualizerLeft}px`;
  canvasElement.style.top = `${visualizerTop}px`;
}

// Handle property changes
function livelyPropertyListener(name, val) {
  switch (name) {
    case "lineColor": {
      const color = hexToRgb(val);
      if (color) linesColor = `rgb(${color.r},${color.g},${color.b})`;
      break;
    }
    case "backgroundColor": {
      const bgColor = hexToRgb(val);
      if (bgColor) backgroundColor = `rgba(${bgColor.r},${bgColor.g},${bgColor.b}, 0.45)`;
      break;
    }
    case "square":
      square = val;
      break;
    case "visualizerGlow":
      visualizerGlow = val;
      break;
    case "contentTop":
      contentTop = val;
      updateStyles();
      break;
    case "contentLeft":
      contentLeft = val;
      updateStyles();
      break;
    case "visualizerWidth":
      visualizerWidth = val; // Set visualizer width
      setSize();
      break;
    case "visualizerHeight":
      visualizerHeight = val; // Set visualizer height
      setSize();
      break;
    case "albumArtSize":
      albumArtSize = val; // Set album art size
      updateStyles();
      break;
    case "titleFontSize":
      titleFontSize = val; // Set title font size
      updateStyles();
      break;
    case "artistFontSize":
      artistFontSize = val; // Set artist font size
      updateStyles();
      break;
    case "songNameLimit":
      songNameLimit = val; // Set song name character limit
      break;
    case "visualizerMargin":
      visualizerMargin = val; // Set space between song data and visualizer
      updateStyles();
      break;
    case "visualizerLeft":
      visualizerLeft = val; // Set horizontal position in pixels
      updateVisualizerPosition();
      break;
    case "visualizerTop":
      visualizerTop = val; // Set vertical position in pixels
      updateVisualizerPosition();
      break;
    case "BackgroundSource":
      BackgroundSource = val;
      changeVideoSource(BackgroundSource);
      break;
    case "cpuDecimalnumber":
      cpuDecimalnumber = val;
      break;
    case "gpuDecimalnumber":
      gpuDecimalnumber = val;
      break;
    case "memDecimalnumber":
      memDecimalnumber = val;
      break;
    case "OpenWeather_API":
      apiKey = val;
      fetchWeather();
      break;
    case "OpenWeather_city":
      city = val;
      fetchWeather();
      break;
    case "OpenWeather_units":
      units = val === 1 ? "imperial" : "metric";
      fetchWeather();
      break;
    case "update_interval":
      update_interval = val;
      startWeatherRefresh();
      break;
    case "OpenWeather_UseCity":
      UseCity = val;
      fetchWeather();
      break;
    case "OpenWeather_Lat":
      Lat = parseFloat(val) || Lat;
      fetchWeather();
      break;
    case "OpenWeather_Lon":
      Lon = parseFloat(val) || Lon;
      fetchWeather();
      break;
    case "show_visualizer":
      show_visualizer = val;
      toggleVisibility();
      break;
    case "weatherbottom":
      weatherbottom = val; // Update top position
      updateWeatherPosition(); // Apply new position
      break;
    case "weatherLeft":
      weatherLeft = val; // Update left position
      updateWeatherPosition(); // Apply new position
      break;
    case "weatherTempColor":
      weatherTempColor = val;
      updateStyles();
      break;
    case "systemUsageTop":
      systemUsageTop = val;
      updateStyles();
      break;
    case "systemUsageRight":
      systemUsageRight = val;
      updateStyles();
      break;
    case "weatherDescriptionColor":
      weatherDescriptionColor = val;
      updateStyles();
      break;
    case "weatherBackground": {
      const wbgColor = hexToRgb(val);
      if (wbgColor) weatherBackground = `rgba(${wbgColor.r},${wbgColor.g},${wbgColor.b}, 0.7)`;
      updateStyles();
      break;
    }
    case "weatherIconSize":
      weatherIconSize = val;
      updateStyles();
      break;
    case "weatherFontSize":
      weatherFontSize = val;
      updateStyles();
      break;
    case "weatherTempFontSize":
      weatherTempFontSize = val;
      updateStyles();
      break;
    case "songTitleFont":
      applyCustomFont("mediaTitleFont", val);
      break;
    case "songArtistFont":
      applyCustomFont("mediaArtistFont", val);
      break;
    case "mediaTitleFont":
      applyCustomFont("mediaTitleFont", val);
      break;
    case "mediaArtistFont":
      applyCustomFont("mediaArtistFont", val);
      break;
    case "weatherFont":
    case "systemUsageFont":
      applyCustomFont(name, val);
      break;
    case "clockFont":
      applyClockFont(resolveFontSelection(val, "clock1TimeFont"));
      break;
    case "clock1TimeFont":
    case "clock1DaysFont":
    case "clock1DateFont":
      applyClockFont(resolveFontSelection(val, name));
      break;
    case "systemUsageColor":
      systemUsageColor = val;
      updateStyles();
      break;
    case "systemUsageBackground": {
      const subgColor = hexToRgb(val);
      if (subgColor) systemUsageBackground = `rgba(${subgColor.r},${subgColor.g},${subgColor.b}, 0.7)`;
      updateStyles();
      break;
    }
    case "systemUsageFontSize":
      systemUsageFontSize = val;
      updateStyles();
      break;
    case "mediaColor":
      mediaColor = val;
      updateStyles();
      break;
    case "mediaTitleColor":
      mediaTitleColor = val;
      updateStyles();
      break;
    case "show_weather":
      show_weather = val;
      toggleVisibility();
      break;
    case "show_cover":
      show_cover = val;
      toggleVisibility();
      break;
    case "show_song_name":
      show_song_name = val;
      toggleVisibility();
      break;
    case "show_singer":
      show_singer = val;
      toggleVisibility();
      break;
    case "show_sys_info":
      show_sys_info = val;
      toggleVisibility();
      break;
    case "show_cpu":
      show_cpu = val;
      toggleVisibility();
      break;
    case "show_gpu":
      show_gpu = val;
      toggleVisibility();
      break;
    case "show_mem":
      show_mem = val;
      toggleVisibility();
      break;
    case "show_animated_background":
      show_animated_background = val;
      toggleVisibility();
      break;
    case "animated_background":
      BackgroundSource = val;
      changeVideoSource(BackgroundSource);
      break;
    case "clock1TimeColor":
      clock1TimeColor = val;
      updateStyles();
      break;
    case "clock1TodayColor":
      clock1TodayColor = val;
      updateStyles();
      break;
    case "clock1OtherDaysColor":
      clock1OtherDaysColor = val;
      updateStyles();
      break;
    case "clock1DateColor":
      clock1DateColor = val;
      updateStyles();
      break;
    case "clock1TimeBottom":
      clock1TimeBottom = val;
      updateStyles();
      break;
    case "clock1TimeFontSize":
      clock1TimeFontSize = val;
      updateStyles();
      break;
    case "clock1TimeGap":
      clock1TimeGap = val;
      updateStyles();
      break;
    case "clock1AmPmFontSize":
      clock1AmPmFontSize = val;
      updateStyles();
      break;
    case "clock1DaysBottom":
      clock1DaysBottom = val;
      updateStyles();
      break;
    case "clock1DaysGap":
      clock1DaysGap = val;
      updateStyles();
      break;
    case "clock1DaysFontSize":
      clock1DaysFontSize = val;
      updateStyles();
      break;
    case "clock1DateBottom":
      clock1DateBottom = val;
      updateStyles();
      break;
    case "clock1DateGap":
      clock1DateGap = val;
      updateStyles();
      break;
    case "clock1DateFontSize":
      clock1DateFontSize = val;
      updateStyles();
      break;
    case "clock1Left":
      clock1Left = val;
      updateStyles();
      break;
    case "clock1Top":
      clock1Top = val;
      updateStyles();
      break;
    case "showAllDays":
      showAllDays = val;
      updateClock();
      break;
    case "show_clock1":
      show_clock1 = val;
      toggleVisibility();
      break;
    case "clock24Hour":
      clock24Hour = val;
      updateClock();
      break;
    case "show_weatherFeelsLike":
      show_weatherFeelsLike = val;
      fetchWeather();
      break;
    case "show_weatherHumidity":
      show_weatherHumidity = val;
      fetchWeather();
      break;
    case "show_weatherWind":
      show_weatherWind = val;
      fetchWeather();
      break;
    case "weatherExtraColor":
      weatherExtraColor = val;
      updateStyles();
      break;
    case "weatherExtraFontSize":
      weatherExtraFontSize = val;
      updateStyles();
      break;
    case "show_network":
      show_network = val;
      toggleVisibility();
      break;
    case "networkBottom":
      networkBottom = val;
      updateStyles();
      break;
    case "networkRight":
      networkRight = val;
      updateStyles();
      break;
    case "networkColor":
      networkColor = val;
      updateStyles();
      break;
    case "networkFontSize":
      networkFontSize = val;
      updateStyles();
      break;
    case "networkBackground": {
      const netBgColor = hexToRgb(val);
      if (netBgColor) networkBackground = `rgba(${netBgColor.r},${netBgColor.g},${netBgColor.b}, 0.7)`;
      updateStyles();
      break;
    }
    case "networkSpeedUnit":
      networkUseMegabits = val === 0;
      break;
    case "updateStaticWallpaper":
      BackgroundImageSource = val;
      updateStaticWallpaper(BackgroundImageSource);
      break;
  }
}



// Handle audio data
function livelyAudioListener(audioArray) {
  if (wallpaperPaused || !show_visualizer) {
    return;
  }

  let maxVal = 1;
  for (let x of audioArray) {
    if (x > maxVal) maxVal = x;
  }

  const offSet = visualizerWidth / audioArray.length;
  ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas

  ctx.beginPath();
  ctx.lineJoin = "round";
  ctx.moveTo(0, visualizerHeight / 2);
  let posInLine = -1;
  for (let x = 0; x < audioArray.length; x++) {
    posInLine++;
    ctx.lineTo(
      offSet * posInLine,
      visualizerHeight / 2 - (audioArray[x] / maxVal) * (visualizerHeight / 2)
    );
    if (square)
      ctx.lineTo(
        offSet * (posInLine + 1),
        visualizerHeight / 2 - (audioArray[x] / maxVal) * (visualizerHeight / 2)
      );
  }
  ctx.lineTo(offSet * (posInLine + (square ? 1 : 0)), visualizerHeight / 2);
  ctx.lineTo(offSet * (posInLine + (square ? 4 : 3)), visualizerHeight / 2);

  if (visualizerGlow) {
    ctx.shadowBlur = 14;
    ctx.shadowColor = linesColor;
  } else {
    ctx.shadowBlur = 0;
    ctx.shadowColor = "transparent";
  }

  ctx.fillStyle = backgroundColor;
  ctx.fill();
  renderLine(linesColor);

  ctx.shadowBlur = 0;
  ctx.shadowColor = "transparent";
}

// Render the visualizer line
function renderLine(color) {
  ctx.lineWidth = 2;
  ctx.strokeStyle = color;
  ctx.stroke();
}

// Convert hex to RGB
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16),
    }
    : null;
}


// Function to update song metadata
function livelyCurrentTrack(data) {
  const obj = JSON.parse(data);
  if (isTrackEmpty(obj)) {
    setIdleMediaState();
    return;
  }

  let title = (obj.Title || "").trim();
  if (!title) {
    title = IDLE_MEDIA_TITLE;
  } else if (title.length > songNameLimit) {
    title = title.substring(0, songNameLimit) + "...";
  }

  document.getElementById("title").innerText = title;
  document.getElementById("artist").innerText = (obj.Artist || "").trim();

  if (obj.Thumbnail != null && obj.Thumbnail !== "") {
    document.getElementById("albumart").src = "data:image/png;base64, " + obj.Thumbnail;
  } else {
    document.getElementById("albumart").src = DEFAULT_ALBUM_ART;
  }
}