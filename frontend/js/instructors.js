// из instructors.html (блок 1)
import { postJSON, setToken } from './api.js';
document.getElementById('open-form').addEventListener('click',function(){location.href='/instructors/apply'});
// BUG-055 (decisions/2026-11-04-ui-followup.md, п.2): «Войти» (data-open-login)
// открывает модалку входа ЛОКАЛЬНО — на странице, откуда нажали, — БЕЗ
// редиректа на / и БЕЗ sessionStorage-флагов open_login/open_login_from.
document.querySelectorAll('[data-open-login]').forEach(function(b){
  b.addEventListener('click',function(e){e.preventDefault();openLogin();});
});
var overlay=document.getElementById('m-login');
function openLogin(){
  overlay.classList.add('open');
  document.body.style.overflow='hidden';
  var em=document.getElementById('login-email');if(em)em.focus();
}
// BUG-056 (п.3/4): закрытие — крестик #login-close (вне карточки), «Отмена»,
// Esc. На этой странице закрытие просто убирает модалку (страница не
// менялась). Клик по фону (вне карточки) окно НЕ закрывает — обработчика
// e.target===overlay здесь НЕТ.
function closeLogin(){
  overlay.classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('login-close').addEventListener('click',closeLogin);
overlay.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',closeLogin);});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'&&overlay.classList.contains('open'))closeLogin();
});
// Вход: POST /api/auth/login → route (§15.5) — механика landing.js:48–70:
// instructor-cabinet → /instructor/dashboard, pending → /instructors/pending,
// rejected → /instructors/rejected (с причиной), student → /cabinet.
// Роутинг — по РОЛИ из ответа, не по open_login_from (BUG-055).
document.getElementById('login-submit').addEventListener('click',function(){
  var err=document.getElementById('login-error');
  err.style.display='none';
  postJSON('/api/auth/login',{
    email:document.getElementById('login-email').value.trim(),
    password:document.getElementById('login-password').value
  }).then(function(res){
    if(res.status===200&&res.data.ok){
      if(res.data.token){try{setToken(res.data.token);}catch(e){}}
      var route=res.data.route||'student-cabinet';
      if(route==='cabinet'){location.href='/instructor/dashboard';}
      else if(route==='pending'){location.href='/instructors/pending';}
      else if(route==='rejected'){
        try{sessionStorage.setItem('instructor_rejected_reason',res.data.reason||'');}catch(e){}
        location.href='/instructors/rejected';
      }
      else{location.href='/cabinet';}
    }
    else{err.textContent=(res.data&&res.data.error)||'Неверный email или пароль';err.style.display='block';}
  }).catch(function(){err.textContent='Ошибка сети';err.style.display='block';});
});
