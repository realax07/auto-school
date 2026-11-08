<!-- shared/LoginModal.vue — модалка входа #m-login (Спринт 12, change
     add-vue-s12-landing-apply, задача 2.1): вынос общего контура модалок
     входа/регистрации каркаса (design.md «Судьба общего контура модалок»).
     Разметка — ДОСЛОВНЫЙ перенос из legacy frontend/index.html, включая
     комментарии-маркеры «Модалка: Вход/Регистрация» (носитель
     LOGIN_MODAL_TEXTS — test_login_modal.py); держать синхронной со
     статической разметкой входа vue/index.html и легаси-дублем
     instructors.html (умирает при миграции /instructors).
     Подключение и wiring (открытие data-open, закрытие BUG-055/056,
     сабмит POST /api/auth/login, route-маппинг §15.5) — App.vue лендинга,
     задача 3.2; ids (login-email/login-password/login-error/login-submit/
     login-close) — якоря e2e (TC-UI-001/053, TC-S9UI-003), дословно. -->
<template>
  <!-- Модалка: Вход (утвержденный мокап) -->
  <!-- BUG-055/056: overlay — замутненная
     страница (blur 8px + затемнение); крестик #login-close ВНЕ карточки
     (закрытие: крестик/«Отмена»/Esc; клик по фону НЕ закрывает) -->
  <div class="overlay" id="m-login"><button class="login-close" id="login-close" type="button" data-close aria-label="Закрыть" title="Закрыть">×</button><div class="modal" role="dialog" aria-label="Вход">
    <h2>Вход</h2><p class="sub">Войдите в личный кабинет</p>
    <div class="field"><label>Логин</label><input type="text" id="login-email" placeholder="email или телефон"></div>
    <div class="field"><label>Пароль</label><input type="password" id="login-password" placeholder="••••••••"></div>
    <p class="err" id="login-error" style="display:none;margin:14px 0 0;font-size:13px;color:#ff9c9c;"></p>
    <div class="actions"><button class="btn btn-primary" id="login-submit">Войти</button><button class="btn btn-ghost" data-close>Отмена</button></div>
    <p class="alt">Нет аккаунта? <button id="to-register">Зарегистрироваться</button></p>
  </div></div>
</template>

<script>
export default { name: 'LoginModal' };
</script>
