/* из instructors.html (блок 1) */
/* из instructors.html (блок 2) */
document.getElementById('open-form').addEventListener('click',function(){location.href='/instructors/apply'});
document.querySelectorAll('[data-open-login]').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();sessionStorage.setItem('open_login','1');sessionStorage.setItem('open_login_from','/instructors');location.href='/';});});
