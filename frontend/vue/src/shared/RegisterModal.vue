<!-- shared/RegisterModal.vue — модалка регистрации #m-register (Спринт 12,
     change add-vue-s12-landing-apply, задачи 2.1/3.2): вынос общего
     контура модалок входа/регистрации каркаса (design.md «Судьба общего
     контура модалок»). Разметка — ДОСЛОВНЫЙ перенос из legacy
     frontend/index.html, включая комментарии-маркеры «Модалка:
     Вход/Регистрация»; держать синхронной со статической разметкой входа
     vue/index.html. После партии — единственный носитель согласия
     регистрации FR-78: эквивалент regSubmit.disabled=!regConsent.checked —
     :disabled кнопки #reg-submit от состояния чекбокса #reg-consent
     (@change; сабмит и consent в payload — из того же состояния checked
     чекбокса, читает App.vue; design.md «Границы правок тестов»).
     Сообщение ошибки — из пропа error (интерполяция {{ }} — эквивалент
     err.textContent=). ids (reg-surname/reg-name/reg-patronymic/reg-email/
     reg-phone/reg-password/reg-password-confirm/reg-consent/reg-submit/
     reg-error) — якоря e2e (TC-UI-002/043…045), дословно. -->
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
       до установки, consent — в payload сабмита. -->
    <label class="reg-check"><input type="checkbox" id="reg-consent" required @change="regConsent = $event.target.checked"><span>Я согласен(на) с <a href="/policy" target="_blank" rel="noopener">политикой персональных данных</a></span></label>
    <p class="err" id="reg-error" :style="{display: error ? 'block' : 'none'}" style="margin:14px 0 0;font-size:13px;color:#ff9c9c;">{{ error }}</p>
    <div class="actions"><button class="btn btn-primary" id="reg-submit" :disabled="!regConsent">Зарегистрироваться</button><button class="btn btn-ghost" data-close>Отмена</button></div>
  </div></div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'RegisterModal',
  props: { error: { type: String, default: '' } },
  setup: function () {
    var regConsent = ref(false);
    return { regConsent: regConsent };
  },
};
</script>
