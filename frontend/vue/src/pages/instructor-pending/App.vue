<!-- Пилотная страница «Ожидание модерации» (/instructors/pending).
     Разметка — перенос 1:1 из legacy frontend/instructor-pending.html
     (FR-86, ОВ-4: без редизайна, тексты без изменений — языковой зонинг RU).
     Стили — подключаемый css styles.css (перенос дословный).
     Держать синхронной со статической разметкой instructors-pending.html.
     Блок 2 (опрос статуса заявки, FR-80…FR-83) — задача 3.1 против
     контракта change add-application-status-polling; таймер и его отмена —
     в этом компоненте (setup/onUnmounted); pinia/vue-router НЕ вводятся
     (research.md п.8). -->
<template>
  <header class="wrap"><a class="brand" href="/instructors"><span class="check">✓</span><span><b>Сбер</b>Автошкола</span></a><a class="back" href="/instructors">← Вернуться на лендинг</a></header>
  <main class="wrap status-screen"><section class="card">
  <div class="icon">◷</div>
  <div class="kicker">Заявка инструктора</div>
  <h1>Заявка на рассмотрении</h1>
  <p>Анкета отправлена. Команда СберАвтошколы проверит данные и документы — ответ придёт на указанную почту. Обычно рассмотрение занимает несколько дней.</p>
  <div class="steps">
  <div class="path-row"><div class="path-icon">✓</div><div><strong>01 · Анкета отправлена</strong><span>Контакты и информация об автомобиле получены</span></div></div>
  <div class="path-row"><div class="path-icon">◷</div><div><strong>02 · Проверка</strong><span>Квалификация и документы — сейчас</span></div></div>
  <div class="path-row"><div class="path-icon">⌁</div><div><strong>03 · Подключение</strong><span>Согласование условий сотрудничества</span></div></div>
  </div>
  <div class="actions"><a class="btn primary" href="/">На главную</a><a class="btn ghost" href="/instructors">О лендинге для инструкторов</a></div>
  </section></main>
  <footer><div class="wrap foot"><span>© СберАвтошкола · Концепция экрана регистрации</span><span>Защита персональных данных должна быть настроена до запуска</span></div></footer>
</template>
