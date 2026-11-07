<!-- Экран отказа «Заявка отклонена» (/instructors/rejected).
     Разметка — перенос 1:1 из legacy frontend/instructor-rejected.html
     (change add-vue-s11-status-forms, задача 2.1; FR-13/FR-17, без
     редизайна, тексты без изменений — языковой зонинг RU). Стили —
     подключаемый css styles.css (перенос дословный).
     Держать синхронной со статической разметкой instructors-rejected.html.
     Поведение js/instructor-rejected.js 1:1 (onMounted): причина из
     sessionStorage «instructor_rejected_reason» — пишет модалка входа
     (landing.js) при route=rejected, КОНТРАКТ ЛОГИНА НЕ МЕНЯЕТСЯ;
     try/catch на недоступность хранилища (тихо, без причины); пусто/нет —
     блок причины скрыт (v-show — эквивалент стекового фрагмента legacy
     «style.display = ''»). Статус при загрузке НЕ проверяется — НОЛЬ
     запросов к API (причина приходит только из ответа логина).
     Id-якорь e2e #reason-text сохранен (TC-S9UI-003). -->
<template>
  <header class="wrap"><a class="brand" href="/instructors"><span class="check">✓</span><span><b>Сбер</b>Автошкола</span></a><a class="back" href="/instructors">← Вернуться на лендинг</a></header>
  <main class="wrap status-screen"><section class="card">
  <div class="icon">⌁</div>
  <div class="kicker">Заявка инструктора</div>
  <h1>Заявка отклонена</h1>
  <p>К сожалению, заявку не удалось одобрить. Ты можешь подать заявку повторно, когда устранишь причину отказа.</p>
  <div class="reason" id="reason-block" v-show="reason"><b>Причина отказа</b><p id="reason-text">{{ reason }}</p></div>
  <div class="actions"><a class="btn primary" href="/">На главную</a><a class="btn ghost" href="/instructors">О лендинге для инструкторов</a></div>
  </section></main>
  <footer><div class="wrap foot"><span>© СберАвтошкола · Концепция экрана регистрации</span><span>Защита персональных данных должна быть настроена до запуска</span></div></footer>
</template>

<script>
// Сессионного контракта у страницы нет: открытие по прямой ссылке —
// нейтральный экран без персональной причины (чужую не раскрываем —
// design). Запросов к API ноль.
import { onMounted, ref } from 'vue';

var REJECTED_REASON_KEY = 'instructor_rejected_reason';

export default {
  setup: function () {
    var reason = ref('');

    onMounted(function () {
      // Поведение legacy js/instructor-rejected.js (1:1, FR-17): чтение
      // sessionStorage в try/catch (недоступен — без причины).
      try {
        var stored = sessionStorage.getItem(REJECTED_REASON_KEY);
        if (stored) { reason.value = stored; }
      } catch (e) { /* sessionStorage недоступен — без причины */ }
    });

    return { reason: reason };
  },
};
</script>
