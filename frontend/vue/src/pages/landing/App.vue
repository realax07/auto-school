<!-- Лендинг «/» (Спринт 12, change add-vue-s12-landing-apply, задача 3.2 —
     ПОСЛЕДНЯЯ задача партии: вход в кабинеты идет через модалки лендинга).
     Разметка — перенос 1:1 из legacy frontend/index.html (тексты дословно,
     включая бренд «Сбер»; стили — styles.css, перенос дословный).
     Держать синхронной со статической разметкой входа vue/index.html
     (носитель LOGIN_MODAL_TEXTS). Модалки — shared/LoginModal.vue и
     shared/RegisterModal.vue. Поведение — wiring legacy js/landing.js 1:1
     (плоский JS, onMounted): открытие/закрытие модалок (data-open/
     data-close/Esc; фон НЕ закрывает #m-login — BUG-055/056; снятие
     open_login/open_login_from при закрытии); consent-гейт #reg-submit —
     в RegisterModal (:disabled от состояния чекбокса, FR-78); сабмиты
     через shared/api.js (postJSON/setToken): POST /api/register — 200 →
     setToken → /cabinet, ошибки — текст сервера в #reg-error; POST
     /api/auth/login — route-маппинг §15.5 дословно (порядок
     res.status===200&&res.data.ok ДО route-разбора): cabinet →
     /instructor/dashboard, pending → /instructors/pending, rejected →
     sessionStorage «instructor_rejected_reason» ДО редиректа
     /instructors/rejected (КОНТРАКТ POLLING/REJECTED НЕ СЛОМАН), прочее →
     /cabinet; ошибки — текст сервера в #login-error; сеть — «Ошибка
     сети». Заглушки спринта-0 (тексты alert дословно): ai-open, .quick
     button, to-teachers. Id/класс-якоря e2e дословно (.intro h1,
     .auth [data-open], #m-login/#m-register, #login-*, #reg-*, #ai-open,
     .quick button, #to-teachers, .brand em — TC-UI-001/002/043…045/053,
     TC-S9UI-003, TC-UI-005/059/060). -->
<template>
<main class="hero"><div class="road"></div><div class="frame">
<header>
  <div class="brand"><span class="check">✓</span><span><em>Сбер</em>Автошкола</span></div>
  <nav><a>О программе</a><a>Тарифы</a><a>Вопросы</a></nav>
  <div class="auth"><button class="login" data-open="register">Зарегистрироваться</button><button class="login solid" data-open="login">Войти</button></div>
</header>
<div class="hero-grid">
<section class="intro">
  <div class="eyebrow">СОВРЕМЕННАЯ АВТОШКОЛА ОТ СБЕРА</div>
  <h1>Права —<span>без лишнего пути.</span></h1>
  <p>Весь путь — от первого занятия<br>до экзамена — в одном месте.</p>
</section>
<div class="side">
<section class="steps">
  <div class="step s4">✓ <b>Права</b><small>04</small></div>
  <div class="step s3">▧ <b>Экзамен</b><small>03</small></div>
  <div class="step s2">◉ <b>Практика</b><small>02</small></div>
  <div class="step s1">◇ <b>Теория</b><small>01</small></div>
</section>
</div>
<section class="assistant">
  <div class="ai-head"><div class="avatar"></div><div><b>Гига ГАИшник</b><span>Твой AI-помощник в обучении и на дороге</span></div></div>
  <div class="prompt"><span>Спроси что угодно про обучение, экзамен или ПДД...</span><button class="send" id="ai-open" title="Открыть чат ассистента">↑</button></div>
  <div class="quick">
    <button>▢ <span>Хочу выучиться<br>на права</span></button>
    <button>☷ <span>Выбрать<br>тариф</span></button>
    <button>₽ <span>Сколько<br>это стоит?</span></button>
    <button>♧ <span>Готов ли я<br>к экзамену?</span></button>
    <button>▢ <span>Разобрать<br>нестандартную ситуацию</span></button>
  </div>
</section>
</div>
<footer>
  <div class="feature"><div class="feature-icon">⌁</div><div><b>AI-тренер<br>и Гига ГАИшник</b><p>Разбор ситуаций, тренировка<br>к экзамену, персональные советы</p></div></div>
  <div class="feature"><div class="feature-icon">▣</div><div><b>Проверенные<br>инструкторы</b><p>С рейтингами, отзывами<br>и прозрачным расписанием</p></div></div>
  <div class="feature"><div class="feature-icon">♢</div><div><b>Вся экосистема Сбера</b><p>Медсправка, страхование,<br>авто и сервисы — в одном месте</p></div></div>
  <div class="tagline">Больше, чем<br>автошкола.<br><b>Это — Сбер.</b><button class="arrow" style="background:none;border:0;padding:0;color:inherit;text-align:left" id="to-teachers" title="Лендинг для водителей-учителей">→</button></div>
</footer>
</div></main>
<LoginModal :error="loginError" />
<RegisterModal :error="regError" />
</template>

<script>
// Контракты вызовов — через общий клиент shared/api.js (postJSON/setToken,
// перенос js/api.js дословен). Wiring — плоский JS как в legacy
// js/landing.js (дословные фрагменты контракта: postJSON('/api/auth/login',
// postJSON('/api/register', setToken(res.data.token),
// location.href='/cabinet', route-маппинг §15.5, instructor_rejected_reason).
// Сообщения ошибок — эквивалент err.textContent=: текст сервера из
// реактивного состояния рендерится в #login-error/#reg-error (проп error
// shared-компонентов, интерполяция {{ }}).
import { onMounted, ref } from 'vue';
import { postJSON, setToken } from '../../shared/api.js';
import LoginModal from '../../shared/LoginModal.vue';
import RegisterModal from '../../shared/RegisterModal.vue';

export default {
  name: 'LandingApp',
  components: { LoginModal: LoginModal, RegisterModal: RegisterModal },
  setup: function () {
    var loginError = ref('');
    var regError = ref('');

    // --- Регистрация: POST /api/register (дизайн 2026-10-08). Кнопка
    // «Зарегистрироваться» (#reg-submit) недоступна (disabled) до
    // установки чекбокса согласия #reg-consent (FR-78 — гейт в
    // RegisterModal); required чекбокса — второй рубеж; consent — в
    // payload сабмита из состояния checked чекбокса. ---
    function doRegister(){
      regError.value='';
      var payload={
        surname:document.getElementById('reg-surname').value.trim(),
        name:document.getElementById('reg-name').value.trim(),
        patronymic:document.getElementById('reg-patronymic').value.trim(),
        email:document.getElementById('reg-email').value.trim(),
        phone:document.getElementById('reg-phone').value.trim(),
        password:document.getElementById('reg-password').value,
        password_confirm:document.getElementById('reg-password-confirm').value,
        consent:document.getElementById('reg-consent').checked
      };
      postJSON('/api/register',payload)
        .then(function(res){
          if(res.status===200&&res.data.ok&&res.data.token){
            try{setToken(res.data.token);}
            catch(e){regError.value='Не удалось сохранить сессию';return;}
            location.href='/cabinet';
          }
          else{regError.value=(res.data&&res.data.error)||'Ошибка регистрации';}
        })
        .catch(function(){regError.value='Ошибка сети';});
    }

    // --- Вход: POST /api/auth/login → route (§15.5): cabinet →
    // /instructor/dashboard, student-cabinet → /cabinet, pending →
    // /instructors/pending, rejected → sessionStorage
    // «instructor_rejected_reason» ДО редиректа /instructors/rejected
    // (контракт polling/rejected — экран С11 читает причину из него). ---
    function doLogin(){
      loginError.value='';
      var payload={
        email:document.getElementById('login-email').value.trim(),
        password:document.getElementById('login-password').value
      };
      postJSON('/api/auth/login',payload)
        .then(function(res){
          if(res.status===200&&res.data.ok){
            if(res.data.token){try{setToken(res.data.token);}catch(e){}}
            var route=res.data.route||'student-cabinet';
            if(route==='cabinet'){location.href='/instructor/dashboard';}
            else if(route==='pending'){location.href='/instructors/pending';}
            else if(route==='rejected'){try{sessionStorage.setItem('instructor_rejected_reason',res.data.reason||'');}catch(e){}location.href='/instructors/rejected';}
            else{location.href='/cabinet';}
          }
          else{loginError.value=(res.data&&res.data.error)||'Неверный email или пароль';}
        })
        .catch(function(){loginError.value='Ошибка сети';});
    }

    onMounted(function(){
      // --- открытие/закрытие модалок (как legacy js/landing.js) ---
      var open=function(id){document.getElementById(id).classList.add('open')};
      var closeAll=function(){document.querySelectorAll('.overlay').forEach(function(o){o.classList.remove('open')})};
      document.querySelectorAll('[data-open="login"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-login')})});
      document.querySelectorAll('[data-open="register"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-register')})});
      document.getElementById('to-register').addEventListener('click',function(){closeAll();open('m-register')});
      document.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',function(){
        closeAll();
        // BUG-056: закрытие (крестик #login-close / «Отмена») оставляет на
        // ТЕКУЩЕЙ странице; флаги старого редиректа-логина убираем (если
        // модалка открылась через них — просто остаёмся здесь)
        sessionStorage.removeItem('open_login');
        sessionStorage.removeItem('open_login_from');
      })});
      // BUG-056: клик по фону (вне карточки) НЕ закрывает модалку входа
      // (#m-login; закрытие — крестик/«Отмена»/Esc). Остальным модалкам клик
      // по фону оставлен как был.
      document.querySelectorAll('.overlay').forEach(function(o){o.addEventListener('click',function(e){if(e.target===o&&o.id!=='m-login')closeAll()})});
      document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll()});
      // --- сабмиты модалок ---
      document.getElementById('reg-submit').addEventListener('click',doRegister);
      document.getElementById('login-submit').addEventListener('click',doLogin);
      // --- ассистент и футер-переход — заглушки спринта-0 (тексты дословно) ---
      var stub=function(msg){return function(){alert(msg)}};
      document.getElementById('ai-open').addEventListener('click',stub('Заглушка: чат ассистента (Hermes) будет подключен позже'));
      document.querySelectorAll('.quick button').forEach(function(b){b.addEventListener('click',stub('Заглушка: сценарии ассистента будут подключены позже'))});
      document.getElementById('to-teachers').addEventListener('click',stub('Заглушка: лендинг для водителей-учителей — следующая страница'));
    });

    return {
      loginError: loginError,
      regError: regError,
    };
  },
};
</script>
