/**
 * Клиентский скрипт сайта (браузер). Не запускайте через `node app.js` —
 * отдавайте файл как статику вместе с index.html (например через uvicorn/FastAPI server.py).
 */
const state = {
  catalog: null,
  meta: null,
  sel: null,
};

function $(s, root) {
  if (typeof document === "undefined") return null;
  return (root ?? document).querySelector(s);
}

function money(p) {
  if (Number(p.amount) <= 0) return "Скоро";
  const n = p.amount === Math.round(p.amount) ? Math.round(p.amount) : p.amount;
  const c = String(p.currency || "RUB").toUpperCase();
  if (c === "RUB") return `${n} ₽`;
  return `${n} ${p.currency}`;
}

function renderGrid(el, items) {
  if (!el || typeof document === "undefined") return;
  el.innerHTML = "";
  items.forEach((p) => {
    const avail = Number(p.amount) > 0;
    const div = document.createElement("article");
    div.className = "product";
    div.innerHTML = `
      <h3>${escapeHtml(p.title)}</h3>
      <p class="product-p">${escapeHtml(p.description)}</p>
      <div class="product-footer">
        <span class="price">${escapeHtml(String(money(p)))}</span>
        <button class="btn btn-sm ${avail ? "glow" : "btn-outline"}" type="button" data-buy="${escapeAttr(
      p.id,
    )}" ${avail ? "" : "disabled"}>
          ${avail ? "Купить" : "Скоро"}
        </button>
      </div>
    `;
    el.appendChild(div);
  });

  el.querySelectorAll("[data-buy]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-buy");
      const item = [...items].find((x) => x.id === id);
      openModal(item);
    });
  });
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(str) {
  return escapeHtml(str).replaceAll("'", "&#39;");
}

function chipsForFeatured(items, max = 4) {
  return items
    .filter((x) => Number(x.amount) > 0)
    .slice(0, max)
    .map((p) => `<span class="mini-chip">${escapeHtml(p.title)} · ${money(p)}</span>`)
    .join("");
}

function openModal(product) {
  if (!product || Number(product.amount) <= 0) return;
  const modalTitle = $("#modalTitle");
  if (!modalTitle) return;
  state.sel = product;
  modalTitle.textContent = product.title;
  const sub = $("#modalSub");
  if (sub) sub.textContent = `${money(product)} · ${product.description}`;
  const lbl = $("#acctLabel");
  if (lbl) lbl.textContent = product.account_label || "Учётные данные";
  const input = $("#acctInput");
  if (input) input.value = "";
  const err = $("#modalErr");
  if (err) err.textContent = "";
  const modal = $("#modal");
  if (modal) {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
  }
  $("#acctInput")?.focus();
}

function closeModal() {
  $("#modal")?.classList.add("hidden");
  $("#modal")?.setAttribute("aria-hidden", "true");
  state.sel = null;
}

async function bootstrap() {
  try {
    const [cRes, mRes] = await Promise.all([fetch("/api/catalog"), fetch("/api/meta")]);
    state.catalog = await cRes.json();
    state.meta = await mRes.json();
  } catch (e) {
    console.error(e);
    return;
  }

  const tg = state.meta.telegram_bot_username;
  const botRow = $("#botLinkRow");
  if (tg && botRow) {
    const a = document.createElement("a");
    a.className = "telegram-link";
    a.href = `https://t.me/${tg}`;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = "Открыть бота в Telegram";
    botRow.appendChild(a);
  }

  const c = state.catalog;
  const fp = $("#featuredPubg");
  if (fp) fp.innerHTML = chipsForFeatured(c.pubg || []);
  renderGrid($("#gridPubg"), c.pubg || []);
  renderGrid($("#gridTelegram"), c.telegram || []);
  renderGrid($("#gridGames"), c.games || []);
  renderGrid($("#gridVpn"), c.vpn || []);
}

function init() {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  $("#backdrop")?.addEventListener("click", closeModal);
  $("#closeBtn")?.addEventListener("click", closeModal);
  $("#payBtn")?.addEventListener("click", async () => {
    const p = state.sel;
    if (!p) return;
    const accountEl = $("#acctInput");
    const account = accountEl ? accountEl.value.trim() : "";
    if (account.length < 3) {
      const errEl = $("#modalErr");
      if (errEl) errEl.textContent = "Введите корректные данные аккаунта.";
      return;
    }
    const errEl = $("#modalErr");
    if (errEl) errEl.textContent = "";
    const payBtn = $("#payBtn");
    if (payBtn) payBtn.disabled = true;
    try {
      const r = await fetch("/api/create-invoice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: p.id, account }),
      });
      const js = await r.json().catch(() => ({}));
      if (!r.ok) {
        const d = typeof js.detail === "string" ? js.detail : JSON.stringify(js.detail || js);
        if (errEl) {
          errEl.textContent = `Ошибка: ${d}`;
        }
        return;
      }
      window.location.href = js.checkout_url;
    } catch (_e) {
      if (errEl) errEl.textContent = "Сеть или сервер недоступны.";
    } finally {
      if (payBtn) payBtn.disabled = false;
    }
  });

  bootstrap();
}

init();
