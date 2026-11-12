<!-- Лендинг инструкторов /instructors (Спринт 14, change
     add-vue-s14-instructor-loop, задача 3.1): полный перенос 1:1 из legacy
     frontend/instructors.html (тексты/разметка/стили дословно — styles.css;
     без редизайна): шапка (бренд с .brand em «Сбер», nav-якоря
     #format/#benefits/#start, «Войти» header-cta data-open-login href="/",
     «Стать инструктором ↗»), hero «Учи водить. Меняй подход.», секции
     «Два формата подключения» (choice own/sber), «Работа в новом формате»,
     нижний CTA #open-form, футер; фоновые градиенты и медиазапросы 850/560.
     Модалка входа — shared/LoginModal.vue variant="instructors" (разметка
     варианта из legacy instructors.html дословно — последний дубль
     m-login умер в этой партии). Держать синхронной со статической
     разметкой входа vue/instructors.html.
     Поведение — wiring legacy js/instructors.js 1:1 (плоский JS,
     onMounted): #open-form → location.href='/instructors/apply';
     data-open-login → открытие #m-login локально (body overflow hidden,
     фокус #login-email) БЕЗ sessionStorage-флагов (BUG-055); закрытие —
     #login-close/[data-close]/Esc, клик по фону НЕ закрывает (BUG-056);
     сабмит — shared/loginWiring.js (route/reason §15.5 дословно).
     Ошибка — эквивалент err.textContent=: текст сервера в #login-error
     из реактивного состояния (проп error, интерполяция {{ }}).
     Id/класс-якоря e2e дословно (.header-cta[data-open-login],
     .header-cta[href="/instructors/apply"], .choice[data-type],
     #open-form, .brand em, #m-login/.overlay.open, #login-close,
     #login-* — TC-UI-003/010/052). -->
<template>
<header class="wrap"><a class="brand" href="#"><span class="check">✓</span><span><em style="font-style:normal;color:var(--green)">Сбер</em>Автошкола<small>Платформа для инструкторов</small></span></a><nav class="nav"><a href="#format">Форматы работы</a><a href="#benefits">Возможности</a><a href="#start">Как подключиться</a></nav><span style="display:flex;gap:10px;margin-left:auto"><a class="header-cta" style="background:#35d879;color:#062113;border-color:#35d879" href="/" data-open-login>Войти</a><a class="header-cta" href="/instructors/apply">Стать инструктором ↗</a></span></header>
<main><section class="hero"><div class="wrap hero-grid"><div><div class="eyebrow"><span class="dot"></span> Новая система обучения вождению</div><h1>Учи водить.<br><span>Меняй подход.</span></h1><p class="lead">Подключайся к СберАвтошколе, работай с учениками и управляй занятиями в удобном цифровом формате. Выбирай, на каком автомобиле работать.</p><div class="actions"><a class="btn primary" href="/instructors/apply">Выбрать формат работы ↗</a><a class="btn ghost" href="#benefits">Как всё устроено ↓</a></div><div class="subnote">Понятный процесс подключения · Цифровые инструменты · Прозрачные условия</div></div>
<div class="visual"><div class="orbit"></div><!-- Спринт 7 (design.md, правка Заказчика): декоративный блок «Ваш следующий маршрут» (svg.route + .pin + .pin-label) убран с главной инструктора --><div class="glass profile"><div class="minihead">Профиль инструктора</div><div class="profile-row"><div class="avatar">♙</div><div><div class="profile-name">Ваш профиль</div><div class="profile-sub">Инструктор категории B</div></div></div><div class="pill">● Профиль в работе</div></div><div class="glass car"><span class="status">Подключение</span><div class="avatar">⌑</div><div class="car-title">Автомобиль</div><div class="car-desc">Свой или предоставленный платформой</div><div class="line"></div><div class="metric"><span>Занятия</span><b>В одном месте</b></div><div class="metric"><span>Расписание</span><b>Под контролем</b></div></div><div class="glass schedule"><div class="sched-title">Ваше расписание <span>● Онлайн</span></div><div class="slots"><div class="slot">10:00</div><div class="slot active">12:00</div><div class="slot">14:00</div><div class="slot">16:00</div></div><div class="metric"><span>Управление занятиями</span><b>↗</b></div></div></div></div></section>
<section class="section wrap" id="format"><div class="section-head"><div><div class="kicker">Два формата подключения</div><h2>Выбирай, как тебе удобнее работать</h2></div><p>Один сервис — два пути. Выбери подходящий вариант, чтобы узнать условия и оставить заявку.</p></div><div class="choice-grid"><a href="/instructors/apply" class="choice" data-type="own"><div class="choice-top"><div class="choice-icon">🚘</div><span class="tag">Со своим автомобилем</span></div><h3>У меня есть свой автомобиль</h3><p>Подключи подходящий автомобиль, пройди проверку документов и начни работать с учениками через платформу.</p><div class="choice-bottom"><span>Узнать условия и подать заявку</span><span class="arrow">↗</span></div></a><a href="/instructors/apply" class="choice" data-type="sber"><div class="choice-top"><div class="choice-icon">🚗</div><span class="tag">На автомобиле Сбера</span></div><h3>Хочу работать на автомобиле Сбера</h3><p>Узнай о возможности работать на автомобиле, предоставленном СберАвтошколой или партнёром.</p><div class="choice-bottom"><span>Узнать условия и подать заявку</span><span class="arrow">↗</span></div></a></div></section>
<section class="section wrap" id="benefits"><div class="section-head"><div><div class="kicker">Работа в новом формате</div><h2>Больше, чем расписание</h2></div><p>Цифровые инструменты помогают сосредоточиться на главном — качественном обучении вождению.</p></div><div class="features"><article class="feature"><div class="feature-icon">♧</div><h3>Поток учеников</h3><p>Работа с заявками и учениками в рамках согласованной модели сотрудничества.</p></article><article class="feature"><div class="feature-icon">▦</div><h3>Гибкое расписание</h3><p>Планируй доступное время, смотри занятия и управляй изменениями в одном интерфейсе.</p></article><article class="feature"><div class="feature-icon">⌁</div><h3>Прогресс обучения</h3><p>История занятий и цифровые инструменты, которые помогают видеть динамику ученика.</p></article></div></section>
<section class="section wrap" id="start"><div class="bottom-cta"><div><h2>Готов подключиться?</h2><p>Оставь заявку — обсудим подходящий формат и условия сотрудничества.</p></div><button class="btn primary" id="open-form">Стать инструктором ↗</button></div></section></main><footer><div class="wrap footer-row"><span>© СберАвтошкола · Концепт лендинга для инструкторов</span><span>Условия подключения уточняются при рассмотрении заявки</span></div></footer>
<LoginModal variant="instructors" :error="loginError" />
</template>

<script>
// Wiring js/instructors.js 1:1 (плоский JS, onMounted). Сабмит входа —
// консолидированный композабл shared/loginWiring.js (useLoginWiring:
// postJSON('/api/auth/login', setToken, route-маппинг §15.5,
// instructor_rejected_reason ДО редиректа) — фрагменты переезжают
// дословно, задача 3.1).
import { onMounted } from 'vue';
import { useLoginWiring } from '../../shared/loginWiring.js';
import LoginModal from '../../shared/LoginModal.vue';

export default {
  name: 'InstructorsApp',
  components: { LoginModal: LoginModal },
  setup: function () {
    var wiring = useLoginWiring();
    var loginError = wiring.loginError;

    onMounted(function(){
      document.getElementById('open-form').addEventListener('click',function(){location.href='/instructors/apply'});
      // BUG-055 (decisions/2026-11-04-ui-followup.md, п.2): «Войти»
      // (data-open-login) открывает модалку входа ЛОКАЛЬНО — на странице,
      // откуда нажали, — БЕЗ редиректа на / и БЕЗ sessionStorage-флагов
      // open_login/open_login_from.
      document.querySelectorAll('[data-open-login]').forEach(function(b){
        b.addEventListener('click',function(e){e.preventDefault();openLogin();});
      });
      var overlay=document.getElementById('m-login');
      function openLogin(){
        overlay.classList.add('open');
        document.body.style.overflow='hidden';
        var em=document.getElementById('login-email');if(em)em.focus();
      }
      // BUG-056 (п.3/4): закрытие — крестик #login-close (вне карточки),
      // «Отмена», Esc. На этой странице закрытие просто убирает модалку
      // (страница не менялась). Клик по фону (вне карточки) окно НЕ
      // закрывает — обработчика e.target===overlay здесь НЕТ.
      function closeLogin(){
        overlay.classList.remove('open');
        document.body.style.overflow='';
      }
      document.getElementById('login-close').addEventListener('click',closeLogin);
      overlay.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',closeLogin);});
      document.addEventListener('keydown',function(e){
        if(e.key==='Escape'&&overlay.classList.contains('open'))closeLogin();
      });
      // Вход: POST /api/auth/login → route (§15.5) — композабл
      // loginWiring.js (маршруты: cabinet → /instructor/dashboard,
      // pending → /instructors/pending, rejected → /instructors/rejected
      // с причиной, student → /cabinet; роутинг по РОЛИ из ответа,
      // не по open_login_from — BUG-055).
      document.getElementById('login-submit').addEventListener('click',wiring.doLogin);
    });

    return {
      loginError: loginError,
    };
  },
};
</script>
