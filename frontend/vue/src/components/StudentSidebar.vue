<!-- ЕДИНЫЙ САЙДБАР УЧЕНИКА (замечание Заказчика 2026-11-16): физически ОДИН
     элемент для всех ученических страниц — правая часть страницы
     подгружается отдельно, сайдбар всегда один и тот же. Потребители:
     cabinet/App.vue (SPA-табы) и instructor-choice/App.vue (активный
     «Выбрать инструктора»). До этого разметка сайдбара дублировалась
     в каждом носителе (cabinet.html/App.vue, instructor-choice.html/App.vue)
     — на страницах вне «активного» переноса терялись ФИО и «Выйти»
     внизу слева (BUG-065).

     Состав (канонический список ученика, Замечание 2026-11-15 №1):
     логотип (side-brand) → навигация (snav: Главная/Мои заявки/Выбрать
     инструктора/Мои брони/Кошелек/Знаки/Правила/Билеты/Штрафы) → учётка
     внизу слева (side-user: uname ФИО + «Выйти», замечание №4).

     Самодостаточность wiring (независимо от страницы):
     - ФИО — компонент тянет САМ: GET /api/auth/me с X-Session-Token из
       sessionStorage (FR-5); 401/403/!ok → toLogin() (FR-7). Пользователь
       уходит наружу событием @me (кабинет обновляет greet по user.name);
     - «Выйти» — POST /api/auth/logout → очистка сессии → редирект на
       главную (FR-8; редирект после любого ответа — design поток 3);
     - навигация: таб-пункты на /cabinet — emit('tab', имя) (SPA-разделы
       кабинета, хеш роутит App.vue); вне кабинета — переход на
       /cabinet#<хеш раздела> (хеши роутятся App.vue при загрузке);
       «Выбрать инструктора» — переход на /instructor-choice (data-goto,
       BUG-047-прецедент: отдельная целевая страница).

     Активный пункт — по props activeTab (НАДЕЖНЕЕ location-производной:
     кабинет переключает разделы через history.replaceState, который НЕ
     fireEvent hashchange — location-состояние протухало бы внутри SPA;
     страница знает активный таб достоверно и передает проп). Fallback —
     location.pathname+hash для страниц без пропа (инвариант не теряется).

     Стили — классы side/side-brand/snav/side-user 1:1 из
     src/pages/cabinet/styles.css (канон кабинета), СКОПИРОВАНЫ в scoped
     (CSS вне JS-бюджета NFR-26): компонент самодостаточен и выглядит
     одинаково на любой странице, независимо от page-CSS носителя.
     Копии базовых .check/.uname/.logout — из styles.css кабинета
     (строки мокапа в page-CSS остаются — design-guard test_cabinet_page;
     scoped-копия выравнивает вид сайдбара на всех страницах). -->
<template>
<aside class="side">
  <div class="side-brand"><span class="check">✓</span><div><em>Сбер</em>Автошкола<small>Кабинет ученика</small></div></div>
  <!-- Канонический список ученика: 8 data-tab + data-goto «Выбрать
       инструктора» (единый состав и порядок на всех страницах).
       Активный пункт — :class по isActive (см. шапку). -->
  <nav class="snav">
    <button type="button" :class="{ on: isActive('Главная') }" data-tab="Главная" @click="go('Главная')"><span class="ico">⌂</span>Главная</button>
    <button type="button" :class="{ on: isActive('Мои заявки') }" data-tab="Мои заявки" @click="go('Мои заявки')"><span class="ico">✉</span>Мои заявки</button>
    <button type="button" :class="{ on: isActive('Выбрать инструктора') }" data-goto="/instructor-choice" @click="gotoChoice"><span class="ico">▤</span>Выбрать инструктора</button>
    <button type="button" :class="{ on: isActive('Мои брони') }" data-tab="Мои брони" @click="go('Мои брони')"><span class="ico">◷</span>Мои брони</button>
    <button type="button" :class="{ on: isActive('Кошелек') }" data-tab="Кошелек" @click="go('Кошелек')"><span class="ico">₽</span>Кошелек</button>
    <button type="button" :class="{ on: isActive('Знаки') }" data-tab="Знаки" @click="go('Знаки')"><span class="ico">◈</span>Знаки</button>
    <button type="button" :class="{ on: isActive('Правила') }" data-tab="Правила" @click="go('Правила')"><span class="ico">☰</span>Правила</button>
    <button type="button" :class="{ on: isActive('Билеты') }" data-tab="Билеты" @click="go('Билеты')"><span class="ico">◉</span>Билеты</button>
    <button type="button" :class="{ on: isActive('Штрафы') }" data-tab="Штрафы" @click="go('Штрафы')"><span class="ico">⚠</span>Штрафы</button>
  </nav>
  <!-- учётка внизу слева (замечание Заказчика №4); ФИО — из /api/auth/me -->
  <div class="side-user"><span class="uname">{{ uname }}</span><button class="logout" type="button" @click="logout">Выйти</button></div>
</aside>
</template>

<script>
// Общий клиент сессии — vue/src/shared/api.js (чанк shared, ADR-008):
// getToken/clearSession/toLogin — единый паттерн кабинетов; fioOf —
// из shared/utils.js (FR-5, дословный перенос js/shared/utils.js).
import { ref } from 'vue';
import { api, getToken, clearSession, toLogin } from '../../shared/api.js';
import { fioOf } from '../../shared/utils.js';

export default {
  name: 'StudentSidebar',
  props: {
    // Активный пункт (каноническое имя: «Главная», «Мои заявки», …,
    // «Выбрать инструктора»). Пусто → fallback по location.pathname+hash.
    activeTab: { type: String, default: '' },
  },
  emits: ['tab', 'me'],
  setup: function (props, ctx) {
    var uname = ref('Иван Иванов');

    // Канонические хеши разделов кабинета (роутятся App.vue при загрузке;
    // BUG-047-паттерн: reload/старые ссылки открывают раздел напрямую).
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

    // Активный пункт: props.activeTab — авторитетный источник (replaceState
    // кабинета не fireEvent hashchange — location-производная протухала бы);
    // без пропа — reliable fallback по pathname+hash.
    function isActive(name) {
      if (props.activeTab) return name === props.activeTab;
      if (name === 'Выбрать инструктора') return page() === '/instructor-choice';
      return page() === '/cabinet' && (location.hash || '') === (TAB_HASH[name] || '');
    }

    // Таб-пункт: в кабинете — SPA (emit наверх, раздел переключает App.vue);
    // вне кабинета — вход в кабинет сразу на разделе (по каноническому хешу).
    function go(name) {
      if (page() === '/cabinet') { ctx.emit('tab', name); return; }
      location.href = '/cabinet' + (TAB_HASH[name] || '');
    }

    // «Выбрать инструктора» — отдельная целевая страница (BUG-047-прецедент);
    // повторный клик по активному пункту страницу не перезагружает.
    function gotoChoice() {
      if (page() !== '/instructor-choice') location.href = '/instructor-choice';
    }

    // «Выйти» (FR-8): POST /api/auth/logout → очистка sessionStorage →
    // редирект на главную, к модалке входа (после любого ответа — design поток 3).
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

    // ФИО ученика (FR-5) — компонент тянет САМ, независимо от страницы:
    // нет токена / 401/403/!ok → toLogin (FR-7, редирект к модалке входа).
    // user уходит наружу (@me) — кабинету для greet «Добро пожаловать, {name}!».
    if (!getToken()) {
      toLogin();
    } else {
      api('/api/auth/me', {}, function (res) {
        if (res.status === 401 || res.status === 403 || !res.data || !res.data.ok) { toLogin(); return; }
        var u = res.data.user || {};
        var fio = fioOf(u);
        if (fio) uname.value = fio;
        ctx.emit('me', u);
      });
    }

    return {
      uname: uname,
      isActive: isActive,
      go: go,
      gotoChoice: gotoChoice,
      logout: logout,
    };
  },
};
</script>

<style scoped>
/* 1:1 из src/pages/cabinet/styles.css (канон кабинета; строки мокапа в
   page-CSS носителей не трогаются — design-guard test_cabinet_page). */
.side{padding:25px 17px;border-right:1px solid rgba(234,255,249,.12);background:rgba(4,16,24,.72);display:flex;flex-direction:column;gap:26px}
.side-brand{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;letter-spacing:-.04em;padding:0 8px}
.side-brand em{font-style:normal;color:#55ed9c}
.side-brand small{display:block;font-size:9px;color:#7d939a;letter-spacing:.12em;text-transform:uppercase;margin-top:3px}
/* логотип: .check — база из styles.css кабинета (строка 12), выравнивает
   галочку логотипа на всех страницах (у instructor-choice была 32px) */
.check{width:36px;height:36px;display:grid;place-items:center;border:4px solid #49ec9a;border-radius:50%;color:#58efa3;font-size:24px;font-weight:500;transform:rotate(-8deg)}
.snav{display:grid;gap:5px}
.snav button{border:1px solid transparent;background:transparent;color:#aab8c0;text-align:left;padding:12px;border-radius:12px;font-size:13px;display:flex;align-items:center;gap:12px}
.snav button .ico{width:20px;text-align:center;font-size:16px}
.snav button.on{color:#8ff2b5;background:#143023;border-color:#286445}
.snav button:hover{background:rgba(255,255,255,.05)}
/* UX-переполнение сайдбара (9 пунктов, design «Решение 3»): на низких
   окнах список пунктов прокручивается, ни один не становится недоступным */
.snav{overflow-y:auto}
/* учётка в сайдбаре (замечание Заказчика №4: нижний левый угол) */
.uname{font-size:14px;color:#dcebe9}
.side-user{margin-top:auto;display:flex;flex-direction:column;gap:10px;align-items:flex-start;font-size:14px;color:#dcebe9}
/* база .logout + hover — из styles.css кабинета (строки 16-17); одинаковый
   вид кнопки на всех страницах, поверх любых page-CSS носителей */
.logout{padding:9px 24px;border:1px solid rgba(238,249,249,.4);border-radius:999px;background:rgba(4,12,17,.28);font-size:14px}
.logout:hover{border-color:#49ec9a}
.side-user .logout{padding:7px 18px;font-size:12px}
/* мобильная вертикаль сайдбара — 1:1 из @media кабинета (строка 205);
   сетка страницы (.app) остается в page-CSS носителя */
@media(max-width:760px){.side{flex-direction:row;align-items:center;padding:10px 14px;border-right:0;border-bottom:1px solid rgba(234,255,249,.12)}.snav{display:flex;overflow:auto;gap:5px}.snav button{white-space:nowrap;padding:9px 10px;font-size:11px}.snav button .ico{display:none}}
</style>
