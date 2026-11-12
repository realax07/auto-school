<!-- shared/LoginModal.vue — модалка входа #m-login (Спринт 12, change
     add-vue-s12-landing-apply, задачи 2.1/3.2): вынос общего контура
     модалок входа/регистрации каркаса (design.md «Судьба общего контура
     модалок»). Разметка — ДОСЛОВНЫЙ перенос из legacy frontend/index.html,
     включая комментарии-маркеры «Модалка: Вход/Регистрация» (носитель
     LOGIN_MODAL_TEXTS — test_login_modal.py); держать синхронной со
     статической разметкой входа vue/index.html.
     Спринт 14 (change add-vue-s14-instructor-loop, задача 3.1): проп
     variant — последний дубль контура входа консолидирован:
     'landing' (дефолт) — разметка С12 дословно, дефолтный рендер НЕ
     меняется (e2e лендинга TC-UI-001/053 и LOGIN_MODAL_TEXTS зеленые без
     правок); 'instructors' — разметка варианта из legacy instructors.html
     дословно (5 отличий, design.md «Судьба контура модалок входа»):
     (1) p БЕЗ .sub; (2) подписи полей — span вместо label; (3) кнопки
     btn primary/ghost (у landing — btn btn-primary/btn btn-ghost);
     (4) БЕЗ alt-строки «Нет аккаунта?» и #to-register; (5) тот же набор
     id (m-login, login-close ВНЕ карточки — БЕЗ data-close, wiring
     инструкторского лендинга вешает закрытие напрямую; login-email/
     password/error/submit; data-close на «Отмене»).
     Подключение (компонент в App.vue) и wiring (открытие data-open/
     data-open-login, закрытие BUG-055/056, сабмит — shared/loginWiring.js,
     route-маппинг §15.5) — постранично. Единственная реактивная связь —
     сообщение ошибки: эквивалент err.textContent= — текст сервера
     рендерится в #login-error из пропа error (интерполяция {{ }},
     design.md «Границы правок тестов»). ids — якоря e2e
     (TC-UI-001/052/053, TC-S9UI-003), дословно. -->
<template>
  <!-- Модалка: Вход (утвержденный мокап) -->
  <!-- BUG-055/056: overlay — замутненная
     страница (blur 8px + затемнение); крестик #login-close ВНЕ карточки
     (закрытие: крестик/«Отмена»/Esc; клик по фону НЕ закрывает) -->
  <div v-if="variant !== 'instructors'" class="overlay" id="m-login"><button class="login-close" id="login-close" type="button" data-close aria-label="Закрыть" title="Закрыть">×</button><div class="modal" role="dialog" aria-label="Вход">
    <h2>Вход</h2><p class="sub">Войдите в личный кабинет</p>
    <div class="field"><label>Логин</label><input type="text" id="login-email" placeholder="email или телефон"></div>
    <div class="field"><label>Пароль</label><input type="password" id="login-password" placeholder="••••••••"></div>
    <p class="err" id="login-error" :style="{display: error ? 'block' : 'none'}" style="margin:14px 0 0;font-size:13px;color:#ff9c9c;">{{ error }}</p>
    <div class="actions"><button class="btn btn-primary" id="login-submit">Войти</button><button class="btn btn-ghost" data-close>Отмена</button></div>
    <p class="alt">Нет аккаунта? <button id="to-register">Зарегистрироваться</button></p>
  </div></div>
  <!-- Вариант 'instructors' — разметка из legacy instructors.html дословно
       (легаси-дубль удален в задаче 4.1; носитель текстов лендинга
       LOGIN_MODAL_TEXTS не затронут) -->
  <div v-else class="overlay" id="m-login"><button class="login-close" id="login-close" type="button" aria-label="Закрыть" title="Закрыть">×</button><div class="modal" role="dialog" aria-label="Вход">
    <h2>Вход</h2><p>Войдите в личный кабинет</p>
    <div class="field"><span>Логин</span><input type="text" id="login-email" placeholder="email или телефон"></div>
    <div class="field"><span>Пароль</span><input type="password" id="login-password" placeholder="••••••••"></div>
    <p class="err" id="login-error" :style="{display: error ? 'block' : 'none'}" style="color:#ff9c9c;">{{ error }}</p>
    <div class="actions"><button class="btn primary" id="login-submit">Войти</button><button class="btn ghost" data-close>Отмена</button></div>
  </div></div>
</template>

<script>
export default {
  name: 'LoginModal',
  props: {
    error: { type: String, default: '' },
    variant: { type: String, default: 'landing' },
  },
};
</script>
