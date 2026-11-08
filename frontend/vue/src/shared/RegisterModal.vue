<!-- shared/RegisterModal.vue — модалка регистрации #m-register (Спринт 12,
     change add-vue-s12-landing-apply, задача 2.1): вынос общего контура
     модалок входа/регистрации каркаса (design.md «Судьба общего контура
     модалок»). Разметка — ДОСЛОВНЫЙ перенос из legacy frontend/index.html,
     включая комментарии-маркеры «Модалка: Вход/Регистрация»; держать
     синхронной со статической разметкой входа vue/index.html. После партии
     — единственный носитель согласия регистрации FR-78 (чекбокс
     #reg-consent со ссылкой /policy; #reg-submit недоступен до установки —
     гейт консента в App.vue, задача 3.2). ids (reg-surname/reg-name/
     reg-patronymic/reg-email/reg-phone/reg-password/reg-password-confirm/
     reg-consent/reg-submit/reg-error) — якоря e2e (TC-UI-002/043…045),
     дословно. -->
<template>
  <!-- Модалка: Регистрация (утвержденный мокап) -->
  <div class="overlay" id="m-register"><div class="modal wide" role="dialog" aria-label="Регистрация">
    <h2>Регистрация</h2><p class="sub">Создайте аккаунт ученика</p>
    <div class="row">
      <div class="field"><label>Фамилия</label><input type="text" id="reg-surname" placeholder="Иванов"></div>
      <div class="field"><label>Имя</label><input type="text" id="reg-name" placeholder="Иван"></div>
    </div>
    <div class="field"><label>Отчество</label><input type="text" id="reg-patronymic" placeholder="Иванович"></div>
    <div class="field"><label>Email</label><input type="email" id="reg-email" placeholder="you@example.com"></div>
    <div class="field"><label>Телефон</label><input type="tel" id="reg-phone" placeholder="+7 (___) ___-__-__"><div class="hint">Используем для связи по расписанию и экзаменам</div></div>
    <div class="row">
      <div class="field"><label>Пароль</label><input type="password" id="reg-password" placeholder="••••••••"></div>
      <div class="field"><label>Подтверждение</label><input type="password" id="reg-password-confirm" placeholder="••••••••"></div>
    </div>
    <!-- Спринт 9 (change add-personal-data-policy, задача 5.2, FR-78):
       обязательный чекбокс согласия с политикой персональных данных
       со ссылкой на /policy (target="_blank"); #reg-submit недоступен
       до установки (landing.js), consent — в payload сабмита. -->
    <label class="reg-check"><input type="checkbox" id="reg-consent" required><span>Я согласен(на) с <a href="/policy" target="_blank" rel="noopener">политикой персональных данных</a></span></label>
    <p class="err" id="reg-error" style="display:none;margin:14px 0 0;font-size:13px;color:#ff9c9c;"></p>
    <div class="actions"><button class="btn btn-primary" id="reg-submit" disabled>Зарегистрироваться</button><button class="btn btn-ghost" data-close>Отмена</button></div>
  </div></div>
</template>

<script>
export default { name: 'RegisterModal' };
</script>
