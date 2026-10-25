// из admin-login.html (блок 1)
import { postJSON } from './api.js';
function doLogin(e){
  e.preventDefault();
  var l=document.getElementById('login').value.trim(), p=document.getElementById('pass').value;
  postJSON('/api/admin/login',{login:l,password:p})
    .then(function(res){
      if(res.status===200&&res.data.ok&&res.data.token){
        sessionStorage.setItem('admin_token',res.data.token);
        location.href='/admin-dashboard';
      }else{
        document.getElementById('err').classList.add('show');
      }
    })
    .catch(function(){document.getElementById('err').classList.add('show');});
  return false;
}
// onsubmit в HTML — обработчику нужна глобальная видимость (ES-модуль
// глобальные объявления не создает)
window.doLogin = doLogin;
