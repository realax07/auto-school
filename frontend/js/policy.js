// Страница /policy — загрузка текста политики из артефакта через API.
// Спринт 9 (change add-personal-data-policy, задача 2.1, FR-76/NFR-25).
// Текст политики в этом модуле ОТСУТСТВУЕТ (grep-контроль NFR-25):
// GET /api/policy при загрузке; 200 {ok,version,date,text} →
// «Версия: X от Y» + абзацы (разбиение по пустой строке) текстовыми
// узлами (textContent/createTextNode, НЕ innerHTML — XSS-гигиена);
// 500/битый JSON/сетевая ошибка → честное сообщение в контейнере
// текста (design.md: «Политика временно недоступна. Попробуйте позже»).
var metaEl = document.getElementById('policy-meta');
var textEl = document.getElementById('policy-text');
var ERROR_MESSAGE = 'Политика временно недоступна. Попробуйте позже';

function showError() {
  metaEl.textContent = '';
  textEl.textContent = '';
  var el = document.createElement('p');
  el.className = 'policy-error';
  el.textContent = ERROR_MESSAGE;
  textEl.appendChild(el);
}

fetch('/api/policy')
  .then(function(r) {
    return r.json().then(function(d) {
      return {status: r.status, data: d};
    }).catch(function() {
      return {status: r.status, data: null}; // ответ не JSON — честная ошибка
    });
  })
  .then(function(res) {
    if (!(res.status === 200 && res.data && res.data.ok && res.data.text)) {
      showError();
      return;
    }
    metaEl.textContent = 'Версия: ' + res.data.version + ' от ' + res.data.date;
    String(res.data.text).split(/\n\s*\n/).forEach(function(chunk) {
      var p = chunk.replace(/^\s+|\s+$/g, '');
      if (!p) return;
      var el = document.createElement('p');
      el.textContent = p; // только текстовые узлы — без HTML-инъекций
      textEl.appendChild(el);
    });
  })
  .catch(showError);
