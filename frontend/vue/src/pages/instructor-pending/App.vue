<!-- Пилотная страница «Ожидание модерации» (/instructors/pending).
     Разметка — перенос 1:1 из legacy frontend/instructor-pending.html
     (FR-86, ОВ-4: без редизайна, тексты без изменений — языковой зонинг RU).
     Стили — подключаемый css styles.css (перенос дословный).
     Держать синхронной со статической разметкой instructors-pending.html.
     Блок 2 (опрос статуса заявки, FR-80…FR-83) — задача 3.1 против
     контракта change add-application-status-polling; таймер и его отмена —
     в этом компоненте (setup/onUnmounted); pinia/vue-router НЕ вводятся
     (research.md п.8).
     Машина состояний экрана — design.md polling-пакета (arch-review-002
     MAJ-1 учтен): STATIC (нет токенов — 0 запросов) / POLLING (первый тик
     сразу, далее каждые 12 с ПОСЛЕ завершения предыдущего запроса) /
     терминальные (approved → обмен → кабинет; rejected → экран отказа;
     404 обмена → подсказка входа, токены localStorage удалены). -->
<template>
  <header class="wrap"><a class="brand" href="/instructors"><span class="check">✓</span><span><b>Сбер</b>Автошкола</span></a><a class="back" href="/instructors">← Вернуться на лендинг</a></header>
  <main class="wrap status-screen"><section class="card">
  <div class="icon">◷</div>
  <div class="kicker">Заявка инструктора</div>
  <h1>Заявка на рассмотрении</h1>
  <p>Анкета отправлена. Команда СберАвтошколы проверит данные и документы — ответ придёт на указанную почту. Обычно рассмотрение занимает несколько дней.</p>
  <p v-if="loginHint" class="login-hint">Войдите с email и паролем.</p>
  <div class="steps">
  <div class="path-row"><div class="path-icon">✓</div><div><strong>01 · Анкета отправлена</strong><span>Контакты и информация об автомобиле получены</span></div></div>
  <div class="path-row"><div class="path-icon">◷</div><div><strong>02 · Проверка</strong><span>Квалификация и документы — сейчас</span></div></div>
  <div class="path-row"><div class="path-icon">⌁</div><div><strong>03 · Подключение</strong><span>Согласование условий сотрудничества</span></div></div>
  </div>
  <div class="actions"><a class="btn primary" href="/">На главную</a><a class="btn ghost" href="/instructors">О лендинге для инструкторов</a></div>
  </section></main>
  <footer><div class="wrap foot"><span>© СберАвтошкола · Концепция экрана регистрации</span><span>Защита персональных данных должна быть настроена до запуска</span></div></footer>
</template>

<script>
// Блок 2 (задача 3.1): опрос статуса заявки по контракту change
// add-application-status-polling (design.md «Машина состояний экрана»).
// Токены в localStorage кладет frontend/js/apply.js при сабмите анкеты:
// application_poll_token (многоразовый, X-Poll-Token) и
// application_exchange_token (одноразовый, тело POST). poll_token в URL
// не пишется (NFR-3/NFR-10). Сетевая ошибка тика — тихо (FR-83); остановка:
// unmount/скрытие вкладки/закрытие — таймер снят; pageshow (bfcache,
// persisted) — ре-арм по обычному графику (MIN-3, NFR-28).
import { onMounted, onUnmounted, ref } from 'vue';
import { postJSON, setToken } from '../../shared/api.js';

// интервал 12 с — решение СА (допустимый диапазон 10–15 с); бюджет
// NFR-28 «не более 5 запросов в минуту» держится в любом окне 60 с.
var POLL_INTERVAL_MS = 12000;
var POLL_KEY = 'application_poll_token';
var EXCHANGE_KEY = 'application_exchange_token';
var STATUS_URL = '/api/instructors/application-status';
var EXCHANGE_URL = '/api/instructors/application-exchange';
var REJECTED_REASON_KEY = 'instructor_rejected_reason';
// route 'cabinet' ответа обмена → кабинет инструктора (механика логина §15.5)
var CABINET_URL = '/instructor/dashboard';
var REJECTED_URL = '/instructors/rejected';

export default {
  setup: function () {
    // Подсказка терминального 404 обмена (MAJ-1): «войдите с email и
    // паролем» — без деталей о токене/заявке (404-неразличение сохраняется)
    var loginHint = ref(false);

    // Режимы экрана: 'static' (нет токенов — запросов нет, FR-80),
    // 'polling', 'paused' (скрытие вкладки / pagehide — возобновляемо),
    // 'terminal' (approved/rejected/404-обмена/unmount — не возобновляется).
    var mode = 'static';
    var timer = null;

    function lsGet(key) {
      try { return localStorage.getItem(key); } catch (e) { return null; }
    }
    function lsRemove(key) {
      try { localStorage.removeItem(key); } catch (e) {}
    }
    function ssSet(key, value) {
      try { sessionStorage.setItem(key, value); } catch (e) {}
    }

    function clearTimer() {
      if (timer !== null) { clearTimeout(timer); timer = null; }
    }

    // Следующий тик — через 12 с ПОСЛЕ завершения предыдущего запроса
    // (наложения запросов нет, design.md; NFR-28: интервал не меняется)
    function armTimer() {
      clearTimer();
      if (mode === 'polling') {
        timer = setTimeout(tick, POLL_INTERVAL_MS);
      }
    }

    function pauseIfPolling() {
      if (mode === 'polling') { mode = 'paused'; }
      clearTimer(); // фоновых таймеров, переживающих страницу, нет (FR-83)
    }

    function tick() {
      timer = null;
      if (mode !== 'polling') return;
      var pollToken = lsGet(POLL_KEY);
      if (!pollToken) { mode = 'static'; return; } // токены исчезли — STATIC
      fetch(STATUS_URL, { headers: { 'X-Poll-Token': pollToken } })
        .then(function (r) {
          return r.json().then(function (d) { return { status: r.status, data: d }; },
            function () { return { status: r.status, data: null }; });
        })
        .catch(function () { return { status: 0, data: null }; }) // сеть — тихо (FR-83)
        .then(function (res) {
          if (mode !== 'polling') return; // остановка в полете — ответ игнорируется
          var d = res.data;
          if (res.status === 200 && d && d.ok) {
            if (d.status === 'approved') { exchange(); return; }
            if (d.status === 'rejected') {
              // терминальное: тот же экран отказа, что после логина
              // route 'rejected' (FR-82, БЕЗ входа; design.md решение СА)
              mode = 'terminal';
              clearTimer();
              ssSet(REJECTED_REASON_KEY, d.reason || '');
              window.location.href = REJECTED_URL;
              return;
            }
          }
          // waiting / сетевая ошибка / прочие ответы — тихо, экран «на
          // рассмотрении», тот же интервал (FR-83, NFR-28)
          armTimer();
        });
    }

    function exchange() {
      var exchangeToken = lsGet(EXCHANGE_KEY);
      if (!exchangeToken) { armTimer(); return; } // вне контракта (токены выдаются вместе) — переходно, waiting
      postJSON(EXCHANGE_URL, { exchange_token: exchangeToken })
        .then(function (res) {
          if (mode !== 'polling') return;
          var d = res.data;
          if (res.status === 200 && d && d.ok && d.token) {
            // терминальное: сессия users выдана, роль instructor (FR-81) —
            // sessionStorage 'session_token' (механика api.js TOKEN_KEY);
            // токены localStorage удаляются ДО редиректа (MAJ-1), polling
            // остановлен; возврат на /instructors/pending → STATIC
            mode = 'terminal';
            clearTimer();
            setToken(d.token);
            lsRemove(POLL_KEY);
            lsRemove(EXCHANGE_KEY);
            window.location.href = CABINET_URL; // route 'cabinet'
            return;
          }
          if (res.status === 404) {
            // ПОСТОЯННЫЙ отказ (MAJ-1): токен не найден/уже потреблен/чужой —
            // повтор невозможен по построению; таймер снят, токены удалены,
            // нейтральная подсказка входа; НЕ waiting (иначе вечный цикл
            // «тик → approved → обмен → 404» против NFR-28)
            mode = 'terminal';
            clearTimer();
            lsRemove(POLL_KEY);
            lsRemove(EXCHANGE_KEY);
            loginHint.value = true;
            return;
          }
          // ПЕРЕХОДНЫЙ отказ (409: guard статуса / «approved без users»;
          // сетевая ошибка; токен НЕ потреблен) — остаемся в waiting,
          // повтор обмена на следующем тике (FR-81)
          armTimer();
        });
    }

    function onVisibilityChange() {
      if (document.hidden) {
        // скрытие вкладки: запросы прекращаются НЕМЕДЛЕННО (ушедший в
        // полете запрос не отменяем — ответ игнорируется, design.md)
        pauseIfPolling();
      } else if (mode === 'paused') {
        // возврат видимости: по обычному графику, БЕЗ немедленного тика
        // (бюджет ≤5/мин держится при частом переключении, NFR-28)
        mode = 'polling';
        armTimer();
      }
    }

    function onPageHide() { pauseIfPolling(); }
    function onBeforeUnload() { pauseIfPolling(); }

    // bfcache restore (back-навигация, MIN-3): ре-арм — только из PAUSED
    // (терминальное и статичное состояния ре-арма не требуют)
    function onPageShow(event) {
      if (event.persisted && mode === 'paused') {
        mode = 'polling';
        armTimer();
      }
    }

    onMounted(function () {
      document.addEventListener('visibilitychange', onVisibilityChange);
      window.addEventListener('pagehide', onPageHide);
      window.addEventListener('beforeunload', onBeforeUnload);
      window.addEventListener('pageshow', onPageShow);
      if (!lsGet(POLL_KEY)) { mode = 'static'; return; } // STATIC: 0 запросов (FR-80)
      mode = 'polling';
      tick(); // первый тик — сразу при загрузке (design.md машина состояний)
    });

    // Таймер и его отмена — в одном компоненте (ТЗ 3.1): уход со страницы
    // (переход по ссылке/unmount) останавливает опрос окончательно
    onUnmounted(function () {
      mode = 'terminal';
      clearTimer();
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('pagehide', onPageHide);
      window.removeEventListener('beforeunload', onBeforeUnload);
      window.removeEventListener('pageshow', onPageShow);
    });

    return { loginHint: loginHint };
  },
};
</script>
