const codeInput = document.querySelector("#codeInput");
const scanForm = document.querySelector("#scanForm");
const itemsList = document.querySelector("#itemsList");
const totalText = document.querySelector("#totalText");
const statusText = document.querySelector("#statusText");
const message = document.querySelector("#message");
const reloadButton = document.querySelector("#reloadButton");
const clearButton = document.querySelector("#clearButton");
const printButton = document.querySelector("#printButton");

function showMessage(text, isError = false) {
  message.hidden = !text;
  message.textContent = text || "";
  message.style.background = isError ? "#ffe3e3" : "#fff3cd";
  message.style.color = isError ? "#7a2020" : "#654d00";
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Erro inesperado.");
  }
  return data;
}

function renderItems(items) {
  const total = items.reduce((sum, item) => sum + item.quantity, 0);
  totalText.textContent = `${total} etiqueta${total === 1 ? "" : "s"}`;
  printButton.disabled = total === 0;
  clearButton.disabled = total === 0;

  if (items.length === 0) {
    itemsList.innerHTML = '<div class="item"><div><strong>Nenhum item bipado</strong><span>Aguardando leitura.</span></div></div>';
    return;
  }

  itemsList.innerHTML = items
    .map((item) => {
      const product = item.product || {};
      const description = product.description || product.name || "Produto nao encontrado";
      return `
        <div class="item ${item.found ? "" : "missing"}">
          <div>
            <strong>${item.code}</strong>
            <span>${description}</span>
          </div>
          <div class="qty">${item.quantity}x</div>
          <button class="remove" type="button" data-code="${item.code}" aria-label="Remover">-</button>
        </div>
      `;
    })
    .join("");
}

async function loadStatus() {
  const status = await request("/api/status");
  const errorText = status.last_error ? " usando fallback local" : "";
  statusText.textContent = `${status.products_count} produtos carregados${errorText}. Modo: ${status.print_mode}.`;
}

async function loadSession() {
  const data = await request("/api/session");
  renderItems(data.items);
}

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("");
  const code = codeInput.value.trim();
  if (!code) return;
  try {
    const data = await request("/api/scan", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
    renderItems(data.items);
    codeInput.value = "";
    codeInput.focus();
  } catch (error) {
    showMessage(error.message, true);
  }
});

itemsList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-code]");
  if (!button) return;
  const data = await request("/api/remove", {
    method: "POST",
    body: JSON.stringify({ code: button.dataset.code }),
  });
  renderItems(data.items);
  codeInput.focus();
});

reloadButton.addEventListener("click", async () => {
  showMessage("");
  try {
    await request("/api/inventory/reload", { method: "POST" });
    await loadStatus();
    await loadSession();
  } catch (error) {
    showMessage(error.message, true);
  }
});

clearButton.addEventListener("click", async () => {
  const data = await request("/api/clear", { method: "POST" });
  renderItems(data.items);
  codeInput.focus();
});

printButton.addEventListener("click", async () => {
  showMessage("");
  try {
    const result = await request("/api/print", { method: "POST" });
    showMessage(`${result.labels} etiqueta(s) enviadas. Log: ${result.log}`);
    await loadSession();
  } catch (error) {
    showMessage(error.message, true);
  }
});

loadStatus().catch((error) => showMessage(error.message, true));
loadSession().catch((error) => showMessage(error.message, true));
