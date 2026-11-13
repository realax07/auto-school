<!-- Админка: вход по прямой ссылке (заглушка). Одна учетка: admin / admin
     Разметка — дословный перенос frontend/admin-login.html (Спринт 15,
     change add-vue-s15-final-migration, задача 2.1; шаблон повторяет вход
     vue/admin-login.html — «Разметку держать синхронной с App.vue»).
     Wiring — эквивалент js/admin/admin-login.js 1:1 (doLogin):
     postJSON('/api/admin/login') из vue/src/shared/api.js (перенос С9,
     тела дословны) → 200 + ok + token → sessionStorage 'admin_token' →
     location.href='/admin-dashboard'; иначе/сеть → реактивное состояние
     ошибки: #err получает класс .show (документированный стековый
     эквивалент legacy err.classList.add('show') — design.md «Границы
     правок тестов»), текст «Неверный логин или пароль» — дословно в
     разметке. Секрет в клиенте не хранится и в логи не попадает. -->
<template>
<div class="hero"><div class="card">
  <h1>Админка</h1>
  <p>Вход только по прямой ссылке</p>
  <div class="err" id="err" :class="{'show': errShow}">Неверный логин или пароль</div>
  <form @submit="doLogin">
    <div class="field"><label>Логин</label><input id="login" type="text" v-model="login" autocomplete="username"></div>
    <div class="field"><label>Пароль</label><input id="pass" type="password" v-model="pass" autocomplete="current-password"></div>
    <button class="btn">Войти</button>
  </form>
  <p class="hint">Демо-доступ спринта-0: admin / admin</p>
</div></div>
</template>

<script>
// Wiring — перенос js/admin/admin-login.js 1:1 (задача 2.1): postJSON —
// из vue/src/shared/api.js (существует с С9 — design.md «Судьба каталога
// js/»); иначе/сеть — .show из реактивного состояния (стековый
// эквивалент задокументирован — MIN-2 С11).
import { reactive, toRefs } from 'vue';
import { postJSON } from '../../shared/api.js';

export default {
  name: 'AdminLoginApp',
  setup: function () {
    var state = reactive({ login: '', pass: '', errShow: false });

    function doLogin(e){
      e.preventDefault();
      var l=state.login.trim(), p=state.pass;
      postJSON('/api/admin/login',{login:l,password:p})
        .then(function(res){
          if(res.status===200&&res.data.ok&&res.data.token){
            sessionStorage.setItem('admin_token',res.data.token);
            location.href='/admin-dashboard';
          }else{
            state.errShow=true;
          }
        })
        .catch(function(){state.errShow=true;});
      return false;
    }

    return Object.assign({ doLogin: doLogin }, toRefs(state));
  },
};
</script>
