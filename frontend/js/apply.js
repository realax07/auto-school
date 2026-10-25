/* из instructor-apply.html (блок 1) */
const radios=[...document.querySelectorAll('input[name="format"]')],plateWrap=document.getElementById('plate-wrap'),plate=document.getElementById('plate');function updateFormat(){const own=document.querySelector('input[name="format"]:checked').value==='own';plateWrap.style.opacity=own?'1':'.55';plate.disabled=!own;if(!own)plate.value='';}radios.forEach(r=>r.addEventListener('change',updateFormat));updateFormat();document.getElementById('pick-file').addEventListener('click',()=>document.getElementById('license-file').click());
// BUG-048 (1): реальная загрузка ВУ. Выбор файла -> мгновенная миниатюра
// (objectURL) вместо области загрузки (иконка+подпись+кнопка скрываются;
// клик по миниатюре снова открывает выбор — label for=license-file).
// Клиентская валидация: JPEG/PNG, <=5 МБ; иначе красный текст ошибки
// и отправка заблокирована (тексты совпадают с серверными — 422 контракт).
var licenseInput=document.getElementById('license-file'),licenseZone=licenseInput.closest('.upload'),licenseThumb=document.getElementById('license-thumb'),licenseError=document.getElementById('license-error'),fileName=document.getElementById('file-name'),licenseObjectUrl=null,licenseFileError=null;
function showLicenseError(msg){licenseError.textContent=msg;licenseError.classList.add('show');}
function clearLicenseError(){licenseError.textContent='';licenseError.classList.remove('show');}
function validateLicenseFile(file){
 if(file.size>5*1024*1024)return 'Файл: изображение больше 5 МБ';
 var type=(file.type||'').toLowerCase(),ext=(file.name.split('.').pop()||'').toLowerCase();
 var okType=['image/jpeg','image/jpg','image/png'].indexOf(type)!==-1;
 var okExt=['jpg','jpeg','png'].indexOf(ext)!==-1;
 if(!okType&&!okExt)return 'Файл: допустимы только изображения JPEG или PNG';
 return null;
}
function resetLicensePreview(){licenseZone.classList.remove('has-file');if(licenseObjectUrl){URL.revokeObjectURL(licenseObjectUrl);licenseObjectUrl=null;}}
licenseInput.addEventListener('change',function(){
 var file=this.files[0];
 resetLicensePreview();licenseFileError=null;clearLicenseError();
 if(!file){fileName.textContent='Прикрепить фото или скан';return;}
 var err=validateLicenseFile(file);
 if(err){ // красный текст ошибки, миниатюры нет, отправка блокируется
   licenseFileError=err;showLicenseError(err);this.value='';
   fileName.textContent='Прикрепить фото или скан';return;
 }
 fileName.textContent=file.name;
 licenseObjectUrl=URL.createObjectURL(file);
 licenseThumb.src=licenseObjectUrl;
 licenseZone.classList.add('has-file');
});
// Wiring (BUG-048, задача 1): сабмит -> POST /api/instructors/apply,
// multipart/form-data (все поля анкеты + license_photo). Токен сессии
// не используется: сессия по этой заявке не выдается.
// 200 {"ok": true} -> редирект /instructors/pending (FR-12);
// 413/415/422 -> сообщение от сервера видно у поля загрузки ВУ (красный
// текст) и под формой (notice). Клиентская ошибка файла блокирует отправку.
document.getElementById('registration').addEventListener('submit',function(e){
  e.preventDefault();
  var notice=document.getElementById('notice');
  notice.classList.remove('show');
  if(licenseFileError){ // валидный файл не выбран — отправка заблокирована
    showLicenseError(licenseFileError);
    licenseError.scrollIntoView({behavior:'smooth',block:'nearest'});
    return;
  }
  clearLicenseError();
  // Явный набор полей (name-атрибуты макета используют дефисы, контракту
  // нужны snake_case ключи) + license_photo.
  function val(id){return document.getElementById(id).value.trim();}
  var fd=new FormData();
  fd.append('surname',val('surname'));
  fd.append('name',val('name'));
  fd.append('patronymic',val('patronymic'));
  fd.append('phone',val('phone'));
  fd.append('email',val('email'));
  fd.append('address',val('address'));
  fd.append('work_format',document.querySelector('input[name="format"]:checked').value);
  fd.append('plate',val('plate'));
  fd.append('license_number',val('license-number'));
  fd.append('license_date',document.getElementById('license-date').value);
  fd.append('license_category',document.getElementById('license-category').value);
  fd.append('experience',document.getElementById('experience').value);
  fd.append('password',document.getElementById('password').value);
  fd.append('password_confirm',document.getElementById('password-confirm').value);
  fd.append('consent',document.querySelector('.checkline input').checked?'true':'false');
  var lf=licenseInput.files[0];
  if(lf)fd.append('license_photo',lf,lf.name);
  fetch('/api/instructors/apply',{method:'POST',body:fd})
    .then(function(r){return r.text().then(function(t){var d=null;try{d=t?JSON.parse(t):null}catch(err){}return {status:r.status,data:d};})})
    .then(function(res){
      if(res.status===200&&res.data&&res.data.ok){location.href='/instructors/pending';}
      else{
        var msg=(res.data&&res.data.error)
          ||(res.status===413?'Файл: изображение больше 5 МБ'
          :res.status===415?'Файл: допустимы только изображения JPEG или PNG'
          :'Ошибка отправки заявки');
        if(res.status===413||res.status===415||(res.status===422&&msg.indexOf('Файл')===0)){
          showLicenseError(msg); // только файловые ошибки — у поля загрузки
        }
        notice.textContent=msg;
        notice.classList.add('show');
        notice.scrollIntoView({behavior:'smooth',block:'nearest'});
      }
    })
    .catch(function(){
      notice.textContent='Ошибка сети';
      notice.classList.add('show');
    });
});
