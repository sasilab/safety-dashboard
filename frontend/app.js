// EP05 attack dashboard — vanilla JS, no build step.
//
// Flow:
//   1. boot() fetches /api/health, /api/attacks, /api/score, /api/settings
//   2. renderCategories() builds the category grid
//   3. selectCategory() lists the attacks in that category
//   4. fire(attack) POSTs /api/attack → renderResult()
//   5. score is re-fetched after every fire
//
// All state lives in `state` for easy inspection from the devtools console.

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const state = {
  categories: [],
  attacks: [],
  selectedCategory: null,
  layersEnabled: [1, 2, 3, 4, 5],
  prefs: {},
  callLLM: false,
};

async function api(path, opts = {}) {
  const r = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...opts,
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${path} ${r.status}: ${text.slice(0, 200)}`);
  }
  return r.json();
}

async function boot() {
  try {
    const [health, attacks, prefs] = await Promise.all([
      api("/api/health"),
      api("/api/attacks"),
      api("/api/settings"),
    ]);
    state.categories = attacks.categories;
    state.attacks = attacks.attacks;
    state.layersEnabled = health.layers_enabled || [1, 2, 3, 4, 5];
    state.prefs = prefs;
    state.callLLM = false;
    renderProviderPill(health);
    renderCategories();
    await refreshScore();
  } catch (e) {
    console.error("boot failed", e);
    appendError(`Boot failed: ${e.message}`);
  }
}

function renderProviderPill(health) {
  const pill = $("#provider-pill");
  if (!pill) return;
  if (health.provider) {
    pill.textContent = `${health.provider}: ${shortenModel(health.llm || "")}`;
    pill.classList.remove("pill-muted", "pill-bad");
    pill.classList.add("pill-good");
  } else {
    pill.textContent = "no LLM (open Settings)";
    pill.classList.remove("pill-good");
    pill.classList.add("pill-muted");
  }
}

function shortenModel(m) {
  if (!m) return "";
  if (m.length <= 28) return m;
  return m.slice(0, 14) + "…" + m.slice(-12);
}

function renderCategories() {
  const grid = $("#category-grid");
  grid.innerHTML = "";
  for (const cat of state.categories) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "category-card";
    card.dataset.id = cat.id;
    const count = state.attacks.filter((a) => a.category === cat.id).length;
    card.innerHTML = `
      <div class="category-emoji">${cat.emoji}</div>
      <div class="category-label">${cat.label}</div>
      <div class="category-count">${count} canned attack${count === 1 ? "" : "s"}</div>`;
    card.addEventListener("click", () => selectCategory(cat.id));
    grid.appendChild(card);
  }
  // Auto-select the first category so the page has content on load.
  if (state.categories.length) selectCategory(state.categories[0].id);
}

function selectCategory(id) {
  state.selectedCategory = id;
  $$(".category-card").forEach((el) => el.classList.toggle("active", el.dataset.id === id));
  const cat = state.categories.find((c) => c.id === id);
  const title = $("#attacks-title");
  title.textContent = `${cat ? cat.emoji + " " + cat.label : "Attacks"} — click Fire to test`;
  const list = $("#attack-list");
  list.innerHTML = "";
  const items = state.attacks.filter((a) => a.category === id);
  if (!items.length) {
    list.innerHTML = `<div class="muted">No attacks in this category.</div>`;
    return;
  }
  for (const a of items) {
    const card = document.createElement("div");
    card.className = "attack-card";
    card.innerHTML = `
      <div class="attack-meta">
        <div class="attack-title">${escapeHtml(a.title)}</div>
        <div class="attack-payload">${escapeHtml(truncate(a.payload, 280))}</div>
        <div class="attack-expected">Expected: caught by Layer ${a.expected_layer}</div>
      </div>
      <button class="btn btn-primary fire-btn" type="button">Fire 🔥</button>`;
    card.querySelector(".fire-btn").addEventListener("click", () => fire({ attack_id: a.id }));
    list.appendChild(card);
  }
}

async function fire(body) {
  try {
    const req = {
      ...body,
      layers_enabled: state.layersEnabled,
      on_topic: state.prefs.on_topic || [],
      health_rules: state.prefs.health_rules || {},
      rejection_threshold: state.prefs.rejection_threshold ?? 0.30,
      call_llm: state.callLLM,
    };
    const path = body.text ? "/api/attack/custom" : "/api/attack";
    const res = await api(path, { method: "POST", body: JSON.stringify(req) });
    renderResult(res);
    await refreshScore();
  } catch (e) {
    appendError(`Attack failed: ${e.message}`);
  }
}

function renderResult(r) {
  const feed = $("#result-feed");
  // Drop the empty-state hint on first result.
  if (feed.querySelector(".muted")) feed.innerHTML = "";
  const card = document.createElement("div");
  card.className = `result-card result-${r.result || "passed"}`;
  const layerStrip = renderLayerStrip(r.layer_status || {});
  const audit = (r.audit_trail || []).map((s) =>
    `<li><strong>${escapeHtml(s.label || ("L"+s.layer))}</strong> — ${escapeHtml(s.action)}${s.detail && Object.keys(s.detail).length ? ` · ${escapeHtml(JSON.stringify(s.detail))}` : ""}</li>`
  ).join("");
  card.innerHTML = `
    <div class="result-header">
      <div class="result-title">${escapeHtml(r.title || r.attack_id || "Custom attack")}
        ${r.expected_layer ? `<small class="muted"> · expected L${r.expected_layer}</small>` : ""}
      </div>
      <div class="result-badge">${(r.result || "passed").toUpperCase()}${r.caught_at_layer ? " · L" + r.caught_at_layer : ""}</div>
    </div>
    <div class="result-payload"><strong>Payload:</strong> ${escapeHtml(truncate(r.payload, 320))}</div>
    ${r.details ? `<div class="result-detail">${escapeHtml(r.details)}</div>` : ""}
    ${r.safe_input ? `<div class="result-safe"><strong>safe_input:</strong> ${escapeHtml(r.safe_input)}</div>` : ""}
    ${r.safe_output ? `<div class="result-safe"><strong>safe_output:</strong> ${escapeHtml(r.safe_output)}</div>` : ""}
    ${r.fence_preview ? `<div class="result-fence"><strong>fence preview:</strong> ${escapeHtml(truncate(r.fence_preview, 360))}</div>` : ""}
    ${r.swap_food ? `<div class="result-detail"><strong>L5 swap →</strong> ${escapeHtml(r.swap_food)} (${escapeHtml(r.swap_reason || "")})</div>` : ""}
    ${r.llm_used && r.llm_response ? `<div class="result-safe"><strong>llm_response:</strong> ${escapeHtml(truncate(r.llm_response, 360))}</div>` : ""}
    ${layerStrip}
    ${audit ? `<ul class="audit-list">${audit}</ul>` : ""}
  `;
  feed.prepend(card);
}

function renderLayerStrip(layerStatus) {
  const order = ["1", "2", "3", "4", "5"];
  const chips = order.map((l) => {
    const status = layerStatus[l] || "not_invoked";
    let cls = "layer-chip";
    if (status === "blocked") cls += " blocked";
    else if (status === "sanitized") cls += " fired";
    else if (status === "override") cls += " override";
    else if (status === "passed") cls += " passed";
    else if (status === "disabled") cls += " disabled";
    else cls += " not_invoked";
    return `<span class="${cls}">L${l} · ${status}</span>`;
  }).join("");
  return `<div class="layer-strip">${chips}</div>`;
}

async function refreshScore() {
  try {
    const s = await api("/api/score");
    $("#score-total").textContent = s.total;
    $("#score-blocked").textContent = s.blocked;
    $("#score-sanitized").textContent = s.sanitized;
    $("#score-override").textContent = s.override;
    $("#score-passed").textContent = s.passed;
    $("#score-rate").textContent = s.total ? `${Math.round(s.defense_rate * 100)}%` : "—";
    $("#score-weakest").textContent = s.weakest_layer ? `L${s.weakest_layer}` : "—";
  } catch (_) { /* score is best-effort */ }
}

function escapeHtml(x) {
  if (x == null) return "";
  return String(x)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
function truncate(s, n) {
  if (s == null) return "";
  s = String(s);
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}
function appendError(msg) {
  const feed = $("#result-feed");
  const card = document.createElement("div");
  card.className = "result-card result-blocked";
  card.innerHTML = `<div class="result-title">⚠️ ${escapeHtml(msg)}</div>`;
  feed.prepend(card);
}

// --- Settings dialog wiring ---

$("#settings-btn")?.addEventListener("click", openSettings);
$("#settings-cancel")?.addEventListener("click", () => $("#settings-dialog").close());
$("#settings-save")?.addEventListener("click", saveSettings);
$("#fire-custom")?.addEventListener("click", () => {
  const text = $("#custom-payload").value.trim();
  if (!text) return;
  fire({ text });
});
$("#score-reset")?.addEventListener("click", async () => {
  await api("/api/score/reset", { method: "POST" });
  await refreshScore();
  $("#result-feed").innerHTML = `<div class="muted">Score reset.</div>`;
});
$("#setting-threshold")?.addEventListener("input", (e) => {
  $("#setting-threshold-display").textContent = `${Math.round(e.target.value * 100)}%`;
});

async function openSettings() {
  const dlg = $("#settings-dialog");
  const prefs = state.prefs;
  $("#setting-provider").value = prefs.provider || "";
  $("#setting-model").value = prefs.model || "";
  $("#setting-api-key").value = "";
  $("#setting-base-url").value = prefs.base_url || "";
  $("#setting-on-topic").value = (prefs.on_topic || []).join(", ");
  const hr = prefs.health_rules || {};
  $("#setting-diabetic").value = (hr.diabetic || []).join(", ");
  $("#setting-allergies").value = (hr.nuts || []).join(", ");
  $("#setting-threshold").value = prefs.rejection_threshold || 0.30;
  $("#setting-threshold-display").textContent =
    `${Math.round((prefs.rejection_threshold || 0.30) * 100)}%`;
  const enabled = new Set(prefs.layers_enabled || [1, 2, 3, 4, 5]);
  $$('input[type=checkbox][data-layer]').forEach((el) => {
    el.checked = enabled.has(Number(el.dataset.layer));
  });
  $("#setting-call-llm").checked = state.callLLM;
  dlg.showModal();
}

async function saveSettings() {
  const enabled = $$('input[type=checkbox][data-layer]')
    .filter((el) => el.checked).map((el) => Number(el.dataset.layer));
  const splitCsv = (s) => s.split(",").map((x) => x.trim()).filter(Boolean);
  const patch = {
    provider: $("#setting-provider").value || null,
    model: $("#setting-model").value || null,
    api_key: $("#setting-api-key").value || null,
    base_url: $("#setting-base-url").value || null,
    layers_enabled: enabled,
    on_topic: splitCsv($("#setting-on-topic").value),
    health_rules: {
      diabetic: splitCsv($("#setting-diabetic").value),
      nuts: splitCsv($("#setting-allergies").value),
    },
    rejection_threshold: Number($("#setting-threshold").value),
  };
  // Don't send api_key if the user left the field blank (means "keep existing").
  if (!patch.api_key) delete patch.api_key;
  state.callLLM = $("#setting-call-llm").checked;
  const updated = await api("/api/settings", {
    method: "POST", body: JSON.stringify(patch),
  });
  state.prefs = updated;
  state.layersEnabled = updated.layers_enabled;
  $("#settings-dialog").close();
  // Re-fetch health so the provider pill reflects the new key.
  const health = await api("/api/health");
  renderProviderPill(health);
}

boot();
