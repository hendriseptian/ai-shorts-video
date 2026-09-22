const CONFIG = {
    storageKey: "miko_ai_shorts_worker_url",
    defaultWorkerUrl: "",
    endpoints: {
        health: "/health",
        options: "/story/options",
        generate: "/story/generate",
        pipeline: "/pipeline/status"
    }
};

const FALLBACK_OPTIONS = {
    categories: [
        "ADVENTURE", "FUNNY", "FRIENDSHIP", "DISCOVERY", "LEARNING",
        "HELPING_OTHERS", "ANIMAL_FRIENDS", "NATURE", "SIMPLE_PROBLEM_SOLVING",
        "EVERYDAY_LIFE", "IMAGINATION", "MUSIC_AND_PLAY"
    ],
    core_values: [
        "KINDNESS", "SHARING", "HONESTY", "COURAGE", "PATIENCE", "CURIOSITY",
        "HELPING_OTHERS", "RESPECT", "CLEANLINESS", "TEAMWORK",
        "PROBLEM_SOLVING", "LEARNING_FROM_MISTAKES", "RESPONSIBILITY",
        "EMPATHY", "GRATITUDE", "SELF_CONFIDENCE", "TAKING_CARE_OF_NATURE"
    ],
    locations: [
        { id: "MIKOS_HOUSE", name: "Miko's House" },
        { id: "RAINBOW_PARK", name: "Rainbow Park" },
        { id: "SUNNY_FOREST", name: "Sunny Forest" },
        { id: "SUNNY_BEACH", name: "Sunny Beach" },
        { id: "LITTLE_SCHOOL", name: "Little School" },
        { id: "PLAYGROUND", name: "Playground" },
        { id: "FLOWER_GARDEN", name: "Flower Garden" },
        { id: "LITTLE_FARM", name: "Little Farm" },
        { id: "CLOUD_HILL", name: "Cloud Hill" },
        { id: "MIKOS_NIGHT_GARDEN", name: "Miko's Night Garden" }
    ],
    supporting_characters: [
        { id: "LULU", name: "Lulu — Rabbit" },
        { id: "BOBI", name: "Bobi — Bear" },
        { id: "KIKI", name: "Kiki — Bird" },
        { id: "TOTO", name: "Toto — Turtle" },
        { id: "NANA", name: "Nana — Squirrel" }
    ],
    durations: [30, 45, 60, 90]
};

const $ = (selector) => document.querySelector(selector);

const els = {
    form: $("#storyForm"),
    category: $("#category"),
    coreValue: $("#coreValue"),
    location: $("#location"),
    supportingCharacter: $("#supportingCharacter"),
    language: $("#language"),
    mainObject: $("#mainObject"),
    duration: $("#duration"),
    episodeId: $("#episodeId"),
    generateBtn: $("#generateBtn"),
    errorBox: $("#errorBox"),
    emptyState: $("#emptyState"),
    loadingState: $("#loadingState"),
    storyResult: $("#storyResult"),
    storyCategory: $("#storyCategory"),
    storyTitle: $("#storyTitle"),
    storyDuration: $("#storyDuration"),
    storyHook: $("#storyHook"),
    storyLesson: $("#storyLesson"),
    sceneList: $("#sceneList"),
    sceneTotal: $("#sceneTotal"),
    voiceScript: $("#voiceScript"),
    youtubeTitle: $("#youtubeTitle"),
    youtubeDescription: $("#youtubeDescription"),
    youtubeHashtags: $("#youtubeHashtags"),
    copyBtn: $("#copyBtn"),
    downloadBtn: $("#downloadBtn"),
    apiStatus: $("#apiStatus"),
    apiStatusText: $("#apiStatusText"),
    settingsBtn: $("#settingsBtn"),
    settingsModal: $("#settingsModal"),
    workerUrl: $("#workerUrl"),
    saveSettingsBtn: $("#saveSettingsBtn"),
    testApiBtn: $("#testApiBtn"),
    settingsStatus: $("#settingsStatus")
};

let lastStory = null;

function normalizeWorkerUrl(value) {
    let url = String(value ?? "").trim();

    if (!url) return "";

    // Allow either:
    // ai-shorts-video.example.workers.dev
    // https://ai-shorts-video.example.workers.dev
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = "https://" + url;
    }

    while (url.endsWith("/")) {
        url = url.slice(0, -1);
    }

    return url;
}

function getWorkerUrl() {
    const saved = localStorage.getItem(CONFIG.storageKey);
    return normalizeWorkerUrl(saved ?? CONFIG.defaultWorkerUrl);
}

function apiUrl(path) {
    const base = getWorkerUrl();
    return `${base}${path}`;
}

function setApiStatus(state, text) {
    els.apiStatus.className = `status-pill status-${state}`;
    els.apiStatusText.textContent = text;
}

function showError(message) {
    els.errorBox.textContent = message;
    els.errorBox.classList.remove("hidden");
}

function clearError() {
    els.errorBox.textContent = "";
    els.errorBox.classList.add("hidden");
}

function setLoading(isLoading) {
    els.generateBtn.disabled = isLoading;

    if (isLoading) {
        els.emptyState.classList.add("hidden");
        els.storyResult.classList.add("hidden");
        els.loadingState.classList.remove("hidden");
        els.generateBtn.querySelector("span:last-child").textContent = "GENERATING...";
    } else {
        els.loadingState.classList.add("hidden");
        els.generateBtn.querySelector("span:last-child").textContent = "GENERATE STORY";
    }
}

async function fetchJson(path, options = {}) {
    const method = String(options.method || "GET").toUpperCase();
    const headers = {
        ...(options.headers || {})
    };

    // Do NOT send Content-Type: application/json on GET requests.
    // From a local file (origin: null), that header can trigger a CORS
    // preflight before the Worker receives the request.
    if (method !== "GET" && options.body !== undefined) {
        headers["Content-Type"] = "application/json";
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    let response;
    try {
        response = await fetch(apiUrl(path), {
            ...options,
            method,
            headers,
            signal: controller.signal
        });
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error("API request timed out after 10 seconds.");
        }
        throw new Error(`Cannot reach Worker API: ${error.message}`);
    } finally {
        clearTimeout(timeoutId);
    }

    let payload = null;
    try {
        payload = await response.json();
    } catch {
        throw new Error(`API returned HTTP ${response.status} without valid JSON.`);
    }

    if (!response.ok) {
        throw new Error(payload?.detail || payload?.error || `API error: HTTP ${response.status}`);
    }

    return payload;
}

function optionId(item) {
    if (typeof item === "string") return item;
    return item?.id ?? item?.value ?? item?.name ?? "";
}

function optionLabel(item) {
    if (typeof item === "string") {
        return item.replaceAll("_", " ");
    }
    return item?.name ?? item?.id ?? item?.value ?? "";
}

function populateSelect(select, items, placeholder = null) {
    select.innerHTML = "";

    if (placeholder !== null) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = placeholder;
        select.appendChild(option);
    }

    (items || []).forEach((item) => {
        const option = document.createElement("option");
        option.value = optionId(item);
        option.textContent = optionLabel(item);
        select.appendChild(option);
    });
}

function renderOptions(data) {
    const source = data && typeof data === "object" ? data : FALLBACK_OPTIONS;

    populateSelect(els.category, source.categories || FALLBACK_OPTIONS.categories);
    populateSelect(els.coreValue, source.core_values || FALLBACK_OPTIONS.core_values);
    populateSelect(els.location, source.locations || FALLBACK_OPTIONS.locations);
    populateSelect(
        els.supportingCharacter,
        source.supporting_characters || FALLBACK_OPTIONS.supporting_characters,
        "Miko only"
    );

    const durations = source.durations?.length
        ? source.durations
        : FALLBACK_OPTIONS.durations;

    populateSelect(
        els.duration,
        durations.map((value) => ({ id: value, name: `${value} seconds` }))
    );

    if (els.category.options.length) els.category.selectedIndex = 0;
    if (els.coreValue.options.length) els.coreValue.selectedIndex = 0;
    if (els.location.options.length) els.location.selectedIndex = 0;
    if (els.duration.options.length) {
        const sixty = [...els.duration.options].findIndex(o => o.value === "60");
        els.duration.selectedIndex = sixty >= 0 ? sixty : 0;
    }
}

async function loadOptions() {
    // Render immediately. This makes the form usable even when index.html
    // is opened directly from file:// and the browser blocks cross-origin fetch.
    renderOptions(FALLBACK_OPTIONS);

    try {
        const data = await fetchJson(CONFIG.endpoints.options);
        renderOptions(data);
        setApiStatus("ok", "API connected");
        return true;
    } catch (error) {
        console.warn("Could not load /story/options; using built-in options.", error);
        // Keep the dropdowns populated. The user can still test generation.
        setApiStatus("error", "Using local options");
        return false;
    }
}

async function checkHealth() {
    try {
        await fetchJson(CONFIG.endpoints.health);
        setApiStatus("ok", "API online");
        return true;
    } catch (error) {
        setApiStatus("error", "API offline");
        console.warn(error);
        return false;
    }
}

function collectForm() {
    return {
        category: els.category.value || null,
        core_value: els.coreValue.value || null,
        location: els.location.value || null,
        supporting_character: els.supportingCharacter.value || null,
        main_object: els.mainObject.value.trim() || null,
        duration: Number(els.duration.value || 60),
        language: els.language.value || "id",
        episode_id: els.episodeId.value.trim() || null
    };
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderStory(story) {
    lastStory = story;

    const episode = story.episode || {};
    const scenes = Array.isArray(story.scenes) ? story.scenes : [];
    const youtube = story.youtube || {};

    els.emptyState.classList.add("hidden");
    els.loadingState.classList.add("hidden");
    els.storyResult.classList.remove("hidden");

    els.storyCategory.textContent = String(episode.category || "STORY").replaceAll("_", " ");
    els.storyTitle.textContent = story.title || "Untitled Story";
    els.storyDuration.textContent = `${episode.duration_target || 0} sec`;
    els.storyHook.textContent = story.hook || "—";
    els.storyLesson.textContent = story.lesson || "—";
    els.sceneTotal.textContent = `${scenes.length} scenes`;

    els.sceneList.innerHTML = scenes.map((scene, index) => `
        <article class="scene-card">
            <div class="scene-number">${String(scene.scene_number ?? index + 1).padStart(2, "0")}</div>
            <div class="scene-main">
                <h5>${escapeHtml(scene.phase || `Scene ${index + 1}`)}</h5>
                <p>${escapeHtml(scene.story || scene.action || "")}</p>
            </div>
            <div class="scene-meta">
                <div class="scene-phase">${escapeHtml(scene.emotion || "—")}</div>
                <span class="scene-duration">${escapeHtml(scene.duration || 0)} sec</span>
            </div>
            <div class="scene-dialogue">${escapeHtml(scene.dialogue || "No dialogue")}</div>
        </article>
    `).join("");

    els.voiceScript.textContent = story.voice_script || "—";
    els.youtubeTitle.textContent = youtube.title || story.title || "—";
    els.youtubeDescription.textContent = youtube.description || "—";

    els.youtubeHashtags.innerHTML = (youtube.hashtags || [])
        .map(tag => `<span class="hashtag">${escapeHtml(tag)}</span>`)
        .join("");

    els.copyBtn.disabled = false;
    els.downloadBtn.disabled = false;
}

async function generateStory(event) {
    event.preventDefault();
    clearError();

    const payload = collectForm();
    setLoading(true);

    try {
        const result = await fetchJson(CONFIG.endpoints.generate, {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (!result.success) {
            throw new Error(result.error || "Story Engine returned an unknown error.");
        }

        renderStory(result.data);
        setApiStatus("ok", "Story generated");
    } catch (error) {
        console.error(error);
        els.loadingState.classList.add("hidden");
        els.emptyState.classList.remove("hidden");
        showError(error.message || "Failed to generate story.");
        setApiStatus("error", "Generation failed");
    } finally {
        setLoading(false);
    }
}

async function copyJson() {
    if (!lastStory) return;

    try {
        await navigator.clipboard.writeText(JSON.stringify(lastStory, null, 2));
        const original = els.copyBtn.textContent;
        els.copyBtn.textContent = "Copied!";
        setTimeout(() => { els.copyBtn.textContent = original; }, 1200);
    } catch (error) {
        console.error(error);
        showError("Clipboard access is unavailable in this browser.");
    }
}

function downloadStory() {
    if (!lastStory) return;

    const safeTitle = String(lastStory.title || "miko-story")
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-|-$/g, "")
        .toLowerCase();

    const blob = new Blob(
        [JSON.stringify(lastStory, null, 2)],
        { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${safeTitle || "miko-story"}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
}

function openSettings() {
    els.workerUrl.value = getWorkerUrl();
    els.settingsStatus.textContent = "";
    els.settingsModal.classList.remove("hidden");
}

function closeSettings() {
    els.settingsModal.classList.add("hidden");
}

async function saveSettings() {
    const value = normalizeWorkerUrl(els.workerUrl.value);

    if (value) {
        try {
            const parsed = new URL(value);

            if (!["http:", "https:"].includes(parsed.protocol)) {
                throw new Error("Unsupported protocol");
            }
        } catch {
            els.settingsStatus.textContent = "Please enter a valid Worker URL.";
            return;
        }
    }

    localStorage.setItem(CONFIG.storageKey, value);
    els.workerUrl.value = value;
    els.settingsStatus.textContent = "Saved. Testing connection...";

    const ok = await checkHealth();

    if (ok) {
        els.settingsStatus.textContent = "Connection successful.";
        await loadOptions();
    } else {
        els.settingsStatus.textContent = "Saved, but the Worker could not be reached.";
    }
}

async function testApi() {
    els.settingsStatus.textContent = "Testing...";
    const ok = await checkHealth();
    els.settingsStatus.textContent = ok
        ? "Worker connection successful."
        : "Worker connection failed. Check URL and CORS.";
}

function bindEvents() {
    els.form.addEventListener("submit", generateStory);
    els.copyBtn.addEventListener("click", copyJson);
    els.downloadBtn.addEventListener("click", downloadStory);
    els.settingsBtn.addEventListener("click", openSettings);
    els.saveSettingsBtn.addEventListener("click", saveSettings);
    els.testApiBtn.addEventListener("click", testApi);

    document.querySelectorAll("[data-close-settings]").forEach((element) => {
        element.addEventListener("click", closeSettings);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeSettings();
    });
}

async function init() {
    bindEvents();

    if (!localStorage.getItem(CONFIG.storageKey) && CONFIG.defaultWorkerUrl) {
        localStorage.setItem(CONFIG.storageKey, CONFIG.defaultWorkerUrl);
    }

    // Populate the UI immediately from the embedded Story Bible options.
    renderOptions(FALLBACK_OPTIONS);

    // Health check is informational; it must never prevent the form from loading.
    const ok = await checkHealth();

    if (ok) {
        await loadOptions();
    } else {
        setApiStatus("error", "API offline");
    }
}


init();
