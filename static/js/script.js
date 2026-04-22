// --- MODAIS ---
function openImportModal() {
  document.getElementById("importModal").style.display = "flex";
}

function closeImportModal() {
  document.getElementById("importModal").style.display = "none";
}

function openConfig() {
  document.getElementById("configModal").style.display = "flex";
  renderizarEmojisConfig();
}

function closeConfig() {
  document.getElementById("configModal").style.display = "none";
}

// --- DADOS ---
function updateCat(title, newCat) {
  fetch("/atualizar_categoria", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title, categoria: newCat }),
  }).then(() => window.location.reload());
}

function toggleContaFixaPaga(id, pago) {
  const mesReferencia = typeof MES_ATUAL !== "undefined" ? MES_ATUAL : "";
  fetch("/atualizar_status_conta_fixa", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, pago, mes_referencia: mesReferencia }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Falha ao atualizar conta fixa");
      }
      return response.json();
    })
    .then(() => window.location.reload())
    .catch((err) => {
      console.error("Erro ao atualizar status da conta fixa:", err);
      alert("Não foi possível atualizar o status da conta fixa.");
      window.location.reload();
    });
}

function salvarERecalcular() {
  const dados = {
    mes_referencia: typeof MES_ATUAL !== "undefined" ? MES_ATUAL : "",
    receitas_detalhadas: [],
    fixas_detalhadas: [],
    pedro_extras_detalhados: [],
  };

  document.querySelectorAll(".item-receita").forEach((div) => {
    const inputs = div.querySelectorAll("input");
    if (inputs[0].value.trim() !== "") {
      dados.receitas_detalhadas.push({
        nome: inputs[0].value.trim(),
        valor: parseFloat(inputs[1].value) || 0,
      });
    }
  });

  document.querySelectorAll(".item-fixa").forEach((div) => {
    const inputs = div.querySelectorAll("input");
    const idInput = div.querySelector(".fixa-id");
    const pagaInput = div.querySelector(".fixa-paga");
    if (inputs[1].value.trim() !== "") {
      dados.fixas_detalhadas.push({
        id: idInput ? idInput.value : "",
        nome: inputs[1].value.trim(),
        valor: parseFloat(inputs[2].value) || 0,
        pago: pagaInput ? pagaInput.checked : false,
      });
    }
  });

  document.querySelectorAll(".item-pedro-extra").forEach((div) => {
    const inputs = div.querySelectorAll("input");
    if (inputs[0].value.trim() !== "") {
      dados.pedro_extras_detalhados.push({
        nome: inputs[0].value.trim(),
        valor: parseFloat(inputs[1].value) || 0,
      });
    }
  });

  const novosEmojis = {};
  document.querySelectorAll(".emoji-config-item").forEach((item) => {
    const cat = item.querySelector(".cat-name").innerText;
    const emoji = item.querySelector("input").value;
    novosEmojis[cat] = emoji;
  });

  // Fallback: se a classe .emoji-config-item não existir, lê os blocos renderizados no modal atual
  if (Object.keys(novosEmojis).length === 0) {
    document.querySelectorAll("#emoji-settings-list > div").forEach((item) => {
      const catEl = item.querySelector(".cat-name");
      const emojiEl = item.querySelector("input");
      if (catEl && emojiEl) {
        novosEmojis[catEl.innerText] = emojiEl.value;
      }
    });
  }

  dados.emojis = novosEmojis;

  fetch("/salvar_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  }).then(() => window.location.reload());
}

function categorizarAutomatico(mes) {
  if (!confirm(`Deseja categorizar itens de ${mes} com base no seu histórico?`)) {
    return;
  }

  fetch("/categorizar_em_lote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mes: mes }),
  })
    .then((response) => {
      if (!response.ok) throw new Error("Erro na resposta do servidor");
      return response.json();
    })
    .then((data) => {
      alert(data.message);
      window.location.reload();
    })
    .catch((err) => {
      console.error("Erro ao categorizar:", err);
      alert("Erro ao processar categorização automática.");
    });
}

function removerArquivo(nome, mes) {
  if (!confirm("Remover todas as compras deste arquivo neste mês?")) return;

  fetch("/remover_arquivo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arquivo: nome, mes: mes }),
  }).then(() => window.location.reload());
}

// --- FILTROS E TABELA ---
function clicarFiltro(cat) {
  const buscaProduto = document.getElementById("buscaProduto");
  const buscaCategoria = document.getElementById("buscaCategoria");
  if (!buscaProduto || !buscaCategoria) return;

  buscaProduto.value = "";
  buscaCategoria.value = cat;
  filtrarTabelaV2();
}

function filtrarTabelaV2() {
  const inputProd = document.getElementById("buscaProduto");
  const inputCat = document.getElementById("buscaCategoria");
  const body = document.getElementById("tabela-body");

  if (!inputProd || !inputCat || !body) return;

  const termoProd = inputProd.value.toLowerCase();
  const termoCat = inputCat.value.toLowerCase();
  const linhas = document.querySelectorAll("#tabela-body tr");
  let somaTotal = 0;

  linhas.forEach((linha) => {
    const desc = linha.cells[1].innerText.toLowerCase();
    const categoriaInput = linha.querySelector(".cat-input");
    const cat = categoriaInput ? categoriaInput.value.toLowerCase() : "";

    const match =
      (termoProd === "" || desc.includes(termoProd)) &&
      (termoCat === "" || cat.includes(termoCat));

    linha.style.display = match ? "" : "none";

    if (match) {
      const textoValor = linha.cells[3].innerText.trim();
      const valorPuro = textoValor.replace("R$", "").trim().replace(".", "").replace(",", ".");
      const valorNum = Number(valorPuro);
      if (!Number.isNaN(valorNum)) {
        somaTotal += valorNum;
      }
    }
  });

  const footer = document.getElementById("tabela-footer");
  const somaDisplay = document.getElementById("soma-filtro");

  if (!footer || !somaDisplay) return;

  if (termoProd !== "" || termoCat !== "") {
    footer.classList.remove("hidden");
    somaDisplay.innerText = "R$ " + somaTotal.toFixed(2).replace(".", ",");
  } else {
    footer.classList.add("hidden");
  }
}

function renderizarEmojisConfig() {
  const container = document.getElementById("emoji-settings-list");
  if (!container) return;

  const inputs = document.querySelectorAll(".cat-input");
  const categoriasDaTabela = Array.from(inputs).map((i) => {
    const valor = i.value.trim();
    return valor.charAt(0).toUpperCase() + valor.slice(1).toLowerCase();
  });

  const categoriasDoDicionario = Object.keys(DICIONARIO_EMOJIS_ATUAL || {});
  const categoriasUnicas = [...new Set([...categoriasDaTabela, ...categoriasDoDicionario])].filter(Boolean);
  categoriasUnicas.sort((a, b) => a.localeCompare(b, "pt-BR"));

  container.innerHTML = categoriasUnicas
    .map((cat) => {
      const emoji = DICIONARIO_EMOJIS_ATUAL[cat] || "🏷️";
      const categoriaSegura = JSON.stringify(cat);
      return `
        <div class="emoji-config-item flex items-center justify-between bg-slate-50 p-2 rounded-lg border border-slate-100 mb-2">
          <span class="cat-name text-[10px] font-bold uppercase text-slate-500">${cat}</span>
          <input
            type="text"
            class="w-10 text-center bg-white border rounded-md text-[10px] p-1"
            value="${emoji}"
            onchange='alterarEmoji(${categoriaSegura}, this.value)'
          >
        </div>
      `;
    })
    .join("");
}

function alterarEmoji(categoria, novoEmoji) {
  fetch("/salvar_emoji", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ categoria: categoria, emoji: novoEmoji }),
  }).catch((err) => console.error("Erro ao salvar emoji:", err));
}

// --- ORDENAÇÃO ---
function ordenarTabela(n) {
  const table = document.getElementById("tabela-body");
  if (!table) return;

  const rows = Array.from(table.rows);
  const direcao = table.getAttribute("data-dir") === "asc" ? "desc" : "asc";

  rows.sort((a, b) => {
    const x = a.getElementsByTagName("TD")[n];
    const y = b.getElementsByTagName("TD")[n];

    if (n === 3) {
      const textoX = x.innerText.trim().replace("R$", "").trim().replace(".", "").replace(",", ".");
      const textoY = y.innerText.trim().replace("R$", "").trim().replace(".", "").replace(",", ".");
      const valX = parseFloat(textoX) || 0;
      const valY = parseFloat(textoY) || 0;
      return direcao === "asc" ? valX - valY : valY - valX;
    }

    if (n === 2) {
      const inputX = x.querySelector(".cat-input");
      const inputY = y.querySelector(".cat-input");
      const valX = inputX ? inputX.value.toLowerCase() : "";
      const valY = inputY ? inputY.value.toLowerCase() : "";
      return direcao === "asc"
        ? valX.localeCompare(valY)
        : valY.localeCompare(valX);
    }

    return direcao === "asc"
      ? x.innerText.toLowerCase().localeCompare(y.innerText.toLowerCase())
      : y.innerText.toLowerCase().localeCompare(x.innerText.toLowerCase());
  });

  table.setAttribute("data-dir", direcao);
  rows.forEach((row) => table.appendChild(row));
}

// --- DASHBOARD ---
function formatarMoeda(valor) {
  return (valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function atualizarComparativoDashboard() {
  const selectA = document.getElementById("compararMesA");
  const selectB = document.getElementById("compararMesB");
  if (!selectA || !selectB || !Array.isArray(DASHBOARD_MENSAL)) return;

  const mesA = DASHBOARD_MENSAL.find((item) => item.mes === selectA.value);
  const mesB = DASHBOARD_MENSAL.find((item) => item.mes === selectB.value);

  const totalA = mesA ? Number(mesA.total) : 0;
  const totalB = mesB ? Number(mesB.total) : 0;
  const delta = totalB - totalA;
  const deltaPct = totalA > 0 ? (delta / totalA) * 100 : 0;

  const totalMesA = document.getElementById("totalMesA");
  const totalMesB = document.getElementById("totalMesB");
  const deltaTotal = document.getElementById("deltaTotal");
  const deltaTotalPercentual = document.getElementById("deltaTotalPercentual");
  const blocoDeltaTotal = document.getElementById("blocoDeltaTotal");

  if (!totalMesA || !totalMesB || !deltaTotal || !deltaTotalPercentual || !blocoDeltaTotal) return;

  totalMesA.innerText = formatarMoeda(totalA);
  totalMesB.innerText = formatarMoeda(totalB);

  const sinal = delta > 0 ? "+" : "";
  deltaTotal.innerText = `${sinal}${formatarMoeda(delta)}`;
  deltaTotalPercentual.innerText = `${sinal}${deltaPct.toFixed(2).replace(".", ",")}%`;

  blocoDeltaTotal.classList.remove("border-red-200", "bg-red-50", "border-emerald-200", "bg-emerald-50", "border-slate-200", "bg-slate-50");

  if (delta > 0) {
    blocoDeltaTotal.classList.add("border-red-200", "bg-red-50");
  } else if (delta < 0) {
    blocoDeltaTotal.classList.add("border-emerald-200", "bg-emerald-50");
  } else {
    blocoDeltaTotal.classList.add("border-slate-200", "bg-slate-50");
  }

  atualizarComparativoCategorias(selectA.value, selectB.value);
}

function atualizarComparativoCategorias(mesA, mesB) {
  const container = document.getElementById("listaComparativoCategorias");
  if (!container) return;

  const categoriasA = (DASHBOARD_CATEGORIAS && DASHBOARD_CATEGORIAS[mesA]) || {};
  const categoriasB = (DASHBOARD_CATEGORIAS && DASHBOARD_CATEGORIAS[mesB]) || {};

  const categorias = new Set([
    ...Object.keys(categoriasA),
    ...Object.keys(categoriasB),
  ]);

  const linhas = Array.from(categorias).map((categoria) => {
    const valorA = Number(categoriasA[categoria] || 0);
    const valorB = Number(categoriasB[categoria] || 0);
    const delta = valorB - valorA;
    const deltaPct = valorA > 0 ? (delta / valorA) * 100 : 0;
    return { categoria, valorA, valorB, delta, deltaPct };
  });

  linhas.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));

  const topLinhas = linhas.slice(0, 10);
  if (topLinhas.length === 0) {
    container.innerHTML = '<p class="text-[11px] text-slate-400">Sem categorias para comparar.</p>';
    return;
  }

  container.innerHTML = topLinhas
    .map((item) => {
      const emoji = (DICIONARIO_EMOJIS_ATUAL && DICIONARIO_EMOJIS_ATUAL[item.categoria]) || "🏷️";
      const sinal = item.delta > 0 ? "+" : "";
      const corDelta =
        item.delta > 0
          ? "text-red-600"
          : item.delta < 0
            ? "text-emerald-600"
            : "text-slate-500";

      return `
        <div class="p-2 rounded-lg border border-slate-100 bg-slate-50">
          <div class="flex justify-between items-center">
            <span class="text-[11px] font-bold text-slate-700">${emoji} ${item.categoria}</span>
            <span class="text-[11px] font-black ${corDelta}">${sinal}${formatarMoeda(item.delta)}</span>
          </div>
          <div class="text-[10px] text-slate-400">
            A: ${formatarMoeda(item.valorA)} | B: ${formatarMoeda(item.valorB)} | ${sinal}${item.deltaPct.toFixed(2).replace(".", ",")}%
          </div>
        </div>
      `;
    })
    .join("");
}

function inicializarDashboard() {
  const selectA = document.getElementById("compararMesA");
  const selectB = document.getElementById("compararMesB");
  if (!selectA || !selectB || !Array.isArray(DASHBOARD_MENSAL) || DASHBOARD_MENSAL.length === 0) return;

  const ultimo = DASHBOARD_MENSAL[DASHBOARD_MENSAL.length - 1]?.mes;
  const penultimo = DASHBOARD_MENSAL[DASHBOARD_MENSAL.length - 2]?.mes || ultimo;

  selectA.value = penultimo;
  selectB.value = ultimo;

  selectA.addEventListener("change", atualizarComparativoDashboard);
  selectB.addEventListener("change", atualizarComparativoDashboard);

  atualizarComparativoDashboard();
}

document.addEventListener("DOMContentLoaded", () => {
  const salvo = localStorage.getItem("sidebar_collapsed");
  if (salvo === "1") {
    document.getElementById("sidebarNav")?.classList.add("collapsed");
  }
  inicializarDashboard();
});

function toggleSidebar() {
  const sidebar = document.getElementById("sidebarNav");
  if (!sidebar) return;
  sidebar.classList.toggle("collapsed");
  localStorage.setItem("sidebar_collapsed", sidebar.classList.contains("collapsed") ? "1" : "0");
}
