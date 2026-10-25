/* из instructor-choice.html (блок 1) */
// Спринт 6, Партия B: сессия и api — общий клиент js/api.js,
// toast/el — общие хелперы js/utils.js
import { api, toLogin, clearSession, getToken } from './api.js';
import { toast, el } from './utils.js';
// --- сессия ученика (единый паттерн кабинета, sdd §10.2–10.3) ---
if(!getToken()){toLogin()}
// ФИО/аватар ученика (FR-5)
api('/api/auth/me',{},function(res){
  if(res.status===401||res.status===403||!res.data||!res.data.ok){toLogin();return}
  var u=res.data.user||{};
  var fio=[u.surname,u.name,u.patronymic].filter(Boolean).join(' ');
  if(fio){document.getElementById('uname').textContent=fio;
    document.getElementById('avatar').textContent=((u.surname||'')[0]||'')+((u.name||'')[0]||'');}
});

// --- поля карточки (реальный шейп GET /api/student/instructors,
//     backend/student_marketplace.py; code-review review-001 #2/#5:
//     нормализация по «догадкам» удалена) ---
var DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
// DOM-хелпер: пользовательские строки — только через textContent
// (code-review review-001 #1, stored XSS через innerHTML запрещен)
// el — общий DOM-хелпер (js/utils.js, textContent — stored XSS)
function instFio(i){return i.full_name||'Инструктор'}
function instExp(i){return +i.experience_years||0}
function slotText(s){return DAYS[s.weekday]+' '+s.start_time+'–'+s.end_time}

// --- состояние фильтров -> query-параметры (фильтрует сервер, FR-32) ---
var state={transmission:'',min_rating:0,min_experience:0,free_weekday:'',free_from:'',free_to:''};
var sent={};       // instructor_id -> заявка подана (в этой сессии страницы)
var instructors=[];// последний ответ API
var fetchSeq=0;
function buildQuery(){
  var q=[];
  if(state.transmission)q.push('transmission='+encodeURIComponent(state.transmission));
  if(state.min_rating>0)q.push('min_rating='+state.min_rating);
  if(state.min_experience>0)q.push('min_experience='+state.min_experience);
  if(state.free_weekday!=='')q.push('free_weekday='+state.free_weekday);
  if(state.free_from)q.push('free_from='+encodeURIComponent(state.free_from));
  if(state.free_to)q.push('free_to='+encodeURIComponent(state.free_to));
  return q.length?('?'+q.join('&')):'';
}
function loadInstructors(){
  var seq=++fetchSeq;
  api('/api/student/instructors'+buildQuery(),{},function(res){
    if(seq!==fetchSeq)return; // устаревший ответ — фильтр уже менялся
    if(res.status===401||res.status===403){toLogin();return}
    if(!res.data||!res.data.ok){toast((res.data&&res.data.error)||'Не удалось загрузить список инструкторов');return}
    instructors=res.data.instructors||[];
    render();
  });
}
function expWord(n){return n%10===1&&n%100!==11?'год':(n%10>=2&&n%10<=4&&(n%100<10||n%100>=20)?'года':'лет')}
// рейтинг — узел (агрегат {average,count} / {has_reviews:false}, FR-35)
function ratingNode(i){
  var r=i.rating;
  if(!r||r.has_reviews===false||!r.count){
    var none=el('div','rating none');
    none.appendChild(el('b',null,'☆ Нет отзывов'));
    none.appendChild(el('small',null,'новый инструктор'));
    return none;
  }
  var box=el('div','rating');
  box.appendChild(el('b',null,'★ '+(+r.average).toFixed(1)));
  box.appendChild(el('small',null,String(r.count)+' отзывов'));
  return box;
}
function render(){
  var list=instructors.slice();
  var sort=document.getElementById('sort').value;
  list.sort(function(a,b){
    if(sort==='exp')return instExp(b)-instExp(a);
    if(sort==='name')return instFio(a).localeCompare(instFio(b),'ru');
    var ra=a.rating&&a.rating.average!=null?+a.rating.average:-1;
    var rb=b.rating&&b.rating.average!=null?+b.rating.average:-1;
    return rb-ra;
  });
  document.getElementById('found').textContent='Найдено: '+list.length;
  document.getElementById('empty').style.display=list.length?'none':'block';
  // Строим карточки через createElement/textContent — пользовательские
  // строки (ФИО инструктора, brand/model) не проходят через innerHTML
  // (code-review review-001 #1, stored XSS)
  var cards=document.getElementById('cards');
  cards.innerHTML='';
  list.forEach(function(i){
    var id=i.id||i.instructor_id, sentNow=!!sent[id];
    var cars=i.cars||[];
    var card=el('article','card');card.dataset.id=String(id);
    var top=el('div','card-top');
    var initials=instFio(i).split(' ').slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('');
    top.appendChild(el('span','icard',initials));
    var who=el('div');
    who.appendChild(el('b',null,instFio(i)));
    who.appendChild(el('small',null,'Стаж: '+instExp(i)+' '+expWord(instExp(i))));
    top.appendChild(who);
    top.appendChild(ratingNode(i));
    card.appendChild(top);
    var meta=el('div','meta');
    meta.appendChild(el('span','pill green','Авто: '+cars.length));
    cars.forEach(function(c){
      var tr=c.transmission==='automatic'?'автомат':c.transmission==='manual'?'механика':(c.transmission||'');
      meta.appendChild(el('span','pill',[c.brand,c.model].filter(Boolean).join(' ')+' · '+(c.year||'')+(tr?' · '+tr:'')));
    });
    card.appendChild(meta);
    var hours=el('div','hours');
    hours.appendChild(el('span',null,'Свободные часы'));
    var slotrow=el('div','slotrow');
    (i.availability||[]).forEach(function(s){slotrow.appendChild(el('span','slot',slotText(s)))});
    hours.appendChild(slotrow);
    card.appendChild(hours);
    if(sentNow)card.appendChild(el('div','warn-note','Заявка подана — статус появится в разделе «Мои заявки»'));
    var btn=el('button','apply'+(sentNow?' sent':''),sentNow?'✓ Заявка отправлена':'Подать заявку');
    btn.type='button';btn.dataset.id=String(id);
    btn.addEventListener('click',function(){
      var id=btn.dataset.id;
      if(sent[id])return;
      api('/api/student/requests',{method:'POST',body:JSON.stringify({instructor_id:+id})},function(res){
        if(res.status===401||res.status===403){toLogin();return}
        if(res.status===200&&res.data&&res.data.ok){
          sent[id]=true;render();
          toast('Заявка отправлена инструктору. Ответ появится в разделе «Мои заявки».');
        }else if(res.status===409){
          // 409 не кэшируем в sent (review-001 #14): состояние «подано»
          // знает только сервер
          toast('У вас уже есть активная заявка этому инструктору.');
        }else{
          toast((res.data&&res.data.error)||'Не удалось отправить заявку');
        }
      });
    });
    card.appendChild(btn);
    cards.appendChild(card);
  });
}
function segBind(id,key){
  var box=document.getElementById(id);
  box.addEventListener('click',function(e){
    var b=e.target.closest('button');if(!b)return;
    box.querySelectorAll('button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');state[key]=b.dataset.v;loadInstructors();
  });
}
segBind('f-trans','transmission');segBind('f-exp','min_experience');segBind('f-day','free_weekday');
document.getElementById('f-rating').addEventListener('input',function(){state.min_rating=+this.value;document.getElementById('rating-val').textContent=this.value;loadInstructors()});
document.getElementById('f-from').addEventListener('change',function(){state.free_from=this.value;loadInstructors()});
document.getElementById('f-to').addEventListener('change',function(){state.free_to=this.value;loadInstructors()});
document.getElementById('sort').addEventListener('change',render);
function reset(){
  state={transmission:'',min_rating:0,min_experience:0,free_weekday:'',free_from:'',free_to:''};
  ['f-trans','f-exp','f-day'].forEach(function(id){document.querySelectorAll('#'+id+' button').forEach(function(b,i){b.classList.toggle('on',i===0)})});
  document.getElementById('f-rating').value=0;document.getElementById('rating-val').textContent='0';
  document.getElementById('f-from').value='';document.getElementById('f-to').value='';
  loadInstructors();
}
document.getElementById('reset').addEventListener('click',reset);
document.getElementById('empty-reset').addEventListener('click',reset);
// «Выйти»: POST /api/auth/logout -> очистка -> главная (к модалке входа)
document.getElementById('logout').addEventListener('click',function(){
  fetch('/api/auth/logout',{method:'POST',headers:{'X-Session-Token':getToken()||''}})
    .catch(function(){})
    .then(function(){clearSession();location.href='/';});
});
if(getToken())loadInstructors();
