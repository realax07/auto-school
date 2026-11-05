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
  // Спринт 3: реальный раздел «Календарь»; Спринт 5: «Мои документы»
  // ВНУТРИ дашборда (BUG-047: standalone-страницы запрещены)
  // Спринт 8 (FR-74): «Бронирования» УДАЛЕН — запросы/брони на слотах
  // календаря; #/bookings — редирект в «Календарь» (BUG-047-механика)
  // Спринт 8 (FR-75/ОВ-5): «Мои ученики» — карточки пар + подраздел
  // «Запросы учеников» (отдельного пункта сайдбара больше нет)
  // BUG-051 (Постановка 2026-10-23, п.6/9/10 + Спринт 7): «Мои документы»
  // переименована в «Профиль и документы»; ДЕМО-заглушка «Мой автомобиль»
  // из сайдбара удалена
  var isCal=(name==='Календарь'),isStu=(name==='Мои ученики'),isCars=(name==='Мои автомобили');
  var isDocs=(name==='Профиль и документы');
  var real=isCal||isStu||isCars||isDocs;
  document.querySelectorAll('.day-content').forEach(function(el){el.style.display=real?'none':''});
  document.getElementById('sec-calendar').style.display=isCal?'block':'none';
  document.getElementById('sec-students').style.display=isStu?'block':'none';
  document.getElementById('sec-cars').style.display=isCars?'block':'none';
  document.getElementById('sec-docs').style.display=isDocs?'block':'none';
  if(isCal)openCalendar();
  if(isStu)openStudents();
  if(isCars)openCars();
  if(isDocs)openDocs();
  var pp=document.getElementById('profile-panel');
  if(pp)pp.style.display='none';
  document.getElementById('page-title').textContent=name;
  document.getElementById('crumb').textContent=name;
  document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  // BUG-047: хеш раздела синхронизируется с табом — reload не сбрасывает
  // раздел, старые ссылки #/my-cars открывают его напрямую. Хеши
  // #/my-docs и #/bookings (прежние «Мои документы»/«Бронирования») ведут в
  // переименованный «Профиль и документы» и «Календарь» (BUG-051; FR-74)
  var wantHash=isCars?'#/my-cars':isDocs?'#/my-docs':'';
  if(location.hash!==wantHash){try{history.replaceState(null,'',location.pathname+location.search+(wantHash||''))}catch(e){}}
  if(!real&&name!=='Мой день')toast('Раздел «'+name+'» — демо-данные, следующий экран в концепции кабинета')
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
      // Спринт 8 (ОВ-5): «Запросы учеников» — подраздел «Моих учеников»
      box.querySelectorAll('[data-goto-requests]').forEach(function(g){g.addEventListener('click',function(){stuOpenRequests()})});
    }
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
// клик по СВОБОДНОМУ слоту переключает выбор, «Сохранить график» ->
// PUT /api/instructor/availability (полная замена), при входе восстановление
// через GET. Спринт 8 (FR-74): запросы (new) и брони (confirmed) — РОВНО на
// выбранных слотах; клик по такому слоту — немедленное решение (модалка
// #m-bk), мимо «Сохранить» (наследование ОВ-6 Спринта 7). Раздел
// «Бронирования» удален (его единственную сетку с запросами на слотах
// заменяет календарь); GET /api/instructor/bookings — контракт без изменений.
var CAL_HOURS=[8,10,12,14,16,18,20];
var CAL_DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
var calBuilt=false;
var calSelected={}; // ключ 'weekday-hour'
var calBookings={}; // ключ 'weekday-hour' -> booking (status new/confirmed)
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
      // FR-74: слот с запросом/бронью — решение, а НЕ правка графика
      if(calBookings[k]){bkOpenSlot(calBookings[k]);return}
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
    // полный сброс ячеек: метки запросов/броней (booked/reqslot) тоже
    // снимаются — перезагрузка рисует актуальное состояние (FR-74)
    el('cal-grid').querySelectorAll('.cal-slot').forEach(function(b){
      b.classList.remove('on','booked','reqslot');
      b.innerHTML='';
    });
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
    calLoadBookings(); // метки запросов/броней поверх графика (FR-74)
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

// --- Раздел «Мои ученики» (FR-75/ОВ-5, мокап my-students.html): карточки
// принятых пар по контракту GET /api/instructor/students (задача 9.1):
// ФИО ученика, next_lesson {date,time} — ближайшая ПОДТВЕРЖДЕННАЯ бронь
// (правило MIN-1, локальная дата сервера) / null → «нет»; planned_count
// (confirmed после следующей), completed_count (confirmed в прошлом).
// ТОЛЬКО confirmed (ОВ-5): запросы в счетчиках не участвуют. Бэкенд 9.1
// может отсутствовать в этой ветке — ошибка показывается ЧЕСТНО (блок +
// тост), пустой список не подменяет ошибку. Карточки — createElement +
// textContent (XSS-гигиена, code-review review-001 #1). ---
var stuTab='students';
function stuShowTab(t){
  stuTab=t;
  document.querySelectorAll('#stu-tabs button').forEach(function(b){b.classList.toggle('on',b.dataset.stu===t)});
  el('stu-tab-students').style.display=t==='students'?'block':'none';
  el('stu-tab-requests').style.display=t==='requests'?'block':'none';
}
function stuNextLine(nl){
  if(!nl)return null; // «нет» — подтвержденных броней впереди нет (ОВ-5)
  var d=nl.date?String(nl.date).split('-').reverse().join('.'):'';
  var t=nl.time||'';
  return [d,t].filter(Boolean).join(' · ')||null;
}
function renderStudents(list){
  var box=el('stu-cards');box.innerHTML='';
  el('stu-n').textContent='·'+list.length;
  el('stu-empty').style.display=list.length?'none':'block';
  list.forEach(function(s){
    var fio=s.full_name||s.name||'Ученик';
    var card=node('article','student');
    var top=node('div','st-top');
    top.appendChild(node('span','stu-sic',stuInitials(fio)));
    top.appendChild(node('b',null,fio));
    card.appendChild(top);
    var line=stuNextLine(s.next_lesson);
    var nx=node('div','stu-next'+(line?'':' none'));
    nx.appendChild(node('span',null,'Следующее плановое занятие'));
    nx.appendChild(document.createTextNode(line||'нет — подтверждённых броней впереди не запланировано'));
    card.appendChild(nx);
    var cnts=node('div','stu-counters');
    var c1=node('div','stu-cnt');
    c1.appendChild(node('b',null,String(s.planned_count||0)));
    c1.appendChild(node('span',null,'плановых занятий дальше'));
    var c2=node('div','stu-cnt');
    c2.appendChild(node('b',null,String(s.completed_count||0)));
    c2.appendChild(node('span',null,'проведено'));
    cnts.appendChild(c1);cnts.appendChild(c2);
    card.appendChild(cnts);
    box.appendChild(card);
  });
}
function stuLoadStudents(){
  apiGet('/api/instructor/students',function(res){
    var err=el('stu-error');
    if(!res||!res.ok){
      // честная ошибка (данных нет — в счетчиках и «следующем» нули не рисуем)
      err.textContent='Не удалось загрузить учеников (GET /api/instructor/students): сервис данных недоступен.';
      err.classList.add('show');
      el('stu-empty').style.display='none';
      el('stu-cards').innerHTML='';
      el('stu-n').textContent='·0';
      toast('Не удалось загрузить учеников');
      return;
    }
    err.classList.remove('show');err.textContent='';
    renderStudents(res.students||[]);
  });
}
function openStudents(){
  stuShowTab(stuTab);
  stuLoadStudents();
  openRequests(); // подраздел «Запросы учеников» — контур Спринта 3
}
// виджет главной → открыть подраздел «Запросы учеников» по требованию (ОВ-5)
function stuOpenRequests(){
  navTo('Мои ученики');
  stuShowTab('requests');
}
document.querySelectorAll('#stu-tabs button').forEach(function(b){b.addEventListener('click',function(){stuShowTab(b.dataset.stu)})});

// --- Подраздел «Запросы учеников» «Моих учеников» (FR-37/38/39, контур
// Спринта 3 — БЕЗ ИЗМЕНЕНИЙ): GET /api/instructor/requests;
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
  el('stu-req-n').textContent='·'+newN; // счетчик подраздела «Мои ученики»
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
// BUG-051: «Мои ученики» — подразделы «Ученики» (карточки привязанных) и
// «Запросы учеников» (входящие; бывшая сайдбар-кнопка «Запросы учеников»)
function stuSwitch(sub){
  document.querySelectorAll('#stu-subtabs button').forEach(function(b){b.classList.toggle('on',b.dataset.subtab===sub)});
  var isReq=sub==='requests';
  el('tab-students').style.display=isReq?'none':'block';
  el('tab-requests').style.display=isReq?'block':'none';
  if(isReq)openRequests();
}
document.querySelectorAll('#stu-subtabs button').forEach(function(b){
  b.addEventListener('click',function(){stuSwitch(b.dataset.subtab)});
});
// Карточки привязанных учеников — шейп GET /api/instructor/summary
// (backend/instructor_summary.py: full_name, car, decided_at)
function bindRequests(){
  // селекторы скоуплены #rq-list: те же data-атрибуты раньше использовал
  // и раздел «Бронирования» (спринт 5, удален в Спринте 8 — FR-74) —
  // скоуп оставлен как страховка от двойных обработчиков
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
        rqState.open=null;openRequests();stuLoadStudents();loadSummary();countNewRequests();
        toast('Заявка принята. Ученик появился в списке «Мои ученики»; остальные активные заявки закроются автоматически.');
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
    // BUG-054: значок «⤢ Смотреть фото» — просмотр ДОСТУПНОГО набора фото
    // авто (загруженные ракурсы + СТС по наличию) в полном размере (m-view,
    // со стрелками ‹ › над фото). Клик по самой плитке по-прежнему открывает
    // карточку-галерею (FR-63); при отсутствии фото значок не показывается.
    if(loaded.length||c.has_sts){
      var hint=node('button','hintview','⤢ Смотреть фото');hint.type='button';
      hint.addEventListener('click',function(e){e.stopPropagation();mcOpenViewCarPhotos(c)});
      shot.appendChild(hint);
    }
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
// BUG-054: полный просмотр фото авто из плитки — ДОСТУПНЫЙ набор
// (mcGalKeys по наличию: 5 ракурсов + СТС), названия кадров — mcGalLabel;
// клик по стрелке плитки не открывает карточку (stopPropagation на месте).
function mcOpenViewCarPhotos(c){
  var sub=(c.brand||'')+' '+(c.model||'')+(c.plate?(' · '+c.plate):'');
  var photos=mcGalKeys().filter(function(k){return mcGalLoaded(c,k)}).map(function(k){
    return {url:mcGalUrl(c,k),title:mcGalLabel(k),sub:sub};
  });
  if(!photos.length)return;
  mcOpenView({title:sub,photos:photos});
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
document.addEventListener('keydown',function(e){if(e.key==='Escape'){mcCloseModal('m-add');mcCloseModal('m-del');mcCloseModal('m-car');mcCloseView();bkCloseSlot();docsCloseReplaceSilent()}});
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
  // FR-71 (review-003 #2): рамка sts видна только при has_sts, т.е. клик по
  // большому окну галереи — это ВСЕГДА ЗАМЕНА СТС → тот же диалог замены,
  // что и у явной кнопки «Заменить СТС»; файл выбирается только после
  // подтверждения (doc-file: kind car_sts → /cars/{id}/photo/sts, ОВ-6)
  if(key==='sts'&&car.has_sts){
    docsAskReplace({kind:'car_sts',carId:car.id,
      name:'СТС · '+[car.brand,car.model].filter(Boolean).join(' '),
      wasMissing:false});
    return;
  }
  // снимок состояния ДО загрузки: wasValidated — замена РАКУРСА вернет
  // validated-авто на валидацию (MAJ-1)
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
    // пересчитана; замена СТС идет через doc-file (kind car_sts, FR-71),
    // поэтому здесь только 5 ракурсов (ОВ-6: замена ракурса validated-авто
    // вернет его на валидацию — MAJ-1)
    openCars();
    if(t.wasValidated){
      // MAJ-1 (решение ПМ): честный тост о повторной валидации
      toast('Фото заменены — авто отправлено на повторную валидацию. Подтвердите заново: до этого авто скрыто из каталога новых учеников.');
    }else{
      toast('Фото ракурса сохранено. Остальные ракурсы не тронуты (замена одного — точечная).');
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
  // Спринт 8 (FR-69/FR-71, баг 5.2-СТС): ЯВНАЯ кнопка СТС на созданном
  // авто — дозагрузка отсутствующего / замена действующего (единый
  // эндпоинт POST …/cars/{id}/photo/sts); замена — через диалог FR-71.
  // Класс нейтральный: '.act-btn.warn' зарезервирован за «Вернуть в
  // черновик» (регресс-локаторы TC-UI-030/032). ---
  var stsBtn=actBtn('',c.has_sts?'Заменить СТС':'Загрузить СТС',function(){
    var t={kind:'car_sts',carId:c.id,
      name:'СТС · '+[c.brand,c.model].filter(Boolean).join(' '),
      wasMissing:!c.has_sts};
    if(c.has_sts){docsAskReplace(t)}else{docsStartUpload(t)}
  });
  stsBtn.dataset.stsBtn='1';
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
    // ОВ-6 (Спринт 8): замена СТС НЕ возвращает validated-авто на
    // валидацию — новая версия уходит администратору в раздел «Документы»;
    // повторная валидация — только замена ракурсов (MAJ-1) или submit.
    note.classList.add('ok');
    note.innerHTML='<b>Проверено администратором.</b> Авто с зелёной галочкой видно новым ученикам в каталоге. Замена фото ракурсов вернет авто на валидацию (жёлтый «На валидации» до нового подтверждения); замена СТС статус авто не меняет — новая версия уйдет администратору в раздел «Документы».';
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

// просмотр документа в полном размере (мокап my-documents, FR-45):
// авторизованный файл GET /api/instructor/documents/{doc_id}/file
// BUG-054: mcOpenView принимает (по месту вызова) НАБОР фото — doc.photos
// («Мои автомобили»: загруженные ракурсы + СТС по наличию) или одиночный
// документ («Мои документы», список из 1). Стрелки ‹ › НАД фото (классы
// .navarrow, обе стороны в разметке ВСЕГДА; при одном фото — скрыты),
// листание циклическое; заголовок view-title — название ТЕКУЩЕГО фото;
// клик по стрелке окно не закрывает; Esc закрывает (общий keydown-контур
// модалок дашборда, mcCloseView).
var mcViewPhotos=[],mcViewIx=0;
function mcOpenView(doc){
  mcViewPhotos=(doc.photos&&doc.photos.length?doc.photos:[doc]).map(function(p){
    return {url:p.url,title:p.title,
      sub:(p.sub!=null?p.sub:(doc.sub||'')),
      doc_id:(p.doc_id!=null?p.doc_id:(doc.doc_id||''))};
  });
  mcViewIx=0;
  mcShowViewPhoto();
  el('m-view').classList.add('open');document.body.style.overflow='hidden';
}
function mcShowViewPhoto(){
  var p=mcViewPhotos[mcViewIx];
  el('view-title').textContent=p.title;
  el('view-sub').textContent=(p.sub||'')+(p.doc_id?(' · doc_id '+p.doc_id):'');
  var many=mcViewPhotos.length>1;
  el('view-prev').style.display=many?'':'none';
  el('view-next').style.display=many?'':'none';
  var img=el('view-img');img.alt=p.title;
  mcLoadImg(p.url,img);
}
function mcNavView(dir){
  mcViewIx=(mcViewIx+dir+mcViewPhotos.length)%mcViewPhotos.length;
  mcShowViewPhoto();
}
function mcCloseView(){el('m-view').classList.remove('open');document.body.style.overflow=''}
el('view-prev').addEventListener('click',function(e){e.stopPropagation();mcNavView(-1)});
el('view-next').addEventListener('click',function(e){e.stopPropagation();mcNavView(1)});
el('view-close').addEventListener('click',mcCloseView);
el('m-view').addEventListener('click',function(e){if(e.target===this)mcCloseView()});

// --- Раздел «Мои документы» (мокап my-documents-s8.html; Спринт 8,
// change add-s8-cars-docs-booking, FR-70/71/72): GET /api/instructor/documents
// — прежний состав + версии/статусы на каждом документе (active_version /
// pending / last_rejected — шейп design.md, блок A). Карточки: бейдж
// «Действует», блок «Ожидает проверки замены», «Отклонено» с ПРИЧИНОЙ
// (ОВ-1); кнопки Загрузить/Заменить (FR-72) — замена только через диалог
// FR-71 с явной кнопкой «Заменить» (без клика файл не отправляется).
// СТС — по КАЖДОМУ авто: авто без СТС → карточка «нет СТС» с «Загрузить»
// (дозагрузка, POST …/cars/{id}/photo/sts — FR-69). Ошибки API — честно
// (тост с текстом сервера). Виджетов в разделе нет (FR-73). ---
var docTarget=null; // цель загрузки/замены {kind:'license'|'car_sts', carId, name, wasMissing}
function docName(d){
  if(d.type==='license')return 'Водительское удостоверение';
  var c=d.car||{};
  return 'СТС · '+[c.brand,c.model].filter(Boolean).join(' ');
}
function docMetaText(d){
  if(d.type==='license')return d.license_number?('ВУ № '+d.license_number):(d.meta||'');
  var c=d.car||{};
  return [c.brand,c.model].filter(Boolean).join(' ')+(c.plate?' · '+c.plate:'');
}
function docVersionLine(d){
  if(d.active_version&&d.active_version.version!=null){
    return 'версия '+d.active_version.version
      +' · загружено '+((d.active_version.uploaded_at||d.uploaded_at||'').split(' ')[0]||'—');
  }
  if(d.uploaded_at)return 'загружено '+String(d.uploaded_at).split(' ')[0];
  return 'документ не загружен';
}
function docSubverNodes(d){
  var out=[];
  if(d.pending){
    var p=node('div','subver pend');
    p.appendChild(node('b',null,'Ожидает проверки замены'));
    var pt=node('span',null,'Загружена новая версия ('
      +((d.pending.uploaded_at||'').split(' ')[0]||'дата неизвестна')
      +'). Пока администратор её не подтвердил, действует текущая версия — документ «не мигает».');
    p.appendChild(pt);
    out.push(p);
  }
  if(d.last_rejected){
    var r=node('div','subver rej');
    r.appendChild(node('b',null,'Причина отказа от администратора'));
    // причина — пользовательский текст: только textContent (XSS-гигиена)
    r.appendChild(node('span',null,d.last_rejected.reject_reason||''));
    r.appendChild(node('br'));
    r.appendChild(node('span','look','решение '+((d.last_rejected.decided_at||'').split(' ')[0]||'—')
      +' · действует предыдущая версия, можно загрузить заново'));
    out.push(r);
  }
  return out;
}
function docCardNode(d){
  var hasFile=!!d.doc_id;
  var card=node('article','doc');
  card.dataset.docId=d.doc_id||'';
  card.dataset.kind=d.type;
  card.dataset.car=String((d.car&&d.car.id)||0);
  var thumb=node('span','thumb');
  if(hasFile){
    thumb.style.cursor='zoom-in';
    var img=document.createElement('img');img.alt=docName(d);
    thumb.appendChild(img);
    thumb.appendChild(node('span','zoom','⤢ Смотреть'));
    mcLoadImg('/api/instructor/documents/'+d.doc_id+'/file',img);
    if(d.pending)thumb.appendChild(node('span','pendtag','замена на проверке'));
    var open=function(){mcOpenView({
      title:docName(d),doc_id:d.doc_id,
      url:'/api/instructor/documents/'+d.doc_id+'/file',sub:docMetaText(d)})};
    thumb.addEventListener('click',open);
    card._open=open;
  }else{
    thumb.appendChild(node('span','ph','🚗'));
  }
  card.appendChild(thumb);
  card.appendChild(node('b','name',docName(d)));
  var meta=node('small','meta');
  meta.appendChild(document.createTextNode(docMetaText(d)));
  meta.appendChild(document.createElement('br'));
  var ver=node('span','ver',docVersionLine(d));
  meta.appendChild(ver);
  card.appendChild(meta);
  if(hasFile){
    card.appendChild(node('span','ds-badge ds-verified','Действует'));
  }else{
    card.appendChild(node('span','ds-badge ds-pending','нет СТС'));
  }
  docSubverNodes(d).forEach(function(s){card.appendChild(s)});
  var act=node('div','doc-actions');
  if(hasFile){
    var view=node('button','btn-u ghost','Открыть');view.type='button';
    view.addEventListener('click',function(){if(card._open)card._open()});
    act.appendChild(view);
  }
  var main=node('button','btn-u',hasFile?'Заменить':'Загрузить');main.type='button';
  main.dataset.uploadDoc='1';main.dataset.kind=d.type;
  main.dataset.car=String((d.car&&d.car.id)||0);
  main.addEventListener('click',function(){
    var t={kind:d.type,carId:(d.car&&d.car.id)||0,name:docName(d),wasMissing:!hasFile};
    if(hasFile){docsAskReplace(t)}else{docsStartUpload(t)} // первая загрузка — без предупреждения FR-71
  });
  act.appendChild(main);
  card.appendChild(act);
  return card;
}
function openDocs(){
  apiGet('/api/instructor/documents',function(res){
    if(!res){toast('Не удалось загрузить документы');return}
    var docs=res.documents||[];
    var lic=docs.filter(function(d){return d.type==='license'});
    var stsDocs=docs.filter(function(d){return d.type==='car_sts'});
    var licBox=el('lic-docs');licBox.innerHTML='';
    lic.forEach(function(d){licBox.appendChild(docCardNode(d))});
    el('lic-n').textContent=lic.length;
    el('no-license').style.display=lic.length?'none':'block';
    if(!lic.length&&res.license_hint)el('no-license-hint').textContent=res.license_hint;
    // СТС по КАЖДОМУ авто (FR-69/FR-72): авто без СТС (легаси/дозагрузка)
    // добавляются карточкой «нет СТС» с кнопкой «Загрузить»
    apiGet('/api/instructor/cars',function(cres){
      var cars=cres?(cres.cars||[]):[];
      var withDoc={};
      stsDocs.forEach(function(d){if(d.car&&d.car.id!=null)withDoc[d.car.id]=1});
      cars.forEach(function(c){
        if(c.has_sts||withDoc[c.id])return;
        stsDocs.push({doc_id:null,type:'car_sts',title:'СТС автомобиля',
          car:{id:c.id,brand:c.brand,model:c.model,plate:c.plate},uploaded_at:null});
      });
      stsDocs.sort(function(a,b){
        return ((a.car&&a.car.id)||0)-((b.car&&b.car.id)||0);
      });
      var stsBox=el('sts-docs');stsBox.innerHTML='';
      stsDocs.forEach(function(d){stsBox.appendChild(docCardNode(d))});
      el('sts-count').textContent=stsDocs.length;
    });
  });
}
// ── загрузка/замена документов (FR-71/FR-72): единый flow с модалкой
// предупреждения #m-replace и скрытым input #doc-file; multipart на
// контрактные эндпоинты (POST /api/instructor/documents/license,
// POST …/cars/{id}/photo/sts); ошибка сервера — честный тост, список
// не меняется до успешной загрузки (после нее — перезагрузка статусов). ---
function docsAskReplace(t){
  docTarget=t;
  el('rep-sub').textContent=t.name;
  el('m-replace').classList.add('open');
  document.body.style.overflow='hidden';
}
function docsCloseReplace(){
  docTarget=null;
  el('m-replace').classList.remove('open');
  document.body.style.overflow='';
}
function docsPickFile(){el('doc-file').value='';el('doc-file').click()}
function docsStartUpload(t){
  docTarget=t; // первая загрузка (нет предыдущей версии) — без предупреждения
  docsPickFile();
}
el('rep-go').addEventListener('click',function(){
  if(!docTarget)return;
  docsPickFile(); // диалог закрывается в обработчике change по результату
});
el('rep-cancel').addEventListener('click',docsCloseReplace);
el('rep-close').addEventListener('click',docsCloseReplace);
el('m-replace').addEventListener('click',function(e){if(e.target===this)docsCloseReplace()});
el('upload-license').addEventListener('click',function(){
  docsStartUpload({kind:'license',carId:0,name:'Водительское удостоверение',wasMissing:true});
});
el('doc-file').addEventListener('change',function(){
  var t=docTarget;docTarget=null;
  docsCloseReplaceSilent();
  if(!t||!this.files.length)return;
  var file=this.files[0];
  var err=mcValidatePhoto(file); // JPEG/PNG ≤5 МБ — как на бэкенде (NFR-9)
  if(err){mcShowPhotoError(err);return}
  if(t.kind==='license'){
    mcUpload('/api/instructor/documents/license','file',file,null,null,function(e){
      if(e)return;
      // review-005 MINOR: первичная загрузка — не «замена»
      toast(t.wasMissing
        ?'ВУ отправлено на проверку администратору: документ появится после подтверждения.'
        :'Замена ВУ отправлена на проверку администратору: до подтверждения действует предыдущая версия.');
      openDocs(); // перезагрузка списка с актуальными статусами (FR-72)
    });
  }else{
    mcUpload('/api/instructor/cars/'+t.carId+'/photo/sts','photo',file,null,null,function(e){
      if(e)return;
      mcPurgeCarUrls(t.carId);
      toast(t.wasMissing
        ?'Фото СТС загружено — документ появился в списке.'
        :'Замена СТС отправлена на проверку администратору: действует предыдущая версия, статус авто не изменился (ОВ-6).');
      openDocs();
      openCars(); // комплектность/СТС-точка в «Моих автомобилях» обновляются
    });
  }
});
function docsCloseReplaceSilent(){
  el('m-replace').classList.remove('open');
  document.body.style.overflow='';
}

// --- Спринт 8 (FR-74, вместо удаленного раздела «Бронирования»): запросы
// (new) и брони (confirmed) РОВНО на выбранных слотах календаря; решения —
// на слоте, немедленно, мимо «Сохранить» (наследование ОВ-6 Спринта 7):
// Принять — одним кликом (POST …/confirm, без комментария), Отклонить —
// комментарий обязателен (POST …/reject {comment}, пустой на сервере — 422),
// у подтвержденной брони — «Отменить бронь» (POST …/cancel, BUG-049).
// API-контракты booking — без изменений (NFR-23). ---
var BK_DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
function bkWhen(b){
  return BK_DAYS[b.weekday]||''
    +' '+String(b.lesson_date||'').split('-').reverse().join('.')
    +' · '+(b.start_time||'')+'–'+(b.end_time||'');
}
function bkCarText(c){return c?[c.brand,c.model].filter(Boolean).join(' ')+(c.year?' '+c.year:''):'—'}
// --- Спринт 8 (FR-74): запросы (new) и брони (confirmed) РОВНО на
// выбранных слотах календаря; решения — на слоте, немедленно, мимо
// «Сохранить» (наследование ОВ-6 Спринта 7): Принять — одним кликом
// (POST …/confirm), Отклонить — комментарий обязателен (POST …/reject
// {comment}, пустой на сервере — 422), у подтвержденной брони —
// «Отменить бронь» (POST …/cancel, BUG-049); NFR-23: контракты booking
// без изменений ---
// --- Брони/запросы — подраздел «Календаря» (бывший раздел
// «Бронирования»; FR-48/FR-49): метки на слотах cal-grid,
// решения — в модалке #m-bk (BUG-052: унаследованный блок снесен) ---
function calLoadBookings(){
  apiGet('/api/instructor/bookings',function(res){
    calBookings={};
    (res?(res.bookings||[]):[]).forEach(function(b){
      if(b.status!=='new'&&b.status!=='confirmed')return;
      var h=parseInt((b.start_time||'').split(':')[0],10);
      if(isNaN(h))return;
      calBookings[b.weekday+'-'+h]=b;
    });
    calMarkBookings();
  });
}

function calMarkBookings(){
  if(!calBuilt)return;
  Object.keys(calBookings).forEach(function(k){
    var b=calBookings[k];
    var cell=el('cal-grid').querySelector('.cal-slot[data-k="'+k+'"]');
    if(!cell)return;
    cell.classList.remove('on'); // слот занят бронью/запросом — не правка графика
    cell.classList.add(b.status==='confirmed'?'booked':'reqslot');
    cell.innerHTML='';
    cell.appendChild(node('small',null,b.student_full_name||''));
    cell.appendChild(document.createTextNode(b.status==='confirmed'?'бронь':'запрос'));
  });
}
// ── модалка решения #m-bk (открывается кликом по слоту) ──
var bkTarget=null;
function bkOpenSlot(b){
  bkTarget=b;
  var confirmed=b.status==='confirmed';
  el('bk-slot-title').textContent=confirmed?'Подтверждённая бронь':'Запрос ученика';
  el('bk-slot-sub').textContent=bkWhen(b)+' · авто: '+bkCarText(b.car);
  el('bk-slot-who').textContent=b.student_full_name||'Ученик';
  el('bk-slot-what').textContent=confirmed?' — бронь подтверждена на слоте вашего графика.':' просит занятие на слоте вашего графика.';
  el('bk-slot-reject').style.display='none';
  el('bk-slot-reason').value='';
  el('bk-slot-reject-go').disabled=true;
  el('bk-slot-confirm').style.display=confirmed?'none':'';
  el('bk-slot-reject-btn').style.display=confirmed?'none':'';
  el('bk-slot-cancel').style.display=confirmed?'':'none';
  el('m-bk').classList.add('open');
  document.body.style.overflow='hidden';
}
function bkCloseSlot(){
  bkTarget=null;
  el('m-bk').classList.remove('open');
  document.body.style.overflow='';
}
function bkApplied(msg){
  bkCloseSlot();
  toast(msg);
  openCalendar(); // перезагрузка графика с актуальными метками слотов
  loadSummary();  // «Занятия на сегодня» на главной обновляются
}
el('bk-slot-confirm').addEventListener('click',function(){
  if(!bkTarget||bkTarget.status!=='new')return;
  var id=bkTarget.id;
  apiSend('POST','/api/instructor/bookings/'+id+'/confirm',{},function(res){
    if(res.status===200&&res.data&&res.data.ok){
      bkApplied('Бронь подтверждена. Слот закреплён в календаре и попадёт в «Занятия на сегодня».');
    }else{
      toast((res.data&&res.data.error)||'Не удалось подтвердить бронь');
    }
  });
});
el('bk-slot-reject-btn').addEventListener('click',function(){
  el('bk-slot-confirm').style.display='none';
  el('bk-slot-reject-btn').style.display='none';
  el('bk-slot-reject-go').style.display='';
  el('bk-slot-reject').style.display='block';
  el('bk-slot-reason').focus();
});
el('bk-slot-reason').addEventListener('input',function(){
  el('bk-slot-reject-go').disabled=!this.value.trim(); // комментарий обязателен
});
el('bk-slot-reject-go').addEventListener('click',function(){
  if(!bkTarget)return;
  var comment=el('bk-slot-reason').value.trim();
  if(!comment)return;
  apiSend('POST','/api/instructor/bookings/'+bkTarget.id+'/reject',{comment:comment},function(res){
    if(res.status===200&&res.data&&res.data.ok){
      bkApplied('Запрос отклонён. Слот снова свободен — ученик может запросить его повторно.');
    }else{
      toast((res.data&&res.data.error)||'Не удалось отклонить запрос');
    }
  });
});
el('bk-slot-cancel').addEventListener('click',function(){
  if(!bkTarget||bkTarget.status!=='confirmed')return;
  apiSend('POST','/api/instructor/bookings/'+bkTarget.id+'/cancel',{},function(res){
    if(res.status===200&&res.data&&res.data.ok){
      bkApplied('Бронь отменена. Слот снова свободен — ученик может запросить его повторно.');
    }else{
      toast((res.data&&res.data.error)||'Не удалось отменить бронь');
    }
  });
});
el('bk-slot-close').addEventListener('click',bkCloseSlot);
el('bk-slot-close2').addEventListener('click',bkCloseSlot);
el('m-bk').addEventListener('click',function(e){if(e.target===this)bkCloseSlot()});

// Хвост старых ссылок (BUG-047): /my-cars теперь 301 на этот дашборд с
// хешем — открываем раздел «Мои автомобили» напрямую.
// BUG-051: прежние хеши #/my-docs и #/bookings ведут в переименованный
// «Профиль и документы» и в «Календарь» (впитал «Бронирования»)
if(location.hash==='#/my-cars')navTo('Мои автомобили');
// FR-74: старая ссылка раздела «Бронирования» — редирект в календарь
// (механика BUG-047; раздел удален без остатков)
if(location.hash==='#/my-docs')navTo('Профиль и документы');
if(location.hash==='#/bookings')navTo('Календарь');

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
