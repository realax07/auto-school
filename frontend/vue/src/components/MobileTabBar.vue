<!-- МОБИЛЬНЫЙ ТАБ-БАР (Спринт 18, change add-mobile-adaptive, задача 18.1.1;
     мокапы design/mocks/mobile/*.html v3 — источник дизайна, согласованы
     Заказчиком 2026-11-17 «Давай реализуем»). Фиксированный таб-бар снизу
     с пятью разделами (Главная, Записи, Обучение, Кошелек, Профиль) —
     SVG-иконки дословно из мокапов (mobile-home.html строка 109), подписи;
     высота 54px ≤ 64px (спека mobile-adaptive). Показ — ТОЛЬКО на мобильных
     ширинах: matchMedia('(max-width:760px)') (требование задачи — показ при
     matchMedia) + CSS-страховка @media(min-width:761px){display:none} —
     desktop (>760px) не меняется (носители e2e 84 защищают).

     Активный таб — по props.activeTab (канонические имена разделов кабинета,
     те же, что у StudentSidebar) и/или location-производной:
     «Мои заявки»/«Мои брони» → «Записи», «Знаки»/«Правила»/«Билеты»/
     «Штрафы» → «Обучение», «Кошелек» → «Кошелек», «Главная»/пусто/
     «Выбрать инструктора» → «Главная» (мокап mobile-choice.html: активен
     домик; мокап mobile-bookings.html: активна «Записи»).

     Навигация (паттерн StudentSidebar.go — самодостаточность wiring):
     в кабинете (/cabinet) — emit('tab', каноническое имя) — раздел
     переключает App.vue (SPA-механика и хеши без изменений); вне кабинета —
     переход на /cabinet#<канонический хеш> (роутятся App.vue кабинета при
     загрузке, BUG-047-паттерн). «Выбрать инструктора» и «Мои заявки» в
     таб-баре не дублируются (5 разделов по спеке) — доступны с «Главной»
     (плитки «Найти водителя»/«Мои заявки»).

     «Обучение» — bottom-sheet-выбор из 4 разделов ПДД (Знаки/Правила/
     Билеты/Штрафы): все разделы С17 остаются доступными с одной кнопки
     (сохранение действий desktop-версии). «Профиль» — bottom-sheet с
     ФИО и «Выйти» (спека mobile-adaptive: ФИО и «Выйти» доступны через
     раздел «Профиль» и top-bar (инициалы) — MAJ-1 итер.003/004: fixed
     полоса сверху, бренд + аватар-инициалы из /me при mount, MIN-7:
     загрузка ФИО только на мобильных ширинах; клик по аватару — Профиль-шит).

     Sheets — bottom-sheet с grab-хендлом и блюром фона (язык мокапов
     .shb/.grab — mobile-login/mobile-book-slot/mobile-dispute; тот же
     язык, что у модалок кабинета).

     Wiring учетки — самодостаточность (данные Hermes ядру не нужны):
     ФИО — GET /api/auth/me при mount (для top-bar-инициалов и Профиля),
     кеш meLoaded; 401/403/!ok → toLogin (FR-7). «Выйти» — POST
     /api/auth/logout → очистка сессии →
     редирект на главную (FR-8, design поток 3). -->
<template>
<div class="mtab-root">
<div v-if="visible" class="mtop" data-test="mtop">
  <div class="mtop-brand"><em>Сбер</em>Автошкола</div>
  <button type="button" class="mtop-ava" data-test="mtop-ava" aria-label="Профиль" @click="openProfile">{{ initials }}</button>
</div>
<nav v-if="visible" class="mtabs" aria-label="Мобильная навигация">
  <!-- 5 разделов спеки mobile-adaptive; SVG-иконки — дословно из мокапов -->
  <button type="button" class="mtab" :class="{ on: active === 'Главная' }" @click="openTab('Главная')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/></svg>
    <span>Главная</span>
  </button>
  <button type="button" class="mtab" :class="{ on: active === 'Записи' }" @click="openTab('Мои брони')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>
    <span>Записи</span>
  </button>
  <button type="button" class="mtab" :class="{ on: active === 'Обучение' }" @click="sheet = 'edu'">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M20 18v3H6.5"/></svg>
    <span>Обучение</span>
  </button>
  <button type="button" class="mtab" :class="{ on: active === 'Кошелек' }" @click="openTab('Кошелек')">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="14" rx="3"/><path d="M3 10h18M16 15h2"/></svg>
    <span>Кошелек</span>
  </button>
  <button type="button" class="mtab" :class="{ on: active === 'Профиль' }" @click="openProfile">
    <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>
    <span>Профиль</span>
  </button>
</nav>

<!-- bottom-sheet: выбор раздела ПДД (спека: разделы ПДД сохраняют всю
     функциональность С17 — доступ с таб-бара сохраняет навигацию) -->
<div v-if="sheet" class="mtab-backdrop" @click.self="closeSheet">
  <div class="mtab-sheet" role="dialog" aria-modal="true" :aria-label="sheet === 'edu' ? 'Обучение — разделы ПДД' : 'Профиль'">
    <div class="grab"></div>
    <template v-if="sheet === 'edu'">
      <div class="sh-t"><b>Обучение · ПДД</b><button class="x" type="button" aria-label="Закрыть" @click="closeSheet">×</button></div>
      <button v-for="s in EDU" :key="s.tab" type="button" class="mi" @click="pickEdu(s.tab)">
        <span class="mi-ico">{{ s.ico }}</span>
        <span class="mi-body"><b>{{ s.tab }}</b><small>{{ s.sub }}</small></span>
        <span class="mi-go">→</span>
      </button>
    </template>
    <template v-else>
      <div class="sh-t"><b>Профиль</b><button class="x" type="button" aria-label="Закрыть" @click="closeSheet">×</button></div>
      <div class="me">
        <span class="mav">{{ initials }}</span>
        <span class="mi-body"><b>{{ uname }}</b><small>кабинет ученика</small></span>
      </div>
      <button class="mi out" type="button" @click="logout"><span class="mi-ico">⎋</span><span class="mi-body"><b>Выйти</b><small>завершить сессию на этом устройстве</small></span></button>
    </template>
  </div>
</div>
</div>
</template>

<script>
// Общий клиент сессии — vue/src/shared/api.js (чанк shared, ADR-008;
// тот же набор, что у StudentSidebar): api/getToken/clearSession/toLogin;
// fioOf — из shared/utils.js (FR-5).
import { ref, computed } from 'vue';
import { api, getToken, clearSession, toLogin } from '../shared/api.js';
import { fioOf } from '../shared/utils.js';

export default {
  name: 'MobileTabBar',
  props: {
    // Активный раздел кабинета (канонические имена StudentSidebar: «Главная»,
    // «Мои заявки», «Мои брони», «Кошелек», «Знаки»…; «Выбрать инструктора»
    // на одноименной странице). Пусто → «Главная».
    activeTab: { type: String, default: '' },
  },
  emits: ['tab'],
  setup: function (props, ctx) {
    // --- показ только на мобильных ширинах (задача 18.1.1: matchMedia) ---
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

    // --- активный таб: каноническое имя раздела → один из 5 табов ---
    // Мокапы v3: bookings — «Записи», pdd-* — «Обучение», wallet —
    // «Кошелек», choice/home — «Главная» (проверено по class="tab on").
    function activeTabName() {
      var name = props.activeTab;
      if (name === 'Мои заявки' || name === 'Мои брони') return 'Записи';
      if (name === 'Знаки' || name === 'Правила' || name === 'Билеты' || name === 'Штрафы') return 'Обучение';
      if (name === 'Кошелек') return 'Кошелек';
      return 'Главная';
    }
    var active = computed(activeTabName);

    // --- навигация (паттерн StudentSidebar.go): в кабинете — SPA-emit,
    //     вне — переход по каноническому хешу раздела ---
    var TAB_HASH = {
      'Главная': '',
      'Мои заявки': '#/my-requests',
      'Мои брони': '#/my-bookings',
      'Кошелек': '#/wallet',
      'Знаки': '#/pdd-signs',
      'Правила': '#/pdd-rules',
      'Билеты': '#/pdd-tickets',
      'Штрафы': '#/pdd-fines',
    };
    function page() {
      return location.pathname.replace(/\/+$/, '') || '/';
    }
    function openTab(name) {
      if (page() === '/cabinet') { ctx.emit('tab', name); return; }
      location.href = '/cabinet' + (TAB_HASH[name] || '');
    }

    // --- «Обучение»: bottom-sheet с 4 разделами ПДД (все остаются
    //     доступны — сохранение действий desktop-версии) ---
    var EDU = [
      { tab: 'Знаки', ico: '◈', sub: '8 групп · 321 знак с описаниями' },
      { tab: 'Правила', ico: '☰', sub: '26 глав действующей редакции' },
      { tab: 'Билеты', ico: '◉', sub: '80 билетов — тренажер экзамена' },
      { tab: 'Штрафы', ico: '⚠', sub: 'Глава 12 КоАП · статьи и наказания' },
    ];
    var sheet = ref(null); // null | 'edu' | 'profile'
    function closeSheet() { sheet.value = null; }
    function pickEdu(name) {
      closeSheet();
      openTab(name);
    }

    // --- «Профиль»: ФИО + «Выйти» (спека mobile-adaptive) ---
    var uname = ref('');
    var meLoaded = ref(false);
    // ФИО — грузится при mount для top-bar (MIN-7: только при visible);
    // openProfile переиспользует кеш
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
    function openProfile() {
      sheet.value = 'profile';
      loadMe();
    }
    // MAJ-1 итер.003 + MIN-7 итер.004: инициалы в top-bar; грузим только
    // на мобильных ширинах (visible) — desktop не делает лишний /me
    if (visible.value) loadMe();
    var initials = computed(function () {
      return (uname.value || '').split(' ').slice(0, 2).map(function (w) { return (w[0] || '').toUpperCase(); }).join('');
    });
    // «Выйти» (FR-8) — дословно паттерн StudentSidebar.logout:
    // POST /api/auth/logout → очистка сессии → редирект на главную.
    function logout() {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'X-Session-Token': getToken() || '' },
      })
        .catch(function () {})
        .then(function () {
          clearSession();
          location.href = '/';
        });
    }

    return {
      visible: visible, active: active,
      // BUG-068: openTab отсутствовал в возвращаемых bindings setup — клики
      // по табам падали TypeError в рантайме (носитель e2e TC-UI-077 ловит)
      openTab: openTab,
      EDU: EDU, sheet: sheet, closeSheet: closeSheet, pickEdu: pickEdu,
      uname: uname, initials: initials, openProfile: openProfile, logout: logout,
    };
  },
};
</script>

<style scoped>
/* Компактный таб-бар (мокап mobile-home.html .tabs/.tab, высота 54px ≤64px
   спеки; палитра — дизайн-система кабинета: #55ed9c/#020b13-семейство). */
.mtop{position:fixed;top:0;left:0;right:0;z-index:55;display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(6,14,20,.96);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-bottom:1px solid rgba(148,163,164,.12)}
.mtop-brand{font-size:14px;font-weight:700}.mtop-brand em{font-style:normal;color:#34d399}
.mtop-ava{width:32px;height:32px;border-radius:50%;background:#123524;color:#34d399;display:grid;place-items:center;font-size:11px;font-weight:700;border:1px solid rgba(52,211,153,.35);cursor:pointer;padding:0}
.mtabs{position:fixed;left:0;right:0;bottom:0;z-index:60;height:54px;display:flex;background:rgba(6,14,20,.96);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-top:1px solid rgba(148,163,164,.14);padding:0 4px}
.mtab{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;background:none;border:0;color:#6b7f8a;font-size:9px;font-weight:600;padding:6px 0 5px}
.mtab svg{opacity:.85;flex:none}
.mtab.on{color:#55ed9c}
.mtab.on svg{filter:drop-shadow(0 0 6px rgba(85,237,156,.45))}
/* CSS-страховка показа только ≤760px (дубль matchMedia): desktop (>760px)
   не меняется — носители e2e 84 защищают */
@media(min-width:761px){.mtabs{display:none!important}}
/* BUG-070 (18.4): корневой div компонента (класс .mtab-root) Vue
   монтирует ПРЯМО в .app кабинета (grid 236px+1fr, без host-элемента) —
   на desktop пустой div занимал ячейку row1-col2, сдвигая .hero в
   row2-col1: контент сжимался до ширины сайдбара (236px, .zn-grid — одна
   колонка). Поймала e2e TC-UI-079 (геометрия сетки знаков). Страховка:
   корневой div >760px ячейку не генерирует; ≤760px не задет (внутри
   fixed .mtabs — сам бар fixed, высота корня — grid-stretch
   min-height:100vh, не характеристика бара). */
@media(min-width:761px){.mtab-root{display:none!important}}
/* bottom-sheet с grab-хендлом и блюром (язык мокапов .shb/.grab) */
.mtab-backdrop{position:fixed;inset:0;z-index:80;background:rgba(3,7,11,.6);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);display:flex;align-items:flex-end}
.mtab-sheet{width:100%;max-height:80vh;overflow:auto;background:#0d161e;border:1px solid rgba(148,163,164,.16);border-bottom:0;border-radius:18px 18px 0 0;padding:10px 18px 26px}
.grab{width:38px;height:4px;border-radius:4px;background:#2d3d49;margin:6px auto 12px}
.sh-t{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.sh-t b{font-size:16px;font-weight:650;letter-spacing:-.02em;color:#f3f7f8}
.x{width:28px;height:28px;border-radius:50%;background:#1a2631;color:#94a3b8;display:grid;place-items:center;font-size:13px;border:0}
/* пункты шита — карточки в стиле кабинета */
.mi{display:flex;align-items:center;gap:12px;width:100%;text-align:left;padding:13px 14px;margin:0 0 9px;border:1px solid rgba(234,255,249,.14);border-radius:14px;background:linear-gradient(150deg,rgba(28,43,52,.78),rgba(15,25,32,.8));color:#dcebe9}
.mi:last-child{margin-bottom:0}
.mi b{font-size:14px;font-weight:600;display:block;letter-spacing:-.01em}
.mi small{display:block;font-size:11px;color:#8fa0aa;margin-top:3px}
.mi-body{flex:1;min-width:0}
.mi-ico{width:38px;height:38px;flex:none;display:grid;place-items:center;border-radius:11px;background:linear-gradient(145deg,#2c4f3d,#132119);color:#a0f2bd;font-size:16px}
.mi-go{color:#55ed9c;font-weight:200;font-size:18px}
.mi.out .mi-ico{background:linear-gradient(145deg,#4a2c24,#241412);color:#ffb28e}
.me{display:flex;align-items:center;gap:13px;padding:14px;margin:0 0 10px;border:1px solid rgba(234,255,249,.16);border-radius:16px;background:linear-gradient(150deg,rgba(28,43,52,.78),rgba(15,25,32,.8))}
.me b{font-size:15px;font-weight:600;display:block;letter-spacing:-.01em}
.me small{display:block;font-size:11px;color:#8fa0aa;margin-top:3px}
.mav{width:44px;height:44px;flex:none;border-radius:13px;background:linear-gradient(145deg,#2c4f3d,#132119);display:grid;place-items:center;color:#a0f2bd;font-size:12px;font-weight:700}
.me .mi-body{flex:1}
</style>
