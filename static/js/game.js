const STATS_KEY = "gemeentle_stats";
const HISTORY_KEY = "gemeentle_history";

function filterGemeenten(query) {
    const gemeenten = window.GEMEENTEN || [];
    if (!query) return [];
    const meta = document.querySelector(".game-meta");
    const guessed = new Set(JSON.parse(meta?.dataset.guessesList || "[]").map((g) => g.toLowerCase()));
    const q = query.toLowerCase();
    const available = gemeenten.filter((g) => !guessed.has(g.toLowerCase()));
    const starts = available.filter((g) => g.toLowerCase().startsWith(q));
    const contains = available.filter((g) => !g.toLowerCase().startsWith(q) && g.toLowerCase().includes(q));
    return [...starts, ...contains].slice(0, 8);
}

function initAutocomplete(form) {
    const input = form.querySelector(".autocomplete__input");
    const list = form.querySelector(".autocomplete__list");
    if (!input || !list) return;

    let activeIdx = -1;

    function optionId(idx) {
        return `autocomplete-option-${idx}`;
    }

    function getItems() {
        return list.querySelectorAll("[role='option']");
    }

    function setActive(idx) {
        const items = getItems();
        const clamped = Math.max(-1, Math.min(idx, items.length - 1));
        items.forEach((el, i) => {
            const active = i === clamped;
            el.classList.toggle("autocomplete__option--active", active);
            el.setAttribute("aria-selected", String(active));
        });
        activeIdx = clamped;
        if (clamped >= 0 && items[clamped]) {
            input.setAttribute("aria-activedescendant", optionId(clamped));
        } else {
            input.removeAttribute("aria-activedescendant");
        }
    }

    function closeList() {
        list.hidden = true;
        list.innerHTML = "";
        activeIdx = -1;
        input.setAttribute("aria-expanded", "false");
        input.removeAttribute("aria-activedescendant");
    }

    function openList(results) {
        list.innerHTML = "";
        activeIdx = -1;
        input.setAttribute("aria-expanded", "true");

        if (results.length === 0) {
            const li = document.createElement("li");
            li.className = "autocomplete__empty";
            li.setAttribute("role", "option");
            li.setAttribute("aria-disabled", "true");
            li.textContent = "Geen gemeente gevonden";
            list.appendChild(li);
        } else {
            results.forEach((name, idx) => {
                const li = document.createElement("li");
                li.id = optionId(idx);
                li.className = "autocomplete__option";
                li.setAttribute("role", "option");
                li.setAttribute("aria-selected", "false");
                li.textContent = name;
                li.dataset.value = name;
                li.addEventListener("mousedown", (e) => {
                    e.preventDefault();
                    input.value = name;
                    closeList();
                });
                list.appendChild(li);
            });
        }
        list.hidden = false;
    }

    input.addEventListener("input", () => {
        if (input.value) openList(filterGemeenten(input.value));
        else closeList();
    });

    input.addEventListener("keydown", (e) => {
        const items = getItems();
        if (e.key === "ArrowDown") {
            e.preventDefault();
            if (list.hidden && input.value) {
                const results = filterGemeenten(input.value);
                if (results.length) openList(results);
            }
            setActive(activeIdx + 1);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive(activeIdx - 1);
        } else if (e.key === "Enter") {
            if (!list.hidden && activeIdx >= 0 && items[activeIdx]) {
                e.preventDefault();
                input.value = items[activeIdx].dataset.value;
                closeList();
                form.requestSubmit();
            } else {
                closeList();
            }
        } else if (e.key === "Escape") {
            closeList();
        } else if (e.key === "Tab") {
            closeList();
        }
    });

    input.addEventListener("blur", () => {
        setTimeout(closeList, 150);
    });

    input.addEventListener("focus", () => {
        if (input.value) {
            const results = filterGemeenten(input.value);
            if (results.length) openList(results);
        }
    });
}

function getStats() {
    const defaults = { played: 0, won: 0, currentStreak: 0, bestStreak: 0 };
    try {
        const raw = localStorage.getItem(STATS_KEY);
        return { ...defaults, ...(raw ? JSON.parse(raw) : {}) };
    } catch {
        return defaults;
    }
}

function getHistory() {
    try {
        const raw = localStorage.getItem(HISTORY_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function syncResult() {
    const meta = document.querySelector(".game-meta");
    if (!meta) return;

    const result = meta.dataset.result;
    const date = meta.dataset.date;
    const gemeente = meta.dataset.gemeente;
    if (result === "playing") return;
    if (meta.dataset.isArchive) return;

    const gameId = `${date}:${gemeente}`;
    const history = getHistory();
    if (history.some((h) => h.gameId === gameId || (!h.gameId && h.date === date && h.gemeente === gemeente))) return;

    const entry = { gameId, date, gemeente, result, guesses: parseInt(meta.dataset.guesses, 10) };
    history.unshift(entry);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));

    const stats = getStats();
    stats.played++;

    if (result === "won") {
        stats.won++;
        const [y, mo, d] = date.split("-").map(Number);
        const prev = new Date(y, mo - 1, d - 1);
        const yStr = `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, "0")}-${String(prev.getDate()).padStart(2, "0")}`;
        const prevEntry = history[1];
        if (prevEntry && prevEntry.date === yStr && prevEntry.result === "won") {
            stats.currentStreak++;
        } else {
            stats.currentStreak = 1;
        }
        stats.bestStreak = Math.max(stats.bestStreak, stats.currentStreak);
    } else {
        stats.currentStreak = 0;
    }

    localStorage.setItem(STATS_KEY, JSON.stringify(stats));
}

function renderStats() {
    const el = document.getElementById("stats-content");
    if (!el) return;
    const s = getStats();
    const pct = s.played > 0 ? Math.round((s.won / s.played) * 100) : 0;
    el.innerHTML = `
        <dl class="stats-grid">
            <div class="stat-item">
                <dd class="stat-value"><output>${s.played}</output></dd>
                <dt class="stat-label">Gespeeld</dt>
            </div>
            <div class="stat-item">
                <dd class="stat-value"><output>${pct}%</output></dd>
                <dt class="stat-label">Gewonnen</dt>
            </div>
            <div class="stat-item">
                <dd class="stat-value"><output>${s.currentStreak}</output></dd>
                <dt class="stat-label">Reeks</dt>
            </div>
            <div class="stat-item">
                <dd class="stat-value"><output>${s.bestStreak}</output></dd>
                <dt class="stat-label">Record</dt>
            </div>
        </dl>`;
}

function startCountdown() {
    const el = document.getElementById("countdown");
    if (!el) return;

    function update() {
        const now = new Date();
        const midnight = new Date(now);
        midnight.setHours(24, 0, 0, 0);
        const diff = midnight - now;
        const h = String(Math.floor(diff / 3600000)).padStart(2, "0");
        const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
        const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");
        el.textContent = `${h}:${m}:${s}`;
    }

    update();
    setInterval(update, 1000);
}

function initShareButton() {
    const btn = document.querySelector(".js-share");
    if (!btn) return;
    btn.addEventListener("click", () => {
        const day = btn.dataset.day;
        const guesses = btn.dataset.guesses;
        const max = 6;
        const squares = guesses === "X" ? "🟥".repeat(max) : "🟥".repeat(parseInt(guesses, 10) - 1) + "🟩" + "⬛".repeat(max - parseInt(guesses, 10));
        const text = `Gemeentle #${day}\n${squares}\nhttps://gemeentle.gijs6.nl`;
        navigator.clipboard.writeText(text).then(() => {
            const original = btn.textContent;
            btn.textContent = "Gekopieerd!";
            setTimeout(() => {
                btn.textContent = original;
            }, 2000);
        });
    });
}

function openDialog(id) {
    const dialog = document.getElementById(id);
    if (!dialog) return;
    if (id === "stats-dialog") renderStats();
    dialog.showModal();
}

function initDialogs() {
    document.querySelectorAll("[data-dialog]").forEach((btn) => {
        btn.addEventListener("click", () => openDialog(btn.dataset.dialog));
    });

    document.querySelectorAll(".dialog-close").forEach((btn) => {
        btn.addEventListener("click", () => btn.closest("dialog")?.close());
    });

    document.querySelectorAll("dialog").forEach((dialog) => {
        dialog.addEventListener("click", (e) => {
            if (e.target === dialog) dialog.close();
        });
    });
}

function animateNewElements() {
    if (document.querySelector(".guess-error")) return;

    const hints = document.querySelectorAll(".hint-list .hint");
    if (hints.length) hints[hints.length - 1].classList.add("hint--new");

    const guessRows = document.querySelectorAll(".guess-list .guess-row");
    if (guessRows.length) guessRows[guessRows.length - 1].classList.add("guess-row--new");
}

function initHtmx() {
    document.addEventListener("htmx:afterSwap", () => {
        syncResult();
        animateNewElements();
        initShareButton();
        startCountdown();

        const form = document.querySelector(".guess-form");
        if (form) initAutocomplete(form);

        const input = document.querySelector("[autofocus]");
        if (input) requestAnimationFrame(() => input.focus());
    });

    document.addEventListener("htmx:beforeRequest", () => {
        const list = document.querySelector(".autocomplete__list");
        if (list) list.hidden = true;

        const btn = document.querySelector(".guess-form .btn");
        const input = document.querySelector(".autocomplete__input");
        if (btn) btn.classList.add("btn--loading");
        if (input) input.disabled = true;
    });
}

function init() {
    const form = document.querySelector(".guess-form");
    if (form) initAutocomplete(form);

    syncResult();
    initShareButton();
    startCountdown();
    initDialogs();
    initHtmx();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
