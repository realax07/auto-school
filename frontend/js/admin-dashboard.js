/* из admin-dashboard.html (блок 1) */
// Реальные данные из API (задача 4.1, дизайн 2026-10-08)
var TOKEN=sessionStorage.getItem('admin_token');
if(!TOKEN){location.href='/admin-login';}
var tb=document.getElementById('rows');
function loadUsers(){
  fetch('/api/admin/users',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.json();
    })
    .then(function(data){
      tb.innerHTML='';
      data.users.forEach(function(u){
        // fix review-001-code blocker: stored XSS — только textContent, без innerHTML с данными
        var tr=document.createElement('tr');
        var date=(u.created_at||'').split(' ')[0].split('-');
        var dateStr=date.length===3?date[2]+'.'+date[1]+'.'+date[0]:u.created_at;
        function td(text){var c=document.createElement('td');c.textContent=text;return c;}
        tr.appendChild(td(u.fio));tr.appendChild(td(u.email));tr.appendChild(td(u.phone));
        var badge=document.createElement('td');var sp=document.createElement('span');sp.className='badge';sp.textContent='Ученик';badge.appendChild(sp);tr.appendChild(badge);
        tr.appendChild(td(dateStr));
        tb.appendChild(tr);
      });
      document.getElementById('count').textContent='Записей: '+data.count;
      document.getElementById('empty').style.display=data.count?'none':'block';
    })
    .catch(function(e){if(e.message!=='unauthorized')throw e;});
}
function exportCsv(){
  fetch('/api/admin/users/export.csv',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.blob();
    })
    .then(function(blob){
      var a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([blob],{type:'text/csv;charset=utf-8'}));
      a.download='users.csv';a.click();
    })
    .catch(function(e){if(e.message!=='unauthorized')throw e;});
}
loadUsers();
function soon(){alert('Заглушка: раздел появится в следующем спринте');}

// --- Раздел «Заявки инструкторов» (change add-instructor-cabinet, правка Заказчика 2026-10-14) ---
function showSection(name, btn){
  document.querySelectorAll('.nav button').forEach(function(b){b.classList.remove('active');});
  if(btn)btn.classList.add('active');
  document.querySelector('table').style.display=name==='users'?'':'none';
  document.getElementById('empty').style.display=name==='users'?'':'none';
  document.querySelector('.toolbar').style.display=name==='users'?'':'none';
  document.getElementById('sec-applications').style.display=name==='applications'?'block':'none';
  if(name==='applications')loadApplications();
}
function loadApplications(){
  fetch('/api/admin/instructor-applications',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.json();
    })
    .then(function(data){
      var tb=document.getElementById('app-rows');
      tb.innerHTML='';
      document.getElementById('app-count').textContent='Заявок: '+data.count;
      document.getElementById('app-empty').style.display=data.count?'none':'block';
      data.applications.forEach(function(a){
        var tr=document.createElement('tr');
        function td(text){var c=document.createElement('td');c.textContent=text||'—';return c;}
        // ФИО из трех полей анкеты (surname/name/patronymic, правка
        // Заказчика 2026-10-14); старое поле fio API больше не отдает
        var fio=[a.surname,a.name,a.patronymic].filter(Boolean).join(' ');
        tr.appendChild(td(fio));tr.appendChild(td(a.email));tr.appendChild(td(a.phone));
        tr.appendChild(td(a.work_format==='own'?'Свой автомобиль':'Авто Сбера'));
        tr.appendChild(td(a.license_number));tr.appendChild(td(a.experience));
        var st=document.createElement('td');var sp=document.createElement('span');
        // BUG-046: «На рассмотрении» — желтый бейдж (решение Заказчика)
        sp.className='badge'+(a.status==='deny'?' red':a.status==='waiting'?' wait':'');
        sp.textContent=a.status==='waiting'?'На рассмотрении':a.status==='approved'?'Одобрена':'Отклонена';
        st.appendChild(sp);tr.appendChild(st);
        tr.appendChild(td(a.review_comment));
        // BUG-046: колонки «Действия» больше нет — одобрение/отклонение
        // только в модальной карточке (клик по строке, решение Заказчика)
        tr.style.cursor='pointer';
        tr.addEventListener('click',function(){openInstructorCard(a.id);});
        tb.appendChild(tr);
      });
    }).catch(function(e){if(e.message!=='unauthorized')console.error(e);});
}
function approve(id){
  if(!confirm('Одобрить заявку? Будет создана учетная запись инструктора.'))return;
  fetch('/api/admin/instructor-applications/'+id+'/approve',{method:'POST',headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){return r.json().then(function(d){return {status:r.status,data:d};});})
    .then(function(res){
      if(res.status===200&&res.data.ok){loadApplications();}
      else{alert((res.data&&res.data.error)||'Ошибка');}
    });
}
// --- Отклонение заявки — только из модальной карточки (BUG-046, решение
// Заказчика «отклонение и одобрение только в модалке»). Причина отказа
// обязательна, подтверждение заблокировано до непустого комментария
// (паттерн BUG-045: кнопки вместе, gap 10px).
function resetCardDeny(){
  document.getElementById('ic-deny-box').style.display='none';
  document.getElementById('ic-deny-comment').value='';
  document.getElementById('ic-deny-confirm').disabled=true;
}
function submitDeny(id){
  var comment=document.getElementById('ic-deny-comment').value.trim();
  if(!comment){alert('Причина отказа обязательна');return;}
  fetch('/api/admin/instructor-applications/'+id+'/deny',{
    method:'POST',headers:{'X-Admin-Token':TOKEN,'Content-Type':'application/json'},
    body:JSON.stringify({comment:comment})})
    .then(function(r){return r.json().then(function(d){return {status:r.status,data:d};});})
    .then(function(res){
      if(res.status===200&&res.data.ok){resetCardDeny();closeInstructorCard();loadApplications();}
      else{alert((res.data&&res.data.error)||'Ошибка');}
    });
}
document.getElementById('ic-deny-comment').addEventListener('input',function(){
  document.getElementById('ic-deny-confirm').disabled=!this.value.trim();
});
document.getElementById('ic-deny-cancel').addEventListener('click',resetCardDeny);

// --- Детальная карточка инструктора (change add-instructor-student-loop,
// задача 1.3, мокап instructor-card-admin): клик по строке -> модально;
// данные GET /api/admin/instructor-applications/{id}; изображение ВУ —
// GET …/{id}/license-image только с X-Admin-Token (FR-24/NFR-1): <img> не
// умеет заголовки, поэтому fetch -> blob -> objectURL. У заявки без ВУ —
// корректное пустое состояние без «битой» картинки.
var IC_CURRENT=null;
function icSet(id,text){var e=document.getElementById(id);e.textContent=(text==null||text==='')?'—':text;}
function openInstructorCard(id){
  IC_CURRENT=id;
  fetch('/api/admin/instructor-applications/'+id,{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.json().then(function(d){return {status:r.status,data:d};});
    })
    .then(function(res){
      if(res.status!==200||!res.data||!res.data.ok){
        alert((res.data&&res.data.error)||'Не удалось загрузить заявку');return;
      }
      var a=res.data.application||res.data;
      var fio=[a.surname,a.name,a.patronymic].filter(Boolean).join(' ');
      document.getElementById('ic-name').textContent=fio||'—';
      document.getElementById('ic-sub').textContent='Заявка инструктора № '+id;
      icSet('ic-last',a.surname);icSet('ic-first',a.name);icSet('ic-pat',a.patronymic);
      icSet('ic-email',a.email);icSet('ic-phone',a.phone);
      icSet('ic-exp',a.experience!=null?a.experience:a.experience_years);
      icSet('ic-car',a.car_info||a.car);
      icSet('ic-status',a.status==='waiting'?'На рассмотрении':a.status==='approved'?'Одобрена':'Отклонена');
      icSet('ic-review',a.review_comment);
      var waiting=(a.status==='waiting');
      document.getElementById('ic-approve').style.display=waiting?'':'none';
      document.getElementById('ic-deny').style.display=waiting?'':'none';
      resetCardDeny(); // каждая карточка открывается без панели отказа
      loadLicenseImage(id,a.license_photo_path||a.license_photo);
      document.getElementById('ic-backdrop').classList.add('open');
      document.body.style.overflow='hidden';
    })
    .catch(function(e){if(e.message!=='unauthorized')console.error(e);});
}
function loadLicenseImage(id,hasPhoto){
  var ph=document.getElementById('ic-license');
  function phText(lines){ // гигиена: без innerHTML (review-002)
    ph.innerHTML='';
    lines.forEach(function(t,i){
      var sp=document.createElement('span');
      if(i)sp.appendChild(document.createElement('br'));
      sp.appendChild(document.createTextNode(t));
      ph.appendChild(sp);
    });
  }
  if(!hasPhoto){
    phText(['Файл ВУ не приложен','заявка без изображения']);
    return;
  }
  phText(['Загрузка…']);
  fetch('/api/admin/instructor-applications/'+id+'/license-image',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(!r.ok){ // 401 без/с неверным токеном, 404 без файла — изображение не возвращается
        return r.json().then(function(d){return {ok:false,error:d&&d.error};},function(){return {ok:false};});
      }
      return r.blob().then(function(b){return {ok:true,blob:b};});
    })
    .then(function(res){
      if(res.ok){
        ph.innerHTML='';
        var img=document.createElement('img');
        img.alt='Изображение водительского удостоверения';
        img.src=URL.createObjectURL(res.blob);
        ph.appendChild(img);
      }else{
        phText(res.error?['Изображение недоступно',res.error]:['Изображение недоступно']);
      }
    })
    .catch(function(){phText(['Изображение недоступно']);});
}
function closeInstructorCard(){
  var img=document.querySelector('#ic-license img');
  if(img&&img.src.startsWith('blob:'))URL.revokeObjectURL(img.src);
  document.getElementById('ic-backdrop').classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('ic-close').addEventListener('click',closeInstructorCard);
document.getElementById('ic-backdrop').addEventListener('click',function(e){
  if(e.target===this)closeInstructorCard();
});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeInstructorCard();});
document.getElementById('ic-approve').addEventListener('click',function(){
  var id=IC_CURRENT;closeInstructorCard();approve(id);
});
// BUG-046: «Отклонить» — панель причины внутри той же модалки (карточка
// не закрывается); подтверждение разблокируется непустым комментарием
document.getElementById('ic-deny').addEventListener('click',function(){
  document.getElementById('ic-deny-box').style.display='block';
  document.getElementById('ic-deny-comment').focus();
});
document.getElementById('ic-deny-confirm').addEventListener('click',function(){
  submitDeny(IC_CURRENT);
});

// onclick-обработчики в HTML — нужна глобальная видимость (ES-модуль
// глобальные объявления не создает)
window.exportCsv = exportCsv;
window.showSection = showSection;
window.soon = soon;
