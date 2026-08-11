/* ============================================================
   script.js — shared utilities for FaceAI dashboard
   ============================================================ */

// ---------------------------------------------------------------
// Ambient background particles
// ---------------------------------------------------------------
function initAmbientParticles() {
  const bg = document.querySelector(".ambient-bg");
  if (!bg) return;
  for (let i = 0; i < 14; i++) {
    const p = document.createElement("div");
    p.className = "particle";
    p.style.left = Math.random() * 100 + "%";
    p.style.bottom = "-10px";
    p.style.animationDelay = (Math.random() * 12) + "s";
    p.style.animationDuration = (10 + Math.random() * 8) + "s";
    bg.appendChild(p);
  }
}

// ---------------------------------------------------------------
// Sidebar (mobile hamburger)
// ---------------------------------------------------------------
function initSidebarToggle() {
  const btn = document.getElementById("hamburgerBtn");
  const sidebar = document.getElementById("sidebar");
  const scrim = document.getElementById("sidebarScrim");
  if (!btn || !sidebar) return;
  const close = () => { sidebar.classList.remove("open"); scrim?.classList.remove("show"); };
  btn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    scrim?.classList.toggle("show");
  });
  scrim?.addEventListener("click", close);
}

// ---------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------
function ensureToastContainer() {
  let c = document.querySelector(".toast-container");
  if (!c) {
    c = document.createElement("div");
    c.className = "toast-container";
    document.body.appendChild(c);
  }
  return c;
}

const TOAST_ICONS = {
  success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>',
  error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>',
};

function showToast(message, type = "success", duration = 3800) {
  const container = ensureToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="icon-wrap">${TOAST_ICONS[type] || TOAST_ICONS.success}</div>
    <div class="msg">${message}</div>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("out");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Configurable API base — can be set via `window.API_BASE` or a meta tag
const API_BASE = (typeof window !== 'undefined' && (window.API_BASE)) || (document.querySelector('meta[name="api-base"]')?.content) || "";

// ---------------------------------------------------------------
// Animated counters
// ---------------------------------------------------------------
function animateCounter(el, target, duration = 900) {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(start + (target - start) * eased);
    el.textContent = value;
    if (progress < 1) requestAnimationFrame(tick);
    else el.textContent = target;
  }
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------
// Fetch wrapper with JSON handling + error toast
// ---------------------------------------------------------------
async function apiFetch(url, options = {}) {
  const opts = Object.assign({ headers: { "Content-Type": "application/json" }, credentials: "same-origin" }, options);
  if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
  const finalUrl = (typeof url === 'string' && url.startsWith('/') && API_BASE) ? (API_BASE.replace(/\/$/, '') + url) : url;
  try {
    const res = await fetch(finalUrl, opts);
    const text = await res.text();
    let data = {};
    try { data = JSON.parse(text); } catch (err) { data = {}; }
    if (!res.ok || data.success === false) {
      const message = data.error || `Request failed (${res.status})` + (text ? `: ${text.substring(0, 200)}` : "");
      throw new Error(message);
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// ---------------------------------------------------------------
// Modal helper
// ---------------------------------------------------------------
function openModal(id) { document.getElementById(id)?.classList.add("show"); }
function closeModal(id) { document.getElementById(id)?.classList.remove("show"); }

function confirmAction({ title, message, confirmLabel = "Confirm", danger = true, onConfirm }) {
  let overlay = document.getElementById("confirmModalOverlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "confirmModalOverlay";
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box">
        <h3 id="confirmModalTitle"></h3>
        <p id="confirmModalMsg"></p>
        <div class="modal-actions">
          <button class="btn btn-outline" id="confirmModalCancel">Cancel</button>
          <button class="btn" id="confirmModalOk"></button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
  }
  document.getElementById("confirmModalTitle").textContent = title;
  document.getElementById("confirmModalMsg").textContent = message;
  const okBtn = document.getElementById("confirmModalOk");
  okBtn.textContent = confirmLabel;
  okBtn.className = "btn " + (danger ? "btn-danger" : "btn-primary");
  const cancelBtn = document.getElementById("confirmModalCancel");

  const close = () => overlay.classList.remove("show");
  const newOk = okBtn.cloneNode(true);
  okBtn.parentNode.replaceChild(newOk, okBtn);
  newOk.addEventListener("click", () => { close(); onConfirm(); });
  cancelBtn.onclick = close;

  overlay.classList.add("show");
}

// ---------------------------------------------------------------
// Debounce helper
// ---------------------------------------------------------------
function debounce(fn, delay = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}

// ---------------------------------------------------------------
// Time-ago formatting
// ---------------------------------------------------------------
function timeAgo(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr.replace(" ", "T"));
  if (isNaN(d)) return dateStr;
  const seconds = Math.floor((new Date() - d) / 1000);
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return Math.floor(seconds / 60) + "m ago";
  if (seconds < 86400) return Math.floor(seconds / 3600) + "h ago";
  return Math.floor(seconds / 86400) + "d ago";
}

function initials(name) {
  if (!name) return "?";
  return name.split(" ").map(p => p[0]).slice(0, 2).join("").toUpperCase();
}

// ---------------------------------------------------------------
// Global init
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initAmbientParticles();
  initSidebarToggle();

  document.querySelectorAll("[data-counter]").forEach(el => {
    const target = parseInt(el.getAttribute("data-counter"), 10) || 0;
    animateCounter(el, target);
  });

  // Global search box (top bar) — redirect to People with query
  const gsearch = document.getElementById("globalSearchInput");
  if (gsearch) {
    gsearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && gsearch.value.trim()) {
        window.location.href = "/people?q=" + encodeURIComponent(gsearch.value.trim());
      }
    });
  }
});
