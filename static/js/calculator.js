/**
 * calculator.js — 7-шаговый wizard-калькулятор маркиз.
 * Расчёт и отправка лидов — через Flask API.
 */

(function () {
  'use strict';

  /* =====================================================================
     СОСТОЯНИЕ
  ===================================================================== */
  var state = {
    step: 1,
    awningType: 'standard',
    config: 'open',
    items: [{ width: 4.0, dim: 3.0, qty: 1, tilt170: false, valance: 'none' }],
    fabric: 'gaviota',
    fabricZip: 'veozip',
    veozipColor: '7605-51198',
    soltisCollection: 'soltis86',
    soltisColor: 'soltis-86-50690',
    copacoCollection: 'copacoSerge5',
    copacoColor: 'White-White-002002',
    frameColor: 'white',
    frameColorZip: 'ral9016',
    control: 'electric',
    motorBrand: 'decolife',
    sensorType: 'none',
    lightingOption: 'none',
    /** Многоканальный пульт (несколько маркиз); иначе при LED — пульт 2 канала */
    multiChannelRemote: false,
    installation: 'none',
    /** Выбранный оттенок стандартной ткани (локтевые / витринные) */
    fabricStdSwatch: null,
  };

  /* =====================================================================
     МЕТАДАННЫЕ СЕРИЙ ТКАНИ Sattler (локтевые / витринные)
  ===================================================================== */
  var STD_FABRIC_SERIES = {
    gaviota: {
      cardTitle: 'Gaviota',
      badge: 'Sattler SUN-TEX',
      description:
        'Базовая линейка: 100% solution-dyed акрил и отделка TEXgard — УФ-стойкость, отталкивание воды и грязи, мягкий текстильный вид. Оптимальное соотношение цены и срока службы на террасах и витринах.',
      catLine: '1-я категория · без доплаты',
      lightboxTitle: 'Gaviota',
    },
    elements: {
      cardTitle: 'Sattler Elements',
      badge: 'Sattler SUN-TEX',
      description:
        'Качество ELEMENTS: spin-dyed акрил с вплетённой УФ-защитой, линии Urban Design, Solids и Stripes. Яркие устойчивые цвета и рисунки для фасадов, где важен характер полотна.',
      catLine: '2-я категория · +5%',
      lightboxTitle: 'Sattler Elements',
    },
    solids: {
      cardTitle: 'Sattler Solids',
      badge: 'Sattler SUN-TEX',
      description:
        'Спокойные однотоны и тонкие фактуры Elements Solids: архитектурная палитра, ровная поверхность и дисциплинированный вид витрины или террасы.',
      catLine: '2-я категория · +5%',
      lightboxTitle: 'Sattler Solids',
    },
    lumera: {
      cardTitle: 'Sattler Lumera',
      badge: 'Sattler SUN-TEX · CBA',
      description:
        'Премиальное качество Lumera с волокном CBA (Clean Brilliant Acrylic): более гладкая «сияющая» поверхность, лучшее сцепление загрязнений для смыва, насыщенный цвет. Доступна линия All Weather с влагозащитой IPC.',
      catLine: '3-я категория · +10%',
      lightboxTitle: 'Sattler Lumera',
    },
    lumera3d: {
      cardTitle: 'Sattler Lumera 3D',
      badge: 'Sattler SUN-TEX · CBA',
      description:
        'Объёмные структуры Lumera 3D Surface: фактурный рисунок при преимуществах CBA-акрила — для премиальных объектов, где ткань — часть дизайна фасада.',
      catLine: '3-я категория · +10%',
      lightboxTitle: 'Sattler Lumera 3D',
    },
  };

  /* =====================================================================
     ДАННЫЕ ТКАНИ VEOZIP (Soltis Veozip / Veosol)
  ===================================================================== */
  var VEOZIP_COLORS = [
    '7605-51198','7605-51197','7605-51196','7605-51195',
    '7605-51194','7605-51193','7605-51192','7605-51191',
    '7605-51190','7605-51189','7605-51188','7605-51187',
    '7605-51186','7605-51185','7605-51184'
  ];

  /* =====================================================================
     ДАННЫЕ КОЛЛЕКЦИЙ SOLTIS 86/92
  ===================================================================== */
  var SOLTIS_COLLECTIONS = [
    {
      id: 'soltis86', label: 'Soltis 86', badge: 'O.F. 5%',
      desc: 'Максимальная прозрачность — до 28% естественного света. Хороший обзор изнутри. Базовая линейка для фасадных ZIP-маркиз.',
      fabrics: [
        {article:'soltis-86-50690', short:'50690'},
        {article:'soltis-86-2044',  short:'2044'},
        {article:'soltis-86-2171',  short:'2171'},
        {article:'soltis-86-2175',  short:'2175'},
        {article:'soltis-86-2135',  short:'2135'},
        {article:'soltis-86-2012',  short:'2012'},
        {article:'soltis-86-2043',  short:'2043'},
        {article:'soltis-86-2047',  short:'2047'},
        {article:'soltis-86-2167',  short:'2167'},
        {article:'soltis-86-51176', short:'51176'},
      ]
    },
    {
      id: 'soltis96', label: 'Soltis 96', badge: 'O.F. 3%',
      desc: 'Усиленная тепловая защита и затенение. Микроперфорация обеспечивает циркуляцию воздуха. Идеально для террас и южных фасадов.',
      fabrics: [
        {article:'96-8102', short:'8102'},
        {article:'96-1103', short:'1103'},
        {article:'96-8861', short:'8861'},
        {article:'96-2135', short:'2135'},
        {article:'96-2171', short:'2171'},
        {article:'96-2043', short:'2043'},
        {article:'96-2047', short:'2047'},
        {article:'96-8450', short:'8450'},
      ]
    },
    {
      id: 'soltisW88', label: 'Soltis W88', badge: 'Водонепр.',
      desc: '100% водонепроницаемость (10 000 мм), лёгкая (490 г/м²). Квадратное переплетение, до 21% света. Подходит для маркиз с повышенной защитой от дождя.',
      fabrics: [
        {article:'W88-8102', short:'8102'},
        {article:'W88-1103', short:'1103'},
        {article:'W88-8861', short:'8861'},
        {article:'W88-2171', short:'2171'},
        {article:'W88-2047', short:'2047'},
      ]
    },
    {
      id: 'soltisW96', label: 'Soltis W96', badge: 'O.F. 3%',
      desc: 'Водонепроницаемая версия Soltis 96. Асимметричное плетение, усиленная плотность. Максимум затенения + защита от дождя.',
      fabrics: [
        {article:'W96-8102', short:'8102'},
        {article:'W96-1103', short:'1103'},
        {article:'W96-8861', short:'8861'},
        {article:'W96-2171', short:'2171'},
        {article:'W96-2047', short:'2047'},
      ]
    },
    {
      id: 'stam6002', label: 'Stam 6002', badge: 'Blackout',
      desc: 'Полное светоблокирование. Плотная ткань 630 г/м², огнестойкая (M2/B1). Матовое PVDF-покрытие. Для зон с требованием полной темноты.',
      fabrics: [
        {article:'6002-20213', short:'20213'},
        {article:'6002-20211', short:'20211'},
        {article:'6002-20209', short:'20209'},
        {article:'6002-20205', short:'20205'},
      ]
    },
  ];

  /* =====================================================================
     ДАННЫЕ КОЛЛЕКЦИЙ COPACO (Screen)
  ===================================================================== */
  var COPACO_COLLECTIONS = [
    {
      id: 'copacoSerge5', label: 'Copaco Serge', badge: 'O.F. 5%',
      desc: 'Базовая наружная серия из стекловолокна с ПВХ-покрытием. Хороший баланс прозрачности и защиты от солнца. Отражает тепло снаружи, сохраняет вид изнутри.',
      fabrics: [
        {article:'White-White-002002',          display:'White-White'},
        {article:'White-Pearl-grey-002007',     display:'White-Pearl-grey'},
        {article:'Linen-White-008002',          display:'Linen-White'},
        {article:'Linen-Linen-008008',          display:'Linen-Linen'},
        {article:'Pearl-grey-Pearl-grey-007007',display:'Pearl-grey'},
        {article:'Sandstone-033033',            display:'Sandstone'},
        {article:'Sand-Sand-003003',            display:'Sand'},
        {article:'Grey-Grey-001001',            display:'Grey-Grey'},
        {article:'Grey-Charcoal-001010',        display:'Grey-Charcoal'},
        {article:'Charcoal-Bronze-001011',      display:'Charcoal-Bronze'},
        {article:'Charcoal-Charcoal-010010',    display:'Charcoal'},
      ]
    },
    {
      id: 'copacoSerge1', label: 'Copaco Serge', badge: 'O.F. 1%',
      desc: 'Плотная версия с максимальной тепловой защитой: отражает 71% солнечного излучения. Стекловолокно + ПВХ, 620 г/м². Минимальный просвет — больше приватности и затенения.',
      fabrics: [
        {article:'White-002002',     display:'White'},
        {article:'Pearl-Grey-007007',display:'Pearl-Grey'},
        {article:'Linen-008008',     display:'Linen'},
        {article:'Pearl-Grey-002007',display:'Pearl-Grey/White'},
        {article:'Grey-001001',      display:'Grey'},
        {article:'Charcoal-001010',  display:'Charcoal'},
      ]
    },
    {
      id: 'copacoSolar', label: 'Copaco Solar', badge: 'O.F. 3%',
      desc: 'Инновационная Block-серия специально для ZIP-систем. Сочетает частичное блокирование с минимальной прозрачностью (3%). Ширина рулона 300 см — меньше швов на больших проёмах.',
      fabrics: [
        {article:'White-White-002002',          display:'White-White'},
        {article:'Pearl-grey-Pearl-grey-007007',display:'Pearl-grey'},
        {article:'Grey-Grey-001001',            display:'Grey-Grey'},
        {article:'Charcoal-Charcoal-001010',    display:'Charcoal'},
      ]
    },
    {
      id: 'copacoLunar', label: 'Copaco Lunar', badge: 'O.F. 0%',
      desc: 'Полное светоблокирование (0% просвет) для ZIP-систем. Максимальная тепло- и светозащита. Рекомендован Copaco для ZIP-маркиз. Для веранд, спален, медиазон.',
      fabrics: [
        {article:'White-Silver-002002',        display:'White-Silver'},
        {article:'Pearl-grey-Silver-007007',   display:'Pearl-grey-Silver'},
        {article:'Grey-Silver-001001',         display:'Grey-Silver'},
        {article:'Charcoal-Silver-001010',     display:'Charcoal-Silver'},
      ]
    },
  ];

  var TOTAL_STEPS = 7;
  var PROJ_STANDARD = ['1.5', '2.0', '2.5', '3.0', '3.5'];
  /** Открытая локтевая Gaviota (прайс): до 4 м вылета (G200 — по прайсу; расчёт G200 в JSON пока без матрицы) */
  var PROJ_OPEN_DECOLIFE = ['1.5', '2.0', '2.5', '3.0', '3.5', '4.0'];
  /** Полукассетная G110 / G220 — до 4 м вылета */
  var PROJ_SEMI_DECOLIFE = ['1.5', '2.0', '2.5', '3.0', '3.5', '4.0'];
  /** Кассетная G500 / G600 / G700 — до 4 м (G700) */
  var PROJ_CASSETTE_DECOLIFE = ['1.5', '2.0', '2.5', '3.0', '3.5', '4.0'];
  var PROJ_STOREFRONT = ['0.8', '1.0', '1.4'];
  var numFmt = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

  window._calcText = '';
  window._userCity = window._userCity || 'Не определён';

  /* =====================================================================
     ВСПОМОГАТЕЛЬНЫЕ
  ===================================================================== */
  function getProjections() {
    if (state.awningType === 'storefront') return PROJ_STOREFRONT;
    if (state.awningType === 'standard' && state.config === 'open') return PROJ_OPEN_DECOLIFE;
    if (state.awningType === 'standard' && state.config === 'semi') return PROJ_SEMI_DECOLIFE;
    if (state.awningType === 'standard' && state.config === 'cassette') return PROJ_CASSETTE_DECOLIFE;
    return PROJ_STANDARD;
  }

  /** Вылет из state: число 3 и строка '3.0' в <select> не совпадали → сброс на средний вылет. Приводим к ключу из getProjections(). */
  function normalizeProjectionDim(dim) {
    var projs = getProjections();
    var n = Number(dim);
    if (!isFinite(n)) return parseFloat(projs[Math.floor(projs.length / 2)] || projs[0]);
    var key = n.toFixed(1);
    if (projs.indexOf(key) === -1) {
      return parseFloat(projs[Math.floor(projs.length / 2)] || projs[0]);
    }
    return parseFloat(key);
  }

  function getConfigOptions() {
    if (state.awningType === 'standard') {
      return [
        {
          value: 'open',
          label: 'Открытая',
          desc: 'Gaviota: серия G90 / G100 / G300 подбирается по размерам и минимальной цене (прайс EUR × курс)',
        },
        {
          value: 'semi',
          label: 'Полукассетная',
          desc: 'Gaviota G110 / G220 — защитный козырёк над валом; серия по минимальной цене',
        },
        {
          value: 'cassette',
          label: 'Кассетная',
          desc: 'Gaviota G500 / G600 / G700 — полная защита ткани в коробе; серия по минимальной цене',
        },
      ];
    }
    if (state.awningType === 'storefront') {
      return [
        {
          value: 'g400',
          label: 'G400 Italy',
          desc:
            'Gaviota — открытая витринная маркиза: лёгкий алюминиевый каркас, спускающиеся локти с пружиной (ветер не складывает полотно, хорошее натяжение ткани). В комплекте — универсальные настенно-потолочные кронштейны, угол 90°. До 7 м в ширину, вынос до 1,4 м.',
        },
        {
          value: 'g450',
          label: 'G450 Desert',
          desc:
            'Gaviota — кассетная витринная маркиза: герметичный короб защищает ткань и механизм от пыли и влаги, продлевая срок службы. Строгий дизайн; в стандарте потолочный крепёж и угол 90°. До 7 м в ширину, вынос до 1,25 м.',
        },
      ];
    }
    return [
      { value: 'zip100', label: 'ZIP 100', desc: 'Короб 100×90 мм · макс. 4×3,5 м' },
      { value: 'zip130', label: 'ZIP 130', desc: 'Короб 130×100 мм · макс. 5×5 м' },
    ];
  }

  /* =====================================================================
     НАВИГАЦИЯ
  ===================================================================== */
  var _goingBack = false;
  var _fabricNavFloatTimer = null;
  var _fabricIdleGuardOpts = { capture: true, passive: true };
  var _fabricIdleBaseY = 0;
  var _fabricIdleBaseX = 0;
  var _fabricIdleWinY = 0;
  var _fabricIdleWinX = 0;

  function captureFabricIdleScrollBaseline() {
    var root = document.scrollingElement || document.documentElement;
    _fabricIdleBaseY = root.scrollTop;
    _fabricIdleBaseX = root.scrollLeft;
    _fabricIdleWinY = window.pageYOffset || 0;
    _fabricIdleWinX = window.pageXOffset || 0;
  }

  /** Отмена таймера «Ткань выбрана» — заметный скролл страницы или колесо (порог отсекает шум и закрытие лайтбокса) */
  function fabricIdleGuardCancelTimer() {
    if (_fabricNavFloatTimer) {
      clearTimeout(_fabricNavFloatTimer);
      _fabricNavFloatTimer = null;
    }
    detachFabricFloatIdleGuards();
  }

  function fabricIdleGuardOnScroll() {
    if (!_fabricNavFloatTimer) return;
    var root = document.scrollingElement || document.documentElement;
    var dy = Math.abs(root.scrollTop - _fabricIdleBaseY);
    var dx = Math.abs(root.scrollLeft - _fabricIdleBaseX);
    var wy = Math.abs((window.pageYOffset || 0) - _fabricIdleWinY);
    var wx = Math.abs((window.pageXOffset || 0) - _fabricIdleWinX);
    if (dy < 14 && dx < 14 && wy < 14 && wx < 14) return;
    fabricIdleGuardCancelTimer();
  }

  function fabricIdleGuardOnWheel(e) {
    if (!_fabricNavFloatTimer) return;
    if (Math.abs(e.deltaY) < 24 && Math.abs(e.deltaX) < 24) return;
    fabricIdleGuardCancelTimer();
  }

  function detachFabricFloatIdleGuards() {
    document.removeEventListener('scroll', fabricIdleGuardOnScroll, _fabricIdleGuardOpts);
    window.removeEventListener('scroll', fabricIdleGuardOnScroll, _fabricIdleGuardOpts);
    window.removeEventListener('wheel', fabricIdleGuardOnWheel, _fabricIdleGuardOpts);
  }

  function attachFabricFloatIdleGuards() {
    detachFabricFloatIdleGuards();
    document.addEventListener('scroll', fabricIdleGuardOnScroll, _fabricIdleGuardOpts);
    window.addEventListener('scroll', fabricIdleGuardOnScroll, _fabricIdleGuardOpts);
    window.addEventListener('wheel', fabricIdleGuardOnWheel, _fabricIdleGuardOpts);
  }

  function goTo(step, back) {
    hideFabricNavFloat();
    _goingBack = !!back;
    state.step = step;
    render();
    window.scrollTo(0, 0);
  }

  function goNext() {
    if (!validateStep(state.step)) return;
    if (state.step < TOTAL_STEPS) goTo(state.step + 1, false);
  }

  function goPrev() {
    if (state.step > 1) goTo(state.step - 1, true);
  }

  /* =====================================================================
     РЕНДЕР ВСЕГО
  ===================================================================== */
  function render() {
    renderProgress();
    renderPanels();
    renderNav();
    renderStepContent(state.step);
  }

  function renderProgress() {
    for (var i = 1; i <= TOTAL_STEPS; i++) {
      var dot = document.getElementById('wzDot' + i);
      var lbl = document.getElementById('wzLbl' + i);
      var line = document.getElementById('wzLine' + i);
      if (dot) {
        dot.className = 'wz-step-dot' + (i === state.step ? ' active' : i < state.step ? ' done' : '');
      }
      if (lbl) {
        lbl.className = 'wz-step-label' + (i === state.step ? ' active' : '');
      }
      if (line) {
        line.className = 'wz-step-line' + (i < state.step ? ' done' : '');
      }
    }
  }

  function renderPanels() {
    for (var i = 1; i <= TOTAL_STEPS; i++) {
      var panel = document.querySelector('[data-step="' + i + '"]');
      if (!panel) continue;
      if (i === state.step) {
        panel.className = 'wz-panel wz-active' + (_goingBack ? ' wz-panel-back' : '');
      } else {
        panel.className = 'wz-panel';
      }
    }
  }

  function renderNav() {
    var prev = document.getElementById('wzPrev');
    var next = document.getElementById('wzNext');
    var calc = document.getElementById('wzCalc');
    if (prev) prev.style.display = state.step > 1 ? 'block' : 'none';
    if (next) next.style.display = state.step < TOTAL_STEPS ? 'block' : 'none';
    if (calc) calc.style.display = state.step === TOTAL_STEPS ? 'block' : 'none';
  }

  function renderStepContent(step) {
    if (step === 1) renderStep1();
    if (step === 2) renderStep2();
    if (step === 3) renderStep3();
    if (step === 4) renderStep4();
    if (step === 5) renderStep5();
    if (step === 6) renderStep6();
  }

  /* =====================================================================
     ШАГ 1: ВИД МАРКИЗЫ
  ===================================================================== */
  function renderStep1() {
    syncCardGroup('typeCards', state.awningType);
    if (typeof updateAwningPreview === 'function') updateAwningPreview(state.awningType);
  }

  /* =====================================================================
     ШАГ 2: ТИП КОНСТРУКЦИИ
  ===================================================================== */
  function renderStep2() {
    var sub = document.getElementById('configStepSub');
    if (sub) {
      sub.textContent =
        state.awningType === 'standard' ? 'Выберите тип локтевой маркизы'
        : state.awningType === 'storefront' ? 'Выберите модель витринной маркизы'
        : 'Выберите модель ZIP маркизы';
    }

    var container = document.getElementById('configCards');
    if (!container) return;

    var opts = getConfigOptions();

    // Ensure config value is valid for current type
    var validValues = opts.map(function(o) { return o.value; });
    if (validValues.indexOf(state.config) === -1) state.config = opts[0].value;

    // Determine columns
    container.className = 'choice-grid choice-grid-' + opts.length;

    while (container.firstChild) container.removeChild(container.firstChild);

    opts.forEach(function(opt) {
      var card = document.createElement('div');
      card.className = 'choice-card' + (state.config === opt.value ? ' selected' : '');
      card.dataset.value = opt.value;

      var lbl = document.createElement('div');
      lbl.className = 'choice-card-label';
      lbl.textContent = opt.label;

      var desc = document.createElement('div');
      desc.className = 'choice-card-desc';
      desc.textContent = opt.desc;

      card.appendChild(lbl);
      card.appendChild(desc);

      card.addEventListener('click', function () {
        state.config = opt.value;
        container.querySelectorAll('.choice-card').forEach(function (c) {
          c.classList.toggle('selected', c.dataset.value === opt.value);
        });
        updateConfigPreview();
      });

      container.appendChild(card);
    });

    var elbowPanel = document.getElementById('elbowArmsPanel');
    if (elbowPanel) {
      if (state.awningType === 'standard') {
        elbowPanel.classList.add('visible');
      } else {
        elbowPanel.classList.remove('visible');
      }
    }

    updateConfigPreview();
  }

  function updateConfigPreview() {
    var preview    = document.getElementById('configPreview');
    var zipPreview = document.getElementById('zipSchemePreview');

    if (state.awningType === 'zip') {
      if (preview) preview.style.display = 'none';
      renderZipScheme(zipPreview);
      return;
    }

    if (zipPreview) zipPreview.style.display = 'none';
    if (!preview) return;
    preview.style.display = 'block';

    var map = { open: 'cfg-open', semi: 'cfg-semi', cassette: 'cfg-cassette', g400: 'cfg-vitrin', g450: 'cfg-vitrin-g450' };
    var activeId = map[state.config] || 'cfg-open';

    ['cfg-open', 'cfg-semi', 'cfg-cassette', 'cfg-vitrin', 'cfg-vitrin-g450'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.className = 'cfg-img' + (id === activeId ? ' cfg-active' : '');
    });
  }

  var ZIP_SCHEME_DATA = {
    zip100: {
      img:   '/static/img/zip100_scheme.png',
      title: 'ZIP 100',
      dims: [
        { label: 'Размер короба',  val: '100 × 90 мм' },
        { label: 'Макс. ширина',   val: '4 000 мм' },
        { label: 'Макс. высота',   val: '3 500 мм' },
        { label: 'Нижняя планка',  val: '45 × 40 мм' },
        { label: 'Направляющая',   val: '27 / 48 мм' },
      ],
      hint: 'Компактный короб 100×90 мм легко вписывается в большинство фасадных решений. Подходит для стандартных оконных и дверных проёмов.'
    },
    zip130: {
      img:   '/static/img/zip130_scheme.png',
      title: 'ZIP 130',
      dims: [
        { label: 'Размер короба',  val: '130 × 100 мм' },
        { label: 'Макс. ширина',   val: '5 000 мм' },
        { label: 'Макс. высота',   val: '5 000 мм' },
        { label: 'Нижняя планка',  val: '65 × 50 мм' },
        { label: 'Направляющая',   val: '40 / 50 мм' },
      ],
      hint: 'Усиленный короб 130×100 мм для больших проёмов. Оптимальный выбор для панорамных окон, зимних садов и широких террас.'
    }
  };

  function renderZipScheme(container) {
    if (!container) return;

    var data = ZIP_SCHEME_DATA[state.config];
    if (!data) { container.style.display = 'none'; return; }

    container.style.display = 'block';

    var dimsHtml = data.dims.map(function (d) {
      return '<div class="zip-scheme-dim-row">'
        + '<span class="zip-scheme-dim-label">' + d.label + '</span>'
        + '<span class="zip-scheme-dim-val">' + d.val + '</span>'
        + '</div>';
    }).join('');

    container.innerHTML =
      '<div class="zip-scheme-wrap">'
      + '<div class="zip-scheme-img-col">'
      +   '<img src="' + data.img + '" alt="' + data.title + ' схема" id="zipSchemeImg">'
      + '</div>'
      + '<div class="zip-scheme-info">'
      +   '<div class="zip-scheme-badge">Технический чертёж</div>'
      +   '<div class="zip-scheme-title">' + data.title + '</div>'
      +   '<div class="zip-scheme-dims">' + dimsHtml + '</div>'
      +   '<div class="zip-scheme-hint">' + data.hint + '</div>'
      + '</div>'
      + '</div>';

    // Click-to-zoom схемы
    var schImg = container.querySelector('#zipSchemeImg');
    if (schImg) {
      schImg.addEventListener('click', function () {
        openSchemeZoom(data.img, data.title);
      });
    }
  }

  function openSchemeZoom(src, title) {
    var existing = document.getElementById('schemeZoomOverlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.id = 'schemeZoomOverlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9998;display:flex;align-items:center;justify-content:center;background:rgba(10,14,30,0.8);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);cursor:zoom-out;animation:fadeIn .22s ease';

    var img = document.createElement('img');
    img.src = src;
    img.alt = title;
    img.style.cssText = 'max-width:90vw;max-height:90vh;object-fit:contain;border-radius:12px;box-shadow:0 24px 64px rgba(0,0,0,0.5);animation:scaleIn .25s cubic-bezier(.34,1.56,.64,1)';

    overlay.appendChild(img);
    overlay.addEventListener('click', function () { overlay.remove(); document.body.style.overflow = ''; });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', esc); }
    });

    document.body.style.overflow = 'hidden';
    document.body.appendChild(overlay);
  }

  /* =====================================================================
     ШАГ 3: РАЗМЕРЫ И КОЛИЧЕСТВО
  ===================================================================== */
  function renderStep3() {
    var sub = document.getElementById('sizeStepSub');
    if (sub) {
      sub.textContent = state.awningType === 'zip'
        ? 'Укажите ширину и высоту для каждой ZIP маркизы'
        : 'Укажите ширину и вылет для каждой маркизы';
    }
    var notice = document.getElementById('zipUpgradeNotice');
    if (notice) notice.classList.remove('visible');
    ensureItemDims();
    renderRows();
    if (state.awningType === 'zip') checkZipAutoSwitch();
  }

  function ensureItemDims() {
    if (state.awningType === 'zip') return;
    state.items.forEach(function (item) {
      item.dim = normalizeProjectionDim(item.dim);
    });
  }

  function renderRows() {
    var wrap = document.getElementById('sizeRows');
    if (!wrap) return;
    while (wrap.firstChild) wrap.removeChild(wrap.firstChild);
    state.items.forEach(function (item, idx) {
      wrap.appendChild(buildRow(item, idx));
    });
    updateAddRowBtn();
  }

  function buildRow(item, idx) {
    var isZip = state.awningType === 'zip';
    var projs = getProjections();

    var row = document.createElement('div');
    row.className = 'size-row';

    // Header
    var header = document.createElement('div');
    header.className = 'size-row-header';

    var numEl = document.createElement('span');
    numEl.className = 'size-row-num';
    numEl.textContent = 'Позиция ' + (idx + 1);

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'size-row-del';
    delBtn.textContent = '\u00d7';
    delBtn.style.display = state.items.length === 1 ? 'none' : 'flex';
    delBtn.addEventListener('click', function () { removeRow(idx); });

    header.appendChild(numEl);
    header.appendChild(delBtn);
    row.appendChild(header);

    // Fields grid
    var fields = document.createElement('div');
    var isSf = state.awningType === 'storefront';
    fields.className = 'size-row-fields' + (isSf ? ' size-row-fields--sf5' : '');

    // Width
    var maxW = isZip ? 5 : (state.awningType === 'storefront' ? 7 : 6);
    fields.appendChild(buildNumberField(
      'Ширина, м', item.width, 2, maxW, 0.1,
      function (v) { state.items[idx].width = v; if (state.awningType === 'zip') checkZipAutoSwitch(); }
    ));

    // Projection or Height
    if (isZip) {
      fields.appendChild(buildNumberField(
        'Высота, м', item.dim, 1, 5, 0.1,
        function (v) { state.items[idx].dim = v; checkZipAutoSwitch(); }
      ));
    } else {
      var nDim = Number(item.dim);
      var selProj = isFinite(nDim) ? nDim.toFixed(1) : projs[0];
      if (projs.indexOf(selProj) === -1) selProj = projs[0];
      fields.appendChild(buildSelectField(
        'Вылет, м', projs, selProj,
        function (v) { state.items[idx].dim = parseFloat(v); }
      ));
    }

    // Qty
    fields.appendChild(buildNumberField(
      'Кол-во, шт', item.qty, 1, 99, 1,
      function (v) { state.items[idx].qty = Math.max(1, Math.round(v || 1)); }
    ));

    if (isSf) {
      if (item.tilt170 === undefined) item.tilt170 = false;
      if (item.valance === undefined) item.valance = 'none';
      fields.appendChild(buildStorefrontTiltField(item, idx));
      fields.appendChild(buildStorefrontValanceField(item, idx));
    }

    row.appendChild(fields);
    return row;
  }

  function buildNumberField(labelText, value, min, max, step, onChange) {
    var wrap = document.createElement('div');
    wrap.className = 'size-row-field';

    var lbl = document.createElement('label');
    lbl.textContent = labelText;

    var input = document.createElement('input');
    input.type = 'number';
    input.className = 'ch-input';
    input.value = value;
    input.min = min;
    input.max = max;
    input.step = step;

    input.addEventListener('change', function () {
      var v = parseFloat(this.value);
      if (isNaN(v) || v < min) { v = min; this.value = min; }
      if (v > max) { v = max; this.value = max; }
      onChange(v);
    });
    input.addEventListener('input', function () {
      var v = parseFloat(this.value);
      if (!isNaN(v)) onChange(v);
    });

    wrap.appendChild(lbl);
    wrap.appendChild(input);
    return wrap;
  }

  function buildSelectField(labelText, options, selected, onChange) {
    var wrap = document.createElement('div');
    wrap.className = 'size-row-field';

    var lbl = document.createElement('label');
    lbl.textContent = labelText;

    var sel = document.createElement('select');
    sel.className = 'ch-select';

    options.forEach(function (v) {
      var opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v + ' м';
      if (v === selected) opt.selected = true;
      sel.appendChild(opt);
    });

    sel.addEventListener('change', function () { onChange(this.value); });

    wrap.appendChild(lbl);
    wrap.appendChild(sel);
    return wrap;
  }

  /** Витринная: угол 90° (стандарт) или 170° (+15% к базе позиции) */
  function buildStorefrontTiltField(item, idx) {
    var wrap = document.createElement('div');
    wrap.className = 'size-row-field';

    var lbl = document.createElement('label');
    lbl.textContent = 'Угол наклона';

    var sel = document.createElement('select');
    sel.className = 'ch-select';
    var opts = [
      { v: '0', t: '90° стандарт' },
      { v: '1', t: '170° (+15% к базе)' }
    ];
    opts.forEach(function (opt) {
      var o = document.createElement('option');
      o.value = opt.v;
      o.textContent = opt.t;
      if ((opt.v === '1') === !!item.tilt170) o.selected = true;
      sel.appendChild(o);
    });
    sel.addEventListener('change', function () {
      state.items[idx].tilt170 = sel.value === '1';
    });

    wrap.appendChild(lbl);
    wrap.appendChild(sel);
    return wrap;
  }

  /** Витринная: волан по ширине маркизы (€/п.м ширины) */
  function buildStorefrontValanceField(item, idx) {
    var wrap = document.createElement('div');
    wrap.className = 'size-row-field';

    var lbl = document.createElement('label');
    lbl.textContent = 'Волан';

    var sel = document.createElement('select');
    sel.className = 'ch-select';
    var opts = [
      { v: 'none', t: 'Нет' },
      { v: 'straight', t: 'Прямой (10 €/м ширины)' },
      { v: 'shaped', t: 'Фигурный (15 €/м ширины)' }
    ];
    opts.forEach(function (opt) {
      var o = document.createElement('option');
      o.value = opt.v;
      o.textContent = opt.t;
      if (opt.v === (item.valance || 'none')) o.selected = true;
      sel.appendChild(o);
    });
    sel.addEventListener('change', function () {
      state.items[idx].valance = sel.value;
    });

    wrap.appendChild(lbl);
    wrap.appendChild(sel);
    return wrap;
  }

  function addRow() {
    if (state.items.length >= 10) return;
    var isZip = state.awningType === 'zip';
    var projs = getProjections();
    var defaultDim = isZip ? 2.0 : parseFloat(projs[Math.floor(projs.length / 2)] || projs[0]);
    state.items.push({ width: 4.0, dim: defaultDim, qty: 1, tilt170: false, valance: 'none' });
    renderRows();
  }

  function removeRow(idx) {
    if (state.items.length <= 1) return;
    state.items.splice(idx, 1);
    renderRows();
  }

  function updateAddRowBtn() {
    var btn = document.getElementById('addRowBtn');
    if (btn) btn.style.display = state.items.length >= 10 ? 'none' : 'flex';
  }

  /* =====================================================================
     ШАГ 4: ТКАНЬ
  ===================================================================== */
  function applyStdFabricCardDescriptions() {
    var root = document.getElementById('fabricCards');
    if (!root) return;
    root.querySelectorAll('.fabric-card[data-value]').forEach(function (card) {
      var key = card.getAttribute('data-value');
      var m = STD_FABRIC_SERIES[key];
      if (!m) return;
      var nameEl = card.querySelector('.fabric-card-name');
      var originEl = card.querySelector('.fabric-card-origin');
      var descEl = card.querySelector('.fabric-card-desc');
      var catEl = card.querySelector('.fabric-card-cat');
      if (nameEl) nameEl.textContent = m.cardTitle;
      if (originEl) originEl.textContent = m.badge;
      if (descEl) descEl.textContent = m.description;
      if (catEl) catEl.textContent = m.catLine;
    });
  }

  function renderStep4() {
    var isZip = state.awningType === 'zip';
    var stdGrp = document.getElementById('fabricStdGroup');
    var zipGrp = document.getElementById('fabricZipGroup');
    var ft = document.getElementById('fabricStepTitle');
    var fs = document.getElementById('fabricStepSub');

    if (ft) {
      ft.textContent = isZip
        ? 'Выберите ткань для ZIP-маркизы'
        : 'Выберите ткань для локтевых и витринных маркиз';
    }
    if (fs) {
      fs.textContent = isZip
        ? 'Ткань влияет на свет, теплозащиту и категорию цены'
        : 'Коллекции Sattler SUN-TEX: внешний вид, УФ-стойкость и категория цены';
    }

    if (stdGrp) stdGrp.style.display = isZip ? 'none' : 'block';
    if (zipGrp) zipGrp.style.display = isZip ? 'block' : 'none';

    if (!isZip) {
      applyStdFabricCardDescriptions();
      syncCardGroup('fabricCards', state.fabric);
      refreshFabricCarousel();
    } else {
      syncCardGroup('fabricZipCards', state.fabricZip);
      renderVeozipColors();
      renderSoltisSection();
      renderCopacoSection();
    }
  }

  function renderVeozipColors() {
    var section = document.getElementById('veozipColorSection');
    if (!section) return;

    var isVeozip = state.fabricZip === 'veozip';
    section.style.display = isVeozip ? 'block' : 'none';
    if (!isVeozip) return;

    var grid = document.getElementById('veozipColorGrid');
    if (!grid) return;

    // Build grid if empty (check for actual swatch elements, not text/comment nodes)
    if (!grid.querySelector('.veozip-swatch')) {
      VEOZIP_COLORS.forEach(function (article) {
        var swatch = document.createElement('div');
        swatch.className = 'veozip-swatch';
        swatch.setAttribute('data-article', article);

        var img = document.createElement('img');
        img.src = '/static/img/fabrics/veozip/thumbs/' + article + '.jpg';
        img.alt = article;
        img.loading = 'lazy';

        var label = document.createElement('div');
        label.className = 'veozip-swatch-article';
        label.textContent = article;

        swatch.appendChild(img);
        swatch.appendChild(label);
        grid.appendChild(swatch);
      });

      grid.addEventListener('click', function (e) {
        var sw = e.target.closest('.veozip-swatch');
        if (!sw) return;
        vzLightbox.open(VEOZIP_COLORS.indexOf(sw.getAttribute('data-article')));
      });
    }

    syncVeozipColor();
  }

  function syncVeozipColor() {
    var grid = document.getElementById('veozipColorGrid');
    if (!grid) return;
    var swatches = grid.querySelectorAll('.veozip-swatch');
    swatches.forEach(function (sw) {
      var active = sw.getAttribute('data-article') === state.veozipColor;
      sw.classList.toggle('selected', active);
    });
    var lbl = document.getElementById('veozipSelectedLabel');
    if (lbl) lbl.textContent = state.veozipColor ? 'Артикул: ' + state.veozipColor : '';
  }

  /* =====================================================================
     ЛАЙТБОКС VEOZIP
  ===================================================================== */
  var vzLightbox = (function () {
    var lb, backdrop, img, imgWrap, prevBtn, nextBtn, closeBtn, selectBtn,
        articleEl, counterEl, dotsEl;
    var currentIdx = 0;
    var isZoomed = false;
    var initialized = false;

    function init() {
      if (initialized) return;
      initialized = true;
      lb       = document.getElementById('vzLightbox');
      backdrop = document.getElementById('vzLbBackdrop');
      imgWrap  = document.getElementById('vzLbImgWrap');
      img      = document.getElementById('vzLbImg');
      prevBtn  = document.getElementById('vzLbPrev');
      nextBtn  = document.getElementById('vzLbNext');
      closeBtn = document.getElementById('vzLbClose');
      selectBtn= document.getElementById('vzLbSelect');
      articleEl= document.getElementById('vzLbArticle');
      counterEl= document.getElementById('vzLbCounter');
      dotsEl   = document.getElementById('vzLbDots');
      if (!lb) { initialized = false; return; }

      rebuildVezipDots();

      // Close on backdrop
      backdrop.addEventListener('click', close);
      closeBtn.addEventListener('click', close);

      // Navigation
      prevBtn.addEventListener('click', function () { goTo(currentIdx - 1); });
      nextBtn.addEventListener('click', function () { goTo(currentIdx + 1); });

      // Select button
      selectBtn.addEventListener('click', function () {
        state.veozipColor = VEOZIP_COLORS[currentIdx];
        syncVeozipColor();
        updateSelectBtn();
        window.setTimeout(function () {
          close();
          scheduleFabricNavFloatAfterFabricChoice();
        }, 340);
      });

      // Zoom on image click
      imgWrap.addEventListener('click', function (e) {
        if (e.target === prevBtn || e.target === nextBtn) return;
        isZoomed = !isZoomed;
        if (isZoomed) {
          var rect = imgWrap.getBoundingClientRect();
          var ox = ((e.clientX - rect.left) / rect.width * 100).toFixed(1) + '%';
          var oy = ((e.clientY - rect.top)  / rect.height * 100).toFixed(1) + '%';
          imgWrap.style.setProperty('--vz-ox', ox);
          imgWrap.style.setProperty('--vz-oy', oy);
        }
        imgWrap.classList.toggle('vz-zoomed', isZoomed);
      });

      // Keyboard navigation
      document.addEventListener('keydown', function (e) {
        if (!lb.classList.contains('vz-open')) return;
        if (e.key === 'Escape') close();
        if (e.key === 'ArrowLeft')  goTo(currentIdx - 1);
        if (e.key === 'ArrowRight') goTo(currentIdx + 1);
      });

      // Touch swipe
      var touchStartX = 0;
      lb.addEventListener('touchstart', function (e) {
        touchStartX = e.touches[0].clientX;
      }, { passive: true });
      lb.addEventListener('touchend', function (e) {
        var dx = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(dx) > 50) goTo(currentIdx + (dx < 0 ? 1 : -1));
      }, { passive: true });
    }

    function rebuildVezipDots() {
      if (!dotsEl) return;
      while (dotsEl.firstChild) dotsEl.removeChild(dotsEl.firstChild);
      VEOZIP_COLORS.forEach(function (_, i) {
        var dot = document.createElement('div');
        dot.className = 'vz-dot';
        dot.addEventListener('click', function () { goTo(i); });
        dotsEl.appendChild(dot);
      });
    }

    function goTo(idx) {
      var n = VEOZIP_COLORS.length;
      currentIdx = (idx % n + n) % n;
      isZoomed = false;
      imgWrap.classList.remove('vz-zoomed');
      var article = VEOZIP_COLORS[currentIdx];

      // Swap image with fade
      img.style.opacity = '0';
      img.style.transform = 'scale(0.97)';
      setTimeout(function () {
        img.src = '/static/img/fabrics/veozip/' + article + '.jpg';
        articleEl.textContent = 'Артикул: ' + article;
        counterEl.textContent = (currentIdx + 1) + ' / ' + n;
        img.style.transition = 'none';
        img.onload = function () {
          img.style.transition = 'opacity 0.25s,transform 0.25s';
          img.style.opacity = '1';
          img.style.transform = 'scale(1)';
        };
      }, 120);

      // Dots
      var dots = dotsEl.querySelectorAll('.vz-dot');
      dots.forEach(function (d, i) { d.classList.toggle('active', i === currentIdx); });

      // Scroll active dot into view
      if (dots[currentIdx]) {
        dots[currentIdx].scrollIntoView({ inline: 'nearest', behavior: 'smooth' });
      }

      updateSelectBtn();
    }

    function updateSelectBtn() {
      if (!selectBtn) return;
      var already = state.veozipColor === VEOZIP_COLORS[currentIdx];
      selectBtn.textContent = already ? '✓ Выбрано' : 'Выбрать этот цвет';
      selectBtn.classList.toggle('vz-already', already);
    }

    function open(idx) {
      init();
      if (!lb) return;
      hideFabricNavFloat();
      document.body.style.overflow = 'hidden';
      lb.classList.add('vz-open');
      goTo(idx != null ? idx : 0);
    }

    function close() {
      if (!lb) return;
      lb.classList.remove('vz-open');
      document.body.style.overflow = '';
      isZoomed = false;
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');
    }

    return { open: open, close: close };
  }());

  /* =====================================================================
     ГАЛЕРЕЯ SOLTIS 86/92
  ===================================================================== */
  function renderSoltisSection() {
    var section = document.getElementById('soltisColorSection');
    if (!section) return;

    var isSoltis = state.fabricZip === 'soltis';
    section.style.display = isSoltis ? 'block' : 'none';
    if (!isSoltis) return;

    buildSoltisSection(section);
    syncSoltisUI();
  }

  function buildSoltisSection(section) {
    if (section.querySelector('.soltis-tabs')) {
      if (!document.getElementById('soltisColDesc')) {
        var _gwS = section.querySelector('.soltis-grid-wrap');
        var _tbS = section.querySelector('.soltis-tabs');
        var _cdS = document.createElement('div');
        _cdS.className = 'soltis-col-desc';
        _cdS.id = 'soltisColDesc';
        if (_gwS) section.insertBefore(_cdS, _gwS);
        else if (_tbS && _tbS.nextSibling) section.insertBefore(_cdS, _tbS.nextSibling);
        else if (_tbS) section.appendChild(_cdS);
      }
      return;
    }

    // Tab bar
    var tabBar = document.createElement('div');
    tabBar.className = 'soltis-tabs';

    SOLTIS_COLLECTIONS.forEach(function (col) {
      var tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'soltis-tab';
      tab.setAttribute('data-col', col.id);
      var labelEl = document.createElement('span');
      labelEl.textContent = col.label;
      tab.appendChild(labelEl);
      if (col.badge) {
        var badge = document.createElement('span');
        badge.className = 'soltis-tab-badge';
        badge.textContent = col.badge;
        tab.appendChild(badge);
      }
      tab.addEventListener('click', function () {
        state.soltisCollection = col.id;
        // reset color to first in collection
        state.soltisColor = col.fabrics[0].article;
        syncSoltisUI();
      });
      tabBar.appendChild(tab);
    });

    section.appendChild(tabBar);

    // Collection description
    var colDesc = document.createElement('div');
    colDesc.className = 'soltis-col-desc';
    colDesc.id = 'soltisColDesc';
    section.appendChild(colDesc);

    // Grid container
    var gridWrap = document.createElement('div');
    gridWrap.className = 'soltis-grid-wrap';
    section.appendChild(gridWrap);

    // Selected label
    var selLbl = document.createElement('div');
    selLbl.className = 'soltis-selected-label';
    selLbl.id = 'soltisSelectedLabel';
    section.appendChild(selLbl);
  }

  function syncSoltisUI() {
    var section = document.getElementById('soltisColorSection');
    if (!section) return;

    // Sync tabs
    var tabs = section.querySelectorAll('.soltis-tab');
    tabs.forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-col') === state.soltisCollection);
    });

    // Rebuild grid for active collection
    var gridWrap = section.querySelector('.soltis-grid-wrap');
    if (!gridWrap) return;
    while (gridWrap.firstChild) gridWrap.removeChild(gridWrap.firstChild);

    var col = SOLTIS_COLLECTIONS.find(function (c) { return c.id === state.soltisCollection; });
    if (!col) return;

    // Update collection description
    var colDescEl = document.getElementById('soltisColDesc');
    if (colDescEl) colDescEl.textContent = col.desc || '';

    var grid = document.createElement('div');
    grid.className = 'soltis-grid';

    col.fabrics.forEach(function (fab, idx) {
      var swatch = document.createElement('div');
      swatch.className = 'soltis-swatch' + (fab.article === state.soltisColor ? ' selected' : '');
      swatch.setAttribute('data-article', fab.article);
      swatch.setAttribute('data-col', col.id);
      swatch.setAttribute('data-idx', idx);

      var img = document.createElement('img');
      img.src = '/static/img/fabrics/' + col.id + '/thumbs/' + fab.short + '.jpg';
      img.alt = fab.article;
      img.loading = 'lazy';

      var lbl = document.createElement('div');
      lbl.className = 'soltis-swatch-article';
      lbl.textContent = fab.article;

      swatch.appendChild(img);
      swatch.appendChild(lbl);

      swatch.addEventListener('click', function () {
        state.soltisColor = fab.article;
        state.soltisCollection = col.id;
        soltisLightbox.open(col, idx);
      });

      grid.appendChild(swatch);
    });

    gridWrap.appendChild(grid);

    // Update selected label
    var selLbl = document.getElementById('soltisSelectedLabel');
    if (selLbl) selLbl.textContent = state.soltisColor ? 'Артикул: ' + state.soltisColor : '';
  }

  /* =====================================================================
     ЛАЙТБОКС SOLTIS
  ===================================================================== */
  var soltisLightbox = (function () {
    var lb, backdrop, img, imgWrap, prevBtn, nextBtn, closeBtn, selectBtn,
        articleEl, collectionEl, counterEl, dotsEl;
    var currentCol = null;
    var currentIdx = 0;
    var isZoomed = false;
    var initialized = false;

    function init() {
      if (initialized) return;
      initialized = true;
      lb          = document.getElementById('vzLightbox');
      backdrop    = document.getElementById('vzLbBackdrop');
      imgWrap     = document.getElementById('vzLbImgWrap');
      img         = document.getElementById('vzLbImg');
      prevBtn     = document.getElementById('vzLbPrev');
      nextBtn     = document.getElementById('vzLbNext');
      closeBtn    = document.getElementById('vzLbClose');
      selectBtn   = document.getElementById('vzLbSelect');
      articleEl   = document.getElementById('vzLbArticle');
      collectionEl= document.getElementById('vzLbTitle');
      counterEl   = document.getElementById('vzLbCounter');
      dotsEl      = document.getElementById('vzLbDots');
      if (!lb) { initialized = false; return; }
    }

    function buildDots(col) {
      while (dotsEl.firstChild) dotsEl.removeChild(dotsEl.firstChild);
      col.fabrics.forEach(function (_, i) {
        var dot = document.createElement('div');
        dot.className = 'vz-dot';
        dot.addEventListener('click', function () { goTo(i); });
        dotsEl.appendChild(dot);
      });
    }

    function goTo(idx) {
      if (!currentCol) return;
      var n = currentCol.fabrics.length;
      currentIdx = (idx % n + n) % n;
      isZoomed = false;
      imgWrap.classList.remove('vz-zoomed');

      var fab = currentCol.fabrics[currentIdx];
      img.style.opacity = '0';
      img.style.transform = 'scale(0.97)';
      setTimeout(function () {
        img.src = '/static/img/fabrics/' + currentCol.id + '/' + fab.short + '.webp';
        articleEl.textContent = 'Артикул: ' + fab.article;
        counterEl.textContent = (currentIdx + 1) + ' / ' + n;
        img.style.transition = 'none';
        img.onload = function () {
          img.style.transition = 'opacity 0.25s,transform 0.25s';
          img.style.opacity = '1';
          img.style.transform = 'scale(1)';
        };
      }, 100);

      var dots = dotsEl.querySelectorAll('.vz-dot');
      dots.forEach(function (d, i) { d.classList.toggle('active', i === currentIdx); });
      updateSelectBtn();
    }

    function updateSelectBtn() {
      if (!selectBtn || !currentCol) return;
      var fab = currentCol.fabrics[currentIdx];
      var already = state.soltisColor === fab.article;
      selectBtn.textContent = already ? '✓ Выбрано' : 'Выбрать этот цвет';
      selectBtn.classList.toggle('vz-already', already);
    }

    function open(col, idx) {
      init();
      if (!lb) return;
      hideFabricNavFloat();
      currentCol = col;

      // Swap lightbox title/badge
      var badge = document.getElementById('vzLbBadge');
      if (badge) badge.textContent = 'Soltis Serge Ferrari';
      if (collectionEl) collectionEl.textContent = col.label + (col.badge ? ' · ' + col.badge : '');

      var desc = document.getElementById('vzLbDesc');
      if (desc) desc.textContent = 'Французская экранная ткань Soltis ' + col.label.replace('Soltis ','') + '. Блокирует до 97% тепла, фильтрует 95% УФ-излучения. Средний срок службы — 35 лет.';

      buildDots(col);

      // Reset old select handler and bind new
      var newBtn = selectBtn.cloneNode(true);
      selectBtn.parentNode.replaceChild(newBtn, selectBtn);
      selectBtn = newBtn;
      selectBtn.addEventListener('click', function () {
        state.soltisColor = currentCol.fabrics[currentIdx].article;
        state.soltisCollection = currentCol.id;
        syncSoltisUI();
        updateSelectBtn();
        window.setTimeout(function () {
          close();
          scheduleFabricNavFloatAfterFabricChoice();
        }, 340);
      });

      // Zoom
      imgWrap.onclick = null;
      imgWrap.addEventListener('click', function onZoom(e) {
        if (e.target === prevBtn || e.target === nextBtn) return;
        isZoomed = !isZoomed;
        if (isZoomed) {
          var rect = imgWrap.getBoundingClientRect();
          imgWrap.style.setProperty('--vz-ox', ((e.clientX-rect.left)/rect.width*100).toFixed(1)+'%');
          imgWrap.style.setProperty('--vz-oy', ((e.clientY-rect.top)/rect.height*100).toFixed(1)+'%');
        }
        imgWrap.classList.toggle('vz-zoomed', isZoomed);
      });

      prevBtn.onclick = function () { goTo(currentIdx - 1); };
      nextBtn.onclick = function () { goTo(currentIdx + 1); };
      backdrop.onclick = close;
      closeBtn.onclick = close;

      document.body.style.overflow = 'hidden';
      lb.classList.add('vz-open');
      goTo(idx != null ? idx : 0);
    }

    function close() {
      if (!lb) return;
      lb.classList.remove('vz-open');
      document.body.style.overflow = '';
      isZoomed = false;
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');
    }

    return { open: open, close: close };
  }());

  /* =====================================================================
     ГАЛЕРЕЯ COPACO
  ===================================================================== */
  function renderCopacoSection() {
    var section = document.getElementById('copacoColorSection');
    if (!section) return;
    var isCopaco = state.fabricZip === 'copaco';
    section.style.display = isCopaco ? 'block' : 'none';
    if (!isCopaco) return;
    buildCopacoSection(section);
    syncCopacoUI();
  }

  function buildCopacoSection(section) {
    if (section.querySelector('.soltis-tabs')) {
      if (!document.getElementById('copacoColDesc')) {
        var _gwC = section.querySelector('.soltis-grid-wrap');
        var _tbC = section.querySelector('.soltis-tabs');
        var _cdC = document.createElement('div');
        _cdC.className = 'soltis-col-desc';
        _cdC.id = 'copacoColDesc';
        if (_gwC) section.insertBefore(_cdC, _gwC);
        else if (_tbC && _tbC.nextSibling) section.insertBefore(_cdC, _tbC.nextSibling);
        else if (_tbC) section.appendChild(_cdC);
      }
      return;
    }

    var tabBar = document.createElement('div');
    tabBar.className = 'soltis-tabs';

    COPACO_COLLECTIONS.forEach(function (col) {
      var tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'soltis-tab';
      tab.setAttribute('data-col', col.id);
      var lbl = document.createElement('span');
      lbl.textContent = col.label;
      tab.appendChild(lbl);
      if (col.badge) {
        var badge = document.createElement('span');
        badge.className = 'soltis-tab-badge';
        badge.textContent = col.badge;
        tab.appendChild(badge);
      }
      tab.addEventListener('click', function () {
        state.copacoCollection = col.id;
        state.copacoColor = col.fabrics[0].article;
        syncCopacoUI();
      });
      tabBar.appendChild(tab);
    });

    section.appendChild(tabBar);

    var colDesc = document.createElement('div');
    colDesc.className = 'soltis-col-desc';
    colDesc.id = 'copacoColDesc';
    section.appendChild(colDesc);

    var gridWrap = document.createElement('div');
    gridWrap.className = 'soltis-grid-wrap';
    section.appendChild(gridWrap);

    var selLbl = document.createElement('div');
    selLbl.className = 'soltis-selected-label';
    selLbl.id = 'copacoSelectedLabel';
    section.appendChild(selLbl);
  }

  function syncCopacoUI() {
    var section = document.getElementById('copacoColorSection');
    if (!section) return;

    section.querySelectorAll('.soltis-tab').forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-col') === state.copacoCollection);
    });

    var gridWrap = section.querySelector('.soltis-grid-wrap');
    if (!gridWrap) return;
    while (gridWrap.firstChild) gridWrap.removeChild(gridWrap.firstChild);

    var col = COPACO_COLLECTIONS.find(function (c) { return c.id === state.copacoCollection; });
    if (!col) return;

    var copacoDescEl = document.getElementById('copacoColDesc');
    if (copacoDescEl) copacoDescEl.textContent = col.desc || '';

    var grid = document.createElement('div');
    grid.className = 'soltis-grid';

    col.fabrics.forEach(function (fab, idx) {
      var swatch = document.createElement('div');
      swatch.className = 'soltis-swatch' + (fab.article === state.copacoColor ? ' selected' : '');
      swatch.setAttribute('data-article', fab.article);

      var img = document.createElement('img');
      img.src = '/static/img/fabrics/' + col.id + '/thumbs/' + fab.article + '.jpg';
      img.alt = fab.article;
      img.loading = 'lazy';

      var lbl = document.createElement('div');
      lbl.className = 'soltis-swatch-article';
      lbl.textContent = fab.display;

      swatch.appendChild(img);
      swatch.appendChild(lbl);

      swatch.addEventListener('click', function () {
        state.copacoColor = fab.article;
        state.copacoCollection = col.id;
        copacoLightbox.open(col, idx);
      });

      grid.appendChild(swatch);
    });

    gridWrap.appendChild(grid);

    var selLbl = document.getElementById('copacoSelectedLabel');
    if (selLbl) selLbl.textContent = state.copacoColor ? 'Артикул: ' + state.copacoColor : '';
  }

  /* =====================================================================
     ЛАЙТБОКС COPACO (использует тот же vzLightbox)
  ===================================================================== */
  var copacoLightbox = (function () {
    var currentCol = null;
    var currentIdx = 0;
    var isZoomed = false;

    function goTo(idx) {
      if (!currentCol) return;
      var n = currentCol.fabrics.length;
      currentIdx = (idx % n + n) % n;
      isZoomed = false;
      var imgWrap = document.getElementById('vzLbImgWrap');
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');

      var fab = currentCol.fabrics[currentIdx];
      var img = document.getElementById('vzLbImg');
      var articleEl = document.getElementById('vzLbArticle');
      var counterEl = document.getElementById('vzLbCounter');
      var dotsEl = document.getElementById('vzLbDots');

      if (img) {
        img.style.opacity = '0';
        img.style.transform = 'scale(0.97)';
        setTimeout(function () {
          img.src = '/static/img/fabrics/' + currentCol.id + '/' + fab.article + '.webp';
          if (articleEl) articleEl.textContent = fab.display + ' · ' + fab.article;
          if (counterEl) counterEl.textContent = (currentIdx + 1) + ' / ' + n;
          img.style.transition = 'none';
          img.onload = function () {
            img.style.transition = 'opacity 0.25s,transform 0.25s';
            img.style.opacity = '1';
            img.style.transform = 'scale(1)';
          };
        }, 100);
      }

      if (dotsEl) {
        dotsEl.querySelectorAll('.vz-dot').forEach(function (d, i) {
          d.classList.toggle('active', i === currentIdx);
        });
      }
      updateSelectBtn();
    }

    function updateSelectBtn() {
      var selectBtn = document.getElementById('vzLbSelect');
      if (!selectBtn || !currentCol) return;
      var fab = currentCol.fabrics[currentIdx];
      var already = state.copacoColor === fab.article && state.copacoCollection === currentCol.id;
      selectBtn.textContent = already ? '✓ Выбрано' : 'Выбрать этот цвет';
      selectBtn.classList.toggle('vz-already', already);
    }

    function open(col, idx) {
      var lb = document.getElementById('vzLightbox');
      if (!lb) return;
      hideFabricNavFloat();
      currentCol = col;

      var dotsEl = document.getElementById('vzLbDots');
      if (dotsEl) {
        while (dotsEl.firstChild) dotsEl.removeChild(dotsEl.firstChild);
        col.fabrics.forEach(function (_, i) {
          var dot = document.createElement('div');
          dot.className = 'vz-dot';
          dot.addEventListener('click', function () { goTo(i); });
          dotsEl.appendChild(dot);
        });
      }

      var badge = document.getElementById('vzLbBadge');
      if (badge) badge.textContent = 'Copaco Screenweavers · Бельгия';
      var titleEl = document.getElementById('vzLbTitle');
      if (titleEl) titleEl.textContent = col.label + (col.badge ? ' · ' + col.badge : '');
      var descEl = document.getElementById('vzLbDesc');
      if (descEl) descEl.textContent = 'Бельгийская экранная ткань Copaco. Оптимально подходит для ZIP-систем. Долговременная устойчивость к UV-излучению и агрессивным климатическим условиям.';

      var selectBtn = document.getElementById('vzLbSelect');
      if (selectBtn) {
        var newBtn = selectBtn.cloneNode(true);
        selectBtn.parentNode.replaceChild(newBtn, selectBtn);
        newBtn.addEventListener('click', function () {
          state.copacoColor = currentCol.fabrics[currentIdx].article;
          state.copacoCollection = currentCol.id;
          syncCopacoUI();
          updateSelectBtn();
          window.setTimeout(function () {
            close();
            scheduleFabricNavFloatAfterFabricChoice();
          }, 340);
        });
      }

      var prevBtn = document.getElementById('vzLbPrev');
      var nextBtn = document.getElementById('vzLbNext');
      var backdrop = document.getElementById('vzLbBackdrop');
      var closeBtn = document.getElementById('vzLbClose');
      var imgWrap = document.getElementById('vzLbImgWrap');

      if (prevBtn) prevBtn.onclick = function () { goTo(currentIdx - 1); };
      if (nextBtn) nextBtn.onclick = function () { goTo(currentIdx + 1); };
      if (backdrop) backdrop.onclick = close;
      if (closeBtn) closeBtn.onclick = close;

      if (imgWrap) {
        imgWrap.onclick = function (e) {
          if (e.target === prevBtn || e.target === nextBtn) return;
          isZoomed = !isZoomed;
          if (isZoomed) {
            var rect = imgWrap.getBoundingClientRect();
            imgWrap.style.setProperty('--vz-ox', ((e.clientX-rect.left)/rect.width*100).toFixed(1)+'%');
            imgWrap.style.setProperty('--vz-oy', ((e.clientY-rect.top)/rect.height*100).toFixed(1)+'%');
          }
          imgWrap.classList.toggle('vz-zoomed', isZoomed);
        };
      }

      document.body.style.overflow = 'hidden';
      lb.classList.add('vz-open');
      goTo(idx != null ? idx : 0);
    }

    function close() {
      var lb = document.getElementById('vzLightbox');
      if (!lb) return;
      lb.classList.remove('vz-open');
      document.body.style.overflow = '';
      isZoomed = false;
      var imgWrap = document.getElementById('vzLbImgWrap');
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');
    }

    return { open: open };
  }());

  /* =====================================================================
     СТАНДАРТНАЯ ТКАНЬ — сетка как у ZIP (veozip-grid) + лайтбокс (#vzLightbox)
  ===================================================================== */
  function parseStdFabricEntry(item) {
    var p = String(item).split('|||');
    return { url: (p[0] || '').trim(), label: (p[1] || '').trim() };
  }

  function getStdFabricItems(brand) {
    var d = window.__FABRIC_STD_DATA;
    if (!d || !d[brand]) return [];
    return d[brand];
  }

  function syncStdFabricGridSelection() {
    var grid = document.getElementById('stdFabricColorGrid');
    if (!grid) return;
    var sw = state.fabricStdSwatch;
    grid.querySelectorAll('.veozip-swatch').forEach(function (sl) {
      var url = sl.getAttribute('data-fabric-url');
      var lab = sl.getAttribute('data-fabric-label');
      var on = !!(sw && sw.url === url && sw.label === lab);
      sl.classList.toggle('selected', on);
    });
    var lbl = document.getElementById('stdFabricSelectedLabel');
    if (lbl) lbl.textContent = sw && sw.label ? ('Оттенок: ' + sw.label) : '';
  }

  function buildStdFabricColorGrid(brand) {
    var grid = document.getElementById('stdFabricColorGrid');
    var brandLabel = document.getElementById('tcBrandLabel');
    if (!grid) return;
    grid.textContent = '';
    var items = getStdFabricItems(brand);
    if (!items.length) return;

    if (!state.fabricStdSwatch || state.fabricStdSwatch.brand !== brand) {
      var f0 = parseStdFabricEntry(items[0]);
      state.fabricStdSwatch = { brand: brand, label: f0.label, url: f0.url };
    } else {
      var sw = state.fabricStdSwatch;
      var stillThere = items.some(function (raw) {
        var p = parseStdFabricEntry(raw);
        return p.url === sw.url && p.label === sw.label;
      });
      if (!stillThere) {
        var f0b = parseStdFabricEntry(items[0]);
        state.fabricStdSwatch = { brand: brand, label: f0b.label, url: f0b.url };
      }
    }

    items.forEach(function (item, index) {
      var parsed = parseStdFabricEntry(item);
      var swatch = document.createElement('div');
      swatch.className = 'veozip-swatch';
      swatch.setAttribute('data-fabric-url', parsed.url);
      swatch.setAttribute('data-fabric-label', parsed.label);
      swatch.setAttribute('data-idx', String(index));
      var img = document.createElement('img');
      img.src = parsed.url;
      img.alt = parsed.label;
      img.loading = 'lazy';
      var art = document.createElement('div');
      art.className = 'veozip-swatch-article';
      art.textContent = parsed.label;
      swatch.appendChild(img);
      swatch.appendChild(art);
      swatch.addEventListener('click', function () {
        standardFabricLightbox.open(brand, index);
      });
      grid.appendChild(swatch);
    });

    var shortLabels = {
      gaviota: 'Gaviota',
      lumera3d: 'Sattler Lumera 3D',
      lumera: 'Sattler Lumera',
      elements: 'Sattler Elements',
      solids: 'Sattler Solids',
    };
    if (brandLabel) brandLabel.textContent = '\u2014 ' + (shortLabels[brand] || brand);
    syncStdFabricGridSelection();
  }

  var standardFabricLightbox = (function () {
    var currentBrand = null;
    var currentEntries = [];
    var currentIdx = 0;
    var isZoomed = false;

    function entriesForBrand(brand) {
      return getStdFabricItems(brand)
        .map(parseStdFabricEntry)
        .filter(function (x) { return x.url; });
    }

    function goTo(idx) {
      if (!currentEntries.length) return;
      var n = currentEntries.length;
      currentIdx = (idx % n + n) % n;
      isZoomed = false;
      var imgWrap = document.getElementById('vzLbImgWrap');
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');

      var ent = currentEntries[currentIdx];
      var img = document.getElementById('vzLbImg');
      var articleEl = document.getElementById('vzLbArticle');
      var counterEl = document.getElementById('vzLbCounter');
      var dotsEl = document.getElementById('vzLbDots');
      var meta = STD_FABRIC_SERIES[currentBrand] || {};

      if (img) {
        img.style.opacity = '0';
        img.style.transform = 'scale(0.97)';
        setTimeout(function () {
          img.src = ent.url;
          if (articleEl) articleEl.textContent = 'Оттенок: ' + ent.label;
          if (counterEl) counterEl.textContent = (currentIdx + 1) + ' / ' + n;
          img.style.transition = 'none';
          img.onload = function () {
            img.style.transition = 'opacity 0.25s,transform 0.25s';
            img.style.opacity = '1';
            img.style.transform = 'scale(1)';
          };
        }, 100);
      }

      if (dotsEl) {
        dotsEl.querySelectorAll('.vz-dot').forEach(function (d, i) {
          d.classList.toggle('active', i === currentIdx);
        });
      }
      updateSelectBtn();
    }

    function updateSelectBtn() {
      var selectBtn = document.getElementById('vzLbSelect');
      if (!selectBtn || !currentEntries.length || !currentBrand) return;
      var ent = currentEntries[currentIdx];
      var sw = state.fabricStdSwatch;
      var already = !!(sw && sw.brand === currentBrand && sw.url === ent.url && sw.label === ent.label);
      selectBtn.textContent = already ? '✓ Выбрано' : 'Выбрать этот цвет';
      selectBtn.classList.toggle('vz-already', already);
    }

    function open(brand, idx) {
      var lb = document.getElementById('vzLightbox');
      if (!lb) return;
      hideFabricNavFloat();
      currentBrand = brand;
      currentEntries = entriesForBrand(brand);
      if (!currentEntries.length) return;

      var meta = STD_FABRIC_SERIES[brand] || {};
      var dotsEl = document.getElementById('vzLbDots');
      if (dotsEl) {
        while (dotsEl.firstChild) dotsEl.removeChild(dotsEl.firstChild);
        currentEntries.forEach(function (_, i) {
          var dot = document.createElement('div');
          dot.className = 'vz-dot';
          dot.addEventListener('click', function () { goTo(i); });
          dotsEl.appendChild(dot);
        });
      }

      var badge = document.getElementById('vzLbBadge');
      if (badge) badge.textContent = meta.badge || 'Sattler SUN-TEX';
      var titleEl = document.getElementById('vzLbTitle');
      if (titleEl) titleEl.textContent = meta.lightboxTitle || meta.cardTitle || brand;
      var descEl = document.getElementById('vzLbDesc');
      if (descEl) descEl.textContent = meta.description || '';

      var selectBtn = document.getElementById('vzLbSelect');
      if (selectBtn) {
        var newBtn = selectBtn.cloneNode(true);
        selectBtn.parentNode.replaceChild(newBtn, selectBtn);
        newBtn.addEventListener('click', function () {
          var ent = currentEntries[currentIdx];
          state.fabricStdSwatch = { brand: currentBrand, label: ent.label, url: ent.url };
          syncStdFabricGridSelection();
          updateSelectBtn();
          window.setTimeout(function () {
            close();
            scheduleFabricNavFloatAfterFabricChoice();
          }, 340);
        });
      }

      var prevBtn = document.getElementById('vzLbPrev');
      var nextBtn = document.getElementById('vzLbNext');
      var backdrop = document.getElementById('vzLbBackdrop');
      var closeBtn = document.getElementById('vzLbClose');
      var imgWrap = document.getElementById('vzLbImgWrap');

      if (prevBtn) prevBtn.onclick = function () { goTo(currentIdx - 1); };
      if (nextBtn) nextBtn.onclick = function () { goTo(currentIdx + 1); };
      if (backdrop) backdrop.onclick = close;
      if (closeBtn) closeBtn.onclick = close;

      if (imgWrap) {
        imgWrap.onclick = function (e) {
          if (e.target === prevBtn || e.target === nextBtn) return;
          isZoomed = !isZoomed;
          if (isZoomed) {
            var rect = imgWrap.getBoundingClientRect();
            imgWrap.style.setProperty('--vz-ox', ((e.clientX - rect.left) / rect.width * 100).toFixed(1) + '%');
            imgWrap.style.setProperty('--vz-oy', ((e.clientY - rect.top) / rect.height * 100).toFixed(1) + '%');
          }
          imgWrap.classList.toggle('vz-zoomed', isZoomed);
        };
      }

      document.body.style.overflow = 'hidden';
      lb.classList.add('vz-open');
      goTo(idx != null ? idx : 0);
    }

    function close() {
      var lb = document.getElementById('vzLightbox');
      if (!lb) return;
      lb.classList.remove('vz-open');
      document.body.style.overflow = '';
      isZoomed = false;
      var imgWrap = document.getElementById('vzLbImgWrap');
      if (imgWrap) imgWrap.classList.remove('vz-zoomed');
    }

    return { open: open, close: close };
  }());

  function refreshFabricCarousel() {
    var preview = document.getElementById('fabricPreview');
    if (!preview) return;
    var noGrid = ['gaviota', 'elements', 'solids', 'lumera', 'lumera3d'].indexOf(state.fabric) === -1;
    if (noGrid) { preview.style.display = 'none'; return; }
    preview.style.display = 'block';
    buildStdFabricColorGrid(state.fabric);
  }

  /** Прокрутка к каталогу «Выберите цвет ткани» — только локтевые и витринные маркизы */
  function scrollToFabricColorCatalog() {
    if (state.awningType !== 'standard' && state.awningType !== 'storefront') return;
    var preview = document.getElementById('fabricPreview');
    if (!preview || preview.style.display === 'none') return;
    window.setTimeout(function () {
      preview.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
    }, 0);
  }

  /** Скрыть плавающую навигацию после ткани (таймер + оверлей) */
  function hideFabricNavFloat() {
    if (_fabricNavFloatTimer) {
      clearTimeout(_fabricNavFloatTimer);
      _fabricNavFloatTimer = null;
    }
    detachFabricFloatIdleGuards();
    var root = document.getElementById('fabricNavFloat');
    if (!root) return;
    root.classList.remove('visible');
    root.setAttribute('aria-hidden', 'true');
  }

  function syncFabricFloatNav() {
    var prev = document.getElementById('fabricFloatPrev');
    var next = document.getElementById('fabricFloatNext');
    if (prev) prev.style.display = state.step > 1 ? 'inline-flex' : 'none';
    if (next) next.style.display = state.step < TOTAL_STEPS ? 'inline-flex' : 'none';
  }

  function showFabricNavFloat() {
    if (state.step !== 4) return;
    detachFabricFloatIdleGuards();
    var root = document.getElementById('fabricNavFloat');
    if (!root) return;
    syncFabricFloatNav();
    root.classList.add('visible');
    root.setAttribute('aria-hidden', 'false');
  }

  /**
   * После выбора ткани: панель «Ткань выбрана» через 3 с простоя.
   * Скролл с заметным смещением или кручение колеса с отменой — не показываем (пользователь ищет «Далее»).
   * Базовая позиция скролла снимается после кадра закрытия лайтбокса, чтобы не ловить ложный scroll.
   */
  function scheduleFabricNavFloatAfterFabricChoice() {
    if (_fabricNavFloatTimer) {
      clearTimeout(_fabricNavFloatTimer);
      _fabricNavFloatTimer = null;
    }
    detachFabricFloatIdleGuards();
    _fabricNavFloatTimer = window.setTimeout(function () {
      _fabricNavFloatTimer = null;
      detachFabricFloatIdleGuards();
      if (state.step !== 4) return;
      showFabricNavFloat();
    }, 3000);
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        captureFabricIdleScrollBaseline();
        attachFabricFloatIdleGuards();
      });
    });
  }

  /* =====================================================================
     ШАГ 5: ЦВЕТ КАРКАСА
  ===================================================================== */
  function renderStep5() {
    var isZip = state.awningType === 'zip';
    var stdGrp = document.getElementById('colorStdGroup');
    var zipGrp = document.getElementById('colorZipGroup');
    var stdSw = document.getElementById('colorStdSwatches');
    var sfSw = document.getElementById('colorStorefrontSwatches');

    if (stdGrp) stdGrp.style.display = isZip ? 'none' : 'block';
    if (zipGrp) zipGrp.style.display = isZip ? 'block' : 'none';

    if (!isZip) {
      var isSf = state.awningType === 'storefront';
      if (stdSw) stdSw.style.display = isSf ? 'none' : 'flex';
      if (sfSw) sfSw.style.display = isSf ? 'flex' : 'none';
      syncSwatchGroup(isSf ? 'colorStorefrontSwatches' : 'colorStdSwatches', state.frameColor);
    } else {
      syncSwatchGroup('colorZipSwatches', state.frameColorZip);
    }
  }

  /* =====================================================================
     ШАГ 6: УПРАВЛЕНИЕ
  ===================================================================== */
  function updateRemoteProfileHint() {
    var hint = document.getElementById('remoteProfileHint');
    if (!hint) return;
    if (state.multiChannelRemote) {
      hint.textContent =
        'В расчёт идёт многоканальный пульт (несколько маркиз с одного пульта).';
    } else if (state.lightingOption === 'standard' && state.awningType === 'standard') {
      hint.textContent =
        'При LED подсветке в расчёт идёт пульт с двумя каналами: маркиза и освещение управляются отдельно.';
    } else {
      hint.textContent =
        'Одноканальный пульт для одной маркизы. Отметьте галочку ниже, если нужен многоканальный пульт.';
    }
  }

  function renderStep6() {
    syncCardGroup('controlCards', state.control);
    syncCardGroup('motorCards', state.motorBrand);
    syncToggleGroup('sensorToggles', state.sensorType);
    syncToggleGroup('ledToggles', state.lightingOption);

    var elOpts = document.getElementById('electricOptions');
    if (elOpts) elOpts.style.display = state.control === 'electric' ? 'block' : 'none';

    // LED: only for standard + electric
    var ledGroup = document.getElementById('ledGroup');
    if (ledGroup) {
      ledGroup.style.display = (state.awningType === 'standard' && state.control === 'electric') ? 'block' : 'none';
    }

    var rpg = document.getElementById('remoteProfileGroup');
    if (rpg) {
      rpg.style.display = state.control === 'electric' ? 'block' : 'none';
    }
    var mrcb = document.getElementById('multiChannelRemoteCb');
    if (mrcb) {
      mrcb.checked = !!state.multiChannelRemote;
    }
    updateRemoteProfileHint();

    // ZIP: скрываем весь блок датчиков
    var sensorSection = document.getElementById('sensorSection');
    if (sensorSection) {
      sensorSection.style.display = state.awningType === 'zip' ? 'none' : 'block';
    }
    if (state.awningType === 'zip' && state.sensorType !== 'none') {
      state.sensorType = 'none';
      syncToggleGroup('sensorToggles', state.sensorType);
    }

    // Cassette + Gaviota (motor decolife): disable
    var decoCard = document.getElementById('motorDecolife');
    if (decoCard) {
      var cassDisabled = state.awningType === 'standard' && state.config === 'cassette';
      if (cassDisabled) {
        decoCard.classList.add('disabled');
        if (state.motorBrand === 'decolife') {
          state.motorBrand = 'simu';
          syncCardGroup('motorCards', state.motorBrand);
        }
      } else {
        decoCard.classList.remove('disabled');
      }
    }
  }

  /* =====================================================================
     ХЕЛПЕРЫ ВЫБОРА
  ===================================================================== */
  function syncCardGroup(containerId, value) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.querySelectorAll('[data-value]').forEach(function (el) {
      el.classList.toggle('selected', el.dataset.value === value);
    });
  }

  function syncSwatchGroup(containerId, value) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.querySelectorAll('.color-swatch').forEach(function (el) {
      el.classList.toggle('selected', el.dataset.value === value);
    });
  }

  function syncToggleGroup(containerId, value) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.querySelectorAll('.toggle-btn').forEach(function (el) {
      el.classList.toggle('selected', el.dataset.value === value);
    });
  }

  /* =====================================================================
     ПРИВЯЗКА КЛИКОВ (вызывается один раз при DOMContentLoaded)
  ===================================================================== */
  function bindAll() {
    // Type cards (Step 1)
    bindCardGroup('typeCards', function (value) {
      state.awningType = value;
      vzLightbox.close();
      // Reset config for new type
      var opts = getConfigOptions();
      state.config = opts[0].value;
      // Цвета G400/G450 (ral9005, ral9t08) только для витринной
      if (value === 'standard' && (state.frameColor === 'ral9005' || state.frameColor === 'ral9t08')) {
        state.frameColor = 'white';
      }
      if (typeof updateAwningPreview === 'function') updateAwningPreview(value);
    });

    // Fabric cards (Step 4)
    bindCardGroup('fabricCards', function (value) {
      state.fabric = value;
      state.fabricStdSwatch = null;
      refreshFabricCarousel();
      scrollToFabricColorCatalog();
    });
    bindCardGroup('fabricZipCards', function (value) {
      state.fabricZip = value;
      renderVeozipColors();
      renderSoltisSection();
      renderCopacoSection();
    });

    // Color swatches (Step 5)
    bindSwatchGroup('colorStdSwatches', function (value) { state.frameColor = value; });
    bindSwatchGroup('colorStorefrontSwatches', function (value) { state.frameColor = value; });
    bindSwatchGroup('colorZipSwatches', function (value) { state.frameColorZip = value; });

    // Control cards (Step 6)
    bindCardGroup('controlCards', function (value) {
      state.control = value;
      renderStep6();
    });
    bindCardGroup('motorCards', function (value) {
      state.motorBrand = value;
    });
    bindToggleGroup('sensorToggles', function (value) { state.sensorType = value; });
    bindToggleGroup('ledToggles', function (value) {
      state.lightingOption = value;
      updateRemoteProfileHint();
    });

    var mrcb = document.getElementById('multiChannelRemoteCb');
    if (mrcb) {
      mrcb.addEventListener('change', function () {
        state.multiChannelRemote = mrcb.checked;
        updateRemoteProfileHint();
      });
    }

    // Install cards (Step 7)
    bindCardGroup('installCards', function (value) { state.installation = value; });

    // Nav buttons
    var prevBtn = document.getElementById('wzPrev');
    var nextBtn = document.getElementById('wzNext');
    var calcBtn = document.getElementById('wzCalc');
    var addRowBtn = document.getElementById('addRowBtn');

    if (prevBtn) prevBtn.addEventListener('click', goPrev);
    if (nextBtn) nextBtn.addEventListener('click', goNext);
    if (calcBtn) calcBtn.addEventListener('click', doCalculate);
    if (addRowBtn) addRowBtn.addEventListener('click', addRow);

    var fabricBackdrop = document.getElementById('fabricNavFloatBackdrop');
    var fabricDismiss = document.getElementById('fabricFloatDismiss');
    var fabricFPrev = document.getElementById('fabricFloatPrev');
    var fabricFNext = document.getElementById('fabricFloatNext');
    if (fabricBackdrop) fabricBackdrop.addEventListener('click', hideFabricNavFloat);
    if (fabricDismiss) fabricDismiss.addEventListener('click', hideFabricNavFloat);
    if (fabricFPrev) fabricFPrev.addEventListener('click', goPrev);
    if (fabricFNext) fabricFNext.addEventListener('click', goNext);

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var fRoot = document.getElementById('fabricNavFloat');
      if (!fRoot || !fRoot.classList.contains('visible')) return;
      var vLb = document.getElementById('vzLightbox');
      if (vLb && vLb.classList.contains('vz-open')) return;
      hideFabricNavFloat();
      e.preventDefault();
    });
  }

  function bindCardGroup(containerId, onChange) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.addEventListener('click', function (e) {
      var card = e.target.closest('[data-value]');
      if (!card || card.classList.contains('disabled')) return;
      var value = card.dataset.value;
      c.querySelectorAll('[data-value]').forEach(function (el) {
        el.classList.toggle('selected', el === card);
      });
      onChange(value);
    });
  }

  function bindSwatchGroup(containerId, onChange) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.addEventListener('click', function (e) {
      var sw = e.target.closest('.color-swatch');
      if (!sw) return;
      c.querySelectorAll('.color-swatch').forEach(function (el) { el.classList.remove('selected'); });
      sw.classList.add('selected');
      onChange(sw.dataset.value);
    });
  }

  function bindToggleGroup(containerId, onChange) {
    var c = document.getElementById(containerId);
    if (!c) return;
    c.addEventListener('click', function (e) {
      var btn = e.target.closest('.toggle-btn');
      if (!btn) return;
      c.querySelectorAll('.toggle-btn').forEach(function (el) { el.classList.remove('selected'); });
      btn.classList.add('selected');
      onChange(btn.dataset.value);
    });
  }

  /* =====================================================================
     ZIP — ЛИМИТЫ И АВТОПЕРЕКЛЮЧЕНИЕ
  ===================================================================== */
  var ZIP_LIMITS = {
    zip100: { maxW: 4.0, maxH: 3.5 },
    zip130: { maxW: 5.0, maxH: 5.0 }
  };

  function checkZipAutoSwitch() {
    if (state.awningType !== 'zip') return;
    if (state.config !== 'zip100') return;

    var lim = ZIP_LIMITS.zip100;
    var needSwitch = false;
    var reasons = [];

    state.items.forEach(function (item) {
      var w = parseFloat(item.width);
      var h = parseFloat(item.dim);
      if (!isNaN(w) && w > lim.maxW) { needSwitch = true; reasons.push('ширина ' + w + '\u00a0м > ' + lim.maxW + '\u00a0м'); }
      if (!isNaN(h) && h > lim.maxH) { needSwitch = true; reasons.push('высота ' + h + '\u00a0м > ' + lim.maxH + '\u00a0м'); }
    });

    var notice = document.getElementById('zipUpgradeNotice');
    var titleEl = document.getElementById('zipUpgradeTitle');
    var textEl  = document.getElementById('zipUpgradeText');

    if (needSwitch) {
      state.config = 'zip130';
      if (notice && titleEl && textEl) {
        titleEl.textContent = 'Автоматически применён ZIP 130';
        var uniqueReasons = reasons.filter(function (v, i, a) { return a.indexOf(v) === i; });
        textEl.textContent = 'Введённые размеры (' + uniqueReasons.join(', ') + ') превышают допустимые для ZIP\u00a0100 (макс. 4\u00d73,5\u00a0м). '
          + 'Для корректного расчёта конструкция изменена на ZIP\u00a0130 (макс. 5\u00d75\u00a0м).';
        notice.classList.add('visible');
      }
    } else {
      if (notice) notice.classList.remove('visible');
    }
  }

  /* =====================================================================
     ВАЛИДАЦИЯ
  ===================================================================== */
  function validateStep(step) {
    clearErrors();
    if (step === 3) {
      var isZip = state.awningType === 'zip';
      var isSf = state.awningType === 'storefront';
      var minW = 2;
      var maxW = 6;
      if (isZip) maxW = 5;
      else if (isSf) maxW = 7;
      else if (state.awningType === 'standard' && state.config === 'open') maxW = 14;
      else if (state.awningType === 'standard' && state.config === 'semi') maxW = 7;
      else if (state.awningType === 'standard' && state.config === 'cassette') maxW = 14;
      var maxDim = 3.5;
      if (isZip) maxDim = 5;
      else if (isSf) maxDim = 1.4;
      else if (state.awningType === 'standard' && state.config === 'open') maxDim = 4;
      else if (state.awningType === 'standard' && state.config === 'semi') maxDim = 4;
      else if (state.awningType === 'standard' && state.config === 'cassette') maxDim = 4;
      var minDim = isZip ? 1 : (isSf ? 0.8 : 1.5);
      for (var i = 0; i < state.items.length; i++) {
        var item = state.items[i];
        var posLabel = 'Позиция ' + (i + 1) + ': ';
        var w = parseFloat(item.width);
        if (isNaN(w) || w < minW || w > maxW) {
          showError('step3Error', posLabel + 'ширина должна быть от ' + minW + ' до ' + maxW + ' м');
          return false;
        }
        if (isZip) {
          var h = parseFloat(item.dim);
          if (isNaN(h) || h < 1 || h > 5) {
            showError('step3Error', posLabel + 'высота должна быть от 1 до 5 м');
            return false;
          }
        } else {
          var pd = parseFloat(item.dim);
          if (isNaN(pd) || pd < minDim || pd > maxDim) {
            showError('step3Error', posLabel + 'вылет должен быть от ' + minDim + ' до ' + maxDim + ' м');
            return false;
          }
          // Скрещённые локти — только у складных локтевых (Gaviota); витринные — выпадающие локти, правило не применяется.
          if (state.awningType === 'standard') {
            if (pd >= w - 1e-9) {
              showError(
                'step3Error',
                posLabel + 'вылет должен быть меньше ширины — иначе типична комплектация со скрещёнными локтями (слабее каркас).'
              );
              return false;
            }
            if (w >= 4 && pd > w - 0.5 + 1e-9) {
              showError(
                'step3Error',
                posLabel + 'при ширине от 4 м вылет не больше (ширина − 0,5 м), без скрещённых локтей. Уменьшите вылет или увеличьте ширину.'
              );
              return false;
            }
          }
        }
        var qty = parseInt(item.qty, 10);
        if (isNaN(qty) || qty < 1) {
          showError('step3Error', posLabel + 'укажите количество (минимум 1 шт)');
          return false;
        }
      }
      if (isZip) checkZipAutoSwitch();
    }
    return true;
  }

  function showError(id, msg) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.className = 'wz-error visible';
  }

  function clearErrors() {
    document.querySelectorAll('.wz-error').forEach(function (el) {
      el.className = 'wz-error';
      el.textContent = '';
    });
  }

  /* =====================================================================
     РАСЧЁТ — POST /api/calculate × N позиций
  ===================================================================== */
  function doCalculate() {
    var calcBtn = document.getElementById('wzCalc');
    if (calcBtn) { calcBtn.disabled = true; calcBtn.textContent = 'Считаем…'; }

    if (state.awningType !== 'zip') {
      state.items.forEach(function (item) {
        item.dim = normalizeProjectionDim(item.dim);
      });
    }

    // Shared params (same for all positions)
    var shared = {
      awning_type: state.awningType,
      config: state.config,
      control: state.control,
      installation: state.installation,
    };

    if (state.awningType === 'zip') {
      shared.fabric_zip = state.fabricZip;
      if (state.fabricZip === 'veozip' && state.veozipColor) {
        shared.veozip_color = state.veozipColor;
      }
      if (state.fabricZip === 'soltis' && state.soltisColor) {
        shared.soltis_color = state.soltisColor;
        shared.soltis_collection = state.soltisCollection;
      }
      if (state.fabricZip === 'copaco' && state.copacoColor) {
        shared.copaco_color = state.copacoColor;
        shared.copaco_collection = state.copacoCollection;
      }
      shared.frame_color_zip = state.frameColorZip;
    } else {
      shared.fabric = state.fabric;
      shared.frame_color = state.frameColor;
      if (state.fabricStdSwatch && state.fabricStdSwatch.label) {
        shared.fabric_color_label = state.fabricStdSwatch.label;
      }
    }

    if (state.control === 'electric') {
      shared.motor_brand = state.motorBrand;
      shared.sensor_type = state.sensorType;
      shared.lighting_option = state.lightingOption;
      if (state.multiChannelRemote) {
        shared.multi_channel_remote = true;
      }
    }

    // Сохраняем параметры для кнопки PDF
    window._lastCalcParamsList = [];

    var promises = state.items.map(function (item) {
      var params = {};
      for (var k in shared) { if (shared.hasOwnProperty(k)) params[k] = shared[k]; }
      params.width = parseFloat(item.width);
      if (state.awningType === 'zip') {
        params.height = parseFloat(item.dim);
      } else {
        params.projection = parseFloat(item.dim);
      }
      if (state.awningType === 'storefront' && item.tilt170) {
        params.storefront_tilt_170 = true;
      }
      if (state.awningType === 'storefront' && item.valance && item.valance !== 'none') {
        params.storefront_valance = item.valance;
      }
      window._lastCalcParamsList.push(params);
      return fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      }).then(function (r) { return r.json(); });
    });

    Promise.all(promises)
      .then(function (results) {
        var hasError = results.some(function (r) { return r.error; });
        if (hasError) {
          var msg = results.map(function (r) { return r.error; }).filter(Boolean).join('; ');
          alert('Ошибка расчёта: ' + msg);
          return;
        }
        renderResult(results);
      })
      .catch(function (err) {
        alert('Сетевая ошибка: ' + err);
      })
      .finally(function () {
        if (calcBtn) { calcBtn.disabled = false; calcBtn.textContent = 'Рассчитать стоимость'; }
      });
  }

  /* =====================================================================
     ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА
  ===================================================================== */
  function renderResult(results) {
    var grandTotal = 0;
    var textLines = ['[Расчёт: Маркизы]'];

    results.forEach(function (res, idx) {
      var item = state.items[idx];
      var qty = parseInt(item.qty, 10) || 1;
      var posTotal = (res.total || 0) * qty;
      grandTotal += posTotal;

      var sizeStr = item.width + '\u00d7' + item.dim + '\u00a0м';
      textLines.push('Поз. ' + (idx + 1) + ': ' + sizeStr + ' \u00d7 ' + qty + '\u00a0шт — ' + posTotal.toLocaleString('ru-RU') + '\u00a0\u20bd');
      if (state.awningType === 'storefront' && item.tilt170) {
        textLines.push('  \u2192 Угол наклона 170° (+15% к базе позиции)');
      }
      if (state.awningType === 'storefront' && item.valance === 'straight') {
        textLines.push('  \u2192 Волан прямой: ' + item.width + '\u00a0м ширины × 10\u00a0€/м');
      } else if (state.awningType === 'storefront' && item.valance === 'shaped') {
        textLines.push('  \u2192 Волан фигурный: ' + item.width + '\u00a0м ширины × 15\u00a0€/м');
      }
      if (res.decolife) {
        var d = res.decolife;
        var dx = d.crossed_arms ? ' · скрещенные локти' : '';
        var sDisp = d.series_display || (d.series || '').replace(/Decolife/g, 'Gaviota');
        textLines.push(
          '  → ' + sDisp + ', стандарт ' + d.std_width + '\u00d7' + d.std_projection + '\u00a0м' + dx
        );
      }
    });
    textLines.push('ИТОГО: ' + grandTotal.toLocaleString('ru-RU') + '\u00a0\u20bd');
    window._calcText = textLines.join('\n');

    // Big price
    var priceEl = document.getElementById('resultPrice');
    if (priceEl) {
      priceEl.textContent = '';
      priceEl.appendChild(document.createTextNode(grandTotal.toLocaleString('ru-RU') + '\u00a0'));
      var span = document.createElement('span');
      span.textContent = '\u20bd';
      priceEl.appendChild(span);
    }
    var resultBlock = document.getElementById('resultBlock');
    if (resultBlock) resultBlock.classList.add('visible');

    var dlCard = document.getElementById('decolifeResultCard');
    if (dlCard) {
      var d0 = results.length && results[0].decolife;
      if (d0) {
        dlCard.hidden = false;
        dlCard.style.display = 'block';
        var badgeEl = document.getElementById('decolifeResultBadge');
        if (badgeEl) {
          if (d0.product_line === 'semi_elbow') {
            badgeEl.textContent = 'Подобранная серия Gaviota (полукассетная)';
          } else if (d0.product_line === 'cassette_elbow') {
            badgeEl.textContent = 'Подобранная серия Gaviota (кассетная)';
          } else {
            badgeEl.textContent = 'Подобранная серия Gaviota (открытая)';
          }
        }
        var sShow = d0.series_display || (d0.series || '').replace(/Decolife/g, 'Gaviota');
        var imgEl = document.getElementById('decolifeResultImg');
        if (imgEl) {
          imgEl.src = d0.thumbnail || '';
          imgEl.alt = sShow || 'Gaviota';
          imgEl.onclick = function () {
            if (d0.thumbnail) openSchemeZoom(d0.thumbnail, sShow || 'Gaviota');
          };
        }
        var tEl = document.getElementById('decolifeResultTitle');
        if (tEl) tEl.textContent = sShow || '';
        var mEl = document.getElementById('decolifeResultMeta');
        if (mEl) {
          var parts = [
            'Стандартный размер по прайсу: ' + d0.std_width + '\u00d7' + d0.std_projection + '\u00a0м',
          ];
          if (d0.crossed_arms) parts.push('конфигурация: скрещенные локти');
          if (d0.frame_note) parts.push(d0.frame_note);
          mEl.textContent = parts.join(' · ');
        }
        var descEl = document.getElementById('decolifeResultDesc');
        if (descEl) descEl.textContent = d0.description || '';
        var multiNote = document.getElementById('decolifeResultMulti');
        if (multiNote) {
          if (results.length > 1) {
            multiNote.textContent = 'Несколько позиций: для каждой серия Gaviota указана в тексте заявки и в детализации.';
            multiNote.style.display = 'block';
          } else {
            multiNote.textContent = '';
            multiNote.style.display = 'none';
          }
        }
      } else {
        dlCard.hidden = true;
        dlCard.style.display = 'none';
        var imgClear = document.getElementById('decolifeResultImg');
        if (imgClear) imgClear.onclick = null;
      }
    }

    // Breakdown
    var body = document.getElementById('breakdownBody');
    if (body) {
      body.textContent = '';
      var multi = results.length > 1;

      results.forEach(function (res, idx) {
        var item = state.items[idx];
        var qty = parseInt(item.qty, 10) || 1;
        var posTotal = (res.total || 0) * qty;

        if (multi) {
          var posHdr = document.createElement('div');
          posHdr.className = 'bd-pos-header';
          posHdr.textContent = 'Позиция ' + (idx + 1) + ': ' + item.width + '\u00d7' + item.dim + '\u00a0м \u00d7 ' + qty + '\u00a0шт';
          body.appendChild(posHdr);
        }

        res.rows.forEach(function (r) {
          var row = document.createElement('div');
          row.className = 'bd-row';
          var lbl = document.createElement('span');
          lbl.className = 'bd-label';
          lbl.textContent = r[0];
          var val = document.createElement('span');
          val.className = 'bd-val';
          val.textContent = numFmt.format(qty > 1 ? r[1] * qty : r[1]);
          row.appendChild(lbl);
          row.appendChild(val);
          body.appendChild(row);
        });

        if (multi) {
          var subRow = document.createElement('div');
          subRow.className = 'bd-row bd-total';
          var subLbl = document.createElement('span');
          subLbl.className = 'bd-label';
          subLbl.textContent = 'Итого позиции:';
          var subVal = document.createElement('span');
          subVal.className = 'bd-val';
          subVal.textContent = numFmt.format(posTotal);
          subRow.appendChild(subLbl);
          subRow.appendChild(subVal);
          body.appendChild(subRow);
        }
      });

      if (multi) {
        var grandRow = document.createElement('div');
        grandRow.className = 'bd-grand';
        var grandLbl = document.createElement('span');
        grandLbl.className = 'bd-grand-label';
        grandLbl.textContent = 'ИТОГО';
        var grandPrice = document.createElement('span');
        grandPrice.className = 'bd-grand-price';
        grandPrice.textContent = numFmt.format(grandTotal);
        grandRow.appendChild(grandLbl);
        grandRow.appendChild(grandPrice);
        body.appendChild(grandRow);
      }
    }

    var breakdownBlock = document.getElementById('breakdownBlock');
    if (breakdownBlock) breakdownBlock.classList.add('visible');

    // PDF button — show and store params for download
    var pdfWrap = document.getElementById('pdfBtnWrap');
    if (pdfWrap) pdfWrap.classList.add('visible');

    // Lead form
    var leadSub = document.getElementById('leadSub');
    if (leadSub) {
      leadSub.textContent = 'Ваш расчёт: ';
      var strong = document.createElement('strong');
      strong.textContent = grandTotal.toLocaleString('ru-RU') + '\u00a0\u20bd';
      leadSub.appendChild(strong);
      leadSub.appendChild(document.createTextNode(' \u2014 выберите удобный способ связи'));
    }

    setTimeout(function () {
      var lf = document.getElementById('leadForm');
      if (lf) {
        lf.classList.add('visible');
        lf.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 600);
  }

  /* =====================================================================
     ГEOПОЗИЦИЯ
  ===================================================================== */
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
      } catch (e) {}
    };
    gx.onerror = gx.ontimeout = function () {};
    gx.send();
  })();

  /* =====================================================================
     ОТПРАВКА ЛИДА
  ===================================================================== */
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

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('#btnWhatsapp,#btnTelegram,#btnMax');
    if (!btn) return;
    var ch = btn.id === 'btnWhatsapp' ? 'whatsapp' : btn.id === 'btnTelegram' ? 'telegram' : 'max';

    try {
      var ymId = window._YM_ID;
      if (typeof ym === 'function' && ymId) ym(ymId, 'reachGoal', 'calculator_lead', { channel: ch, calculator_type: 'awning' });
    } catch (er) {}

    if ((btn.id === 'btnWhatsapp' || btn.id === 'btnTelegram') && window._calcText) {
      e.preventDefault();
      var city = window._userCity || 'Не определён';
      var txt = '\u{1F4CD} Город: ' + city + '\n\nДобрый день! Хочу обсудить расчёт:\n' + window._calcText;
      var enc = encodeURIComponent(txt);
      var url = btn.id === 'btnWhatsapp'
        ? 'https://api.whatsapp.com/send?phone=79064297420&text=' + enc
        : 'https://t.me/comfort_dom_andrey?text=' + enc;
      window.open(url, '_blank');
      fetch('/api/submit-lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: '(мессенджер)',
          city: window._userCity || 'Не определён',
          calc_text: window._calcText || '',
          channel: ch,
        }),
      }).catch(function () {});
    }
  });

  function showOk(phone) {
    var lf = document.getElementById('leadForm');
    if (lf) { lf.classList.remove('visible'); lf.style.display = 'none'; }
    var s = document.getElementById('leadSuccess');
    var sub = document.getElementById('successSub');
    if (s && sub) {
      sub.textContent = 'Перезвоним на ';
      var st = document.createElement('strong');
      st.textContent = phone;
      sub.appendChild(st);
      sub.appendChild(document.createTextNode(' в течение 15 минут. Расчёт уже у менеджера.'));
      s.classList.add('visible');
    }
    try {
      var ymId = window._YM_ID;
      if (typeof ym === 'function' && ymId) ym(ymId, 'reachGoal', 'calculator_lead', { calculator_type: 'awning' });
    } catch (er) {}
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
    inp.addEventListener('blur', function () {
      if (digits(this.value).length <= 1) this.value = '';
    });
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
    bindAll();
    render();
  });

})();

/* =========================================================================
   СКАЧАТЬ КП — вызывается из кнопки в HTML
   ========================================================================= */
function downloadKP() {
  var btn = document.getElementById('pdfDownloadBtn');
  if (!btn) return;

  var params = (window._lastCalcParamsList && window._lastCalcParamsList[0]) || null;
  if (!params) {
    alert('Сначала выполните расчёт.');
    return;
  }

  // Если несколько позиций — берём параметры первой (общая конфигурация та же)
  // для агрегированного КП используем объединённые данные
  var allParams = window._lastCalcParamsList || [params];

  // UI: loading state
  var origContent = btn.innerHTML;
  btn.classList.add('pdf-btn-loading');
  btn.innerHTML = '<svg class="pdf-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Формируем КП…';

  fetch('/api/pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(allParams[0]),
  })
    .then(function (response) {
      if (!response.ok) {
        return response.json().then(function (e) { throw new Error(e.error || 'Ошибка сервера'); });
      }
      return response.blob();
    })
    .then(function (blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      var type = (allParams[0].awning_type || 'awning').replace('standard','маркиза').replace('storefront','витринная').replace('zip','ZIP');
      var now = new Date();
      var pad = function (n) { return String(n).padStart(2, '0'); };
      var ts = pad(now.getDate()) + '_' + pad(now.getMonth() + 1) + '_' + now.getFullYear()
             + '_' + pad(now.getHours()) + '_' + pad(now.getMinutes()) + '_' + pad(now.getSeconds());
      a.download = 'КП_' + type + '_' + ts + '.pdf';
      a.href = url;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(function () {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 1000);
    })
    .catch(function (err) {
      alert('Не удалось сформировать КП: ' + err.message);
    })
    .finally(function () {
      btn.innerHTML = origContent;
      btn.classList.remove('pdf-btn-loading');
    });
}
