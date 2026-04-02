/**
 * Админка: матрицы Decolife (decolife_*_elbow.json), OCR, сохранение.
 * DOM через createElement.
 */
(function () {
  "use strict";

  var catalog = null;
  var tierLabels = {};
  var catalogReady = false;
  var state = {
    line: "",
    modelId: "",
    tier: "",
    prices: {},
    widths: [],
    projections: [],
    title: "",
    /** Строки выноса без цен (показать пустой ряд до заполнения ячеек) */
    extraProjections: []
  };

  function $(id) {
    return document.getElementById(id);
  }

  function setStatus(text, ok) {
    var el = $("decolifeStatus");
    if (!el) return;
    el.textContent = text || "";
    el.className = "status " + (ok ? "ok" : "err");
  }

  function clearEl(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function normDim(s) {
    var n = parseFloat(String(s).replace(",", ".").replace(/\s/g, ""));
    if (isNaN(n)) return null;
    return n.toFixed(1);
  }

  function numSort(arr) {
    return (arr || []).slice().sort(function (a, b) {
      return parseFloat(a) - parseFloat(b);
    });
  }

  function recomputeAxes() {
    state.widths = numSort(Object.keys(state.prices));
    var colSet = {};
    var i;
    for (i = 0; i < state.widths.length; i++) {
      var row = state.prices[state.widths[i]] || {};
      var ks = Object.keys(row);
      var j;
      for (j = 0; j < ks.length; j++) {
        colSet[ks[j]] = true;
      }
    }
    var extra = state.extraProjections || [];
    for (i = 0; i < extra.length; i++) {
      colSet[extra[i]] = true;
    }
    state.projections = numSort(Object.keys(colSet));
  }

  function syncPricesFromInputs() {
    var table = $("decolifeMatrixTable");
    if (!table) return;
    var inputs = table.querySelectorAll("input[data-w][data-p]");
    var k;
    for (k = 0; k < inputs.length; k++) {
      var inp = inputs[k];
      var w = inp.getAttribute("data-w");
      var p = inp.getAttribute("data-p");
      var v = parseFloat(String(inp.value).replace(",", "."));
      if (!state.prices[w]) {
        state.prices[w] = {};
      }
      if (isNaN(v) || inp.value === "") {
        delete state.prices[w][p];
      } else {
        state.prices[w][p] = Math.round(v);
      }
    }
    var wk;
    for (wk in state.prices) {
      if (Object.keys(state.prices[wk]).length === 0) {
        delete state.prices[wk];
      }
    }
    recomputeAxes();
  }

  function renderTable() {
    var table = $("decolifeMatrixTable");
    if (!table) return;
    clearEl(table);
    recomputeAxes();

    /* Как в прайс-листе: ширина — по горизонтали (столбцы), вынос — по вертикали (строки). JSON: prices[width][projection]. */
    var thead = document.createElement("thead");
    var trh = document.createElement("tr");
    var th0 = document.createElement("th");
    th0.textContent = "Вынос \\ Ширина";
    trh.appendChild(th0);
    var hi;
    for (hi = 0; hi < state.widths.length; hi++) {
      var wk = state.widths[hi];
      var th = document.createElement("th");
      var del = document.createElement("button");
      del.type = "button";
      del.className = "btn-del";
      del.setAttribute("aria-label", "Удалить столбец ширины");
      del.textContent = "×";
      del.dataset.width = wk;
      del.addEventListener("click", function () {
        syncPricesFromInputs();
        removeWidth(this.dataset.width);
      });
      th.appendChild(document.createTextNode(wk + " "));
      th.appendChild(del);
      trh.appendChild(th);
    }
    thead.appendChild(trh);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    var ri;
    for (ri = 0; ri < state.projections.length; ri++) {
      var pk = state.projections[ri];
      var tr = document.createElement("tr");
      var td0 = document.createElement("td");
      td0.style.whiteSpace = "nowrap";
      td0.appendChild(document.createTextNode(pk + " "));
      var delR = document.createElement("button");
      delR.type = "button";
      delR.className = "btn-del";
      delR.setAttribute("aria-label", "Удалить строку выноса");
      delR.textContent = "×";
      delR.dataset.proj = pk;
      delR.addEventListener("click", function () {
        syncPricesFromInputs();
        removeProjection(this.dataset.proj);
      });
      td0.appendChild(delR);
      tr.appendChild(td0);
      var ci;
      for (ci = 0; ci < state.widths.length; ci++) {
        var wcol = state.widths[ci];
        var rowObj = state.prices[wcol] || {};
        var td = document.createElement("td");
        var inp = document.createElement("input");
        inp.type = "text";
        inp.setAttribute("inputmode", "numeric");
        var val = rowObj[pk];
        inp.value = val !== undefined && val !== null ? String(val) : "";
        inp.dataset.w = wcol;
        inp.dataset.p = pk;
        inp.addEventListener("input", function () {
          this.classList.add("cell-dirty");
        });
        inp.addEventListener("change", function () {
          this.classList.add("cell-dirty");
        });
        td.appendChild(inp);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
  }

  function removeWidth(w) {
    delete state.prices[w];
    recomputeAxes();
    renderTable();
  }

  function removeProjection(p) {
    var i;
    for (i = 0; i < state.widths.length; i++) {
      var w = state.widths[i];
      if (state.prices[w] && state.prices[w][p] !== undefined) {
        delete state.prices[w][p];
      }
    }
    state.extraProjections = (state.extraProjections || []).filter(function (x) {
      return x !== p;
    });
    recomputeAxes();
    renderTable();
  }

  function fillLineSelect() {
    var sel = $("decolifeLineSelect");
    if (!sel || !catalog) return;
    clearEl(sel);
    var i;
    for (i = 0; i < catalog.length; i++) {
      var L = catalog[i];
      var opt = document.createElement("option");
      opt.value = L.key;
      opt.textContent = L.label;
      sel.appendChild(opt);
    }
    if (catalog.length && !state.line) {
      state.line = catalog[0].key;
    }
    sel.value = state.line;
  }

  function fillModelSelect() {
    var sel = $("decolifeModelSelect");
    if (!sel || !catalog) return;
    clearEl(sel);
    var line = null;
    var i;
    for (i = 0; i < catalog.length; i++) {
      if (catalog[i].key === state.line) {
        line = catalog[i];
        break;
      }
    }
    if (!line || !line.models.length) {
      return;
    }
    for (i = 0; i < line.models.length; i++) {
      var m = line.models[i];
      var opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.short_label || m.series || m.id;
      sel.appendChild(opt);
    }
    if (!state.modelId || !sel.querySelector('option[value="' + state.modelId + '"]')) {
      state.modelId = line.models[0].id;
    }
    sel.value = state.modelId;
  }

  function fillTierSelect() {
    var sel = $("decolifeTierSelect");
    if (!sel || !catalog) return;
    clearEl(sel);
    var line = null;
    var i;
    for (i = 0; i < catalog.length; i++) {
      if (catalog[i].key === state.line) {
        line = catalog[i];
        break;
      }
    }
    if (!line) return;
    var model = null;
    for (i = 0; i < line.models.length; i++) {
      if (line.models[i].id === state.modelId) {
        model = line.models[i];
        break;
      }
    }
    if (!model) return;
    var tiers = model.tiers || [];
    for (i = 0; i < tiers.length; i++) {
      var t = tiers[i];
      var opt = document.createElement("option");
      opt.value = t;
      opt.textContent = tierLabels[t] || t;
      sel.appendChild(opt);
    }
    if (!state.tier || !sel.querySelector('option[value="' + state.tier + '"]')) {
      state.tier = tiers[0] || "";
    }
    sel.value = state.tier;
  }

  function updateTitle() {
    var el = $("decolifeMatrixTitle");
    if (!el) return;
    el.textContent = state.title || "—";
  }

  function loadMatrix() {
    if (!state.line || !state.modelId || !state.tier) return;
    setStatus("Загрузка…", true);
    var url = "/admin/api/decolife-matrix?line=" + encodeURIComponent(state.line) +
      "&model_id=" + encodeURIComponent(state.modelId) +
      "&tier=" + encodeURIComponent(state.tier);
    fetch(url, { credentials: "same-origin" })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (!x.ok) {
          setStatus(x.j.error || "Ошибка загрузки", false);
          return;
        }
        var j = x.j;
        state.prices = JSON.parse(JSON.stringify(j.prices || {}));
        state.widths = j.widths || [];
        state.projections = j.projections || [];
        state.extraProjections = [];
        state.title = (j.series || "") + " — " + (j.tier_label || state.tier);
        updateTitle();
        renderTable();
        setStatus("Загружено", true);
      })
      .catch(function (e) {
        setStatus(String(e), false);
      });
  }

  function mergeParsedPrices(prices) {
    var wk = Object.keys(prices || {});
    var i;
    for (i = 0; i < wk.length; i++) {
      var wRaw = wk[i];
      var w = normDim(wRaw);
      if (!w) continue;
      if (!state.prices[w]) {
        state.prices[w] = {};
      }
      var row = prices[wRaw];
      if (!row || typeof row !== "object") continue;
      var pk = Object.keys(row);
      var j;
      for (j = 0; j < pk.length; j++) {
        var pRaw = pk[j];
        var p = normDim(pRaw);
        if (!p) continue;
        var val = row[pRaw];
        var num = parseInt(String(val).replace(/\s/g, "").replace(/\u00a0/g, ""), 10);
        if (!isNaN(num)) {
          state.prices[w][p] = num;
        }
      }
    }
    recomputeAxes();
    renderTable();
    var inputs = $("decolifeMatrixTable").querySelectorAll("input[data-w]");
    for (i = 0; i < inputs.length; i++) {
      inputs[i].classList.add("cell-dirty");
    }
  }

  function saveMatrix() {
    syncPricesFromInputs();
    if (!state.line || !state.modelId || !state.tier) {
      setStatus("Выберите линейку, модель и ткань", false);
      return;
    }
    setStatus("Сохранение…", true);
    fetch("/admin/api/decolife-matrix", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        line: state.line,
        model_id: state.modelId,
        tier: state.tier,
        prices: state.prices
      })
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (!x.ok) {
          setStatus(x.j.error || "Ошибка", false);
          return;
        }
        var inputs = $("decolifeMatrixTable").querySelectorAll("input.cell-dirty");
        var k;
        for (k = 0; k < inputs.length; k++) {
          inputs[k].classList.remove("cell-dirty");
        }
        setStatus("Сохранено, ячеек: " + (x.j.cells_written != null ? x.j.cells_written : "—"), true);
      })
      .catch(function (e) {
        setStatus(String(e), false);
      });
  }

  function parseImage() {
    var inp = $("decolifeImageInput");
    if (!inp || !inp.files || !inp.files[0]) {
      setStatus("Выберите файл изображения", false);
      return;
    }
    if (!state.line || !state.modelId || !state.tier) {
      setStatus("Выберите модель и ткань", false);
      return;
    }
    setStatus("Распознавание…", true);
    var fd = new FormData();
    fd.append("image", inp.files[0]);
    fd.append("line", state.line);
    fd.append("model_id", state.modelId);
    fd.append("tier", state.tier);
    fetch("/admin/parse-decolife-price-image", {
      method: "POST",
      credentials: "same-origin",
      body: fd
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (!x.ok || !x.j.ok) {
          setStatus(x.j.error || "Ошибка OCR", false);
          return;
        }
        var d = x.j.data || {};
        mergeParsedPrices(d.prices || {});
        var st = x.j.stats || {};
        setStatus(
          "Распознано ячеек: " + (st.cells != null ? st.cells : "—") +
            ", правок верификации: " + (st.corrections != null ? st.corrections : 0),
          true
        );
      })
      .catch(function (e) {
        setStatus(String(e), false);
      });
  }

  /** Новый столбец = новая ширина (м). */
  function addWidthColumn() {
    syncPricesFromInputs();
    var raw = $("decolifeNewWidth") && $("decolifeNewWidth").value;
    var w = normDim(raw);
    if (!w) {
      setStatus("Укажите ширину (например 3.5)", false);
      return;
    }
    if (!state.prices[w]) {
      state.prices[w] = {};
    }
    $("decolifeNewWidth").value = "";
    recomputeAxes();
    renderTable();
    setStatus("Добавлен столбец ширины " + w + " м", true);
  }

  /** Новая строка = новый вынос (м). */
  function addProjectionRow() {
    syncPricesFromInputs();
    var raw = $("decolifeNewProj") && $("decolifeNewProj").value;
    var p = normDim(raw);
    if (!p) {
      setStatus("Укажите вынос (например 2.5)", false);
      return;
    }
    if (state.widths.length === 0) {
      setStatus("Сначала добавьте хотя бы один столбец ширины", false);
      return;
    }
    if (!state.extraProjections) {
      state.extraProjections = [];
    }
    if (state.projections.indexOf(p) < 0 && state.extraProjections.indexOf(p) < 0) {
      state.extraProjections.push(p);
    }
    $("decolifeNewProj").value = "";
    recomputeAxes();
    renderTable();
    setStatus("Добавлена строка выноса " + p + " м — введите цены", true);
  }

  function fetchCatalog(cb) {
    if (catalogReady && catalog) {
      cb();
      return;
    }
    fetch("/admin/api/decolife-catalog", { credentials: "same-origin" })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (!x.ok) {
          setStatus(x.j.error || "Каталог недоступен", false);
          return;
        }
        catalog = x.j.lines || [];
        tierLabels = x.j.tier_labels || {};
        catalogReady = true;
        fillLineSelect();
        fillModelSelect();
        fillTierSelect();
        if (cb) {
          cb();
        }
      })
      .catch(function (e) {
        setStatus(String(e), false);
      });
  }

  function wireEvents() {
    var lineSel = $("decolifeLineSelect");
    var modelSel = $("decolifeModelSelect");
    var tierSel = $("decolifeTierSelect");
    if (!lineSel || lineSel.getAttribute("data-wired")) return;
    lineSel.setAttribute("data-wired", "1");

    lineSel.addEventListener("change", function () {
      state.line = lineSel.value;
      state.modelId = "";
      state.tier = "";
      fillModelSelect();
      fillTierSelect();
      loadMatrix();
    });
    modelSel.addEventListener("change", function () {
      state.modelId = modelSel.value;
      state.tier = "";
      fillTierSelect();
      loadMatrix();
    });
    tierSel.addEventListener("change", function () {
      state.tier = tierSel.value;
      loadMatrix();
    });

    $("decolifeParseBtn").addEventListener("click", parseImage);
    $("decolifeSaveBtn").addEventListener("click", saveMatrix);
    $("decolifeAddWidthBtn").addEventListener("click", addWidthColumn);
    $("decolifeAddProjBtn").addEventListener("click", addProjectionRow);
  }

  window.decolifeAdminInit = function () {
    wireEvents();
    fetchCatalog(function () {
      loadMatrix();
    });
  };
})();
