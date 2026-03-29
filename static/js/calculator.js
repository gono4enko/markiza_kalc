/**
 * calculator.js — UI-логика калькулятора маркиз.
 * Секреты (TG-токен, email) удалены.
 * Расчёт и отправка лидов — через Flask API.
 */

(function () {
  'use strict';

  /* =====================================================================
     ПРЕВЬЮ КОНСТРУКЦИИ
  ===================================================================== */
  window.updateConfigPreview = function (sel) {
    var type = document.getElementById('awning-type');
    var preview = document.getElementById('configPreview');
    if (!preview) return;
    var awningType = type ? type.value : 'standard';
    ['cfg-open', 'cfg-semi', 'cfg-cassette', 'cfg-vitrin'].forEach(function (id) {
      var imgEl = document.getElementById(id);
      if (imgEl) imgEl.className = 'cfg-img';
    });
    if (awningType === 'zip') { preview.className = ''; return; }
    var showId = 'cfg-open';
    if (awningType === 'storefront') {
      showId = 'cfg-vitrin';
    } else if (sel) {
      var map = { open: 'cfg-open', semi: 'cfg-semi', cassette: 'cfg-cassette' };
      showId = map[sel.value] || 'cfg-open';
    }
    var activeEl = document.getElementById(showId);
    if (activeEl) activeEl.className = 'cfg-img cfg-active';
    preview.className = 'cfg-visible';
  };

  /* =====================================================================
     КАРУСЕЛЬ ТКАНЕЙ
  ===================================================================== */
  window.tcScroll = function (dir) {
    var t = document.getElementById('tcTrack');
    if (t) t.scrollLeft += dir * 200;
  };

  window.updateFabricPreview = function () {
    var awningType = document.getElementById('awning-type');
    var fabricSel = document.getElementById('fabric');
    var preview = document.getElementById('fabricPreview');
    if (!preview || !awningType || !fabricSel) return;
    if (awningType.value !== 'standard') { preview.style.display = 'none'; return; }
    var brand = fabricSel.value || 'gaviota';
    if (typeof buildFabricCarousel === 'function') buildFabricCarousel(brand);
    preview.style.display = 'block';
  };

  /* =====================================================================
     DOM-ЭЛЕМЕНТЫ
  ===================================================================== */
  var el = {};

  function initElements() {
    el = {
      awningType: document.getElementById('awning-type'),
      config: document.getElementById('config'),
      width: document.getElementById('width'),
      projection: document.getElementById('projection'),
      height: document.getElementById('height'),
      heightGroup: document.getElementById('heightGroup'),
      projectionGroup: document.getElementById('projectionGroup'),
      fabric: document.getElementById('fabric'),
      fabricZip: document.getElementById('fabric-zip'),
      fabricGroup: document.getElementById('fabric-group'),
      fabricZipGroup: document.getElementById('fabric-zip-group'),
      frameColor: document.getElementById('frameColor'),
      frameColorZip: document.getElementById('frameColor-zip'),
      frameColorStdGroup: document.getElementById('frameColor-standard-group'),
      frameColorZipGroup: document.getElementById('frameColor-zip-group'),
      control: document.getElementById('control'),
      motorBrand: document.getElementById('motorBrand'),
      sensorType: document.getElementById('sensorType'),
      sensorGroup: document.getElementById('sensorGroup'),
      lightingOption: document.getElementById('lightingOption'),
      lightingGroup: document.getElementById('lightingGroup'),
      electricOptions: document.getElementById('electricOptions'),
      installationSelect: document.getElementById('installationSelect'),
      calcBtn: document.getElementById('calcBtn'),
      widthHint: document.getElementById('width-unavailable'),
      projHint: document.getElementById('projection-unavailable'),
      heightHint: document.getElementById('height-unavailable'),
    };
  }

  /* =====================================================================
     СОБЫТИЯ
  ===================================================================== */
  function bindEvents() {
    el.awningType.addEventListener('change', switchType);
    el.config.addEventListener('change', updateUI);
    el.control.addEventListener('change', updateUI);
    el.width.addEventListener('input', function () { validateWidth(); updateUI(); });
    el.height.addEventListener('input', function () { validateHeight(); updateUI(); });
    el.projection.addEventListener('change', updateUI);
    el.motorBrand.addEventListener('change', updateUI);
    el.calcBtn.addEventListener('click', doCalculate);
  }

  function switchType() {
    var t = el.awningType.value;
    if (t === 'zip') {
      el.heightGroup.style.display = 'block';
      el.projectionGroup.style.display = 'none';
      el.fabricGroup.style.display = 'none';
      el.fabricZipGroup.style.display = 'block';
      el.frameColorStdGroup.style.display = 'none';
      el.frameColorZipGroup.style.display = 'block';
      el.sensorGroup.style.display = 'none';
      el.lightingGroup.style.display = 'none';
      el.config.options.length = 0;
      [['zip100', 'ZIP 100'], ['zip130', 'ZIP 130']].forEach(function (pair) {
        var o = document.createElement('option');
        o.value = pair[0]; o.textContent = pair[1];
        el.config.appendChild(o);
      });
      el.control.options[0].disabled = true;
      el.control.value = 'electric';
    } else {
      el.heightGroup.style.display = 'none';
      el.projectionGroup.style.display = 'block';
      el.fabricGroup.style.display = 'block';
      el.fabricZipGroup.style.display = 'none';
      el.frameColorStdGroup.style.display = 'block';
      el.frameColorZipGroup.style.display = 'none';
      el.sensorGroup.style.display = 'block';
      el.control.options[0].disabled = false;
      if (t === 'standard') {
        el.config.options.length = 0;
        [['open', 'Открытая'], ['semi', 'Полукассетная'], ['cassette', 'Кассетная']].forEach(function (pair) {
          var o = document.createElement('option');
          o.value = pair[0]; o.textContent = pair[1];
          el.config.appendChild(o);
        });
        el.lightingGroup.style.display = 'block';
        updateProjectionOptions(['1.5', '2.0', '2.5', '3.0', '3.5'], '3.0');
        el.sensorType.options.length = 0;
        [['none', 'Без датчика'], ['radio', 'Датчик ветровых колебаний'], ['speed', 'Датчик ветра и солнца']].forEach(function (pair) {
          var o = document.createElement('option');
          o.value = pair[0]; o.textContent = pair[1];
          el.sensorType.appendChild(o);
        });
      } else {
        el.config.options.length = 0;
        [['g400', 'G400'], ['g450', 'G450']].forEach(function (pair) {
          var o = document.createElement('option');
          o.value = pair[0]; o.textContent = pair[1];
          el.config.appendChild(o);
        });
        el.lightingGroup.style.display = 'none';
        updateProjectionOptions(['0.8', '1.0', '1.4'], '1.0');
        el.sensorType.options.length = 0;
        [['none', 'Без датчика'], ['speed', 'Датчик ветра и солнца']].forEach(function (pair) {
          var o = document.createElement('option');
          o.value = pair[0]; o.textContent = pair[1];
          el.sensorType.appendChild(o);
        });
      }
    }
    updateUI();
    var configSel = document.getElementById('config');
    if (configSel) window.updateConfigPreview(configSel);
  }

  function updateProjectionOptions(opts, def) {
    var cur = el.projection.value;
    el.projection.options.length = 0;
    opts.forEach(function (v) {
      var o = document.createElement('option');
      o.value = v; o.textContent = v;
      if (v === cur) o.selected = true;
      el.projection.appendChild(o);
    });
    if (opts.indexOf(cur) === -1) el.projection.value = def;
  }

  function updateUI() {
    var ctrl = el.control.value;
    el.electricOptions.style.display = ctrl === 'electric' ? 'block' : 'none';
    if (el.awningType.value === 'standard' && el.config.value === 'cassette') {
      Array.from(el.motorBrand.options).forEach(function (o) {
        if (o.value === 'decolife') {
          o.disabled = true;
          if (el.motorBrand.value === 'decolife') el.motorBrand.value = 'simu';
        }
      });
    } else {
      Array.from(el.motorBrand.options).forEach(function (o) { o.disabled = false; });
    }
  }

  function validateWidth() {
    el.widthHint.textContent = '';
    var w = parseFloat(el.width.value);
    var max = el.awningType.value === 'zip' ? 5 : 6;
    if (w > max) { el.widthHint.textContent = 'Максимум ' + max + ' м'; el.width.value = max; }
    if (w < 2) { el.widthHint.textContent = 'Минимум 2 м'; el.width.value = 2; }
  }

  function validateHeight() {
    el.heightHint.textContent = '';
    var h = parseFloat(el.height.value);
    if (h > 5) { el.heightHint.textContent = 'Максимум 5 м'; el.height.value = 5; }
    if (h < 1) { el.heightHint.textContent = 'Минимум 1 м'; el.height.value = 1; }
  }

  /* =====================================================================
     РАСЧЁТ — POST /api/calculate
  ===================================================================== */
  window._calcText = '';

  function doCalculate() {
    var params = {
      awning_type: el.awningType.value,
      config: el.config.value,
      width: parseFloat(el.width.value),
      control: el.control.value,
      installation: el.installationSelect.value,
    };

    if (el.awningType.value === 'zip') {
      params.height = parseFloat(el.height.value);
      params.fabric_zip = el.fabricZip.value;
      params.frame_color_zip = el.frameColorZip.value;
    } else {
      params.projection = parseFloat(el.projection.value);
      params.fabric = el.fabric.value;
      params.frame_color = el.frameColor.value;
    }

    if (el.control.value === 'electric') {
      params.motor_brand = el.motorBrand.value;
      params.sensor_type = el.sensorType ? el.sensorType.value : 'none';
      params.lighting_option = el.lightingOption ? el.lightingOption.value : 'none';
    }

    el.calcBtn.disabled = true;
    el.calcBtn.textContent = 'Считаем…';

    fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) { alert('Ошибка расчёта: ' + data.error); return; }
        renderResult(data);
      })
      .catch(function (err) { alert('Сетевая ошибка: ' + err); })
      .finally(function () {
        el.calcBtn.disabled = false;
        el.calcBtn.textContent = 'Рассчитать стоимость';
      });
  }

  var numFmt = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

  function renderResult(data) {
    var resultPrice = document.getElementById('resultPrice');
    resultPrice.textContent = '';
    var priceText = document.createTextNode(data.total.toLocaleString('ru-RU') + '\u00A0');
    var priceSpan = document.createElement('span');
    priceSpan.textContent = '₽';
    resultPrice.appendChild(priceText);
    resultPrice.appendChild(priceSpan);
    document.getElementById('resultBlock').classList.add('visible');

    // Детализация — строим DOM вместо innerHTML
    var body = document.getElementById('breakdownBody');
    body.textContent = '';
    data.rows.forEach(function (r, i) {
      var row = document.createElement('div');
      row.className = 'bd-row' + (i === data.rows.length - 1 ? ' bd-total' : '');
      var lbl = document.createElement('span');
      lbl.className = 'bd-label';
      lbl.textContent = r[0];
      var val = document.createElement('span');
      val.className = 'bd-val';
      val.textContent = numFmt.format(r[1]);
      row.appendChild(lbl);
      row.appendChild(val);
      body.appendChild(row);
    });
    document.getElementById('breakdownBlock').classList.add('visible');

    window._calcText = data.text;

    // Форма заявки
    var leadSub = document.getElementById('leadSub');
    leadSub.textContent = 'Ваш расчёт: ';
    var strong = document.createElement('strong');
    strong.textContent = data.total.toLocaleString('ru-RU') + ' ₽';
    leadSub.appendChild(strong);
    leadSub.appendChild(document.createTextNode(' — выберите удобный способ связи'));

    setTimeout(function () {
      var lf = document.getElementById('leadForm');
      lf.classList.add('visible');
      lf.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 600);
  }

  /* =====================================================================
     ОТПРАВКА ЛИДА — POST /api/submit-lead
  ===================================================================== */
  window._userCity = window._userCity || 'Не определён';

  (function () {
    if (window._geoDone) return;
    window._geoDone = true;
    var gx = new XMLHttpRequest();
    gx.timeout = 4000;
    gx.open('GET', 'https://ipapi.co/json/');
    gx.onload = function () {
      try {
        var g = JSON.parse(gx.responseText);
        window._userCity = g.city
          ? g.city + (g.region && g.region !== g.city ? ' (' + g.region + ')' : '')
          : g.region || 'Не определён';
      } catch (e) { }
    };
    gx.onerror = gx.ontimeout = function () { };
    gx.send();
  })();

  window.submitLead = function () {
    var inp = document.getElementById('leadPhone');
    var raw = inp.value.replace(/\D/g, '');
    if (raw.length !== 11) { inp.classList.add('err'); inp.focus(); return; }
    var phone = '+' + raw;
    var btn = document.getElementById('leadBtn');
    btn.textContent = 'Отправляем…';
    btn.disabled = true;

    fetch('/api/submit-lead', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone: phone,
        city: window._userCity || 'Не определён',
        calc_text: window._calcText || '',
        channel: 'callback',
      }),
    })
      .then(function () { showOk(phone); })
      .catch(function () { showOk(phone); });
  };

  // Клики по кнопкам мессенджеров
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('#btnWhatsapp,#btnTelegram,#btnMax');
    if (!btn) return;
    var ch = btn.id === 'btnWhatsapp' ? 'whatsapp' : btn.id === 'btnTelegram' ? 'telegram' : 'max';

    try {
      var ymId = window._YM_ID;
      if (typeof ym === 'function' && ymId) ym(ymId, 'reachGoal', 'calculator_lead', { channel: ch, calculator_type: 'awning' });
    } catch (er) { }

    if ((btn.id === 'btnWhatsapp' || btn.id === 'btnTelegram') && window._calcText) {
      e.preventDefault();
      var city = window._userCity || 'Не определён';
      var txt = '📍 Город: ' + city + '\n\nДобрый день! Хочу обсудить расчёт:\n' + window._calcText;
      var enc = encodeURIComponent(txt);
      var url = btn.id === 'btnWhatsapp'
        ? 'https://api.whatsapp.com/send?phone=79064297420&text=' + enc
        : 'https://t.me/comfort_dom_andrey?text=' + enc;
      window.open(url, '_blank');

      // Уведомление бэкенду о переходе
      fetch('/api/submit-lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: '(мессенджер)',
          city: window._userCity || 'Не определён',
          calc_text: window._calcText || '',
          channel: ch,
        }),
      }).catch(function () { });
    }
  });

  function showOk(phone) {
    var lf = document.getElementById('leadForm');
    lf.classList.remove('visible');
    lf.style.display = 'none';
    var s = document.getElementById('leadSuccess');
    var sub = document.getElementById('successSub');
    sub.textContent = 'Перезвоним на ';
    var st = document.createElement('strong');
    st.textContent = phone;
    sub.appendChild(st);
    sub.appendChild(document.createTextNode(' в течение 15 минут. Расчёт уже у менеджера.'));
    s.classList.add('visible');

    try {
      var ymId = window._YM_ID;
      if (typeof ym === 'function' && ymId) ym(ymId, 'reachGoal', 'calculator_lead', { calculator_type: 'awning' });
    } catch (er) { }
  }

  /* =====================================================================
     МАСКА ТЕЛЕФОНА
  ===================================================================== */
  (function () {
    var inp = document.getElementById('leadPhone');
    if (!inp) return;

    function digits(v) {
      var d = v.replace(/\D/g, '');
      if (d.charAt(0) === '8') d = '7' + d.slice(1);
      if (d.length > 0 && d.charAt(0) !== '7') d = '7' + d;
      return d.slice(0, 11);
    }

    function fmt2(d) {
      if (!d) return '';
      var f = '+7';
      if (d.length > 1) f += ' (' + d.slice(1, Math.min(4, d.length));
      if (d.length >= 4) f += ') ' + d.slice(4, Math.min(7, d.length));
      if (d.length >= 7) f += '-' + d.slice(7, Math.min(9, d.length));
      if (d.length >= 9) f += '-' + d.slice(9, 11);
      return f;
    }

    inp.addEventListener('focus', function () {
      if (!this.value) this.value = '+7 (';
      var self = this;
      setTimeout(function () { self.setSelectionRange(self.value.length, self.value.length); }, 0);
    });
    inp.addEventListener('blur', function () { if (digits(this.value).length <= 1) this.value = ''; });
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace') {
        e.preventDefault();
        var d = digits(this.value);
        if (d.length <= 1) { this.value = ''; return; }
        this.value = fmt2(d.slice(0, -1));
        this.setSelectionRange(this.value.length, this.value.length);
        this.classList.remove('err');
      } else if (e.key === 'Delete') {
        e.preventDefault();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        window.submitLead();
      }
    });
    inp.addEventListener('input', function (e) {
      if (e.inputType === 'deleteContentBackward' || e.inputType === 'deleteContentForward') return;
      var d = digits(this.value);
      if (!d) { this.value = ''; return; }
      this.value = fmt2(d);
      this.setSelectionRange(this.value.length, this.value.length);
      this.classList.remove('err');
    });
  })();

  /* =====================================================================
     ИНИЦИАЛИЗАЦИЯ
  ===================================================================== */
  document.addEventListener('DOMContentLoaded', function () {
    initElements();
    bindEvents();

    var awningTypeEl = document.getElementById('awning-type');
    if (awningTypeEl) {
      awningTypeEl.addEventListener('change', function () {
        if (typeof updateAwningPreview === 'function') updateAwningPreview(this.value);
        var configSel = document.getElementById('config');
        if (configSel) window.updateConfigPreview(configSel);
      });
      if (typeof updateAwningPreview === 'function') updateAwningPreview(awningTypeEl.value);
      var configSelInit = document.getElementById('config');
      if (configSelInit) window.updateConfigPreview(configSelInit);
    }

    switchType();
    updateUI();
  });

})();
