/**
 * Таблица автоматики: локтевая / витринная / ZIP × Somfy · Simu · Gaviota (ключ decolife).
 */
(function () {
  "use strict";

  var SEGMENTS = [
    { key: "elbow", label: "Локтевая" },
    { key: "storefront", label: "Витринная" },
    { key: "zip", label: "ZIP" },
  ];
  var BRANDS = [
    { key: "somfy", label: "Somfy" },
    { key: "simu", label: "Simu" },
    { key: "decolife", label: "Gaviota" },
  ];
  var REMOTE_KEYS = [
    { key: "single", label: "1 канал (max)" },
    { key: "dual_light", label: "до 5 каналов (max)" },
    { key: "multi", label: "до 15 каналов (max)" },
  ];

  var activeSegment = "elbow";
  var pricingFullRef = null;

  function $(id) {
    return document.getElementById(id);
  }

  function clearEl(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function setParseStatus(text, ok) {
    var el = $("automationParseStatus");
    if (!el) return;
    el.textContent = text || "";
    el.className = "status " + (ok ? "ok" : "err");
  }

  function ensureRoot() {
    if (!pricingFullRef) return;
    if (!pricingFullRef._automation_eur || typeof pricingFullRef._automation_eur !== "object") {
      pricingFullRef._automation_eur = {};
    }
  }

  function bucket(seg) {
    ensureRoot();
    if (!pricingFullRef._automation_eur[seg]) {
      pricingFullRef._automation_eur[seg] = {
        motor_body: {},
        motor_zip: {},
        manual_eur: 50,
        remotes: {},
        sensor_radio: {},
        sensor_speed: {},
      };
    }
    return pricingFullRef._automation_eur[seg];
  }

  function inpId(seg, suffix) {
    return "auto_" + seg + "_" + suffix;
  }

  function appendSectionTitle(host, text) {
    var t = document.createElement("div");
    t.className = "auto-section-title";
    t.textContent = text;
    host.appendChild(t);
  }

  function renderAutomationEditor() {
    var host = $("automationEditorHost");
    if (!host || !pricingFullRef) return;
    clearEl(host);
    var seg = activeSegment;
    var b = bucket(seg);

    if (seg === "zip") {
      appendSectionTitle(host, "Трубчатый привод ZIP (EUR)");
      var tblz = document.createElement("table");
      tblz.className = "auto-table";
      var trz = document.createElement("tr");
      var th0 = document.createElement("th");
      th0.textContent = "Позиция";
      trz.appendChild(th0);
      var zi;
      for (zi = 0; zi < BRANDS.length; zi++) {
        var th = document.createElement("th");
        th.textContent = BRANDS[zi].label;
        trz.appendChild(th);
      }
      tblz.appendChild(trz);
      var mz = b.motor_zip || {};
      var rowsZip = [
        { label: "Somfy (малый)", keys: ["somfy_small", "", ""] },
        { label: "Somfy (большой)", keys: ["somfy_large", "", ""] },
        { label: "Simu / Gaviota", keys: ["", "simu", "decolife"] },
      ];
      var ri;
      for (ri = 0; ri < rowsZip.length; ri++) {
        var rz = rowsZip[ri];
        var tr = document.createElement("tr");
        var td0 = document.createElement("td");
        td0.className = "brand-col";
        td0.textContent = rz.label;
        tr.appendChild(td0);
        var ci;
        for (ci = 0; ci < 3; ci++) {
          var td = document.createElement("td");
          var k = rz.keys[ci];
          if (k) {
            var inp = document.createElement("input");
            inp.type = "number";
            inp.step = "0.01";
            inp.className = "eur-inp";
            inp.id = inpId(seg, "mz_" + k);
            inp.value = mz[k] != null ? String(mz[k]) : "";
            td.appendChild(inp);
          } else {
            td.textContent = "—";
          }
          tr.appendChild(td);
        }
        tblz.appendChild(tr);
      }
      host.appendChild(tblz);
    } else {
      appendSectionTitle(host, "Трубчатый привод (EUR)");
      var tbl = document.createElement("table");
      tbl.className = "auto-table";
      var trh = document.createElement("tr");
      var thc = document.createElement("th");
      thc.textContent = "Модель привода";
      trh.appendChild(thc);
      var hi;
      for (hi = 0; hi < BRANDS.length; hi++) {
        var thh = document.createElement("th");
        thh.textContent = BRANDS[hi].label;
        trh.appendChild(thh);
      }
      tbl.appendChild(trh);
      var tr1 = document.createElement("tr");
      var tdL = document.createElement("td");
      tdL.className = "brand-col";
      tdL.textContent = "Базовая позиция (прайс)";
      tr1.appendChild(tdL);
      var mb = b.motor_body || {};
      var bi;
      for (bi = 0; bi < BRANDS.length; bi++) {
        var bk = BRANDS[bi].key;
        var tdx = document.createElement("td");
        var inpx = document.createElement("input");
        inpx.type = "number";
        inpx.step = "0.01";
        inpx.className = "eur-inp";
        inpx.id = inpId(seg, "mb_" + bk);
        inpx.value = mb[bk] != null ? String(mb[bk]) : "";
        tdx.appendChild(inpx);
        tr1.appendChild(tdx);
      }
      tbl.appendChild(tr1);
      host.appendChild(tbl);
    }

    appendSectionTitle(host, "Ручное управление");
    var manRow = document.createElement("div");
    manRow.className = "row";
    var manWrap = document.createElement("div");
    var manLab = document.createElement("label");
    manLab.setAttribute("for", inpId(seg, "manual"));
    manLab.textContent = "Редуктор / кренк (EUR)";
    var manInp = document.createElement("input");
    manInp.type = "number";
    manInp.step = "0.01";
    manInp.id = inpId(seg, "manual");
    manInp.value = b.manual_eur != null ? String(b.manual_eur) : "50";
    manWrap.appendChild(manLab);
    manWrap.appendChild(manInp);
    manRow.appendChild(manWrap);
    host.appendChild(manRow);

    appendSectionTitle(host, "Пульты управления (EUR)");
    var rt = document.createElement("table");
    rt.className = "auto-table";
    var rth = document.createElement("tr");
    var rth0 = document.createElement("th");
    rth0.textContent = "Тип / max каналов";
    rth.appendChild(rth0);
    var rh;
    for (rh = 0; rh < BRANDS.length; rh++) {
      var rthb = document.createElement("th");
      rthb.textContent = BRANDS[rh].label;
      rth.appendChild(rthb);
    }
    rt.appendChild(rth);
    var rem = b.remotes || {};
    var rk;
    for (rk = 0; rk < REMOTE_KEYS.length; rk++) {
      var rv = REMOTE_KEYS[rk];
      var rtr = document.createElement("tr");
      var rtd0 = document.createElement("td");
      rtd0.className = "brand-col";
      rtd0.textContent = rv.label;
      rtr.appendChild(rtd0);
      var rx;
      for (rx = 0; rx < BRANDS.length; rx++) {
        var brand = BRANDS[rx].key;
        var pack = (rem[brand] && rem[brand][rv.key]) || {};
        var rtd = document.createElement("td");
        var ilab = document.createElement("input");
        ilab.type = "text";
        ilab.id = inpId(seg, "rm_" + brand + "_" + rv.key + "_l");
        ilab.placeholder = "Название";
        ilab.value = pack.label != null ? String(pack.label) : "";
        var ieur = document.createElement("input");
        ieur.type = "number";
        ieur.step = "0.01";
        ieur.className = "eur-inp";
        ieur.id = inpId(seg, "rm_" + brand + "_" + rv.key + "_e");
        ieur.value = pack.eur != null ? String(pack.eur) : "";
        var icap = document.createElement("input");
        icap.type = "number";
        icap.step = "1";
        icap.min = "1";
        icap.className = "eur-inp";
        icap.style.maxWidth = "4em";
        icap.title = "channels_max — сколько радиоканалов покрывает модель";
        icap.id = inpId(seg, "rm_" + brand + "_" + rv.key + "_c");
        icap.value = pack.channels_max != null ? String(pack.channels_max) : "";
        icap.placeholder = "max";
        rtd.appendChild(ilab);
        rtd.appendChild(document.createElement("br"));
        rtd.appendChild(ieur);
        var capLab = document.createElement("label");
        capLab.setAttribute("for", icap.id);
        capLab.textContent = " кан.";
        capLab.style.marginLeft = "4px";
        capLab.style.fontSize = "12px";
        rtd.appendChild(document.createElement("br"));
        rtd.appendChild(icap);
        rtd.appendChild(capLab);
        rtr.appendChild(rtd);
      }
      rt.appendChild(rtr);
    }
    host.appendChild(rt);

    appendSectionTitle(host, "Датчики (EUR)");
    var st = document.createElement("table");
    st.className = "auto-table";
    var sr = b.sensor_radio || {};
    var ss = b.sensor_speed || {};
    var strh = document.createElement("tr");
    strh.appendChild(document.createElement("th")).textContent = "Тип";
    var sx;
    for (sx = 0; sx < BRANDS.length; sx++) {
      strh.appendChild(document.createElement("th")).textContent = BRANDS[sx].label;
    }
    st.appendChild(strh);
    var trSr = document.createElement("tr");
    trSr.appendChild(document.createElement("td")).textContent = "Радио / ветер";
    for (sx = 0; sx < BRANDS.length; sx++) {
      var bk2 = BRANDS[sx].key;
      var tds = document.createElement("td");
      var isr = document.createElement("input");
      isr.type = "number";
      isr.step = "0.01";
      isr.className = "eur-inp";
      isr.id = inpId(seg, "sr_" + bk2);
      isr.value = sr[bk2] != null ? String(sr[bk2]) : "";
      tds.appendChild(isr);
      trSr.appendChild(tds);
    }
    st.appendChild(trSr);
    var trSp = document.createElement("tr");
    trSp.appendChild(document.createElement("td")).textContent = "Ветер + солнце";
    for (sx = 0; sx < BRANDS.length; sx++) {
      var bk3 = BRANDS[sx].key;
      var tdp = document.createElement("td");
      var isp = document.createElement("input");
      isp.type = "number";
      isp.step = "0.01";
      isp.className = "eur-inp";
      isp.id = inpId(seg, "sp_" + bk3);
      isp.value = ss[bk3] != null ? String(ss[bk3]) : "";
      tdp.appendChild(isp);
      trSp.appendChild(tdp);
    }
    st.appendChild(trSp);
    host.appendChild(st);
  }

  function buildSegTabs() {
    var wrap = $("automationSegTabs");
    if (!wrap || wrap.getAttribute("data-built")) return;
    wrap.setAttribute("data-built", "1");
    var i;
    for (i = 0; i < SEGMENTS.length; i++) {
      var S = SEGMENTS[i];
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = S.label;
      btn.dataset.seg = S.key;
      btn.addEventListener("click", function () {
        flushAutomationPricing();
        activeSegment = this.dataset.seg;
        var j;
        for (j = 0; j < wrap.children.length; j++) {
          wrap.children[j].classList.toggle("active", wrap.children[j] === this);
        }
        renderAutomationEditor();
      });
      wrap.appendChild(btn);
    }
    wrap.children[0].classList.add("active");
  }

  function deepMergeRemotes(target, src) {
    if (!src || typeof src !== "object") return;
    var bk;
    for (bk in src) {
      if (!Object.prototype.hasOwnProperty.call(src, bk)) continue;
      if (!target[bk]) target[bk] = {};
      var vars = src[bk];
      var vk;
      for (vk in vars) {
        if (!Object.prototype.hasOwnProperty.call(vars, vk)) continue;
        var p = vars[vk];
        if (p && typeof p === "object") {
          target[bk][vk] = target[bk][vk] || {};
          if (p.label != null) target[bk][vk].label = String(p.label);
          if (p.eur != null) target[bk][vk].eur = parseFloat(p.eur) || 0;
          if (p.channels_max != null) {
            var cm = parseInt(p.channels_max, 10);
            if (!isNaN(cm) && cm > 0) target[bk][vk].channels_max = cm;
          }
        }
      }
    }
  }

  function mergeOcrIntoActive(data) {
    if (!data || typeof data !== "object") return;
    var b = bucket(activeSegment);
    if (data.motor_body && typeof data.motor_body === "object") {
      b.motor_body = b.motor_body || {};
      var mk;
      for (mk in data.motor_body) {
        if (Object.prototype.hasOwnProperty.call(data.motor_body, mk)) {
          b.motor_body[mk] = parseFloat(data.motor_body[mk]) || 0;
        }
      }
    }
    if (data.motor_zip && typeof data.motor_zip === "object") {
      b.motor_zip = b.motor_zip || {};
      var zk;
      for (zk in data.motor_zip) {
        if (Object.prototype.hasOwnProperty.call(data.motor_zip, zk)) {
          b.motor_zip[zk] = parseFloat(data.motor_zip[zk]) || 0;
        }
      }
    }
    if (data.manual_eur != null) {
      b.manual_eur = parseFloat(data.manual_eur) || 0;
    }
    if (data.remotes) {
      b.remotes = b.remotes || {};
      deepMergeRemotes(b.remotes, data.remotes);
    }
    if (data.sensor_radio && typeof data.sensor_radio === "object") {
      b.sensor_radio = b.sensor_radio || {};
      var sk;
      for (sk in data.sensor_radio) {
        if (Object.prototype.hasOwnProperty.call(data.sensor_radio, sk)) {
          b.sensor_radio[sk] = parseFloat(data.sensor_radio[sk]) || 0;
        }
      }
    }
    if (data.sensor_speed && typeof data.sensor_speed === "object") {
      b.sensor_speed = b.sensor_speed || {};
      var tk;
      for (tk in data.sensor_speed) {
        if (Object.prototype.hasOwnProperty.call(data.sensor_speed, tk)) {
          b.sensor_speed[tk] = parseFloat(data.sensor_speed[tk]) || 0;
        }
      }
    }
    renderAutomationEditor();
  }

  function parseImage() {
    var inp = $("automationImageInput");
    if (!inp || !inp.files || !inp.files[0]) {
      setParseStatus("Выберите изображение", false);
      return;
    }
    setParseStatus("Распознавание…", true);
    var fd = new FormData();
    fd.append("image", inp.files[0]);
    fd.append("segment", activeSegment);
    fetch("/admin/parse-automation-price-image", { method: "POST", credentials: "same-origin", body: fd })
      .then(function (r) {
        return r.json().then(function (j) {
          return { ok: r.ok, j: j };
        });
      })
      .then(function (x) {
        if (!x.ok || !x.j.ok) {
          setParseStatus(x.j.error || "Ошибка", false);
          return;
        }
        mergeOcrIntoActive(x.j.data || {});
        setParseStatus("Данные подставлены в «" + activeSegment + "». Сохраните тарифы.", true);
      })
      .catch(function (e) {
        setParseStatus(String(e), false);
      });
  }

  function flushAutomationPricing() {
    if (!pricingFullRef) return;
    var host = $("automationEditorHost");
    if (!host || !host.firstChild) {
      return;
    }
    ensureRoot();
    var seg = activeSegment;
    var b = bucket(seg);
    if (seg === "zip") {
      b.motor_zip = {};
      var zkeys = ["somfy_small", "somfy_large", "simu", "decolife"];
      var zi;
      for (zi = 0; zi < zkeys.length; zi++) {
        var zk = zkeys[zi];
        var elz = $(inpId(seg, "mz_" + zk));
        if (elz && elz.value !== "") {
          b.motor_zip[zk] = parseFloat(elz.value) || 0;
        }
      }
    } else {
      b.motor_body = {};
      var bi;
      for (bi = 0; bi < BRANDS.length; bi++) {
        var bk = BRANDS[bi].key;
        var elb = $(inpId(seg, "mb_" + bk));
        if (elb && elb.value !== "") {
          b.motor_body[bk] = parseFloat(elb.value) || 0;
        }
      }
    }
    var elman = $(inpId(seg, "manual"));
    if (elman) {
      b.manual_eur = parseFloat(elman.value) || 0;
    }
    b.remotes = {};
    var ri;
    for (ri = 0; ri < BRANDS.length; ri++) {
      var br = BRANDS[ri].key;
      b.remotes[br] = {};
      var rj;
      for (rj = 0; rj < REMOTE_KEYS.length; rj++) {
        var rvk = REMOTE_KEYS[rj].key;
        var il = $(inpId(seg, "rm_" + br + "_" + rvk + "_l"));
        var ie = $(inpId(seg, "rm_" + br + "_" + rvk + "_e"));
        if (il || ie) {
          var ic = $(inpId(seg, "rm_" + br + "_" + rvk + "_c"));
          var packW = {
            label: il && il.value ? String(il.value).trim() : "Пульт управления",
            eur: ie && ie.value !== "" ? parseFloat(ie.value) || 0 : 0,
          };
          if (ic && ic.value !== "") {
            var cm = parseInt(ic.value, 10);
            if (!isNaN(cm) && cm > 0) packW.channels_max = cm;
          }
          b.remotes[br][rvk] = packW;
        }
      }
    }
    b.sensor_radio = {};
    b.sensor_speed = {};
    for (bi = 0; bi < BRANDS.length; bi++) {
      var bk4 = BRANDS[bi].key;
      var els = $(inpId(seg, "sr_" + bk4));
      var elp = $(inpId(seg, "sp_" + bk4));
      if (els && els.value !== "") b.sensor_radio[bk4] = parseFloat(els.value) || 0;
      if (elp && elp.value !== "") b.sensor_speed[bk4] = parseFloat(elp.value) || 0;
    }
  }

  function fillAutomationFromPricing(pf) {
    pricingFullRef = pf;
    buildSegTabs();
    renderAutomationEditor();
  }

  function initAutomationUi() {
    buildSegTabs();
    var btn = $("automationParseBtn");
    if (btn && !btn.getAttribute("data-wired")) {
      btn.setAttribute("data-wired", "1");
      btn.addEventListener("click", parseImage);
    }
  }

  window.flushAutomationPricing = flushAutomationPricing;
  window.fillAutomationFromPricing = fillAutomationFromPricing;
  window.automationAdminInit = initAutomationUi;

  document.addEventListener("DOMContentLoaded", function () {
    initAutomationUi();
  });
})();
