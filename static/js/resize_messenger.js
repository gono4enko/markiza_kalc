/**
 * Отправляет высоту iframe в родительское окно (Tilda postMessage).
 * Вставляется в <head> шаблона index.html.
 */
(function () {
  function sendHeight() {
    var h = document.documentElement.scrollHeight;
    window.parent.postMessage({ iframeHeight: h }, '*');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sendHeight);
  } else {
    sendHeight();
  }

  window.addEventListener('resize', sendHeight);

  // Повторная отправка через 500 мс — после анимаций раскрытия блоков
  var observer = new MutationObserver(sendHeight);
  observer.observe(document.body, { childList: true, subtree: true, attributes: true });
})();
