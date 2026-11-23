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
  <div class="m-cta"><button class="login solid" data-open="register">Зарегистрироваться</button><button class="login" data-open="login">Войти</button></div>
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
  <!-- Волна 21.3 (add-roles-theme-landing): блок интерактивен (синхронно
       с vue/index.html — правило двух копий). -->
  <div class="prompt"><input type="text" id="ai-input" placeholder="Спроси что угодно про обучение, экзамен или ПДД..." aria-label="Вопрос ГигаЧату"><button class="send" id="ai-open" title="Отправить вопрос">↑</button></div>
  <div class="quick">
    <button data-scenario="Хочу выучиться на права"><span>Хочу выучиться<br>на права</span></button>
    <button data-scenario="Как выбрать тариф обучения"><span>Выбрать<br>тариф</span></button>
    <button data-scenario="Сколько стоит обучение в автошколе"><span>Сколько<br>это стоит?</span></button>
    <button data-scenario="Готов ли я к экзамену в ГИБДД"><span>Готов ли я<br>к экзамену?</span></button>
    <button data-scenario="Разбор нестандартной дорожной ситуации"><span>Разобрать<br>нестандартную ситуацию</span></button>
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
import { useLoginWiring } from '../../shared/loginWiring.js';
import LoginModal from '../../shared/LoginModal.vue';
import RegisterModal from '../../shared/RegisterModal.vue';

export default {
  name: 'LandingApp',
  components: { LoginModal: LoginModal, RegisterModal: RegisterModal },
  setup: function () {
    // Спринт 14 (change add-vue-s14-instructor-loop, задача 3.1):
    // консолидация wiring входа — doLogin вынесен в композабл
    // shared/loginWiring.js ДОСЛОВНО (postJSON('/api/auth/login',
    // setToken, route-маппинг §15.5, instructor_rejected_reason ДО
    // редиректа — комментарии переехали с ним); второй живой потребитель —
    // лендинг инструкторов /instructors. Регистрация (doRegister) —
    // остается на лендинге (register-wiring не консолидируется).
    var loginWiring = useLoginWiring();
    var loginError = loginWiring.loginError;
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

    // --- Вход (§15.5): сабмит — консолидированный композабл
    // shared/loginWiring.js (route-маппинг §15.5 дословно: cabinet →
    // /instructor/dashboard, pending → /instructors/pending, rejected →
    // sessionStorage «instructor_rejected_reason» ДО редиректа
    // /instructors/rejected — контракт polling/rejected — экран С11 читает
    // причину из него, прочее → /cabinet). ---

    onMounted(function(){
      // --- открытие/закрытие модалок (как legacy js/landing.js) ---
      var open=function(id){document.getElementById(id).classList.add('open')};
      var closeAll=function(){document.querySelectorAll('.overlay').forEach(function(o){o.classList.remove('open')})};
      document.querySelectorAll('[data-open="login"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-login')})});
      document.querySelectorAll('[data-open="register"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-register');regShowChoice()})});
      document.getElementById('to-register').addEventListener('click',function(){closeAll();open('m-register');regShowChoice()});
      // Волна 21.1 (add-roles-theme-landing): двухшаговая регистрация по
      // мокапу auth-register-choice — выбор роли → форма ученика / анкета
      // инструктора (/instructors/apply, модерация существующим контуром).
      function regShowChoice(){
        document.getElementById('reg-choice').style.display='flex';
        document.getElementById('reg-student-form').style.display='none';
        document.getElementById('reg-back').style.display='none';
        document.getElementById('reg-sub').textContent='Кем вы хотите зарегистрироваться?';
      }
      function regShowStudentForm(){
        document.getElementById('reg-choice').style.display='none';
        document.getElementById('reg-student-form').style.display='block';
        document.getElementById('reg-back').style.display='';
        document.getElementById('reg-sub').textContent='Создайте аккаунт ученика';
      }
      document.getElementById('reg-role-student').addEventListener('click',regShowStudentForm);
      document.getElementById('reg-back').addEventListener('click',regShowChoice);
      document.getElementById('reg-role-instructor').addEventListener('click',function(){
        // инструкторская регистрация — существующая анкета с модерацией
        window.location.href='/instructors/apply';
      });
      // Волна 21.3 (add-roles-theme-landing): лендинг-блок ГигаЧата
      // интерактивен — send незалогиненному открывает регистрацию с
      // подсказкой (введённый вопрос сохраняется в ai_prefill — чат
      // «Главной» подхватит после входа); залогиненному — редирект в
      // чат «Главной» с предзаполнением. quick-сценарии — то же с
      // контекстом сценария (спека landing-assistant).
      function aiPrefillAndRegister(question){
        try { sessionStorage.setItem('ai_prefill', question); } catch (e) {}
        open('m-register'); regShowChoice();
        document.getElementById('reg-sub').textContent =
          'Задайте этот вопрос ГигаЧату после входа';
      }
      document.getElementById('ai-open').addEventListener('click',function(){
        var q = '';
        try { q = document.getElementById('ai-input').value.trim(); } catch (e) {}
        try { sessionStorage.setItem('ai_prefill', q); } catch (e) {}
        var logged = null;
        try { logged = sessionStorage.getItem('session_token'); } catch (e) {}
        if (logged) { window.location.href = '/cabinet'; return; }
        open('m-register'); regShowChoice();
        document.getElementById('reg-sub').textContent =
          'Задайте этот вопрос ГигаЧату после входа';
      });
      document.getElementById('ai-input').addEventListener('keydown',function(e){
        if (e.key === 'Enter') document.getElementById('ai-open').click();
      });
      document.querySelectorAll('.quick [data-scenario]').forEach(function(b){
        b.addEventListener('click',function(){
          // MAJ-4 (review-…-001): quick для залогиненного — в чат «Главной»,
          // как и #ai-open; незалогиненному — регистрация с подсказкой.
          var logged = null;
          try { logged = sessionStorage.getItem('session_token'); } catch (e) {}
          if (logged) {
            try { sessionStorage.setItem('ai_prefill', b.getAttribute('data-scenario')); } catch (e) {}
            window.location.href = '/cabinet';
            return;
          }
          aiPrefillAndRegister(b.getAttribute('data-scenario'));
        });
      });
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
      document.getElementById('login-submit').addEventListener('click',loginWiring.doLogin);
      // Волна 21.3: лендинг-блок ГигаЧата интерактивен — живые листенеры
      // #ai-open/#ai-input/.quick [data-scenario] выше (заглушки спринта-0
      // удалены: дублировали обработчики — alert на каждый клик).
      // to-teachers — легаси-заглушка вне скоупа волны (лендинг водителей).
      var stubTeachers=function(msg){return function(){alert(msg)}};
      document.getElementById('to-teachers').addEventListener('click',stubTeachers('Заглушка: лендинг для водителей-учителей — следующая страница'));
    });

    return {
      loginError: loginError,
      regError: regError,
    };
  },
};
</script>
