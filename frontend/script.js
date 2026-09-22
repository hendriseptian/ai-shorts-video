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

function getWorkerUrl() {
    const saved = localStorage.getItem(CONFIG.storageKey);
    return (saved ?? CONFIG.defaultWorkerUrl).trim().replace(/\/+$/, "");
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
    const response = await fetch(apiUrl(path), {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

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

async function loadOptions() {
    setApiStatus("checking", "Loading options...");

    const data = await fetchJson(CONFIG.endpoints.options);

    populateSelect(els.category, data.categories || []);
    populateSelect(els.coreValue, data.core_values || []);
    populateSelect(els.location, data.locations || []);
    populateSelect(els.supportingCharacter, data.supporting_characters || [], "Miko only");

    const durations = data.durations?.length ? data.durations : [30, 45, 60, 90];
    populateSelect(els.duration, durations.map((value) => ({
        id: value,
        name: `${value} seconds`
    })));

    if (els.category.options.length) els.category.selectedIndex = 0;
    if (els.coreValue.options.length) els.coreValue.selectedIndex = 0;
    if (els.location.options.length) els.location.selectedIndex = 0;

    setApiStatus("ok", "API connected");
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
    const value = els.workerUrl.value.trim().replace(/\/+$/, "");

    if (value) {
        try {
            new URL(value);
        } catch {
            els.settingsStatus.textContent = "Please enter a valid URL.";
            return;
        }
    }

    localStorage.setItem(CONFIG.storageKey, value);
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

    const ok = await checkHealth();

    if (ok) {
        try {
            await loadOptions();
        } catch (error) {
            console.error(error);
            showError(`API is reachable, but options could not be loaded: ${error.message}`);
        }
    } else {
        openSettings();
    }
}

init();
