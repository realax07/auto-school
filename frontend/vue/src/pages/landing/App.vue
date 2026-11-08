<!-- Заглушка лендинга «/» (Спринт 12, change add-vue-s12-landing-apply,
     задача 2.1 — arch-review-001 MIN-2: без модуля страницы вход не
     собирается). ПОЛНАЯ разметка страницы + модалки
     shared/LoginModal.vue / shared/RegisterModal.vue + wiring
     js/landing.js 1:1 — задача 3.2 (лендинг — последняя задача партии).
     Держать синхронной со статической разметкой входа vue/index.html
     (носитель LOGIN_MODAL_TEXTS). -->
<template>
  <div></div>
</template>

<script>
// Wiring (модалки BUG-055/056, consent FR-78, сабмиты, route-маппинг
// §15.5, заглушки ai-open/quick/to-teachers) — задача 3.2.
export default { name: 'LandingApp' };
</script>
