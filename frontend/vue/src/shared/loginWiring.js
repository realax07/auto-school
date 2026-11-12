// Спринт 14 (change add-vue-s14-instructor-loop, задача 3.1): консолидация
// wiring входа — обещание design С12 «Судьба общего контура модалок»
// выполнено на живом втором потребителе /instructors (легаси-дубль модалки
// входа instructors.html умирает в этой партии — копий m-login вне каркаса
// не остается). Сабмит входа вынесен из App.vue лендинга «/» ДОСЛОВНО
// (фрагменты контракта — design.md «Границы правок тестов», правки носителя
// минимальны): payload email/password → postJSON('/api/auth/login') →
// setToken(res.data.token) → route-маппинг §15.5 с sessionStorage
// «instructor_rejected_reason» ДО редиректа /instructors/rejected
// (КОНТРАКТ POLLING/REJECTED НЕ СЛОМАТЬ — экран С11 читает причину из
// этого ключа независимо от точки входа модалки). Сообщение ошибки —
// эквивалент err.textContent=: текст сервера рендерится в #login-error
// из реактивного состояния (проп error, интерполяция {{ }}). location.href
// на «/» НЕТ (BUG-055 — вход не уводит с текущей страницы до route-разбора).
// Open/close-семантика остается ПОСТРАНИЧНО (design.md «Судьба контура
// модалок входа»): лендинг «/» — data-open/data-close + снятие
// open_login/open_login_from при закрытии (BUG-056); /instructors —
// data-open-login, открытие локально БЕЗ флагов, закрытие без работы
// с флагами (BUG-055).
import { ref } from 'vue';
import { postJSON, setToken } from './api.js';

export function useLoginWiring() {
  var loginError = ref('');
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
  return { loginError: loginError, doLogin: doLogin };
}
