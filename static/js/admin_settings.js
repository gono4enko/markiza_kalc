/**
 * Админка: матрицы прайса, тарифы, тексты/картинки КП.
 * DOM собирается через createElement (без innerHTML).
 */
(function () {
  "use strict";

  var MATRIX_KEYS = [
    "PRICES_OPEN",
    "PRICES_SEMI",
    "PRICES_CASSETTE",
    "PRICES_G400",
    "PRICES_G450",
    "ZIP100",
    "ZIP130",
  ];
  var MATRIX_LABELS = {
    PRICES_OPEN: "Локтевая открытая (EUR ячейка)",
    PRICES_SEMI: "Локтевая полукассета",
    PRICES_CASSETTE: "Локтевая кассета",
    PRICES_G400: "Витринная G400",
    PRICES_G450: "Витринная G450",
    ZIP100: "ZIP 100",
    ZIP130: "ZIP 130",
  };
  var MOTOR_BRANDS = ["somfy", "simu", "decolife"];
  var SENSOR_KEYS = [
    "somfy_radio",
    "somfy_speed",
    "simu_radio",
    "simu_speed",
    "decolife_radio",
    "decolife_speed",
  ];

  var pricingFull = null;
  var currentMatrixKey = MATRIX_KEYS[0];

  function $(id) {
    return document.getElementById(id);
  }

  function setStatus(el, text, ok) {
    if (!el) return;
    el.textContent = text;
    el.className = "status " + (ok ? "ok" : "err");
  }

  function clearEl(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function numSortKeys(obj) {
    return Object.keys(obj || {}).sort(function (a, b) {
      return parseFloat(a) - parseFloat(b);
    });
  }

  function initTabs() {
    var btns = document.querySelectorAll(".tab-btn");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var tab = this.getAttribute("data-tab");
        for (var j = 0; j < btns.length; j++) {
          btns[j].classList.toggle("active", btns[j] === this);
        }
        var panels = document.querySelectorAll(".panel");
        for (var k = 0; k < panels.length; k++) {
          panels[k].classList.toggle("active", panels[k].id === "panel-" + tab);
        }
        if (tab === "decolife" && typeof window.decolifeAdminInit === "function") {
          window.decolifeAdminInit();
        }
        if (tab === "scalars" && typeof window.automationAdminInit === "function") {
          window.automationAdminInit();
        }
      });
    }
  }

  function fillMatrixSelect() {
    var sel = $("matrixSelect");
    clearEl(sel);
    for (var i = 0; i < MATRIX_KEYS.length; i++) {
      var k = MATRIX_KEYS[i];
      var opt = document.createElement("option");
      opt.value = k;
      opt.textContent = MATRIX_LABELS[k] || k;
      sel.appendChild(opt);
    }
    sel.value = currentMatrixKey;
  }

  function renderMatrixTable() {
    var table = $("matrixTable");
    clearEl(table);
    if (!pricingFull || !currentMatrixKey) return;
    var tbl = pricingFull[currentMatrixKey];
    if (!tbl || typeof tbl !== "object") return;

    var rowKeys = numSortKeys(tbl);
    var colSet = {};
    for (var r = 0; r < rowKeys.length; r++) {
      var row = tbl[rowKeys[r]];
      if (row && typeof row === "object") {
        var ck = Object.keys(row);
        for (var c = 0; c < ck.length; c++) {
          colSet[ck[c]] = true;
        }
      }
    }
    var colKeys = Object.keys(colSet).sort(function (a, b) {
      return parseFloat(a) - parseFloat(b);
    });

    var thead = document.createElement("thead");
    var trh = document.createElement("tr");
    var th0 = document.createElement("th");
    th0.textContent = "м \\ м";
    trh.appendChild(th0);
    for (var h = 0; h < colKeys.length; h++) {
      var th = document.createElement("th");
      th.textContent = colKeys[h];
      trh.appendChild(th);
    }
    thead.appendChild(trh);
    table.appendChild(thead);

    var tbody = document.createElement("tbody");
    for (var ri = 0; ri < rowKeys.length; ri++) {
      var rk = rowKeys[ri];
      var tr = document.createElement("tr");
      var tdR = document.createElement("td");
      tdR.textContent = rk;
      tr.appendChild(tdR);
      var rowObj = tbl[rk] || {};
      for (var ci = 0; ci < colKeys.length; ci++) {
        var ck = colKeys[ci];
        var td = document.createElement("td");
        var inp = document.createElement("input");
        inp.type = "text";
        inp.setAttribute("inputmode", "decimal");
        var val = rowObj[ck];
        inp.value = val !== undefined && val !== null ? String(val) : "";
        inp.dataset.row = rk;
        inp.dataset.col = ck;
        inp.addEventListener("change", function () {
          var r = this.dataset.row;
          var c = this.dataset.col;
          var v = parseFloat(String(this.value).replace(",", "."));
          if (!pricingFull[currentMatrixKey][r]) {
            pricingFull[currentMatrixKey][r] = {};
          }
          if (isNaN(v)) {
            delete pricingFull[currentMatrixKey][r][c];
          } else {
            pricingFull[currentMatrixKey][r][c] = v;
          }
        });
        td.appendChild(inp);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
  }

  function applyScalarsToPricing() {
    if (!pricingFull) return;
    pricingFull.euro_rate = parseInt($("euro_rate").value, 10) || 100;
    pricingFull._delivery_pct = parseFloat($("delivery_pct").value) || 0;
    pricingFull.use_decolife_open_elbow = $("use_open").checked;
    pricingFull.use_decolife_semi_elbow = $("use_semi").checked;
    pricingFull.use_decolife_cassette_elbow = $("use_cass").checked;
  }

  function fillScalarsFromPricing() {
    if (!pricingFull) return;
    $("euro_rate").value = String(pricingFull.euro_rate != null ? pricingFull.euro_rate : 100);
    $("delivery_pct").value = String(
      pricingFull._delivery_pct != null ? pricingFull._delivery_pct : 0.1
    );
    $("use_open").checked = !!pricingFull.use_decolife_open_elbow;
    $("use_semi").checked = !!pricingFull.use_decolife_semi_elbow;
    $("use_cass").checked = !!pricingFull.use_decolife_cassette_elbow;
  }

  function savePricingJson() {
    if (typeof window.flushAutomationPricing === "function") {
      window.flushAutomationPricing();
    }
    applyScalarsToPricing();
    fetch("/admin/api/pricing-full", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pricingFull),
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (x.ok && x.j.ok) {
          setStatus($("pricingStatus"), "Сохранено.", true);
        } else {
          setStatus($("pricingStatus"), (x.j && x.j.error) || "Ошибка сохранения", false);
        }
      })
      .catch(function () {
        setStatus($("pricingStatus"), "Сеть / сервер", false);
      });
  }

  function saveScalarsOnly() {
    if (typeof window.flushAutomationPricing === "function") {
      window.flushAutomationPricing();
    }
    applyScalarsToPricing();
    fetch("/admin/api/pricing-full", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pricingFull),
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        var good = x.ok && x.j.ok;
        var msg = good ? "Сохранено." : (x.j && x.j.error) || "Ошибка сохранения";
        setStatus($("pricingStatus"), msg, good);
        setStatus($("scalarStatus"), msg, good);
      })
      .catch(function () {
        setStatus($("pricingStatus"), "Сеть / сервер", false);
        setStatus($("scalarStatus"), "Сеть / сервер", false);
      });
  }

  function appendField(parent, labelText, child) {
    var wrap = document.createElement("div");
    wrap.className = "field";
    var lab = document.createElement("label");
    lab.textContent = labelText;
    wrap.appendChild(lab);
    wrap.appendChild(child);
    parent.appendChild(wrap);
    return wrap;
  }

  function appendImageRow(parent, inputId, initialUrl) {
    var row = document.createElement("div");
    row.className = "upload-row";
    var inp = document.createElement("input");
    inp.type = "text";
    inp.id = inputId;
    inp.value = initialUrl || "";
    row.appendChild(inp);
    var file = document.createElement("input");
    file.type = "file";
    file.accept = ".jpg,.jpeg,.png,.webp,.gif";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-sec";
    btn.textContent = "Загрузить файл";
    btn.addEventListener("click", function () {
      file.click();
    });
    file.addEventListener("change", function () {
      if (!file.files || !file.files[0]) return;
      var fd = new FormData();
      fd.append("file", file.files[0]);
      fetch("/admin/api/kp-upload", { method: "POST", body: fd })
        .then(function (r) {
          return r.json();
        })
        .then(function (j) {
          if (j.ok && j.url) {
            inp.value = j.url;
            updateImgPreview(preview, j.url);
          } else {
            alert((j && j.error) || "Ошибка загрузки");
          }
        })
        .catch(function () {
          alert("Ошибка сети");
        });
      file.value = "";
    });
    row.appendChild(btn);
    parent.appendChild(row);
    var preview = document.createElement("img");
    preview.className = "img-prev";
    preview.alt = "";
    parent.appendChild(preview);
    updateImgPreview(preview, inp.value);
    inp.addEventListener("input", function () {
      updateImgPreview(preview, inp.value);
    });
    return inp;
  }

  function updateImgPreview(imgEl, url) {
    if (!imgEl) return;
    var u = (url || "").trim();
    if (u) {
      imgEl.src = u;
      imgEl.style.display = "";
    } else {
      imgEl.removeAttribute("src");
      imgEl.style.display = "none";
    }
  }

  function renderMotorBlocks(merged) {
    var wrap = $("motorsWrap");
    clearEl(wrap);
    var motors = (merged && merged.motors) || {};
    for (var i = 0; i < MOTOR_BRANDS.length; i++) {
      var b = MOTOR_BRANDS[i];
      var m = motors[b] || {};
      var section = document.createElement("div");
      section.className = "section";
      var head = document.createElement("div");
      head.className = "section-h";
      head.textContent = "КП: привод / комплект (" + b + ")";
      section.appendChild(head);
      var body = document.createElement("div");
      body.className = "section-b";

      var d1 = document.createElement("input");
      d1.type = "text";
      d1.id = "motor_" + b + "_disp";
      d1.value = m.display_name || "";
      appendField(body, "Отображаемое имя", d1);

      var d2 = document.createElement("input");
      d2.type = "text";
      d2.id = "motor_" + b + "_head";
      d2.value = m.headline || "";
      appendField(body, "Заголовок блока", d2);

      var taP = document.createElement("textarea");
      taP.id = "motor_" + b + "_princ";
      taP.rows = 4;
      taP.value = m.principle_html || "";
      appendField(body, "Принцип работы (HTML)", taP);

      var imgField = document.createElement("div");
      imgField.className = "field";
      var labImg = document.createElement("label");
      labImg.textContent = "Изображение комплекта / пульта (URL)";
      imgField.appendChild(labImg);
      appendImageRow(imgField, "motor_" + b + "_img", m.image_kit || "");
      body.appendChild(imgField);

      var bh = m.bullets_html || [];
      for (var j = 0; j < 6; j++) {
        var taB = document.createElement("textarea");
        taB.id = "motor_" + b + "_bul_" + j;
        taB.rows = 2;
        taB.value = bh[j] != null ? String(bh[j]) : "";
        appendField(body, "Пункт списка " + (j + 1) + " (HTML)", taB);
      }

      section.appendChild(body);
      wrap.appendChild(section);
    }
  }

  function renderSensorBlocks(merged) {
    var wrap = $("sensorsWrap");
    clearEl(wrap);
    var sensors = (merged && merged.sensors) || {};
    for (var i = 0; i < SENSOR_KEYS.length; i++) {
      var key = SENSOR_KEYS[i];
      var s = sensors[key] || {};
      var section = document.createElement("div");
      section.className = "section";
      var head = document.createElement("div");
      head.className = "section-h";
      head.textContent = "КП: датчик " + key.replace("_", " ");
      section.appendChild(head);
      var body = document.createElement("div");
      body.className = "section-b";

      var inpM = document.createElement("input");
      inpM.type = "text";
      inpM.id = "sensor_" + key + "_model";
      inpM.value = s.model || "";
      appendField(body, "Модель (название)", inpM);

      var taI = document.createElement("textarea");
      taI.id = "sensor_" + key + "_intro";
      taI.rows = 3;
      taI.value = s.intro || "";
      appendField(body, "Вступление (HTML)", taI);

      var imgFieldS = document.createElement("div");
      imgFieldS.className = "field";
      var labImgS = document.createElement("label");
      labImgS.textContent = "Изображение (URL)";
      imgFieldS.appendChild(labImgS);
      appendImageRow(imgFieldS, "sensor_" + key + "_img", s.image || "");
      body.appendChild(imgFieldS);

      var bullets = s.bullets_html || [];
      for (var j = 0; j < 6; j++) {
        var taB = document.createElement("textarea");
        taB.id = "sensor_" + key + "_bul_" + j;
        taB.rows = 2;
        taB.value = bullets[j] != null ? String(bullets[j]) : "";
        appendField(body, "Пункт " + (j + 1) + " (HTML)", taB);
      }

      section.appendChild(body);
      wrap.appendChild(section);
    }
  }

  function fillKpLabels(merged) {
    var pl = (merged && merged.pdf_labels) || {};
    $("pl_eq").value = pl.section_equipment || "";
    $("pl_se").value = pl.section_sensor || "";
    $("pl_dis").value = pl.disclaimer || "";
  }

  function collectKpPayload() {
    var pdf_labels = {
      section_equipment: $("pl_eq").value,
      section_sensor: $("pl_se").value,
      disclaimer: $("pl_dis").value,
    };
    var motors = {};
    for (var i = 0; i < MOTOR_BRANDS.length; i++) {
      var b = MOTOR_BRANDS[i];
      var bullets = [];
      for (var j = 0; j < 6; j++) {
        var ta = $("motor_" + b + "_bul_" + j);
        if (ta && ta.value.trim()) {
          bullets.push(ta.value.trim());
        }
      }
      motors[b] = {
        display_name: $("motor_" + b + "_disp").value,
        headline: $("motor_" + b + "_head").value,
        principle_html: $("motor_" + b + "_princ").value,
        image_kit: $("motor_" + b + "_img").value,
        bullets_html: bullets,
      };
    }
    var sensors = {};
    for (var k = 0; k < SENSOR_KEYS.length; k++) {
      var key = SENSOR_KEYS[k];
      var bl = [];
      for (var j = 0; j < 6; j++) {
        var t = $("sensor_" + key + "_bul_" + j);
        if (t && t.value.trim()) {
          bl.push(t.value.trim());
        }
      }
      sensors[key] = {
        model: $("sensor_" + key + "_model").value,
        intro: $("sensor_" + key + "_intro").value,
        image: $("sensor_" + key + "_img").value,
        bullets_html: bl,
      };
    }
    return {
      version: 1,
      pdf_labels: pdf_labels,
      motors: motors,
      sensors: sensors,
    };
  }

  function saveKp() {
    var payload = collectKpPayload();
    fetch("/admin/api/kp-content", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (x.ok && x.j.ok) {
          setStatus($("kpStatus"), "kp_content.json сохранён.", true);
        } else {
          setStatus($("kpStatus"), (x.j && x.j.error) || "Ошибка", false);
        }
      })
      .catch(function () {
        setStatus($("kpStatus"), "Сеть / сервер", false);
      });
  }

  function loadKpDefaultsToForm() {
    fetch("/admin/api/kp-defaults")
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        fillKpLabels(data);
        renderMotorBlocks(data);
        renderSensorBlocks(data);
        setStatus($("kpStatus"), "Подставлены дефолты из кода (сохраните при необходимости).", true);
      })
      .catch(function () {
        setStatus($("kpStatus"), "Не удалось загрузить дефолты", false);
      });
  }

  function loadAll() {
    fetch("/admin/api/pricing-full")
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        pricingFull = data;
        fillMatrixSelect();
        fillScalarsFromPricing();
        if (typeof window.fillAutomationFromPricing === "function") {
          window.fillAutomationFromPricing(pricingFull);
        }
        renderMatrixTable();
      })
      .catch(function () {
        setStatus($("pricingStatus"), "Не удалось загрузить прайс", false);
      });

    fetch("/admin/api/kp-content")
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        var merged = data.merged || {};
        fillKpLabels(merged);
        renderMotorBlocks(merged);
        renderSensorBlocks(merged);
      })
      .catch(function () {
        setStatus($("kpStatus"), "Не удалось загрузить КП", false);
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    $("matrixSelect").addEventListener("change", function () {
      currentMatrixKey = this.value;
      renderMatrixTable();
    });
    $("savePricingBtn").addEventListener("click", savePricingJson);
    $("saveScalarsBtn").addEventListener("click", saveScalarsOnly);
    $("saveKpBtn").addEventListener("click", saveKp);
    $("kpDefaultsBtn").addEventListener("click", loadKpDefaultsToForm);
    loadAll();
  });
})();
