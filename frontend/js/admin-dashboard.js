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
  // Спринт 7: селекторы скоуплены id-ами (в админке три таблицы:
  // пользователи, заявки, автомобили — querySelector('table') больше не годится)
  var users=name==='users',apps=name==='applications',cars=name==='cars';
  var docs=name==='documents'; // Спринт 8: раздел «Документы» (ОВ-1/ОВ-4)
  document.getElementById('users-table').style.display=users?'':'none';
  document.getElementById('empty').style.display=users?'':'none';
  document.querySelector('.toolbar').style.display=users?'':'none';
  document.getElementById('sec-applications').style.display=apps?'block':'none';
  document.getElementById('sec-cars-admin').style.display=cars?'block':'none';
  document.getElementById('sec-documents').style.display=docs?'block':'none';
  if(apps)loadApplications();
  if(cars)acLoad();
  if(docs)dcLoad();
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

// --- Спринт 7 (change add-car-validation-booking, задача 7.2, ОВ-4/ОВ-5):
// раздел «Автомобили» — единственный раздел про авто. GET
// /api/admin/cars/completeness (+status): таблица всех авто; фильтр
// «На валидации»; модалка с чек-листом комплектности — «Подтвердить»
// ЗАБЛОКИРОВАНО при <3 ракурсов или нет СТС (перечень виден); POST
// /api/admin/cars/{id}/validate (сервер 409 — страховка). Кнопки
// блокировки больше нет: контур block замещен статусной моделью. ---
var AC_ANGLES=[['front','Спереди'],['rear','Сзади'],['left','Слева'],['right','Справа'],['interior','Салон']];
var AC_STATUS={draft:['Черновик','ac-b-draft'],validating:['На валидации','ac-b-val'],validated:['Проверено','ac-b-ok']};
var AC_TRANS={manual:'механика',automatic:'автомат'};
var acCars=[],acFilter='all',acCurrent=null;
function acLoad(){
  fetch('/api/admin/cars/completeness',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.json();
    })
    .then(function(data){
      acCars=data.cars||[];
      acRender();
    })
    .catch(function(e){if(e.message!=='unauthorized')console.error(e);});
}
function acCounters(c){return c.counters||{angles:(c.photos?Object.keys(c.photos).filter(function(k){return c.photos[k]}).length:0),sts:!!c.has_sts}}
function acRender(){
  var tb=document.getElementById('ac-rows');
  tb.innerHTML='';
  var list=acCars.filter(function(c){return acFilter==='all'||c.status===acFilter});
  document.getElementById('ac-count').textContent='Автомобилей: '+list.length;
  document.getElementById('ac-empty').style.display=list.length?'none':'block';
  var nVal=acCars.filter(function(c){return c.status==='validating'}).length;
  document.getElementById('ac-n-val').textContent=nVal?('·'+nVal):'';
  list.forEach(function(c){
    var st=AC_STATUS[c.status]||AC_STATUS.draft;
    var k=acCounters(c);
    var eligible=k.angles>=3&&k.sts;
    var tr=document.createElement('tr');
    function td(text){var cell=document.createElement('td');cell.textContent=text;return cell;}
    tr.appendChild(td(c.instructor_full_name||'—'));
    tr.appendChild(td([c.brand,c.model].filter(Boolean).join(' ')));
    tr.appendChild(td(c.plate||'—'));
    var stTd=document.createElement('td');
    var sp=document.createElement('span');
    sp.className='ac-badge '+st[1];
    sp.textContent=st[0];
    stTd.appendChild(sp);tr.appendChild(stTd);
    var complTd=document.createElement('td');
    complTd.className='ac-compl';
    var cspan=document.createElement('span');
    cspan.className=eligible?'ok':'miss';
    cspan.textContent=k.angles+'/5'+(k.sts?' + СТС ✓':' · нет СТС');
    complTd.appendChild(cspan);tr.appendChild(complTd);
    tr.style.cursor='pointer';
    tr.addEventListener('click',function(){acOpen(c);});
    tb.appendChild(tr);
  });
}
document.querySelectorAll('#ac-filters button').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('#ac-filters button').forEach(function(x){x.classList.remove('on');});
    b.classList.add('on');
    acFilter=b.dataset.f;
    acRender();
  });
});
function acOpen(c){
  acCurrent=c;
  var st=AC_STATUS[c.status]||AC_STATUS.draft;
  document.getElementById('ac-title').textContent=[c.brand,c.model].filter(Boolean).join(' ');
  document.getElementById('ac-sub').textContent='Авто № '+c.id+' · инструктор '+(c.instructor_full_name||'—');
  var badge=document.getElementById('ac-status');
  badge.className='ac-badge '+st[1];
  badge.textContent=st[0];
  acSet('ac-owner',c.instructor_full_name);
  acSet('ac-brand',[c.brand,c.model].filter(Boolean).join(' '));
  acSet('ac-year',c.year);
  acSet('ac-plate',c.plate);
  acSet('ac-trans',AC_TRANS[c.transmission]||c.transmission);
  var k=acCounters(c);
  acSet('ac-compl',k.angles+'/5'+(k.sts?' + СТС ✓':' · СТС нет'));
  acSet('ac-status-row',st[0]);
  // чек-лист: флаги загрузки (админу изображения не выдаются — NFR-7)
  var tb=document.getElementById('ac-thumbs');
  tb.innerHTML='';
  AC_ANGLES.forEach(function(a){
    var has=!!(c.photos&&c.photos[a[0]]);
    var d=document.createElement('div');
    d.className='ac-thumb'+(has?' has':'');
    d.appendChild(Object.assign(document.createElement('span'),{className:'mark',textContent:has?'✓':'—'}));
    d.appendChild(Object.assign(document.createElement('span'),{className:'tg',textContent:a[1]}));
    tb.appendChild(d);
  });
  var sts=document.createElement('div');
  sts.className='ac-thumb'+(c.has_sts?' has':'');
  sts.appendChild(Object.assign(document.createElement('span'),{className:'mark',textContent:c.has_sts?'✓':'—'}));
  sts.appendChild(Object.assign(document.createElement('span'),{className:'tg',textContent:'СТС'}));
  tb.appendChild(sts);
  acRenderVerdict();
  document.getElementById('ac-backdrop').classList.add('open');
  document.body.style.overflow='hidden';
}
function acSet(id,text){var e=document.getElementById(id);e.textContent=(text==null||text==='')?'—':String(text);}
function acRenderVerdict(){
  var c=acCurrent,ap=document.getElementById('ac-approve'),v=document.getElementById('ac-verdict');
  var k=acCounters(c);
  if(c.status!=='validating'){
    v.innerHTML=c.status==='validated'
      ?'<b>Подтверждено ранее.</b> Статус «Проверено» установлен администратором; повторное подтверждение недоступно.'
      :'<b>Черновик.</b> Инструктор ещё не отправлял авто на валидацию — подтверждение недоступно.';
    ap.style.display='none';
    return;
  }
  ap.style.display='';
  var miss=[];
  if(k.angles<3)miss.push('фото ракурсов ('+k.angles+' из 3 минимум)');
  if(!k.sts)miss.push('фото СТС');
  if(miss.length){
    ap.disabled=true;
    v.innerHTML='<b>Подтверждение заблокировано.</b> Не хватает: '+miss.join(', ')+'. Условие — любые 3 фото ракурсов + СТС (ОВ-4). Инструктору виден тот же перечень — досылет и отправит снова.';
  }else{
    ap.disabled=false;
    v.innerHTML='<b>Комплект достаточен:</b> '+k.angles+' фото ракурсов (нужно минимум 3) + СТС. Подтверждение установит статус «Проверено» — авто вернётся в каталог новых учеников с зелёной галочкой.';
  }
}
function acClose(){
  document.getElementById('ac-backdrop').classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('ac-close').addEventListener('click',acClose);
document.getElementById('ac-dummy').addEventListener('click',acClose);
document.getElementById('ac-backdrop').addEventListener('click',function(e){
  if(e.target===this)acClose();
});
document.addEventListener('keydown',function(e){if(e.key==='Escape')acClose();});
document.getElementById('ac-approve').addEventListener('click',function(){
  if(!acCurrent||acCurrent.status!=='validating')return;
  var id=acCurrent.id,btn=this;
  btn.disabled=true;
  fetch('/api/admin/cars/'+id+'/validate',{method:'POST',headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){return r.json().then(function(d){return {status:r.status,data:d};});})
    .then(function(res){
      btn.disabled=false;
      if(res.status===200&&res.data&&res.data.ok){
        acClose();
        toastMsg('Авто подтверждено: статус «Проверено», зелёная галочка у инструктора. Из фильтра «На валидации» исчезнет.');
        acLoad();
      }else{
        // 409 «Комплект неполный…» — серверная страховка ОВ-4
        toastMsg((res.data&&res.data.error)||'Не удалось подтвердить авто');
        acLoad();
      }
    })
    .catch(function(){btn.disabled=false;toastMsg('Не удалось подтвердить авто');});
});
function toastMsg(m){
  // тост раздела «Автомобили» (#ac-toast — общий для confirm-успеха и 409)
  var t=document.getElementById('ac-toast');
  t.textContent=m;
  t.classList.add('show');
  clearTimeout(window._acToastTimer);
  window._acToastTimer=setTimeout(function(){t.classList.remove('show')},3400);
}
// =========================================================================
// Спринт 8 (change add-s8-cars-docs-booking, задачи 4.1/7.1, ОВ-1/ОВ-4;
// мокап design/mocks/admin-documents.html): раздел «Документы» —
// верификация замененных версий документов инструкторов (единая модель
// ВУ+СТС). GET /api/admin/documents?status=pending (default; pending/
// verified/rejected): тип, версия, uploaded_at; license — ФИО инструктора,
// car_sts — марка/модель/госномер + владелец. Предпросмотр — GET
// …/{version_id}/file: ИЗОБРАЖЕНИЕ ДОЛЖНО ОТКРЫВАТЬСЯ (ОВ-4; fetch ->
// blob -> objectURL — <img> не умеет заголовки). «Подтвердить» → POST
// …/verify (только pending — иначе 409); «Отклонить» → модалка с
// ОБЯЗАТЕЛЬНОЙ причиной (кнопка заблокирована без текста; сервер 422 —
// страховка), POST …/reject {reason}. После решения строка уходит из
// списка. Вкладка «История» — verified+rejected, фильтры по типу/решению.
// Пользовательские строки (ФИО/причины) — только textContent (XSS). ---
var dcState={tab:'pending',ftype:'all',fh:'all',pending:[],history:[],denyTarget:null};
var DC_ST={pending:['Ожидает верификации','dc-b-pend'],verified:['Подтверждено','dc-b-ok'],rejected:['Отклонено','dc-b-rej']};
function dcFetch(status){
  // контракт design.md блок C: X-Admin-Token; status — query-параметр
  return fetch('/api/admin/documents?status='+encodeURIComponent(status),
    {headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.json();
    })
    .then(function(d){
      if(!d||!d.ok)throw new Error((d&&d.error)||'Не удалось загрузить документы');
      return d.documents||[];
    });
}
function dcLoad(){
  Promise.all([dcFetch('pending'),dcFetch('verified'),dcFetch('rejected')])
    .then(function(res){
      dcState.pending=res[0];
      // история: решения (verified + rejected) — свежие сверху
      dcState.history=res[1].concat(res[2]).sort(function(a,b){
        return String(b.decided_at||'').localeCompare(String(a.decided_at||''));
      });
      dcRender();
    })
    .catch(function(e){if(e.message!=='unauthorized'){dcState.pending=[];dcState.history=[];dcRender();toastMsg(e.message||'Не удалось загрузить документы');}});
}
function dcTitle(d){
  if(d.type==='license')return d.instructor_full_name||'—';
  var c=d.car||{};
  return [c.brand,c.model].filter(Boolean).join(' ')+(c.plate?' · '+c.plate:'');
}
function dcSub(d){
  if(d.type==='license'){
    return 'ВУ · версия '+d.version+' · инструктор '+(d.instructor_full_name||'—');
  }
  var c=d.car||{};
  return 'СТС · версия '+d.version+' · инструктор '+(d.owner_full_name||d.instructor_full_name||'—')
    +([c.brand,c.model].filter(Boolean).join(' ')?' · авто '+[c.brand,c.model].filter(Boolean).join(' '):'');
}
function dcWhen(d){return String(d.decided_at||d.uploaded_at||'').split('.')[0]}
function dcRender(){
  var tab=dcState.tab,box=document.getElementById('dc-list');
  document.getElementById('dc-filters').style.display=tab==='pending'?'flex':'none';
  document.getElementById('dc-filters-hist').style.display=tab==='history'?'flex':'none';
  document.getElementById('dc-hist-note').style.display=tab==='history'?'block':'none';
  document.getElementById('dc-n-pending').textContent=dcState.pending.length?('·'+dcState.pending.length):'';
  var rows,emptyText;
  if(tab==='pending'){
    // фильтр «СТС» (data-f="sts") сопоставляется с типом документа car_sts
    var ftype=dcState.ftype==='sts'?'car_sts':dcState.ftype;
    rows=dcState.pending.filter(function(d){return ftype==='all'||d.type===ftype});
    emptyText='Очередь пуста — нет ожидающих версий по выбранному фильтру.';
    document.getElementById('dc-count').textContent='Ожидающих версий: '+rows.length;
  }else{
    rows=dcState.history.filter(function(d){return dcState.fh==='all'||d.status===dcState.fh});
    emptyText='Нет решений по выбранному фильтру.';
    document.getElementById('dc-count').textContent='Записей в истории: '+rows.length;
  }
  document.getElementById('dc-empty').textContent=emptyText;
  document.getElementById('dc-empty').style.display=rows.length?'none':'block';
  box.innerHTML='';
  rows.forEach(function(d){
    var row=document.createElement('div');row.className='dc-row';
    // миниатюра-предпросмотр: клик — модалка с изображением (ОВ-4)
    var thumb=document.createElement('span');thumb.className='dc-thumb';
    thumb.dataset.preview=String(d.id);thumb.title='Открыть предпросмотр';
    thumb.textContent=d.type==='license'?'🪪':'🚗';
    var zoom=document.createElement('span');zoom.className='zoom';zoom.textContent='⤢ Предпросмотр';
    thumb.appendChild(zoom);
    row.appendChild(thumb);
    var info=document.createElement('div');info.className='dc-info';
    var line=document.createElement('div');line.className='dc-line';
    var t=document.createElement('span');
    t.className='dc-type '+(d.type==='license'?'dc-t-lic':'dc-t-sts');
    t.textContent=d.type==='license'?'ВУ':'СТС';
    line.appendChild(t);
    line.appendChild(Object.assign(document.createElement('b'),{textContent:dcTitle(d)}));
    info.appendChild(line);
    info.appendChild(Object.assign(document.createElement('small'),{textContent:dcSub(d)}));
    info.appendChild(Object.assign(document.createElement('small'),
      {textContent:(tab==='pending'?'загружено ':'решение от ')+dcWhen(d)+' · версия № '+d.version}));
    var st=DC_ST[d.status]||DC_ST.pending;
    var line2=document.createElement('div');line2.className='dc-line';
    line2.appendChild(Object.assign(document.createElement('span'),{className:'dc-badge '+st[1],textContent:st[0]}));
    if(tab==='pending'){
      line2.appendChild(Object.assign(document.createElement('small'),
        {style:'color:#7e909a',textContent:'действует предыдущая версия'}));
    }
    info.appendChild(line2);
    // причина отказа — в истории (rejected): текст виден админу и инструктору
    if(d.status==='rejected'&&d.reject_reason){
      info.appendChild(Object.assign(document.createElement('div'),
        {className:'dc-rej-reason',textContent:'Причина отказа: '+d.reject_reason}));
    }
    row.appendChild(info);
    var act=document.createElement('div');act.className='dc-actions';
    var view=document.createElement('button');view.type='button';
    view.className='dc-act view';view.textContent='Предпросмотр';
    view.dataset.view=String(d.id);
    act.appendChild(view);
    if(tab==='pending'){
      var ap=document.createElement('button');ap.type='button';
      ap.className='dc-act approve';ap.textContent='✓ Подтвердить';
      ap.dataset.approve=String(d.id);
      act.appendChild(ap);
      var dn=document.createElement('button');dn.type='button';
      dn.className='dc-act deny';dn.textContent='Отклонить…';
      dn.dataset.opendeny=String(d.id);
      act.appendChild(dn);
    }
    row.appendChild(act);
    box.appendChild(row);
  });
}
function dcOpenPreview(id){
  var pool=dcState.pending.concat(dcState.history);
  var d=null;
  pool.forEach(function(x){if(x.id===id)d=x});
  if(!d)return;
  document.getElementById('dc-view-title').textContent=(d.type==='license'?'ВУ · ':'СТС · ')+dcTitle(d);
  document.getElementById('dc-view-sub').textContent=dcSub(d)+' · загружено '+dcWhen(d);
  var ph=document.getElementById('dc-view-full');
  ph.innerHTML='';
  ph.appendChild(Object.assign(document.createElement('span'),{textContent:'Загрузка…'}));
  fetch('/api/admin/documents/'+id+'/file',{headers:{'X-Admin-Token':TOKEN}})
    .then(function(r){
      if(r.status===401){location.href='/admin-login';throw new Error('unauthorized');}
      return r.ok?r.blob():null;
    })
    .then(function(blob){
      if(!blob){ph.innerHTML='';ph.appendChild(Object.assign(document.createElement('span'),{textContent:'Изображение недоступно'}));return}
      ph.innerHTML='';
      var img=document.createElement('img');
      img.alt='Предпросмотр документа';
      img.src=URL.createObjectURL(blob);
      ph.appendChild(img);
    })
    .catch(function(e){if(e.message!=='unauthorized'){ph.innerHTML='';ph.appendChild(Object.assign(document.createElement('span'),{textContent:'Изображение недоступно'}));}});
  document.getElementById('dc-view').classList.add('open');
  document.body.style.overflow='hidden';
}
function dcClosePreview(){
  var img=document.querySelector('#dc-view-full img');
  if(img&&img.src.startsWith('blob:'))URL.revokeObjectURL(img.src);
  document.getElementById('dc-view').classList.remove('open');
  document.body.style.overflow='';
}
function dcOpenDeny(id){
  var d=null;
  dcState.pending.forEach(function(x){if(x.id===id)d=x});
  if(!d)return;
  dcState.denyTarget=id;
  document.getElementById('dc-deny-sub').textContent=(d.type==='license'?'ВУ · ':'СТС · ')+dcTitle(d);
  document.getElementById('dc-reason').value='';
  document.getElementById('dc-deny-go').disabled=true; // ОВ-1: причина обязательна
  document.getElementById('dc-deny').classList.add('open');
  document.body.style.overflow='hidden';
  document.getElementById('dc-reason').focus();
}
function dcCloseDeny(){
  dcState.denyTarget=null;
  document.getElementById('dc-deny').classList.remove('open');
  document.body.style.overflow='';
}
document.getElementById('dc-reason').addEventListener('input',function(){
  // пустая причина → кнопка заблокирована (сервер вернул бы 422 — ОВ-1)
  document.getElementById('dc-deny-go').disabled=!this.value.trim();
});
document.getElementById('dc-deny-go').addEventListener('click',function(){
  var id=dcState.denyTarget,btn=this;
  var reason=document.getElementById('dc-reason').value.trim();
  if(!id||!reason)return;
  btn.disabled=true;
  fetch('/api/admin/documents/'+id+'/reject',{
    method:'POST',headers:{'X-Admin-Token':TOKEN,'Content-Type':'application/json'},
    body:JSON.stringify({reason:reason})})
    .then(function(r){return r.json().then(function(d){return {status:r.status,data:d};});})
    .then(function(res){
      btn.disabled=false;
      if(res.status===200&&res.data&&res.data.ok){
        dcCloseDeny();
        toastMsg('Замена отклонена с причиной. Действующей осталась предыдущая версия — инструктор не остался без документа.');
        dcLoad(); // строка уходит из списка
      }else{
        // 422 «причина обязательна» / 409 «не pending» — серверная страховка
        toastMsg((res.data&&res.data.error)||'Не удалось отклонить замену');
      }
    })
    .catch(function(){btn.disabled=false;toastMsg('Не удалось отклонить замену');});
});
document.getElementById('dc-deny-cancel').addEventListener('click',dcCloseDeny);
document.getElementById('dc-deny-close').addEventListener('click',dcCloseDeny);
document.getElementById('dc-deny').addEventListener('click',function(e){
  if(e.target===this)dcCloseDeny();
});
document.getElementById('dc-view-close').addEventListener('click',dcClosePreview);
document.getElementById('dc-view').addEventListener('click',function(e){
  if(e.target===this)dcClosePreview();
});
document.getElementById('dc-list').addEventListener('click',function(e){
  var t=e.target.closest('[data-preview],[data-view]');
  if(t){dcOpenPreview(+t.dataset.preview||+t.dataset.view);return}
  var ap=e.target.closest('[data-approve]');
  if(ap){
    var id=+ap.dataset.approve,btn=ap;
    btn.disabled=true;
    fetch('/api/admin/documents/'+id+'/verify',{method:'POST',headers:{'X-Admin-Token':TOKEN}})
      .then(function(r){return r.json().then(function(d){return {status:r.status,data:d};});})
      .then(function(res){
        btn.disabled=false;
        if(res.status===200&&res.data&&res.data.ok){
          toastMsg('Замена подтверждена: новая версия стала действующей, предыдущая переведена в архив.');
          dcLoad();
        }else{
          // 409 «только pending» — серверная страховка
          toastMsg((res.data&&res.data.error)||'Не удалось подтвердить замену');
          dcLoad();
        }
      })
      .catch(function(){btn.disabled=false;toastMsg('Не удалось подтвердить замену');});
    return;
  }
  var dn=e.target.closest('[data-opendeny]');
  if(dn)dcOpenDeny(+dn.dataset.opendeny);
});
document.querySelectorAll('#dc-tabs button').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('#dc-tabs button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');
    dcState.tab=b.dataset.tab;
    dcRender();
  });
});
document.querySelectorAll('#dc-filters button').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('#dc-filters button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');
    dcState.ftype=b.dataset.f;
    dcRender();
  });
});
document.querySelectorAll('#dc-filters-hist button').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('#dc-filters-hist button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');
    dcState.fh=b.dataset.fh;
    dcRender();
  });
});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'){dcClosePreview();dcCloseDeny();}
});
// onclick-обработчики в HTML — нужна глобальная видимость (ES-модуль
// глобальные объявления не создает)
window.exportCsv = exportCsv;
window.showSection = showSection;
window.soon = soon;
