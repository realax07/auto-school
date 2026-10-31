/* из instructor-dashboard.html (блок 1) */
// Спринт 6, Партия B: общие хелперы — из js/utils.js и js/api.js
import { toast as baseToast, nowMoscow } from './utils.js';
import { apiGet, apiSend, clearSession } from './api.js';
// Спринт 3: даты кабинета — актуальные, TimeZone Europe/Moscow (GMT+3),
// локаль ru. Дефолтные строки HTML сохранены (design-guard сверяет с
// мокапом) — здесь они заменяются на текущую дату.
(function(){
  var now=new Date();
  var cap=function(s){return s.charAt(0).toUpperCase()+s.slice(1)};
  function parts(opts){var o={};new Intl.DateTimeFormat('ru-RU',Object.assign({timeZone:'Europe/Moscow'},opts)).formatToParts(now).forEach(function(x){o[x.type]=x.value});return o}
  var sh=parts({weekday:'short',day:'numeric',month:'long',year:'numeric'});
  var lo=parts({weekday:'long',day:'numeric',month:'long'});
  var chip=document.querySelector('.date-chip');
  if(chip)chip.innerHTML='◷ &nbsp; '+cap(sh.weekday)+', '+sh.day+' '+sh.month+' '+sh.year;
  var kick=document.querySelector('.kicker');
  if(kick)kick.textContent=cap(lo.weekday)+' · '+lo.day+' '+lo.month;
})();
// FR-20: ФИО из учетной записи; приветствие по имени (правка Заказчика 2026-10-14)
fetch('/api/auth/me',{headers:{'X-Session-Token':sessionStorage.getItem('session_token')||''}})
  .then(function(r){if(!r.ok){location.href='/';return;}return r.json();})
  .then(function(d){if(!d||!d.ok){return;}
    var u=d.user||{};
    var fio=[u.surname,u.name,u.patronymic].filter(Boolean).join(' ');
    document.getElementById('user-fio').textContent=fio||'Инструктор';
    var ini=((u.surname||'')[0]||'')+((u.name||'')[0]||'');
    document.getElementById('avatar').textContent=ini||'—';
    if(u.name){document.getElementById('hello-name').textContent='Добрый день, '+u.name;}
  }).catch(function(){location.href='/';});
// Виджет «Занятия на сегодня» (спринт 3): пустой массив занятий в панели
// расписания -> заглушка «Сегодня занятий нет»; демо-данные остаются как есть.
(function(){
  var todayAppointments=Array.prototype.slice.call(document.querySelectorAll('.appointments .appointment'));
  if(todayAppointments.length!==0)return;
  var stub=document.getElementById('today-empty');
  var wrap=document.querySelector('.appointments');
  var head=document.getElementById('today-count');
  if(stub)stub.style.display='block';
  if(wrap)wrap.style.display='none';
  if(head)head.textContent='Сегодня · занятий нет';
})();
let weekShift=0;
function toast(msg){baseToast(msg,2600)}
function navTo(name){
  if(name==='__logout__'){logout();return}
  // BUG-047 (скрины Заказчика 2026-10-17): «Мои автомобили» — раздел этого
  // дашборда (таб), отдельной страницы /my-cars больше нет (301 →
  // /instructor/dashboard#/my-cars открывает этот же раздел)
  // Спринт 3: реальные разделы «Календарь» и «Запросы учеников»
  // Спринт 5 (change add-booking-docs): разделы «Бронирования», «Мои документы»
  // — тоже ВНУТРИ дашборда (BUG-047-прецедент: standalone-страницы запрещены)
  var isCal=(name==='Календарь'),isReq=(name==='Запросы учеников'),isCars=(name==='Мои автомобили');
  var isDocs=(name==='Мои документы'),isBk=(name==='Бронирования');
  document.querySelectorAll('.day-content').forEach(function(el){el.style.display=(isCal||isReq||isCars||isDocs||isBk)?'none':''});
  document.getElementById('sec-calendar').style.display=isCal?'block':'none';
  document.getElementById('sec-requests').style.display=isReq?'block':'none';
  document.getElementById('sec-cars').style.display=isCars?'block':'none';
  document.getElementById('sec-docs').style.display=isDocs?'block':'none';
  document.getElementById('sec-bookings').style.display=isBk?'block':'none';
  if(isCal)openCalendar();
  if(isReq)openRequests();
  if(isCars)openCars();
  if(isDocs)openDocs();
  if(isBk)openBookings();
  var pp=document.getElementById('profile-panel');
  if(pp)pp.style.display='none';
  document.getElementById('page-title').textContent=name;
  document.getElementById('crumb').textContent=name;
  document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  // BUG-047: хеш раздела синхронизируется с табом — reload не сбрасывает
  // раздел, старые ссылки#/my-cars открывают его напрямую
  var wantHash=isCars?'#/my-cars':isDocs?'#/my-docs':isBk?'#/bookings':'';
  if(location.hash!==wantHash){try{history.replaceState(null,'',location.pathname+location.search+(wantHash||''))}catch(e){}}
  if(name!=='Мой день'&&!isCal&&!isReq&&!isCars&&!isDocs&&!isBk)toast('Раздел «'+name+'» — демо-данные, следующий экран в концепции кабинета')
}

// --- Виджеты главной (change add-instructor-student-loop, FR-40/FR-41):
// GET /api/instructor/summary (students, today_lessons) + GET /api/instructor/requests
// (счётчик новых). До ответа / при ошибке API — честные пустые состояния.
// Шейпы — по backend/instructor_summary.py и backend/student_requests.py
// (code-review review-001 #2/#4: вымышленные алиасы fio/since/… удалены).
function el(id){return document.getElementById(id)}
// DOM-хелпер: пользовательские строки — только через textContent
// (code-review review-001 #1: stored XSS через innerHTML запрещен)
function node(tag,cls,text){var n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n}
function stuInitials(fio){return (fio||'').split(/\s+/).filter(Boolean).slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('')||'—'}
function loadSummary(){
  if(!token)return;
  apiGet('/api/instructor/summary',function(res){
    if(!res||!res.ok)return;
    var students=res.students||[];
    el('w-students-n').textContent=students.length;
    var box=el('w-students-list');
    box.innerHTML='';
    if(!students.length){
      box.innerHTML='<div class="w-empty"><b>Пока нет привязанных учеников</b>Принятые заявки появятся в этом списке.</div>';
    }else{
      students.forEach(function(s){
        var row=node('div','w-stu');
        row.appendChild(node('span','w-sic',stuInitials(s.full_name)));
        var who=node('div');
        who.appendChild(node('b',null,s.full_name||''));
        var date=s.decided_at?String(s.decided_at).split(' ')[0]:'';
        if(date)who.appendChild(node('small',null,'с инструктора с '+date));
        row.appendChild(who);
        row.appendChild(node('span','car',s.car||'авто не выбрано'));
        box.appendChild(row);
      });
    }
    var lessons=res.today_lessons||[];
    if(lessons.length){
      el('w-today-empty').style.display='none';
      el('w-today-list').style.display='block';
      el('w-today-list').innerHTML='';
      lessons.forEach(function(l){
        var row=node('div','w-req');
        var div=node('div');
        // шейп бэка (instructor_summary.py): student_full_name, start_time/
        // end_time «ЧЧ:ММ:СС» — рендерим ФИО и окно «ЧЧ:ММ–ЧЧ:ММ» (FR-49)
        div.appendChild(node('b',null,l.student_full_name||'Занятие'));
        div.appendChild(node('small',null,(l.start_time||'').slice(0,5)+'–'+(l.end_time||'').slice(0,5)));
        row.appendChild(div);
        el('w-today-list').appendChild(row);
      });
    }else{
      // честная заглушка FR-41: реального расписания нет
      el('w-today-empty').style.display='block';
      el('w-today-list').style.display='none';
    }
  });
}
function countNewRequests(){
  apiGet('/api/instructor/requests',function(res){
    if(!res||!res.ok)return;
    var list=(res.requests||[]).filter(function(r){return (r.status||'')==='new'});
    el('w-requests-n').textContent=list.length+' новых';
    var box=el('w-requests-list');
    box.innerHTML='';
    if(!list.length){
      box.innerHTML='<div class="w-empty"><b>Новых запросов нет</b>Заявки учеников появятся здесь.</div>';
    }else{
      list.slice(0,3).forEach(function(r){
        var row=node('div','w-req');
        var div=node('div');
        div.appendChild(node('b',null,rqFio(r)));
        div.appendChild(node('small',null,rqDate(r)+' · стаж '+(rqExp(r)===0?'нет':rqExp(r))));
        row.appendChild(div);
        var go=node('span','go','→');go.dataset.gotoRequests='1';
        row.appendChild(go);
        box.appendChild(row);
      });
      box.querySelectorAll('[data-goto-requests]').forEach(function(g){g.addEventListener('click',function(){navTo('Запросы учеников')})});
    }
    var badge=el('nav-req-badge');
    badge.style.display=list.length?'inline-block':'none';
    badge.textContent='+'+list.length;
  });
}

document.querySelectorAll('.nav button').forEach(b=>b.addEventListener('click',()=>navTo(b.dataset.tab)));
function changeWeek(dir){weekShift+=dir;const days=document.querySelectorAll('#week .day .dnum');days.forEach((el,i)=>el.textContent=String(12+weekShift*7+i));toast(weekShift===0?'Текущая неделя':'Неделя переключена — демонстрационные даты')}

// --- Wiring Спринта 2, часть 2 (change add-instructor-cabinet) ---
// Токен — sessionStorage, ключ session_token (единый паттерн кабинета
// ученика, sdd §10.2–10.3). Единственные отличия от мокапа — wiring.
var TOKEN_KEY='session_token';
var token=null;
try{token=sessionStorage.getItem(TOKEN_KEY)}catch(e){}
// clearSession — общий (js/api.js), тот же sessionStorage.clear()
function toLogin(){clearSession();location.href='/'}
// GET /api/instructor/dashboard до отрисовки (FR-18): 401/403 -> редирект
// на главную, к модалке входа; 200 -> ФИО шапки и инициалы аватара из
// учетки (FR-20), демо-строка «Инструктор · Категория B» не подменяется.
if(!token){toLogin()}else{
fetch('/api/instructor/dashboard',{headers:{'X-Session-Token':token}})
  .then(function(r){return r.json().then(function(d){return{status:r.status,data:d}})})
  .then(function(res){
    if(res.status===401||res.status===403||!res.data||!res.data.ok){toLogin();return}
    var i=res.data.instructor||{};
    var fio=[i.surname,i.name,i.patronymic].filter(Boolean).join(' ');
    document.querySelector('.user b').textContent=fio;
    var initials=[(i.surname||'').trim()[0],(i.name||'').trim()[0]].filter(Boolean).join('').toUpperCase();
    document.querySelector('.avatar').textContent=initials;
    loadSummary();countNewRequests();
  })
  .catch(function(){toLogin()});
}
// JSON-GET/POST с инструкторской сессией — общий клиент js/api.js
// (cb получает {ok,...} или null / {status,data})

// --- Раздел «Календарь» (FR-29/FR-30): сетка недели × 2-часовые интервалы,
// клик переключает выбор, «Сохранить график» -> PUT /api/instructor/availability
// (полная замена), при входе восстановление через GET.
var CAL_HOURS=[8,10,12,14,16,18,20];
var CAL_DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
var calBuilt=false;
var calSelected={}; // ключ 'weekday-hour'
function calBuildGrid(){
  var grid=el('cal-grid');
  var now=nowMoscow();
  var mon=new Date(now);mon.setDate(mon.getDate()-((mon.getDay()+6)%7));
  var todayIdx=(now.getDay()+6)%7;
  var html='<div class="cal-corner">МСК</div>';
  for(var d=0;d<7;d++){
    var dt=new Date(mon);dt.setDate(mon.getDate()+d);
    html+='<div class="cal-dh'+(d===todayIdx?' today':'')+'" data-day="'+d+'"><small>'+CAL_DAYS[d]+'</small><b>'+dt.getDate()+'</b></div>';
  }
  CAL_HOURS.forEach(function(h){
    var p=function(n){return (n<10?'0':'')+n};
    html+='<div class="cal-tlabel">'+p(h)+':00–'+p(h+2)+':00</div>';
    for(var d2=0;d2<7;d2++){
      html+='<button type="button" class="cal-slot" data-k="'+d2+'-'+h+'" aria-label="Интервал '+CAL_DAYS[d2]+', '+p(h)+':00"></button>';
    }
  });
  grid.innerHTML=html;
  grid.querySelectorAll('.cal-slot').forEach(function(b){
    b.addEventListener('click',function(){
      var k=b.dataset.k;
      if(calSelected[k])delete calSelected[k];else calSelected[k]=true;
      b.classList.toggle('on');
      el('cal-changed').style.display='inline';
    });
  });
  calBuilt=true;
}
function openCalendar(){
  if(!calBuilt)calBuildGrid();
  apiGet('/api/instructor/availability',function(res){
    calSelected={};
    el('cal-grid').querySelectorAll('.cal-slot').forEach(function(b){b.classList.remove('on')});
    if(!res)return;
    (res.intervals||[]).forEach(function(iv){
      var s=parseInt((iv.start_time||'').split(':')[0],10);
      var e=parseInt((iv.end_time||'').split(':')[0],10);
      if(isNaN(s)||isNaN(e))return;
      // отмечаем все слоты сетки, покрываемые интервалом (напр. 10:00–14:00
      // -> слоты 10–12 и 12–14)
      CAL_HOURS.forEach(function(h){
        if(h<e&&h+2>s){
          var k=iv.weekday+'-'+h;
          calSelected[k]=true;
          var b=el('cal-grid').querySelector('.cal-slot[data-k="'+k+'"]');
          if(b)b.classList.add('on');
        }
      });
    });
    el('cal-changed').style.display='none';
  });
}
el('cal-save').addEventListener('click',function(){
  var intervals=Object.keys(calSelected).map(function(k){
    var parts=k.split('-'),d=+parts[0],h=+parts[1],p=function(n){return (n<10?'0':'')+n};
    return {weekday:d,start_time:p(h)+':00',end_time:p(h+2)+':00'};
  });
  apiSend('PUT','/api/instructor/availability',{intervals:intervals},function(res){
    if(res.status===200&&res.data&&res.data.ok){
      el('cal-changed').style.display='none';
      toast('График сохранён: '+intervals.length+' интервалов. Он виден ученикам в фильтре свободного времени.');
    }else{
      toast((res.data&&res.data.error)||'Не удалось сохранить график');
    }
  });
});

// --- Раздел «Запросы учеников» (FR-37/38/39): GET /api/instructor/requests;
// Принять -> POST /api/instructor/requests/{id}/accept {car_id} (авто из
// GET /api/instructor/cars; при 0 авто действие недоступно — ОВ-4);
// Отказать -> POST …/{id}/deny {comment}, кнопка заблокирована до непустого
// комментария.
var rqState={list:[],filter:'all',open:null,cars:null};
// Поля — реальный шейп GET /api/instructor/requests
// (backend/student_requests.py: id, status, created_at, decided_at,
// student_full_name, student_experience_years, car:{brand,model,…})
function rqFio(r){return r.student_full_name||'Ученик'}
function rqExp(r){return (r.student_experience_years!=null)?+r.student_experience_years:0}
function rqDate(r){return String(r.created_at||'').split('.')[0]}
function rqCarName(r){
  var c=r.car;
  return c?([c.brand,c.model].filter(Boolean).join(' ')||'авто не выбрано'):'авто не выбрано';
}
function carTitle(c){
  var name=[c.brand,c.model].filter(Boolean).join(' ')||'Автомобиль';
  return name+(c.year?' · '+c.year:'');
}
function carSub(c){
  var tr=c.transmission==='automatic'?'автомат':c.transmission==='manual'?'механика':(c.transmission||'');
  return tr+(c.plate?' · '+c.plate:'');
}
function rqStatusBadge(s){
  var cls=s==='new'?'rq-st-new':s==='accepted'?'rq-st-acc':'rq-st-den';
  var text=s==='new'?'Новая':s==='accepted'?'Принята':'Отказана';
  return node('span','rq-status '+cls,text);
}
function expWord2(n){return n%10===1&&n%100!==11?'год':(n%10>=2&&n%10<=4&&(n%100<10||n%100>=20)?'года':'лет')}
function renderRequests(){
  var box=el('rq-list');box.innerHTML='';
  var list=rqState.list.filter(function(r){return rqState.filter==='all'||r.status===rqState.filter});
  var newN=rqState.list.filter(function(r){return r.status==='new'}).length;
  el('rq-new-n').textContent='·'+newN;
  if(!list.length){box.innerHTML='<div class="rq-none">Заявок в этой категории нет.</div>';return}
  // DOM-строительство (code-review review-001 #1): ФИО/бренд/модель —
  // только textContent, без сборки HTML из пользовательских строк
  list.forEach(function(r){
    var art=node('article','rq');
    var top=node('div','rq-top');
    top.appendChild(node('span','rq-sic',stuInitials(rqFio(r))));
    var who=node('div');
    who.appendChild(node('b',null,rqFio(r)));
    who.appendChild(node('small',null,'Стаж вождения: '+(rqExp(r)===0?'нет':rqExp(r)+' '+expWord2(rqExp(r)))+' · '+rqDate(r)));
    top.appendChild(who);
    top.appendChild(rqStatusBadge(r.status));
    art.appendChild(top);
    if(r.status==='accepted'){
      art.appendChild(node('div','rq-decided','Ученик в разделе «Мои ученики» · автомобиль: '+rqCarName(r)));
    }
    if(r.status==='new'){
      var actions=node('div','rq-actions');
      var acc=node('button','rq-act accept','✓ Принять…');acc.type='button';acc.dataset.accept=String(r.id);
      var den=node('button','rq-act deny','✕ Отказать…');den.type='button';den.dataset.denypanel=String(r.id);
      actions.appendChild(acc);actions.appendChild(den);
      art.appendChild(actions);
      art.appendChild(acceptPanelNode(r));
      art.appendChild(denyPanelNode(r));
    }
    box.appendChild(art);
  });
  bindRequests();
}
function acceptPanelNode(r){
  var panel=node('div','rq-accept'+(rqState.open==='accept-'+r.id?' open':''));
  panel.id='rq-accept-'+r.id;
  if(rqState.cars&&!rqState.cars.length){
    panel.appendChild(node('div','rq-no-cars','Принять заявку нельзя: у вас нет автомобилей. Заведите автомобиль в разделе «Мой автомобиль».'));
    return panel;
  }
  panel.appendChild(node('h4',null,'Выберите автомобиль для ученика'));
  (rqState.cars||[]).forEach(function(c,i){
    var lab=node('label','rq-caropt');
    var radio=document.createElement('input');
    radio.type='radio';radio.name='car-'+r.id;radio.value=String(c.id);
    if(i===0)radio.checked=true;
    lab.appendChild(radio);
    var div=node('div');
    div.appendChild(node('b',null,carTitle(c)));
    div.appendChild(node('small',null,carSub(c)));
    lab.appendChild(div);
    panel.appendChild(lab);
  });
  var btn=node('button','rq-confirm','✓ Принять ученика');btn.type='button';btn.dataset.confirm=String(r.id);
  panel.appendChild(btn);
  return panel;
}
function denyPanelNode(r){
  var panel=node('div','rq-deny'+(rqState.open==='deny-'+r.id?' open':''));
  panel.id='rq-deny-'+r.id;
  panel.appendChild(node('h4',null,'Комментарий к отказу (обязательно)'));
  var ta=document.createElement('textarea');
  ta.id='rq-ta-'+r.id;
  ta.placeholder='Например: не совпадают графики занятий…';
  panel.appendChild(ta);
  var actions=node('div','rq-deny-actions');
  var btn=node('button','rq-deny-confirm','✕ Отказать');btn.type='button';btn.dataset.deny=String(r.id);btn.disabled=true;
  actions.appendChild(btn);
  actions.appendChild(node('span','rq-note','Без комментария кнопка недоступна. Текст увидит ученик в разделе «Мои заявки».'));
  panel.appendChild(actions);
  return panel;
}
function loadCars(cb){
  if(rqState.cars){cb();return}
  apiGet('/api/instructor/cars',function(res){
    rqState.cars=res?(res.cars||res.vehicles||[]):null;
    cb();
  });
}
function openRequests(){
  loadCars(function(){
    apiGet('/api/instructor/requests',function(res){
      rqState.list=res?(res.requests||res.items||[]):[];
      renderRequests();
    });
  });
}
function bindRequests(){
  // селекторы скоуплены #rq-list: атрибуты data-accept/denypanel/deny/confirm
  // используются и разделом «Бронирования» (спринт 5) — без скоупа
  // обработчики навесились бы на чужие кнопки
  document.querySelectorAll('#rq-list [data-accept]').forEach(function(b){b.addEventListener('click',function(){
    rqState.open=rqState.open==='accept-'+b.dataset.accept?null:'accept-'+b.dataset.accept;
    renderRequests();
  })});
  document.querySelectorAll('#rq-list [data-denypanel]').forEach(function(b){b.addEventListener('click',function(){
    rqState.open=rqState.open==='deny-'+b.dataset.denypanel?null:'deny-'+b.dataset.denypanel;
    renderRequests();
    var ta=el('rq-ta-'+b.dataset.denypanel);if(ta)ta.focus();
  })});
  document.querySelectorAll('#rq-list [data-deny]').forEach(function(b){
    var id=b.dataset.deny,ta=el('rq-ta-'+id);
    ta.addEventListener('input',function(){b.disabled=!ta.value.trim()}); // FR-38: без комментария заблокировано
    b.addEventListener('click',function(){
      if(!ta.value.trim())return;
      apiSend('POST','/api/instructor/requests/'+id+'/deny',{comment:ta.value.trim()},function(res){
        if(res.status===200&&res.data&&res.data.ok){
          rqState.open=null;openRequests();
          toast('Заявка отклонена. Ученик увидит ваш комментарий в «Моих заявках».');
        }else{
          toast((res.data&&res.data.error)||'Не удалось отклонить заявку');
        }
      });
    });
  });
  document.querySelectorAll('#rq-list [data-confirm]').forEach(function(b){b.addEventListener('click',function(){
    var id=b.dataset.confirm;
    var radio=document.querySelector('input[name="car-'+id+'"]:checked');
    if(!radio){toast('Выберите автомобиль');return}
    apiSend('POST','/api/instructor/requests/'+id+'/accept',{car_id:+radio.value},function(res){
      if(res.status===200&&res.data&&res.data.ok){
        rqState.open=null;openRequests();loadSummary();countNewRequests();
        toast('Заявка принята. Остальные активные заявки ученика закроются автоматически.');
      }else if(res.status===409){
        toast((res.data&&res.data.error)||'Заведите автомобиль, чтобы принять ученика');
      }else{
        toast((res.data&&res.data.error)||'Не удалось принять заявку');
      }
    });
  })});
  document.querySelectorAll('#rq-filters button').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('#rq-filters button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');rqState.filter=b.dataset.f;rqState.open=null;renderRequests();
  })});
}

// --- Раздел «Мои автомобили» (BUG-047: JS перенесен из frontend/my-cars.html;
// Спринт 5 (change add-booking-docs): новый контракт — 5 фото-слотов ракурсов
// + СТС (multipart sts_photo обязателен при создании), комплектность,
// миниатюры после выбора/загрузки (баг 5.2), ошибки 413/415/422 тостами.
// CRUD /api/instructor/cars, PATCH-редактирование, удаление с подтверждением.
// Пользовательские строки — только через textContent (stored XSS запрещен)) ---
var mcTransLabel={manual:'механика',automatic:'автомат'};
// Ракурсы — контракт backend/instructor_cars.py (ANGLES) + подписи мокапа
var mcAngles=[['front','Спереди'],['rear','Сзади'],['left','Слева'],['right','Справа'],['interior','Салон']];
// Спринт 7 (change add-car-validation-booking): статусы валидации
// (мокап my-cars-s7): «Черновик» серый / «На валидации» жёлтый / «Проверено»
// зелёный + галочка (:before в CSS)
var mcSTATUS={draft:['Черновик','st-draft'],validating:['На валидации','st-val'],validated:['Проверено','st-ok']};
var mcCars=[],mcEditing=null,mcDeleting=null,mcTransVal='manual';
var mcStsFile=null;     // выбранный в модалке файл СТС (multipart sts_photo)
var mcObjectUrls={};    // URL эндпоинта -> blob URL (фото выдаются только с сессией — обычный <img src> получит 401)
var mcView={};          // car_id -> текущий ракурс главного снимка карточки
var mcGal={car:null,bigKey:'front'}; // модалка-галерея: авто + открытый кадр ('front'…'interior'|'sts')
// Загрузка авторизованного изображения в blob (X-Session-Token); кэш по URL
function mcLoadImg(url,img){
  if(!url)return;
  if(mcObjectUrls[url]){img.src=mcObjectUrls[url];return}
  var xhr=new XMLHttpRequest();
  xhr.open('GET',url);
  xhr.setRequestHeader('X-Session-Token',token||'');
  xhr.responseType='blob';
  xhr.onload=function(){
    if(xhr.status!==200)return; // 404 «не загружено» — плейсхолдер, не битая картинка
    mcObjectUrls[url]=URL.createObjectURL(xhr.response);
    img.src=mcObjectUrls[url];
  };
  xhr.send();
}
function openCars(){
  apiGet('/api/instructor/cars',function(d){
    if(!d){toast('Не удалось загрузить автомобили');return}
    mcCars=d.cars||[];
    mcRender();
    if(mcGal.car){ // модалка галереи открыта — обновить её данные тем же авто
      var fresh=mcCars.find(function(x){return x.id===mcGal.car.id});
      if(fresh)mcRenderGalCar(fresh);else mcCloseModal('m-car');
    }
  });
}
// Комплектность (ОВ-1): 5 ракурсов + СТС; недостающее — по-русски
function mcMissing(c){
  var miss=[];
  var photos=c.photos||{};
  mcAngles.forEach(function(a){if(!photos[a[0]])miss.push(a[1].toLowerCase())});
  if(!c.has_sts)miss.push('СТС');
  return miss;
}
function mcLoadedAngles(c){
  var photos=c.photos||{};
  return mcAngles.filter(function(a){return photos[a[0]]});
}
// ── главный снимок карточки: выбранный ракурс + стрелки ‹ › поверх фото
//    (стрелки листают только ЗАГРУЖЕННЫЕ ракурсы, клик не открывает модалку) ──
function mcCycleView(c,dir){
  var avail=mcLoadedAngles(c);
  if(avail.length<2)return;
  var i=0;avail.forEach(function(a,ix){if(a[0]===mcView[c.id])i=ix});
  mcView[c.id]=avail[(i+dir+avail.length)%avail.length][0];
  mcRender();
}
function mcRender(){
  var box=el('cars');box.innerHTML='';
  el('empty').style.display=mcCars.length?'none':'block';
  el('count').textContent='Автомобилей: '+mcCars.length;
  mcCars.forEach(function(c){
    var miss=mcMissing(c),full=!miss.length;
    var photos=c.photos||{};
    var loaded=mcLoadedAngles(c);
    if(!mcView[c.id]||!photos[mcView[c.id]])mcView[c.id]=loaded.length?loaded[0][0]:null;
    var st=mcSTATUS[c.status]||mcSTATUS.draft;
    var art=node('article','car');
    art.dataset.carId=String(c.id);
    art.style.cursor='pointer';
    var head=node('div','car-head');
    var hd=node('div');
    hd.appendChild(node('b','title',(c.brand||'')+' '+(c.model||'')));
    hd.appendChild(node('small','sub',(c.year||'')+' год выпуска'));
    head.appendChild(hd);
    head.appendChild(node('span','status '+st[1],st[0]));
    art.appendChild(head);
    var meta=node('div','meta');
    meta.appendChild(node('span','pill green',mcTransLabel[c.transmission]||c.transmission||''));
    meta.appendChild(node('span','pill plate',c.plate||''));
    art.appendChild(meta);
    // главный снимок: текущий ракурс (миниатюра из авторизованного эндпоинта —
    // фикс 5.2) + стрелки ‹ › поверх фото с полупрозрачным фоном
    var shot=node('div','shot');
    if(mcView[c.id]){
      var img=document.createElement('img');img.alt=mcView[c.id];
      shot.appendChild(img);mcLoadImg(photos[mcView[c.id]],img);
    }else{
      shot.appendChild(node('span','ph','🚗'));
    }
    if(loaded.length>1){
      var prev=node('button','navarrow prev','‹');prev.type='button';
      prev.title='Предыдущий ракурс';prev.setAttribute('aria-label','Предыдущий ракурс');
      prev.addEventListener('click',function(e){e.stopPropagation();mcCycleView(c,-1)});
      var next=node('button','navarrow next','›');next.type='button';
      next.title='Следующий ракурс';next.setAttribute('aria-label','Следующий ракурс');
      next.addEventListener('click',function(e){e.stopPropagation();mcCycleView(c,1)});
      shot.appendChild(prev);shot.appendChild(next);
    }
    shot.appendChild(node('span','hintview','⤢ Открыть карточку'));
    art.appendChild(shot);
    // комплектность: полоса 5 ракурсов + СТС-точка + «Не хватает: …»
    var compl=node('div','compl');
    var lab=node('div','compl-lab');
    lab.appendChild(node('span',null,'Комплектность: '+loaded.length+'/5 ракурсов'+(c.has_sts?' · СТС ✓':' · СТС —')));
    lab.appendChild(node('span',null,full?'полный':'не полный'));
    compl.appendChild(lab);
    var bar=node('div','compl-bar');
    mcAngles.forEach(function(a){bar.appendChild(node('i',photos[a[0]]?'f':''))});
    bar.appendChild(node('span','sts-dot'+(c.has_sts?' f':'')));
    compl.appendChild(bar);
    if(!full){
      var m=node('div','missing');
      m.appendChild(document.createTextNode('Не хватает: '));
      var mb=node('b',null,miss.join(', '));
      m.appendChild(mb);
      m.appendChild(document.createTextNode(' — досылайте в карточке авто.'));
      compl.appendChild(m);
    }
    art.appendChild(compl);
    var act=node('div','cactions');
    var edit=node('button','edit','Редактировать');edit.type='button';
    edit.addEventListener('click',function(e){e.stopPropagation();mcOpenAdd(c)});
    var del=node('button','del','Удалить');del.type='button';
    del.addEventListener('click',function(e){e.stopPropagation();mcOpenDelete(c)});
    act.appendChild(edit);act.appendChild(del);
    art.appendChild(act);
    // FR-63: клик по авто — модалка-галерея (инфо + ракурсы + СТС + статусы)
    art.addEventListener('click',function(){mcOpenCar(c)});
    box.appendChild(art);
  });
}
// ── модалка добавления/редактирования ──
function mcOpenAdd(c){
  mcEditing=c||null;
  el('add-title').textContent=c?'Редактирование автомобиля':'Новый автомобиль';
  el('add-sub').textContent=c?'Поля и СТС сохраняются; ракурсы меняются в карточке':'Появится в списке и в выборе авто при принятии заявки. Без фото СТС создать нельзя.';
  // СТС меняется только при создании (замена контрактом не предусмотрена)
  el('sts-field').style.display=c?'none':'flex';
  el('f-brand').value=c?(c.brand||''):'';
  el('f-model').value=c?(c.model||''):'';
  el('f-year').value=c?(c.year||''):'';
  el('f-plate').value=c?(c.plate||''):'';
  mcSetTrans(c?(c.transmission||'manual'):'manual');
  mcResetUpload();
  mcValidate();
  el('m-add').classList.add('open');document.body.style.overflow='hidden';
  el('f-brand').focus();
}
function mcSetTrans(v){mcTransVal=v;document.querySelectorAll('#f-trans button').forEach(function(b){b.classList.toggle('on',b.dataset.v===v)})}
document.querySelectorAll('#f-trans button').forEach(function(b){b.addEventListener('click',function(){mcSetTrans(b.dataset.v)})});
function mcCloseModal(id){el(id).classList.remove('open');document.body.style.overflow=''}
document.querySelectorAll('#sec-cars [data-close]').forEach(function(b){b.addEventListener('click',function(){mcCloseModal(b.dataset.close)})});
el('m-del').addEventListener('click',function(e){if(e.target===this)mcCloseModal('m-del')});
el('m-add').addEventListener('click',function(e){if(e.target===this)mcCloseModal('m-add')});
el('m-car').addEventListener('click',function(e){if(e.target===this)mcCloseModal('m-car')});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){mcCloseModal('m-add');mcCloseModal('m-del');mcCloseModal('m-car')}});
// валидация формы (поля * обязательны; бэкенд вернёт 422 по конкретному полю)
['f-brand','f-model','f-year','f-plate'].forEach(function(id){
  el(id).addEventListener('input',mcValidate);
});
function mcValidate(){
  var ok=el('f-brand').value.trim()
        &&el('f-model').value.trim()
        &&el('f-year').value.trim()
        &&el('f-plate').value.trim()
        // FR-44: при создании СТС обязателен — кнопка заблокирована без файла
        &&(mcEditing||mcStsFile);
  el('save-car').disabled=!ok;
}
// ── загрузка файла с прогрессом (модалка СТС / слот ракурса) ──
var upThumbUrl=null;
function mcResetUpload(){
  var p=el('up-prog'),l=el('up-lab');
  p.classList.remove('on');l.classList.remove('on');p.firstElementChild.style.width='0';
  l.textContent='Загрузка… 0%';
  el('f-sts').value='';
  mcStsFile=null;
  // BUG-048 (3): миниатюра и ошибка сбрасываются при открытии/закрытии модалки
  el('up-zone').classList.remove('has-thumb');
  if(upThumbUrl){URL.revokeObjectURL(upThumbUrl);upThumbUrl=null}
  el('up-thumb').removeAttribute('src');
  var errBox=el('up-photo-err');errBox.textContent='';errBox.classList.remove('show');
}
function mcShowPhotoError(msg){
  var errBox=el('up-photo-err');
  errBox.textContent=msg;errBox.classList.add('show');toast(msg);
}
// Клиентская предварительная проверка (как на бэкенде): JPEG/PNG, <=5 МБ.
// Неверный формат/размер — понятное сообщение, файл не отправляется.
function mcValidatePhoto(file){
  if(file.size>5*1024*1024)return 'Файл: изображение больше 5 МБ';
  if(file.type!=='image/jpeg'&&file.type!=='image/png')return 'Фото: допустимы только изображения JPEG или PNG';
  return null;
}
// multipart-загрузка с прогрессом; 413 (размер) / 415 (формат) / 422 — тосты
function mcUpload(path,fieldName,file,bar,lab,onDone){
  var fd=new FormData();fd.append(fieldName,file);
  var xhr=new XMLHttpRequest();
  xhr.open('POST',path);
  xhr.setRequestHeader('X-Session-Token',token||'');
  xhr.upload.onprogress=function(e){
    if(!e.lengthComputable)return;
    var v=Math.round(e.loaded/e.total*100);
    if(bar)bar.style.width=v+'%';
    if(lab)lab.textContent='Загрузка… '+v+'%';
  };
  xhr.onload=function(){
    if(xhr.status===200){
      if(lab)lab.textContent='Фото загружено ✓';
      onDone(null);
    }else{
      var msg='';
      try{var d=JSON.parse(xhr.responseText);if(d&&d.error)msg=d.error}catch(e){}
      if(xhr.status===413)msg=msg||'Файл: изображение больше 5 МБ';
      if(xhr.status===415)msg=msg||'Фото: допустимы только изображения JPEG или PNG';
      toast(msg||'Не удалось загрузить фото ('+xhr.status+')');
      onDone(msg||'error');
    }
  };
  xhr.onerror=function(){toast('Не удалось загрузить фото');onDone('network')};
  xhr.send(fd);
}
// СТС в модалке: миниатюра до отправки (BUG-048), ошибки — у поля + тост
el('f-sts').addEventListener('change',function(){
  var zone=el('up-zone'),thumb=el('up-thumb');
  zone.classList.remove('has-thumb');
  if(upThumbUrl){URL.revokeObjectURL(upThumbUrl);upThumbUrl=null}
  var errBox=el('up-photo-err');errBox.textContent='';errBox.classList.remove('show');
  if(!this.files.length)return;
  var file=this.files[0];
  var err=mcValidatePhoto(file);
  if(err){ // неверный формат/размер: сообщение, файл не выбирается
    this.value='';mcStsFile=null;mcShowPhotoError(err);return;
  }
  mcStsFile=file;
  // BUG-048 (3): мгновенная миниатюра вместо зоны загрузки — до отправки
  upThumbUrl=URL.createObjectURL(file);
  thumb.src=upThumbUrl;
  zone.classList.add('has-thumb');
  var p=el('up-prog'),l=el('up-lab');
  p.classList.add('on');l.classList.add('on');
  p.firstElementChild.style.width='100%';
  l.textContent='Файл выбран: '+mcStsFile.name+' — сохраните автомобиль';
  mcValidate();
});
// ── Спринт 7: модалка-галерея авто (мокап my-cars-s7, FR-63/64/65).
// Большое окно: клик — загрузка/замена фото открытого ракурса или СТС
// (POST /api/instructor/cars/{id}/photo/{angle}, angle ∈ 5 ракурсов + 'sts');
// миниатюры переключают кадр; стрелки ‹ › — цикл по 5 ракурсам + СТС,
// клик по стрелке НЕ открывает выбор файла. Статусные действия:
// «Отправить на валидацию» (draft→validating) / «Вернуть в черновик»
// (validating→draft, ОВ-3). У validated-авто замена фото/СТС возвращает
// его на валидацию — validated→validating на бэкенде (MAJ-1 review-001).──
function mcGalKeys(){return mcAngles.map(function(a){return a[0]}).concat(['sts'])}
function mcGalLoaded(c,key){
  if(key==='sts')return !!c.has_sts;
  return !!(c.photos&&c.photos[key]);
}
function mcGalLabel(key){
  if(key==='sts')return 'СТС — свидетельство о регистрации';
  return mcAngles.filter(function(a){return a[0]===key})[0][1];
}
function mcGalUrl(c,key){
  if(key==='sts')return c.sts_url||null;
  return (c.photos&&c.photos[key])||null;
}
function mcOpenCar(c,keepKey){
  mcGal.car=c;
  // открытый кадр: сохраняем (после дозагрузки), иначе первый загруженный ракурс
  var keys=mcGalKeys();
  if(!(keepKey&&keys.indexOf(keepKey)!==-1&&mcGalLoaded(c,keepKey))){
    var first=mcLoadedAngles(c);
    mcGal.bigKey=first.length?first[0][0]:'front';
  }else{mcGal.bigKey=keepKey}
  mcRenderGalCar(c);
}
// перерисовка модалки по (свежим) данным авто
function mcRenderGalCar(c){
  mcGal.car=c;
  var st=mcSTATUS[c.status]||mcSTATUS.draft;
  el('mc-title').textContent=(c.brand||'')+' '+(c.model||'');
  el('mc-sub').textContent='Госномер '+(c.plate||'—')+' · '+(c.year||'—')+' · '+(mcTransLabel[c.transmission]||c.transmission||'—');
  var stEl=el('mc-status');stEl.className='status '+st[1];stEl.textContent=st[0];
  // информация
  var info=el('mc-info');info.innerHTML='';
  [['Марка / модель',(c.brand||'—')+' '+(c.model||'—')],
   ['Год выпуска',c.year||'—'],
   ['Коробка передач',mcTransLabel[c.transmission]||c.transmission||'—'],
   ['Госномер',c.plate||'—'],
   ['Статус',st[0]],
   ['Создан',((c.created_at||'').split(' ')[0]||'—')]].forEach(function(r){
    var row=node('div','gal-row');
    row.appendChild(node('span',null,r[0]));
    row.appendChild(node('b',null,String(r[1])));
    info.appendChild(row);
  });
  mcRenderGal();
  mcRenderGalCompl();
  mcRenderGalActs();
  el('m-car').classList.add('open');document.body.style.overflow='hidden';
}
function mcRenderGal(){
  var c=mcGal.car;if(!c)return;
  var big=el('mc-big');big.innerHTML='';
  var url=mcGalUrl(c,mcGal.bigKey);
  if(url){
    var img=document.createElement('img');img.alt=mcGalLabel(mcGal.bigKey);
    big.appendChild(img);mcLoadImg(url,img);
  }else{
    big.appendChild(node('span','ph',mcGal.bigKey==='sts'?'🪪':'🚗'));
  }
  big.appendChild(node('span','up-hint',mcGalLabel(mcGal.bigKey)+' · клик — '+(url?'заменить фото':'загрузить фото')));
  var prog=node('div','prog');prog.id='mc-prog';prog.appendChild(node('i'));big.appendChild(prog);
  // стрелки: цикл по 5 ракурсам + СТС, полупрозрачный фон, поверх кадра
  var prev=node('button','navarrow prev','‹');prev.type='button';
  prev.title='Предыдущий кадр';prev.setAttribute('aria-label','Предыдущий кадр');
  prev.addEventListener('click',function(e){e.stopPropagation();mcNavGal(-1)});
  var next=node('button','navarrow next','›');next.type='button';
  next.title='Следующий кадр';next.setAttribute('aria-label','Следующий кадр');
  next.addEventListener('click',function(e){e.stopPropagation();mcNavGal(1)});
  big.appendChild(prev);big.appendChild(next);
  big.onclick=function(){mcPickGal(c,mcGal.bigKey,big)};
  // миниатюры: 5 ракурсов + СТС; загружен — blob-миниатюра, нет — плейсхолдер «＋»
  var tb=el('mc-thumbs');tb.innerHTML='';
  mcGalKeys().forEach(function(k){
    var b=node('button','gal-thumb'+(k==='sts'?' sts-t':'')+(k===mcGal.bigKey?' sel':''));
    b.type='button';b.dataset.galkey=k;
    b.title=mcGalLabel(k);
    var u=mcGalUrl(c,k);
    if(u){
      var timg=document.createElement('img');timg.alt=mcGalLabel(k);
      b.appendChild(timg);mcLoadImg(u,timg);
    }else{
      b.appendChild(node('span','no','—'));
      b.appendChild(node('span','plus','＋'));
    }
    b.appendChild(node('span','tg',k==='sts'?'СТС':mcGalLabel(k)));
    b.addEventListener('click',function(){mcGal.bigKey=k;mcRenderGal()});
    tb.appendChild(b);
  });
}
function mcNavGal(dir){
  var keys=mcGalKeys();
  var i=keys.indexOf(mcGal.bigKey);
  mcGal.bigKey=keys[(i+dir+keys.length)%keys.length];
  mcRenderGal();
}
// клик по большому окну → выбор файла для текущего кадра (ракурс или СТС)
var mcGalTarget=null;
function mcPickGal(car,key,bigEl){
  // снимок статуса ДО загрузки: validated → замена вернет авто на валидацию
  mcGalTarget={carId:car.id,angle:key,big:bigEl,wasValidated:car.status==='validated'};
  el('gal-file').value='';
  el('gal-file').click();
}
// сброс blob-кэша фото авто (NIT-1: revoke вместо роста памяти; заодно
// после замены фото не показывается устаревший blob по тому же URL)
function mcPurgeCarUrls(carId){
  var pfx='/api/instructor/cars/'+carId+'/';
  Object.keys(mcObjectUrls).forEach(function(u){
    if(u.indexOf(pfx)===0){URL.revokeObjectURL(mcObjectUrls[u]);delete mcObjectUrls[u]}
  });
}
el('gal-file').addEventListener('change',function(){
  if(!mcGalTarget||!this.files.length)return;
  var t=mcGalTarget;mcGalTarget=null;
  var file=this.files[0];
  var err=mcValidatePhoto(file);
  if(err){mcShowPhotoError(err);return}
  var prog=el('mc-prog'),bar=prog.firstElementChild;
  var big=t.big;big.classList.add('busy');prog.classList.add('on');
  mcUpload('/api/instructor/cars/'+t.carId+'/photo/'+t.angle,'photo',file,bar,null,function(e){
    big.classList.remove('busy');prog.classList.remove('on');bar.style.width='0';
    if(e)return;
    mcPurgeCarUrls(t.carId);
    // перезагрузка карточек и модалки: кадр стал загруженным, комплектность
    // пересчитана; у validated-авто бэкенд вернул статус validating
    // (MAJ-1) — бейдж сменится на желтый «На валидации»
    openCars();
    if(t.wasValidated){
      // MAJ-1 (решение ПМ): честный тост о повторной валидации
      toast('Фото заменены — авто отправлено на повторную валидацию. Подтвердите заново: до этого авто скрыто из каталога новых учеников.');
    }else{
      toast(t.angle==='sts'
        ?'Фото СТС сохранено. Оно появится и в «Моих документах»; статус авто не изменился.'
        :'Фото ракурса сохранено. Остальные ракурсы не тронуты (замена одного — точечная).');
    }
  });
});
function mcRenderGalCompl(){
  var c=mcGal.car;if(!c)return;
  var miss=mcMissing(c),full=!miss.length;
  var loaded=mcLoadedAngles(c);
  el('mc-compl-lab').textContent=loaded.length+'/5 ракурсов · '+(c.has_sts?'СТС загружено':'СТС не загружено');
  var badge=el('mc-compl-badge');
  badge.className='status '+(full?'st-ok':'st-val');
  badge.textContent=full?'Комплект полный':'Комплект неполный';
  var bar=el('mc-bar');bar.innerHTML='';
  var photos=c.photos||{};
  mcAngles.forEach(function(a){bar.appendChild(node('i',photos[a[0]]?'f':''))});
  bar.appendChild(node('span','sts-dot'+(c.has_sts?' f':'')));
  var m=el('mc-missing');m.innerHTML='';
  if(full){m.textContent='Всё на месте. Авто готово к подтверждению администратором.';}
  else{
    m.appendChild(document.createTextNode('Не хватает: '));
    m.appendChild(node('b',null,miss.join(', ')));
  }
}
// для ОВ-4/мокапа: условие отправки — любые 3 ракурса + СТС
function mcValMissing(c){
  var miss=[],loaded=mcLoadedAngles(c);
  if(loaded.length<3)miss.push('фото: '+loaded.length+' из 3 необходимых');
  if(!c.has_sts)miss.push('СТС');
  return miss;
}
function mcRenderGalActs(){
  var c=mcGal.car,box=el('mc-acts'),note=el('mc-note');
  box.innerHTML='';note.classList.remove('ok');note.innerHTML='';
  function actBtn(cls,label,fn,dis){
    var b=node('button','act-btn'+(cls?' '+cls:''),label);
    b.type='button';b.disabled=!!dis;b.addEventListener('click',fn);
    box.appendChild(b);return b;
  }
  if(c.status==='draft'){
    var vm=mcValMissing(c);
    var btn=actBtn('primary','Отправить на валидацию',function(){
      btn.disabled=true;
      apiSend('POST','/api/instructor/cars/'+c.id+'/submit',{},function(res){
        if(res.status===401||res.status===403)return;
        if(res.status===200&&res.data&&res.data.ok){
          toast('Авто отправлено на валидацию. Администратор увидит его в разделе «Автомобили». До подтверждения авто скрыто из каталога новых учеников.');
          openCars();
        }else{
          btn.disabled=false;
          toast((res.data&&res.data.error)||'Не удалось отправить на валидацию');
        }
      });
    },!!vm.length);
    var ph=actBtn('','Дослать фото/СТС',function(){
      var firstMissing=mcGalKeys().filter(function(k){return !mcGalLoaded(c,k)})[0];
      if(firstMissing){mcGal.bigKey=firstMissing;mcRenderGal()}
    });
    note.innerHTML=vm.length
      ?'Отправка заблокирована, пока не хватает: <b>'+vm.join(', ')+'</b>. Загрузите недостающее кликом по большому окну или миниатюре — кнопка станет активной. Требование валидации: любые 3 фото ракурсов + СТС.'
      :'Требование выполнено: любые 3 фото + СТС. После отправки авто получит статус «На валидации» и будет скрыто из каталога новых учеников до подтверждения администратором.';
  }else if(c.status==='validating'){
    // ОВ-3: отзыв с валидации разрешён в любой момент
    actBtn('warn','Вернуть в черновик',function(){
      apiSend('POST','/api/instructor/cars/'+c.id+'/withdraw',{},function(res){
        if(res.status===401||res.status===403)return;
        if(res.status===200&&res.data&&res.data.ok){
          toast('Авто возвращено в черновик — можно дослать фото или СТС и отправить на валидацию снова.');
          openCars();
        }else{
          toast((res.data&&res.data.error)||'Не удалось вернуть в черновик');
        }
      });
    });
    note.innerHTML='Авто на валидации у администратора: подтверждение — только его действие. Сейчас авто показывается вашим принятым ученикам с жёлтым бейджем <b>«Не проверено»</b>, из каталога для новых — скрыто. Вернуть в черновик можно в любой момент.';
  }else{
    // MAJ-1 (review-001, решение ПМ): честная копия — замена фото/СТС
    // у validated-авто вернет его на валидацию (бэкенд переводит
    // validated → validating при загрузке), бейдж станет желтым
    // «На валидации» до повторного подтверждения администратором.
    note.classList.add('ok');
    note.innerHTML='<b>Проверено администратором.</b> Авто с зелёной галочкой видно новым ученикам в каталоге. Изменение фото или СТС вернет авто на валидацию: бейдж сменится на жёлтый «На валидации», а подтверждение придется получить заново.';
  }
}
// сохранить (POST multipart с sts_photo / PATCH JSON-поля)
el('save-car').addEventListener('click',function(){
  var data={
    brand:el('f-brand').value.trim(),
    model:el('f-model').value.trim(),
    year:+el('f-year').value,
    plate:el('f-plate').value.trim(),
    transmission:mcTransVal
  };
  var btn=this;btn.disabled=true;
  function finish(carId){
    btn.disabled=false;
    mcCloseModal('m-add');openCars();
    if(carId)toast('Автомобиль создан. Теперь загрузите 5 фото ракурсов в его карточке.');
    else toast('Изменения сохранены.');
  }
  if(mcEditing){
    apiSend('PATCH','/api/instructor/cars/'+mcEditing.id,data,function(res){
      if(res.status===401||res.status===403){btn.disabled=false;return}
      if(!res.data||!res.data.ok){btn.disabled=false;toast((res.data&&res.data.error)||'Не удалось сохранить');return}
      finish(null);
    });
  }else{
    // FR-44: multipart с обязательным sts_photo; без файла авто НЕ создается
    var fd=new FormData();
    Object.keys(data).forEach(function(k){fd.append(k,String(data[k]))});
    fd.append('sts_photo',mcStsFile);
    var xhr=new XMLHttpRequest();
    xhr.open('POST','/api/instructor/cars');
    xhr.setRequestHeader('X-Session-Token',token||'');
    var p=el('up-prog'),bar=p.firstElementChild,l=el('up-lab');
    xhr.upload.onprogress=function(e){
      if(!e.lengthComputable)return;
      var v=Math.round(e.loaded/e.total*100);
      bar.style.width=v+'%';l.textContent='Сохранение… '+v+'%';
    };
    xhr.onload=function(){
      btn.disabled=false;
      var d=null;try{d=JSON.parse(xhr.responseText)}catch(e){}
      if(xhr.status===200&&d&&d.ok){finish(d.car_id);return}
      // 422 «загрузите фото СТС» / валидация полей — внятный тост, авто не создан
      toast((d&&d.error)||'Не удалось добавить автомобиль');
    };
    xhr.onerror=function(){btn.disabled=false;toast('Не удалось добавить автомобиль')};
    xhr.send(fd);
  }
});
// ── удаление с подтверждением (DELETE /api/instructor/cars/{id}) ──
function mcOpenDelete(c){
  mcDeleting=c;
  el('del-what').textContent=(c.brand||'')+' '+(c.model||'')+' · '+(c.plate||'');
  el('m-del').classList.add('open');document.body.style.overflow='hidden';
}
el('del-cancel').addEventListener('click',function(){mcCloseModal('m-del')});
el('del-confirm').addEventListener('click',function(){
  if(!mcDeleting)return;
  var id=mcDeleting.id;
  apiSend('DELETE','/api/instructor/cars/'+id,null,function(res){
    mcCloseModal('m-del');
    if(res.status===401||res.status===403)return;
    if(!res.data||!res.data.ok){toast((res.data&&res.data.error)||'Не удалось удалить автомобиль');return}
    mcPurgeCarUrls(id); // NIT-1: revoke blob-URL всех фото удаляемого авто
    toast('Автомобиль удалён. car_id у принятых заявок сброшен, связь с учениками сохранена (ОВ-3).');
    openCars();
  });
});
el('open-add').addEventListener('click',function(){mcOpenAdd(null)});

// --- Раздел «Мои документы» (мокап my-documents.html, FR-45):
// GET /api/instructor/documents → ВУ (анкета; без ВУ — пустое состояние
// с подсказкой) + СТС по каждому авто; просмотр — GET
// /api/instructor/documents/{doc_id}/file, только владелец ---
function mcOpenView(doc){
  el('view-title').textContent=doc.title;
  el('view-sub').textContent=(doc.sub||'')+(doc.doc_id?(' · doc_id '+doc.doc_id):'');
  var full=el('view-full');full.innerHTML='';
  var img=document.createElement('img');img.alt=doc.title;
  mcLoadImg(doc.url,img);
  full.appendChild(img);
  el('m-view').classList.add('open');document.body.style.overflow='hidden';
}
function mcCloseView(){el('m-view').classList.remove('open');document.body.style.overflow=''}
el('view-close').addEventListener('click',mcCloseView);
el('m-view').addEventListener('click',function(e){if(e.target===this)mcCloseView()});
function docCardNode(d){
  var card=document.createElement('button');
  card.type='button';card.className='doc';card.dataset.docId=d.doc_id;
  var thumb=node('span','thumb');
  var img=document.createElement('img');img.alt=d.title;
  thumb.appendChild(img);
  thumb.appendChild(node('span','zoom','⤢ Смотреть'));
  mcLoadImg('/api/instructor/documents/'+d.doc_id+'/file',img);
  card.appendChild(thumb);
  card.appendChild(node('b','name',d.title));
  var meta=node('small','meta');
  meta.appendChild(document.createTextNode(d.meta||''));
  meta.appendChild(document.createElement('br'));
  meta.appendChild(document.createTextNode('загружено '+((d.uploaded_at||'').split(' ')[0]||'—')));
  card.appendChild(meta);
  card.appendChild(node('span','pill'+(d.type==='car_sts'?'':' warn'),
    d.type==='car_sts'?'привязан к авто':'основной документ'));
  card.addEventListener('click',function(){mcOpenView({
    title:d.title,doc_id:d.doc_id,url:'/api/instructor/documents/'+d.doc_id+'/file',
    sub:d.meta||''})});
  return card;
}
function openDocs(){
  apiGet('/api/instructor/documents',function(res){
    if(!res){toast('Не удалось загрузить документы');return}
    var docs=res.documents||[];
    var lic=docs.filter(function(d){return d.type==='license'});
    var sts=docs.filter(function(d){return d.type==='car_sts'});
    var licBox=el('lic-docs');licBox.innerHTML='';
    lic.forEach(function(d){
      var meta=[d.license_number?'ВУ № '+d.license_number:''];
      d.meta=meta.filter(Boolean).join(' · ');
      licBox.appendChild(docCardNode(d));
    });
    el('lic-n').textContent=lic.length;
    el('no-license').style.display=lic.length?'none':'block';
    if(!lic.length&&res.license_hint)el('no-license-hint').textContent=res.license_hint;
    var stsBox=el('sts-docs');stsBox.innerHTML='';
    sts.forEach(function(d){
      var c=d.car||{};
      d.meta=[c.brand,c.model].filter(Boolean).join(' ')
        +(c.plate?' · '+c.plate:'');
      stsBox.appendChild(docCardNode(d));
    });
    el('sts-count').textContent=sts.length;
  });
}

// --- Раздел «Бронирования» (мокап booking-instructor.html, FR-48/FR-49):
// GET /api/instructor/bookings: новые — Принять (без комментария, ОВ-2) /
// Отклонить (комментарий обязателен — 422, иначе слот не освободится);
// подтверждённые — в сетке недели поверх графика availability ---
var bkState={list:[],filter:'all',open:null,intervals:[]};
var BK_DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
function bkWhen(b){
  return BK_DAYS[b.weekday]||''
    +' '+String(b.lesson_date||'').split('-').reverse().join('.')
    +' · '+(b.start_time||'')+'–'+(b.end_time||'');
}
function bkCarText(c){return c?[c.brand,c.model].filter(Boolean).join(' ')+(c.year?' '+c.year:''):'—'}
function openBookings(){
  apiGet('/api/instructor/availability',function(res){
    bkState.intervals=res?(res.intervals||[]):[];
    apiGet('/api/instructor/bookings',function(res2){
      bkState.list=res2?(res2.bookings||[]):[];
      bkRenderList();
      bkRenderGrid();
      var n=bkState.list.filter(function(b){return b.status==='new'}).length;
      var badge=el('nav-bk-badge');
      badge.style.display=n?'inline-block':'none';
      badge.textContent='+'+n;
    });
  });
}
function bkRenderList(){
  var box=el('bk-list');box.innerHTML='';
  el('bk-new-n').textContent=(function(){
    var n=bkState.list.filter(function(b){return b.status==='new'}).length;
    return n?('·'+n):'';
  })();
  var list=bkState.list.filter(function(b){return bkState.filter==='all'||b.status===bkState.filter});
  if(!list.length){box.innerHTML='<div class="bk-none">Броней в этой категории нет.</div>';return}
  var BK_ST={new:['Новый запрос','st-new'],confirmed:['Подтверждена','st-ok'],rejected:['Отклонена','st-den']};
  list.forEach(function(b){
    var art=node('article','req');
    var top=node('div','req-top');
    top.appendChild(node('span','sic',stuInitials(b.student_full_name)));
    var who=node('div');
    who.appendChild(node('b',null,b.student_full_name||'Ученик'));
    who.appendChild(node('small',null,bkWhen(b)+' · авто: '+bkCarText(b.car)));
    top.appendChild(who);
    var st=BK_ST[b.status]||BK_ST.new;
    top.appendChild(node('span','status '+st[1],st[0]));
    art.appendChild(top);
    if(b.reject_comment){
      var com=node('div','comment'+(b.status==='rejected'?' denied':''));
      com.appendChild(node('span',null,b.status==='rejected'?'Ваш комментарий при отказе':'Комментарий ученика'));
      com.appendChild(document.createTextNode(b.reject_comment));
      art.appendChild(com);
    }
    if(b.decided_at)art.appendChild(node('div','bk-hint','Решение: '+String(b.decided_at).split('.')[0]));
    if(b.status==='new'){
      var actions=node('div','bk-actions');
      var acc=node('button','act accept','✓ Принять');acc.type='button';acc.dataset.confirm=String(b.id);
      var den=node('button','act deny','✕ Отклонить…');den.type='button';den.dataset.denypanel=String(b.id);
      actions.appendChild(acc);actions.appendChild(den);
      art.appendChild(actions);
      // панель отказа: подтверждение заблокировано до непустого комментария
      // (ОВ-2; пустой комментарий на сервере → 422)
      var panel=node('div','deny-panel'+(bkState.open===b.id?' open':''));
      panel.id='bk-deny-'+b.id;
      panel.appendChild(node('h4',null,'Комментарий при отказе — обязателен (без него действие заблокировано)'));
      var ta=document.createElement('textarea');
      ta.id='bk-ta-'+b.id;
      ta.placeholder='Например: в это время пересдача экзамена, выберите другой слот';
      panel.appendChild(ta);
      var da=node('div','deny-actions');
      var dbt=node('button','deny-confirm','✕ Отклонить запрос');dbt.type='button';dbt.dataset.senddeny=String(b.id);dbt.disabled=true;
      da.appendChild(dbt);
      da.appendChild(node('span','deny-note','Комментарий увидит ученик; слот освободится для повторного запроса.'));
      panel.appendChild(da);
      art.appendChild(panel);
    }
    // BUG-049: у подтвержденной брони должна работать отмена
    // (POST …/cancel — эндпоинт guard-статусом 'confirmed')
    if(b.status==='confirmed'){
      var cact=node('div','bk-actions');
      var cbtn=node('button','act deny','✕ Отменить бронь');
      cbtn.type='button';cbtn.dataset.cancel=String(b.id);
      cact.appendChild(cbtn);
      art.appendChild(cact);
    }
    box.appendChild(art);
  });
  bkBindList();
}
function bkBindList(){
  // селекторы скоуплены #bk-list: те же data-атрибуты использует
  // раздел «Запросы учеников» — глобальный querySelectorAll дважды
  // навесил бы обработчики (см. bindRequests)
  document.querySelectorAll('#bk-list [data-confirm]').forEach(function(b){b.addEventListener('click',function(){
    // ОВ-2: подтверждение — БЕЗ комментария, атомарно
    apiSend('POST','/api/instructor/bookings/'+b.dataset.confirm+'/confirm',{},function(res){
      if(res.status===200&&res.data&&res.data.ok){
        toast('Бронь подтверждена. Слот закреплён в календаре и попадёт в «Занятия на сегодня».');
        openBookings();loadSummary();
      }else{
        toast((res.data&&res.data.error)||'Не удалось подтвердить бронь');
      }
    });
  })});
  document.querySelectorAll('#bk-list [data-cancel]').forEach(function(b){b.addEventListener('click',function(){
    // BUG-049: отмена подтвержденной брони — слот освобождается
    apiSend('POST','/api/instructor/bookings/'+b.dataset.cancel+'/cancel',{},function(res){
      if(res.status===200&&res.data&&res.data.ok){
        toast('Бронь отменена. Слот снова свободен — ученик может запросить его повторно.');
        openBookings();loadSummary();
      }else{
        toast((res.data&&res.data.error)||'Не удалось отменить бронь');
      }
    });
  })});
  document.querySelectorAll('#bk-list [data-denypanel]').forEach(function(b){b.addEventListener('click',function(){
    var id=b.dataset.denypanel;
    bkState.open=bkState.open===id?null:id;
    bkRenderList();
    var ta=el('bk-ta-'+id);if(ta)ta.focus();
  })});
  document.querySelectorAll('#bk-list [data-senddeny]').forEach(function(btn){
    var id=btn.dataset.senddeny,ta=el('bk-ta-'+id);
    ta.addEventListener('input',function(){btn.disabled=!ta.value.trim()});
    btn.addEventListener('click',function(){
      if(!ta.value.trim())return;
      apiSend('POST','/api/instructor/bookings/'+id+'/reject',{comment:ta.value.trim()},function(res){
        if(res.status===200&&res.data&&res.data.ok){
          bkState.open=null;
          toast('Запрос отклонён. Слот снова свободен — ученик может запросить его повторно.');
          openBookings();
        }else{
          toast((res.data&&res.data.error)||'Не удалось отклонить запрос');
        }
      });
    });
  });
  document.querySelectorAll('#bk-filters button').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('#bk-filters button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');bkState.filter=b.dataset.f;bkRenderList();
  })});
}
// сетка недели: интервалы графика × дни; поверх — брони (confirmed — синяя
// с учеником, new — жёлтый запрос, клик ведёт к решению)
function bkRenderGrid(){
  var grid=el('bk-grid');grid.innerHTML='';
  var now=nowMoscow();
  var mon=new Date(now);mon.setDate(mon.getDate()-((mon.getDay()+6)%7));
  var todayIdx=(now.getDay()+6)%7;
  var corner=node('span','corner','время');grid.appendChild(corner);
  for(var d=0;d<7;d++){
    var dt=new Date(mon);dt.setDate(mon.getDate()+d);
    var dh=node('div','dh'+(d===todayIdx?' today':''));
    dh.appendChild(node('small',null,BK_DAYS[d]));
    dh.appendChild(node('b',null,String(dt.getDate())));
    grid.appendChild(dh);
  }
  var rows={};
  bkState.intervals.forEach(function(iv){
    rows[iv.start_time+'-'+iv.end_time]={start_time:iv.start_time,end_time:iv.end_time};
  });
  var keys=Object.keys(rows).sort();
  if(!keys.length){
    grid.appendChild(node('div','bk-none','График на неделю пуст — задайте его в разделе «Календарь».'));
    return;
  }
  keys.forEach(function(k){
    var iv=rows[k];
    var tl=node('span','tlabel',iv.start_time.slice(0,5)+'–'+iv.end_time.slice(0,5));
    grid.appendChild(tl);
    for(var d2=0;d2<7;d2++){
      var booking=null;
      bkState.list.forEach(function(b){
        if(b.weekday===d2&&b.start_time===iv.start_time&&b.end_time===iv.end_time
           &&(b.status==='confirmed'||b.status==='new'))booking=b;
      });
      var cell=document.createElement('button');
      cell.type='button';
      if(booking&&booking.status==='confirmed'){
        cell.className='slot booked';
        cell.appendChild(node('small',null,booking.student_full_name||''));
        cell.appendChild(document.createTextNode('подтверждено'));
        cell.title='Подтверждённая бронь: '+(booking.student_full_name||'');
      }else if(booking){
        cell.className='slot reqslot';
        cell.appendChild(node('small',null,booking.student_full_name||''));
        cell.appendChild(document.createTextNode('запрос'));
        cell.title='Новый запрос: '+(booking.student_full_name||'')+' (нажмите для перехода к решению)';
        cell.addEventListener('click',function(){
          bkState.filter='new';
          document.querySelectorAll('#bk-filters button').forEach(function(x){x.classList.toggle('on',x.dataset.f==='new')});
          bkRenderList();
          window.scrollTo({top:0,behavior:'smooth'});
        });
      }else{
        cell.className='slot on';
        cell.textContent='свободно';
        cell.title='В графике — свободно';
      }
      grid.appendChild(cell);
    }
  });
}

// Хвост старых ссылок (BUG-047): /my-cars теперь 301 на этот дашборд с
// хешем — открываем раздел «Мои автомобили» напрямую
if(location.hash==='#/my-cars')navTo('Мои автомобили');
if(location.hash==='#/my-docs')navTo('Мои документы');
if(location.hash==='#/bookings')navTo('Бронирования');

// Выход (FR-22): POST /api/auth/logout -> по любому ответу очистка
// sessionStorage -> редирект на лендинг инструкторов (спринт 3, правка:
// выход из кабинета ведет на /instructors, а не на главную).
function logout(){
fetch('/api/auth/logout',{method:'POST',headers:{'X-Session-Token':token||''}})
  .catch(function(){})
  .then(function(){clearSession();location.href='/instructors'});
}

// onclick-обработчики в HTML — нужна глобальная видимость (ES-модуль
// глобальные объявления не создает)
window.toast = toast;
window.navTo = navTo;
window.changeWeek = changeWeek;
window.logout = logout;
