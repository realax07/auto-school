// из index.html (блок 1)
import { postJSON, setToken } from './api.js';
(function(){
  var open=function(id){document.getElementById(id).classList.add('open')};
  var closeAll=function(){document.querySelectorAll('.overlay').forEach(function(o){o.classList.remove('open')})};
  document.querySelectorAll('[data-open="login"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-login')})});
  document.querySelectorAll('[data-open="register"]').forEach(function(b){b.addEventListener('click',function(){closeAll();open('m-register')})});
  document.getElementById('to-register').addEventListener('click',function(){closeAll();open('m-register')});
  document.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',function(){
    closeAll();
    // Вход открыт с лендинга инструкторов: Отмена возвращает туда
    if(sessionStorage.getItem('open_login_from')){location.href=sessionStorage.getItem('open_login_from');}
  })});
  document.querySelectorAll('.overlay').forEach(function(o){o.addEventListener('click',function(e){if(e.target===o)closeAll()})});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll()});
  // Регистрация: fetch POST /api/register (дизайн 2026-10-08)
  document.getElementById('reg-submit').addEventListener('click',function(){
    var err=document.getElementById('reg-error');
    err.style.display='none';
    var payload={
      surname:document.getElementById('reg-surname').value.trim(),
      name:document.getElementById('reg-name').value.trim(),
      patronymic:document.getElementById('reg-patronymic').value.trim(),
      email:document.getElementById('reg-email').value.trim(),
      phone:document.getElementById('reg-phone').value.trim(),
      password:document.getElementById('reg-password').value,
      password_confirm:document.getElementById('reg-password-confirm').value
    };
    postJSON('/api/register',payload)
      .then(function(res){
        if(res.status===200&&res.data.ok&&res.data.token){
          try{setToken(res.data.token);}
          catch(e){err.textContent='Не удалось сохранить сессию';err.style.display='block';return;}
          location.href='/cabinet';
        }
        else{err.textContent=(res.data&&res.data.error)||'Ошибка регистрации';err.style.display='block';}
      })
      .catch(function(){err.textContent='Ошибка сети';err.style.display='block';});
  });
  // Вход: POST /api/auth/login → route (§15.5): cabinet → /instructor/dashboard,
  // student-cabinet → /cabinet, pending → /instructors/pending, rejected → /instructors/rejected
  document.getElementById('login-submit').addEventListener('click',function(){
    var err=document.getElementById('login-error');
    err.style.display='none';
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
        else{err.textContent=(res.data&&res.data.error)||'Неверный email или пароль';err.style.display='block';}
      })
      .catch(function(){err.textContent='Ошибка сети';err.style.display='block';});
  });
  // Вход инструктора с лендинга инструкторов: авто-открытие модалки входа
  if(sessionStorage.getItem('open_login')){sessionStorage.removeItem('open_login');sessionStorage.setItem('open_login_from','/instructors');closeAll();open('m-login');}
  // ассистент и футер-переход — заглушки спринта-0
  var stub=function(msg){return function(){alert(msg)}};
  document.getElementById('ai-open').addEventListener('click',stub('Заглушка: чат ассистента (Hermes) будет подключен позже'));
  document.querySelectorAll('.quick button').forEach(function(b){b.addEventListener('click',stub('Заглушка: сценарии ассистента будут подключены позже'))});
  document.getElementById('to-teachers').addEventListener('click',stub('Заглушка: лендинг для водителей-учителей — следующая страница'));
})();
