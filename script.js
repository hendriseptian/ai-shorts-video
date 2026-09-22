const CONFIG = {
    storageKey: "miko_ai_shorts_worker_url",
    defaultWorkerUrl: "https://ai-shorts-video.hendriseptian25.workers.dev",
    endpoints: {
        health: "/health",
        options: "/story/options",
        generate: "/story/generate",
        imagePrompts: "/story/image-prompts",
        imagesGenerate: "/images/generate",
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
let lastVisualPrompts = null;

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
    return normalizeWorkerUrl(saved || CONFIG.defaultWorkerUrl);
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
    const timeoutMs = Number(options.timeoutMs || 10000);
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

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

async function generateVisualPrompts(story) {
    const episode = story?.episode || {};

    return await fetchJson(CONFIG.endpoints.imagePrompts, {
        method: "POST",
        body: JSON.stringify({
            story,
            episode_id: episode.episode_id || null,
            language: episode.language || "id"
        })
    });
}

function ensureVisualPromptStyles() {
    if (document.getElementById("visualPromptDynamicStyles")) return;

    const style = document.createElement("style");
    style.id = "visualPromptDynamicStyles";
    style.textContent = `
        .visual-prompts-panel {
            margin-top: 18px;
            border: 1px solid rgba(139, 92, 246, .28);
            border-radius: 18px;
            padding: 18px;
            background: rgba(15, 23, 42, .72);
        }

        .visual-prompts-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }

        .visual-prompts-header h3 {
            margin: 0;
            font-size: 16px;
        }

        .visual-prompts-header p {
            margin: 4px 0 0;
            opacity: .65;
            font-size: 12px;
        }

        .visual-prompts-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .visual-prompts-actions button,
        .visual-prompt-copy {
            border: 1px solid rgba(255,255,255,.1);
            background: rgba(255,255,255,.05);
            color: inherit;
            border-radius: 9px;
            padding: 7px 10px;
            cursor: pointer;
            font-size: 11px;
        }

        .visual-prompts-actions button:hover,
        .visual-prompt-copy:hover {
            background: rgba(139,92,246,.18);
        }

        .visual-prompt-card {
            border: 1px solid rgba(255,255,255,.07);
            border-radius: 14px;
            padding: 14px;
            margin-top: 10px;
            background: rgba(2, 6, 23, .42);
        }

        .visual-prompt-card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }

        .visual-prompt-number {
            font-weight: 700;
            font-size: 12px;
        }

        .visual-prompt-meta {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            opacity: .7;
            font-size: 10px;
        }

        .visual-prompt-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: .08em;
            opacity: .55;
            margin: 10px 0 5px;
        }

        .visual-prompt-text {
            white-space: pre-wrap;
            line-height: 1.55;
            font-size: 12px;
            color: rgba(255,255,255,.86);
        }

        .visual-prompt-negative {
            color: rgba(255,255,255,.58);
        }

        .visual-prompt-status {
            font-size: 11px;
            opacity: .7;
            margin-top: 10px;
        }
    `;
    document.head.appendChild(style);
}

function renderVisualPrompts(result) {
    lastVisualPrompts = result;

    const scenes = Array.isArray(result?.prompts) ? result.prompts : [];
    if (!scenes.length) return;

    ensureVisualPromptStyles();

    let panel = document.getElementById("visualPromptsPanel");

    if (!panel) {
        panel = document.createElement("section");
        panel.id = "visualPromptsPanel";
        panel.className = "visual-prompts-panel";

        const anchor = els.sceneList?.closest("section, .card, .panel") || els.sceneList;
        if (anchor?.parentNode) {
            anchor.parentNode.insertBefore(panel, anchor.nextSibling);
        } else if (els.storyResult) {
            els.storyResult.appendChild(panel);
        }
    }

    panel.innerHTML = `
        <div class="visual-prompts-header">
            <div>
                <h3>🎨 Visual Prompts</h3>
                <p>${scenes.length} scene image prompts · 9:16 · 1080×1920</p>
            </div>
            <div class="visual-prompts-actions">
                <button type="button" id="generateAllMikoImages" class="generate-all-images-v4">🐱 Generate All Images</button>
                <button type="button" id="copyAllVisualPrompts">Copy All</button>
                <button type="button" id="downloadVisualPrompts">Download</button>
            </div>
        </div>

        <div id="visualPromptList">
            ${scenes.map((item, index) => `
                <article class="visual-prompt-card">
                    <div class="visual-prompt-card-head">
                        <div class="visual-prompt-number">
                            SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}
                        </div>
                        <div class="visual-prompts-actions">
                            <button
                                type="button"
                                class="visual-prompt-copy"
                                data-copy-visual="${index}"
                            >Copy Prompt</button>
                        </div>
                    </div>

                    <div class="visual-prompt-meta">
                        <span>${escapeHtml(item.aspect_ratio || "9:16")}</span>
                        <span>•</span>
                        <span>${escapeHtml(item.resolution || "1080x1920")}</span>
                        <span>•</span>
                        <span>${escapeHtml(item.world_lock || "Miko World")}</span>
                    </div>

                    <div class="visual-prompt-label">Image Prompt</div>
                    <div class="visual-prompt-text">${escapeHtml(item.prompt || "—")}</div>

                    <div class="visual-prompt-label">Negative Prompt</div>
                    <div class="visual-prompt-text visual-prompt-negative">${escapeHtml(item.negative_prompt || "—")}</div>
                </article>
            `).join("")}
        </div>

        <div class="visual-prompt-status">
            Image generation is not connected yet. These prompts are ready for the next provider stage.
        </div>
    `;

    panel.querySelectorAll("[data-copy-visual]").forEach((button) => {
        button.addEventListener("click", async () => {
            const index = Number(button.dataset.copyVisual);
            const item = scenes[index];
            if (!item) return;

            const content = [
                `SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}`,
                "",
                "IMAGE PROMPT:",
                item.prompt || "",
                "",
                "NEGATIVE PROMPT:",
                item.negative_prompt || ""
            ].join("\\n");

            try {
                await navigator.clipboard.writeText(content);
                const original = button.textContent;
                button.textContent = "Copied!";
                setTimeout(() => { button.textContent = original; }, 1000);
            } catch (error) {
                console.error(error);
                showError("Clipboard access is unavailable in this browser.");
            }
        });
    });

    panel.querySelector("#generateAllMikoImages")?.addEventListener("click", async () => {
        const button = panel.querySelector("#generateAllMikoImages");
        if (!button || button.disabled) return;
        await generateAllMikoImagesV4(scenes, panel);
    });

    panel.querySelector("#copyAllVisualPrompts")?.addEventListener("click", async () => {
        const content = scenes.map((item, index) => [
            `SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}`,
            "",
            "IMAGE PROMPT:",
            item.prompt || "",
            "",
            "NEGATIVE PROMPT:",
            item.negative_prompt || "",
            "",
            "----------------------------------------",
            ""
        ].join("\\n")).join("\\n");

        try {
            await navigator.clipboard.writeText(content);
            const button = panel.querySelector("#copyAllVisualPrompts");
            const original = button.textContent;
            button.textContent = "Copied!";
            setTimeout(() => { button.textContent = original; }, 1000);
        } catch (error) {
            console.error(error);
            showError("Clipboard access is unavailable in this browser.");
        }
    });

    panel.querySelector("#downloadVisualPrompts")?.addEventListener("click", () => {
        const blob = new Blob(
            [JSON.stringify(result, null, 2)],
            { type: "application/json" }
        );

        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "miko-visual-prompts.json";
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    });
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
    if (!select) {
        console.warn("populateSelect: target select not found");
        return;
    }

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

    if (!els.category || !els.coreValue || !els.location || !els.supportingCharacter || !els.duration) {
        console.warn("renderOptions: Story Setup select elements are not ready yet.");
        return false;
    }

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

    return true;
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

        // Generate visual prompts from the same story.
        // Story generation remains successful even if the prompt stage fails.
        try {
            const visualResult = await generateVisualPrompts(result.data);

            if (!visualResult?.success) {
                throw new Error(
                    visualResult?.error || "Image prompt engine returned an unknown error."
                );
            }

            renderVisualPromptsV4(visualResult);
            setApiStatus("ok", "Story + visual prompts ready");
        } catch (promptError) {
            console.error("Visual prompt generation failed:", promptError);
            showError(
                `Story generated, but visual prompts failed: ${promptError.message}`
            );
            setApiStatus("error", "Story ready / prompts failed");
        }
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
    const value = normalizeWorkerUrl(els.workerUrl.value) || CONFIG.defaultWorkerUrl;

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
    // IMPORTANT: populate Story Setup before optional UI patches.
    // This prevents the Miko reference panel from blocking dropdown setup.
    try {
        renderOptions(FALLBACK_OPTIONS);
    } catch (error) {
        console.error("Initial Story Setup render failed:", error);
    }

    try {
        bindEvents();
    } catch (error) {
        console.error("Event binding failed:", error);
    }

    try {
        installMikoReferenceUIV4();
    } catch (error) {
        console.error("Miko reference UI failed:", error);
    }

    if (!localStorage.getItem(CONFIG.storageKey) && CONFIG.defaultWorkerUrl) {
        localStorage.setItem(CONFIG.storageKey, CONFIG.defaultWorkerUrl);
    }

    // Re-render after all UI patches in case the page was initialized late.
    renderOptions(FALLBACK_OPTIONS);

    const ok = await checkHealth();

    if (ok) {
        await loadOptions();
    } else {
        // Keep local Story Bible options available even when Worker is offline.
        renderOptions(FALLBACK_OPTIONS);
        setApiStatus("error", "API offline / local options ready");
    }
}


if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}

/* ============================================================
   MIKO CHARACTER CONSISTENCY + IMAGE GENERATION PATCH V4
   ============================================================
   This patch is designed for the current visual-prompt UI.
   It:
   1. Requires a Miko master reference image.
   2. Resizes it below 512x512.
   3. Sends it to /images/generate.
   4. Uses FLUX.2 Klein 4B reference-image generation.
   5. Requests 576x1024 (true 9:16).
   6. Adds Generate Image / Regenerate / Download.
   ============================================================ */

const MIKO_REFERENCE_KEY = "miko_master_reference_image_v1";

function getMikoReference() {
    return localStorage.getItem(MIKO_REFERENCE_KEY) || "";
}

function saveMikoReference(dataUrl) {
    localStorage.setItem(MIKO_REFERENCE_KEY, dataUrl);
}

function removeMikoReference() {
    localStorage.removeItem(MIKO_REFERENCE_KEY);
}

function mikoReferenceCss() {
    if (document.getElementById("mikoReferenceCssV4")) return;

    const style = document.createElement("style");
    style.id = "mikoReferenceCssV4";
    style.textContent = `
        .miko-reference-panel-v4 {
            margin: 0 0 18px;
            padding: 20px;
            border: 1px solid rgba(167,139,250,.28);
            border-radius: 20px;
            background: radial-gradient(circle at top right, rgba(139,92,246,.10), transparent 32%), rgba(15,23,42,.82);
            box-shadow: 0 16px 45px rgba(0,0,0,.22);
        }

        .miko-reference-head-v4 {
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:14px;
            flex-wrap:wrap;
        }

        .miko-reference-eyebrow-v4 {
            color:#a78bfa;
            font-size:10px;
            font-weight:900;
            letter-spacing:.12em;
        }

        .miko-reference-head-v4 h3 {
            margin:4px 0;
        }

        .miko-reference-head-v4 p {
            margin:0;
            color:#94a3b8;
            font-size:11px;
        }

        .miko-ref-status-v4 {
            padding:6px 9px;
            border-radius:999px;
            font-size:10px;
            font-weight:800;
        }

        .miko-ref-missing-v4 {
            color:#fecdd3;
            background:rgba(251,113,133,.08);
            border:1px solid rgba(251,113,133,.22);
        }

        .miko-ref-ready-v4 {
            color:#bbf7d0;
            background:rgba(52,211,153,.08);
            border:1px solid rgba(52,211,153,.22);
        }

        .miko-reference-body-v4 {
            display:grid;
            grid-template-columns:150px 1fr;
            gap:16px;
            margin-top:15px;
        }

        .miko-reference-preview-v4 {
            width:150px;
            height:150px;
            overflow:hidden;
            display:grid;
            place-items:center;
            border:1px solid rgba(255,255,255,.10);
            border-radius:15px;
            background:rgba(2,6,23,.6);
        }

        .miko-reference-preview-v4 img {
            width:100%;
            height:100%;
            object-fit:contain;
        }

        .miko-reference-empty-v4 {
            display:flex;
            flex-direction:column;
            gap:5px;
            align-items:center;
            color:#94a3b8;
            font-size:10px;
            text-align:center;
        }

        .miko-reference-empty-v4 strong {
            color:#ddd6fe;
            font-size:18px;
        }

        .miko-reference-controls-v4 {
            display:flex;
            align-items:flex-start;
            align-content:flex-start;
            gap:9px;
            flex-wrap:wrap;
        }

        .miko-upload-v4 {
            display:inline-flex;
            align-items:center;
            min-height:40px;
            padding:9px 13px;
            border:1px solid rgba(167,139,250,.35);
            border-radius:11px;
            color:white;
            background:rgba(139,92,246,.15);
            cursor:pointer;
            font-size:12px;
            font-weight:800;
        }

        .miko-reference-controls-v4 p {
            flex-basis:100%;
            margin:0;
            color:#64748b;
            font-size:10px;
        }

        .image-generate-button-v4 {
            min-height:34px;
            padding:7px 11px;
            border:1px solid rgba(56,189,248,.22);
            border-radius:9px;
            color:#dbeafe;
            background:rgba(56,189,248,.07);
            cursor:pointer;
            font-size:10px;
            font-weight:800;
        }

        .image-generate-button-v4:hover {
            background:rgba(56,189,248,.14);
            border-color:rgba(56,189,248,.38);
        }

        .image-generate-button-v4:disabled {
            opacity:.55;
            cursor:not-allowed;
        }

        .image-status-v4 {
            margin-top:10px;
            min-height:18px;
            font-size:11px;
            line-height:1.5;
        }

        .image-status-loading-v4 { color:#fbbf24; }
        .image-status-success-v4 { color:#86efac; }
        .image-status-error-v4 { color:#fca5a5; }

        .generated-image-v4 {
            margin-top:12px;
            padding-top:12px;
            border-top:1px solid rgba(255,255,255,.07);
        }

        .generated-image-v4 img {
            display:block;
            width:min(100%, 320px);
            height:auto;
            max-height:560px;
            object-fit:contain;
            border-radius:13px;
            border:1px solid rgba(255,255,255,.10);
            background:#020617;
        }

        .generated-image-meta-v4 {
            display:flex;
            gap:7px;
            flex-wrap:wrap;
            margin-top:8px;
            color:#94a3b8;
            font-size:10px;
        }

        .generated-image-actions-v4 {
            display:flex;
            gap:7px;
            flex-wrap:wrap;
            margin-top:8px;
        }

        .generated-image-actions-v4 button {
            min-height:32px;
            padding:6px 10px;
            border:1px solid rgba(255,255,255,.10);
            border-radius:9px;
            color:#e5e7eb;
            background:rgba(255,255,255,.045);
            cursor:pointer;
            font-size:10px;
            font-weight:700;
        }

        .generate-all-images-v4 {
            border:1px solid rgba(139,92,246,.35) !important;
            background:rgba(139,92,246,.14) !important;
            font-weight:800;
        }

        .generate-all-images-v4:disabled {
            opacity:.55;
            cursor:not-allowed;
        }

        .generate-all-status-v4 {
            margin-top:12px;
            padding:9px 11px;
            border-radius:10px;
            background:rgba(255,255,255,.035);
            border:1px solid rgba(255,255,255,.06);
            color:#cbd5e1;
            font-size:11px;
            line-height:1.45;
        }

        .image-generating-v4 {
            margin-top:10px;
            color:#a78bfa;
            font-size:10px;
            font-weight:800;
        }

        @media (max-width:560px) {
            .miko-reference-body-v4 {
                grid-template-columns:1fr;
            }

            .miko-reference-preview-v4 {
                width:140px;
                height:140px;
            }
        }
    `;
    document.head.appendChild(style);
}

function renderMikoReferenceV4() {
    const preview = document.getElementById("mikoReferencePreviewV4");
    const status = document.getElementById("mikoReferenceStatusV4");
    if (!preview || !status) return;

    const reference = getMikoReference();

    if (!reference) {
        preview.innerHTML = `
            <div class="miko-reference-empty-v4">
                <strong>🐱 MIKO</strong>
                <span>Master cat reference</span>
            </div>
        `;
        status.textContent = "● Reference required";
        status.className = "miko-ref-status-v4 miko-ref-missing-v4";
        return;
    }

    preview.innerHTML = `<img src="${reference}" alt="Miko master reference">`;
    status.textContent = "● Miko cat reference ready";
    status.className = "miko-ref-status-v4 miko-ref-ready-v4";
}

function resizeMikoReferenceV4(dataUrl) {
    return new Promise((resolve, reject) => {
        const img = new Image();

        img.onload = () => {
            // Cloudflare FLUX.2 Klein reference images must be smaller than 512x512.
            const maxDimension = 480;
            const scale = Math.min(
                maxDimension / img.width,
                maxDimension / img.height,
                1
            );

            const canvas = document.createElement("canvas");
            canvas.width = Math.max(1, Math.round(img.width * scale));
            canvas.height = Math.max(1, Math.round(img.height * scale));

            const ctx = canvas.getContext("2d");
            if (!ctx) {
                reject(new Error("Could not prepare Miko reference image."));
                return;
            }

            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            resolve(canvas.toDataURL("image/png"));
        };

        img.onerror = () => reject(new Error("Could not read Miko reference image."));
        img.src = dataUrl;
    });
}

function installMikoReferenceUIV4() {
    mikoReferenceCss();

    if (document.getElementById("mikoReferencePanelV4")) {
        renderMikoReferenceV4();
        return;
    }

    const panel = document.createElement("section");
    panel.id = "mikoReferencePanelV4";
    panel.className = "miko-reference-panel-v4";

    panel.innerHTML = `
        <div class="miko-reference-head-v4">
            <div>
                <div class="miko-reference-eyebrow-v4">CHARACTER LOCK</div>
                <h3>🐱 Miko Master Reference</h3>
                <p>
                    This image is the identity reference for every generated scene.
                    Miko must remain a cat.
                </p>
            </div>
            <span id="mikoReferenceStatusV4" class="miko-ref-status-v4 miko-ref-missing-v4">
                ● Reference required
            </span>
        </div>

        <div class="miko-reference-body-v4">
            <div id="mikoReferencePreviewV4" class="miko-reference-preview-v4">
                <div class="miko-reference-empty-v4">
                    <strong>🐱 MIKO</strong>
                    <span>Master cat reference</span>
                </div>
            </div>

            <div class="miko-reference-controls-v4">
                <label class="miko-upload-v4">
                    Upload Miko Reference
                    <input
                        id="mikoReferenceFileV4"
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        hidden
                    >
                </label>

                <button type="button" id="clearMikoReferenceV4" class="btn-secondary">
                    Clear
                </button>

                <p>
                    Use a clean full-body image of Miko as a cat:
                    orange-white fur + blue hoodie. The same reference is reused
                    for every scene.
                </p>
            </div>
        </div>
    `;

    const target =
        document.querySelector("#storyForm")?.parentElement ||
        document.querySelector("main") ||
        document.body;

    target.insertBefore(panel, target.firstChild);

    document.getElementById("mikoReferenceFileV4")?.addEventListener("change", async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
            showError("Miko reference must be PNG, JPEG, or WebP.");
            return;
        }

        try {
            const source = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(String(reader.result || ""));
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });

            const resized = await resizeMikoReferenceV4(source);
            saveMikoReference(resized);
            renderMikoReferenceV4();
            clearError();
        } catch (error) {
            console.error(error);
            showError(error.message || "Could not prepare Miko reference.");
        }
    });

    document.getElementById("clearMikoReferenceV4")?.addEventListener("click", () => {
        removeMikoReference();
        renderMikoReferenceV4();
    });

    renderMikoReferenceV4();
}

async function generateMikoImageV4(item, button, imageContainer, statusElement = null) {
    const reference = getMikoReference();

    if (!reference) {
        const message = "Miko Master Reference belum di-upload. Upload gambar Miko (kucing) terlebih dahulu.";
        if (statusElement) {
            statusElement.textContent = `❌ ${message}`;
            statusElement.className = "image-status-v4 image-status-error-v4";
        }
        throw new Error(message);
    }

    const original = button.textContent;
    if (statusElement) {
        statusElement.textContent = "⏳ Mengirim Scene ke Cloudflare Workers AI...";
        statusElement.className = "image-status-v4 image-status-loading-v4";
    }
    button.disabled = true;
    button.textContent = "Generating...";

    if (imageContainer) {
        imageContainer.innerHTML = `<div class="image-generating-v4">🎨 Generating Miko...</div>`;
    }

    try {
        const result = await fetchJson(CONFIG.endpoints.imagesGenerate, {
            method: "POST",
            timeoutMs: 120000,
            body: JSON.stringify({
                prompt: item.prompt || "",
                negative_prompt: item.negative_prompt || "",
                reference_image: reference,
                width: 576,
                height: 1024,
                scene_number: item.scene_number || null
            })
        });

        if (!result?.success || !result?.image) {
            throw new Error(result?.error || "Image generation returned no image.");
        }

        if (imageContainer) {
            imageContainer.innerHTML = `
                <div class="generated-image-v4">
                    <img
                        src="${result.image}"
                        alt="Generated Miko Scene ${escapeHtml(item.scene_number || "")}"
                    >
                    <div class="generated-image-meta-v4">
                        <span>🐱 Miko CAT LOCK</span>
                        <span>•</span>
                        <span>${escapeHtml(result.aspect_ratio || "9:16")}</span>
                        <span>•</span>
                        <span>${escapeHtml(result.resolution || "576x1024")}</span>
                        <span>•</span>
                        <span>Reference ON</span>
                    </div>
                    <div class="generated-image-actions-v4">
                        <button type="button" data-regenerate-image>Regenerate</button>
                        <button type="button" data-download-image>Download</button>
                    </div>
                </div>
            `;

            imageContainer.querySelector("[data-regenerate-image]")?.addEventListener(
                "click",
                () => generateMikoImageV4(item, button, imageContainer, imageContainer?.parentElement?.querySelector(".image-status-v4"))
            );

            imageContainer.querySelector("[data-download-image]")?.addEventListener(
                "click",
                () => {
                    const anchor = document.createElement("a");
                    anchor.href = result.image;
                    anchor.download = `miko-scene-${String(item.scene_number || 1).padStart(2, "0")}.png`;
                    document.body.appendChild(anchor);
                    anchor.click();
                    anchor.remove();
                }
            );
        }

        if (statusElement) {
            statusElement.textContent = "✅ Miko image berhasil dibuat.";
            statusElement.className = "image-status-v4 image-status-success-v4";
        }

        return result;
    } catch (error) {
        if (statusElement) {
            statusElement.textContent = `❌ ${error?.message || "Image generation failed."}`;
            statusElement.className = "image-status-v4 image-status-error-v4";
        }
        throw error;
    } finally {
        button.disabled = false;
        button.textContent = original;
    }
}

/*
   Replace your existing renderVisualPrompts() with this version if you want
   the image buttons integrated directly into each scene card.
*/
async function generateAllMikoImagesV4(scenes, panel) {
    const reference = getMikoReference();
    const progress = panel.querySelector("#generateAllStatusV4");
    const masterButton = panel.querySelector("#generateAllMikoImages");
    const buttons = [...panel.querySelectorAll("[data-generate-image]")];

    if (!reference) {
        const message = "Miko Master Reference belum di-upload. Upload gambar Miko (kucing) terlebih dahulu.";
        if (progress) progress.textContent = `❌ ${message}`;
        showError(message);
        return;
    }

    if (!scenes.length) return;

    clearError();
    if (masterButton) {
        masterButton.disabled = true;
        masterButton.textContent = "Generating All...";
    }
    buttons.forEach((button) => { button.disabled = true; });

    const failed = [];
    let completed = 0;

    if (progress) {
        progress.textContent = `⏳ Generating Scene 01/${String(scenes.length).padStart(2, "0")}...`;
    }

    try {
        for (let index = 0; index < scenes.length; index += 1) {
            const item = scenes[index];
            const button = buttons[index];
            const imageContainer = document.getElementById(`generatedImage-${index}`);
            const statusElement = document.getElementById(`imageStatus-${index}`);
            const sceneNo = String(item.scene_number ?? index + 1).padStart(2, "0");

            if (progress) {
                progress.textContent = `⏳ Generating Scene ${sceneNo}/${String(scenes.length).padStart(2, "0")}...`;
            }

            try {
                await generateMikoImageV4(item, button, imageContainer, statusElement);
                completed += 1;
            } catch (error) {
                failed.push({ scene: sceneNo, error: error?.message || "Unknown error" });
                // Continue to the next scene so one failed generation does not
                // cancel the complete batch.
                if (statusElement) {
                    statusElement.textContent = `❌ Scene ${sceneNo} failed — continuing...`;
                }
            }

            // Small gap between requests to avoid sending a burst to Workers AI.
            if (index < scenes.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        if (failed.length === 0) {
            if (progress) {
                progress.textContent = `✅ All ${completed} Miko images generated successfully.`;
            }
            setApiStatus("ok", `All ${completed} Miko images ready`);
        } else {
            const failedScenes = failed.map(item => `Scene ${item.scene}`).join(", ");
            if (progress) {
                progress.textContent = `⚠️ ${completed}/${scenes.length} generated. Failed: ${failedScenes}.`;
            }
            showError(
                `Batch image generation selesai: ${completed}/${scenes.length} berhasil. Failed: ${failedScenes}.`
            );
            setApiStatus("error", `${completed}/${scenes.length} images ready`);
        }
    } finally {
        if (masterButton) {
            masterButton.disabled = false;
            masterButton.textContent = "🐱 Generate All Images";
        }
        buttons.forEach((button) => {
            // Individual buttons are re-enabled by generateMikoImageV4.
            // Re-enable untouched buttons here as well.
            button.disabled = false;
        });
    }
}

function renderVisualPromptsV4(result) {
    lastVisualPrompts = result;

    const scenes = Array.isArray(result?.prompts) ? result.prompts : [];
    if (!scenes.length) return;

    ensureVisualPromptStyles();

    let panel = document.getElementById("visualPromptsPanel");

    if (!panel) {
        panel = document.createElement("section");
        panel.id = "visualPromptsPanel";
        panel.className = "visual-prompts-panel";

        const anchor = els.sceneList?.closest("section, .card, .panel") || els.sceneList;

        if (anchor?.parentNode) {
            anchor.parentNode.insertBefore(panel, anchor.nextSibling);
        } else if (els.storyResult) {
            els.storyResult.appendChild(panel);
        }
    }

    panel.innerHTML = `
        <div class="visual-prompts-header">
            <div>
                <h3>🎨 Visual Prompts + Miko Images</h3>
                <p>${scenes.length} scenes · Miko reference locked · 9:16 · 576×1024</p>
            </div>

            <div class="visual-prompts-actions">
                <button type="button" id="copyAllVisualPrompts">Copy All</button>
                <button type="button" id="downloadVisualPrompts">Download</button>
            </div>
        </div>

        <div id="visualPromptList">
            ${scenes.map((item, index) => `
                <article class="visual-prompt-card">
                    <div class="visual-prompt-card-head">
                        <div class="visual-prompt-number">
                            SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}
                        </div>

                        <div class="visual-prompts-actions">
                            <button
                                type="button"
                                class="visual-prompt-copy"
                                data-copy-visual="${index}"
                            >Copy Prompt</button>

                            <button
                                type="button"
                                class="image-generate-button-v4"
                                data-generate-image="${index}"
                            >🐱 Generate Image</button>
                        </div>
                    </div>

                    <div class="visual-prompt-meta">
                        <span>9:16</span>
                        <span>•</span>
                        <span>576×1024</span>
                        <span>•</span>
                        <span>${escapeHtml(item.world_lock || "Miko World")}</span>
                    </div>

                    <div class="visual-prompt-label">Image Prompt</div>
                    <div class="visual-prompt-text">${escapeHtml(item.prompt || "—")}</div>

                    <div class="visual-prompt-label">Negative Prompt</div>
                    <div class="visual-prompt-text visual-prompt-negative">${escapeHtml(item.negative_prompt || "—")}</div>

                    <div id="imageStatus-${index}" class="image-status-v4" aria-live="polite"></div>
                    <div id="generatedImage-${index}"></div>
                </article>
            `).join("")}
        </div>

        <div id="generateAllStatusV4" class="generate-all-status-v4">
            Ready — generate one scene or all scenes sequentially.
        </div>

        <div class="visual-prompt-status">
            🐱 Every image uses the same Miko Master Reference.
            Miko is locked as a cat.
        </div>
    `;

    panel.querySelectorAll("[data-copy-visual]").forEach((button) => {
        button.addEventListener("click", async () => {
            const index = Number(button.dataset.copyVisual);
            const item = scenes[index];
            if (!item) return;

            const content = [
                `SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}`,
                "",
                "IMAGE PROMPT:",
                item.prompt || "",
                "",
                "NEGATIVE PROMPT:",
                item.negative_prompt || ""
            ].join("\n");

            try {
                await navigator.clipboard.writeText(content);
                const original = button.textContent;
                button.textContent = "Copied!";
                setTimeout(() => { button.textContent = original; }, 1000);
            } catch (error) {
                console.error(error);
                showError("Clipboard access is unavailable in this browser.");
            }
        });
    });

    // Event delegation: keeps Generate Image working even after panel re-rendering.
    panel.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-generate-image]");
        if (!button || !panel.contains(button)) return;

        event.preventDefault();
        event.stopPropagation();

        const index = Number(button.dataset.generateImage);
        const item = scenes[index];
        const imageContainer = document.getElementById(`generatedImage-${index}`);
        const statusElement = document.getElementById(`imageStatus-${index}`);

        if (!item) return;

        try {
            clearError();
            await generateMikoImageV4(item, button, imageContainer, statusElement);
        } catch (error) {
            console.error("Miko image generation failed:", error);
            showError(error.message || "Miko image generation failed.");
        }
    });

    panel.querySelector("#copyAllVisualPrompts")?.addEventListener("click", async () => {
        const content = scenes.map((item, index) => [
            `SCENE ${String(item.scene_number ?? index + 1).padStart(2, "0")}`,
            "",
            "IMAGE PROMPT:",
            item.prompt || "",
            "",
            "NEGATIVE PROMPT:",
            item.negative_prompt || "",
            "",
            "----------------------------------------",
            ""
        ].join("\n")).join("\n");

        try {
            await navigator.clipboard.writeText(content);
            const button = panel.querySelector("#copyAllVisualPrompts");
            const original = button.textContent;
            button.textContent = "Copied!";
            setTimeout(() => { button.textContent = original; }, 1000);
        } catch (error) {
            console.error(error);
            showError("Clipboard access is unavailable in this browser.");
        }
    });

    panel.querySelector("#downloadVisualPrompts")?.addEventListener("click", () => {
        const blob = new Blob(
            [JSON.stringify(result, null, 2)],
            { type: "application/json" }
        );

        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "miko-visual-prompts.json";
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    });
}

function initMikoConsistencyV4() {
    installMikoReferenceUIV4();
}

