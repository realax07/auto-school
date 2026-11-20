<!-- МОБИЛЬНЫЙ ТАБ-БАР ИНСТРУКТОРА (change add-instructor-mobile, задача 20.0.1;
     мокапы design/mocks/mobile-instructor/mi-*.html — согласованы Заказчиком
     2026-11-18, PR#152). Паттерн 1:1 с MobileTabBar.vue (С18): fixed top-bar
     (бренд + инициалы из /me, MIN-7: только на мобильных ширинах), нижний
     таб-бар 54px, «Ещё» → bottom-sheet с остальными разделами и «Выход».
     Показ — ТОЛЬКО ≤760px (matchMedia + CSS-страховка); desktop (>760px)
     не меняется. Активный таб — по location.hash (navTo App.vue синхронизирует
     хеши BUG-047): без хеша → «День», #/bookings → «Неделя», #/earnings →
     «Кошелёк», #/my-cars, #/my-docs → «Ещё». Навигация — emit('tab', имя
     раздела) → navTo App.vue (SPA одной страницы /instructor/dashboard). -->
<template>
<div class="itab-root">
<div v-if="visible" class="itop" data-test="itop">
  <div class="itop-brand"><em>Сбер</em>Автошкола · инструктор</div>
  <button type="button" class="itop-ava" data-test="itop-ava" aria-label="Профиль" @click="go('Профиль и документы')">{{ initials }}</button>
</div>
<nav v-if="visible" class="itabs" aria-label="Мобильная навигация инструктора">
  <button type="button" class="itab" :class="{ on: active === 'День' }" @click="go('Мой день')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/></svg>
    <span>День</span>
  </button>
  <button type="button" class="itab" :class="{ on: active === 'Неделя' }" @click="go('Расписание')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>
    <span>Неделя</span>
  </button>
  <button type="button" class="itab" :class="{ on: active === 'Кошелёк' }" @click="go('Доходы и выплаты')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="13" rx="3"/><path d="M16 11h5v3h-5a1.5 1.5 0 0 1 0-3z"/></svg>
    <span>Кошелёк</span>
  </button>
  <button type="button" class="itab" :class="{ on: active === 'Профиль' }" @click="go('Профиль и документы')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.4"/><path d="M5 20c1.4-3.4 3.9-4.8 7-4.8s5.6 1.4 7 4.8"/></svg>
    <span>Профиль</span>
  </button>
  <button type="button" class="itab" :class="{ on: active === 'Ещё' }" @click="openMore">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></svg>
    <span>Ещё</span>
  </button>
</nav>
<div v-if="visible && sheet" class="isheet-w" data-test="isheet" @click.self="closeSheet">
  <div class="isheet">
    <div class="igrab"></div>
    <div class="ish-t"><b>Ещё разделы</b><button type="button" class="ix" @click="closeSheet">✕</button></div>
    <button type="button" class="irow" @click="go('Календарь')">▦ Календарь</button>
    <button type="button" class="irow" @click="go('Мои ученики')">♧ Мои ученики</button>
    <button type="button" class="irow" @click="go('Мои автомобили')">▰ Мои автомобили</button>
    <button type="button" class="irow" @click="go('Материалы и обучение')">◈ Материалы и обучение</button>
    <button type="button" class="irow out" @click="logout">⎋ Выйти</button>
  </div>
</div>
</div>
</template>
<script>
// Общий клиент сессии (ADR-008, чанк shared) — паттерн MobileTabBar С18.
import { ref, computed } from 'vue';
import { api, getToken, clearSession, toLogin } from '../shared/api.js';
import { fioOf } from '../shared/utils.js';

export default {
  name: 'InstructorTabBar',
  emits: ['tab'],
  setup: function (props, ctx) {
    var visible = ref(false);
    if (typeof window.matchMedia === 'function') {
      var mq = window.matchMedia('(max-width:760px)');
      visible.value = mq.matches;
      var onMq = function (e) {
        visible.value = e.matches;
        if (!e.matches) closeSheet();
        else loadMe(); // MIN-7: выход на мобильную ширину — инициалы догружаются
      };
      if (mq.addEventListener) mq.addEventListener('change', onMq);
      else if (mq.addListener) mq.addListener(onMq);
    }

    // Активный таб по location.hash (navTo App.vue синхронизирует хеш — BUG-047)
    function activeTabName() {
      var h = location.hash || '';
      if (h.indexOf('#/bookings') === 0) return 'Неделя';
      if (h.indexOf('#/earnings') === 0) return 'Кошелёк';
      return 'День';
    }
    var active = ref(activeTabName());
    var uname = ref('');
    var meLoaded = ref(false);
    function loadMe() {
      if (meLoaded.value) return;
      meLoaded.value = true;
      if (!getToken()) { toLogin(); return; }
      api('/api/auth/me', {}, function (res) {
        if (res.status === 401 || res.status === 403 || !res.data || !res.data.ok) { toLogin(); return; }
        var fio = fioOf(res.data.user || {});
        if (fio) uname.value = fio;
      });
    }
    if (visible.value) loadMe();
    var initials = computed(function () {
      return (uname.value || '').split(' ').slice(0, 2).map(function (w) { return (w[0] || '').toUpperCase(); }).join('');
    });

    var sheet = ref(false);
    function closeSheet() { sheet.value = false; }
    function openMore() { sheet.value = true; }
    function go(name) {
      closeSheet();
      active.value = name === 'Расписание' ? 'Неделя'
        : name === 'Доходы и выплаты' ? 'Кошелёк'
        : name === 'Профиль и документы' ? 'Профиль'
        : (name === 'Мой день') ? 'День' : 'Ещё';
      ctx.emit('tab', name);
    }
    // «Выйти» — дословный паттерн MobileTabBar.logout (FR-8)
    function logout() {
      fetch('/api/auth/logout', { method: 'POST', headers: { 'X-Session-Token': getToken() || '' } })
        .catch(function () {})
        .then(function () { clearSession(); location.href = '/'; });
    }

    return {
      visible: visible, active: active, initials: initials,
      sheet: sheet, closeSheet: closeSheet, openMore: openMore,
      go: go, logout: logout,
    };
  },
};
</script>
<style scoped>
.itop{position:fixed;top:0;left:0;right:0;z-index:55;display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(6,14,20,.96);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-bottom:1px solid rgba(148,163,164,.12)}
.itop-brand{font-size:13.5px;font-weight:700}.itop-brand em{font-style:normal;color:#34d399}
.itop-ava{width:32px;height:32px;border-radius:50%;background:#123524;color:#34d399;display:grid;place-items:center;font-size:11px;font-weight:700;border:1px solid rgba(52,211,153,.35);cursor:pointer;padding:0}
.itabs{position:fixed;left:0;right:0;bottom:0;z-index:60;height:54px;display:flex;background:rgba(6,14,20,.96);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-top:1px solid rgba(148,163,164,.14);padding:0 4px}
.itab{flex:1;min-width:0;min-height:44px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;background:none;border:0;color:#6b7f8a;font-size:9px;font-weight:600;padding:6px 0 5px;cursor:pointer}
.itab svg{opacity:.85;flex:none}
.itab.on{color:#55ed9c}
.itab.on svg{filter:drop-shadow(0 0 6px rgba(85,237,156,.45))}
.isheet-w{position:fixed;inset:0;z-index:80;background:rgba(3,7,11,.6);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);display:flex;align-items:flex-end}
.isheet{width:100%;max-width:390px;margin:0 auto;background:#0d151d;border-radius:18px 18px 0 0;padding:10px 18px 26px}
.igrab{width:38px;height:4px;border-radius:4px;background:#2d3d49;margin:6px auto 12px}
.ish-t{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.ish-t b{font-size:16px;font-weight:750}
.ix{width:28px;height:28px;border-radius:50%;background:#1a2631;color:#94a3b8;display:grid;place-items:center;font-size:13px;border:0;cursor:pointer}
.irow{display:flex;align-items:center;gap:10px;width:100%;min-height:44px;padding:11px 12px;border:0;border-radius:12px;background:none;color:#e9eff1;font-size:14px;cursor:pointer;text-align:left}
.irow:hover{background:#ffffff08}
.irow.out{color:#f87171}
/* CSS-страховка: показ только ≤760px (дубль matchMedia) */
@media(min-width:761px){.itab-root{display:none!important}}
</style>
