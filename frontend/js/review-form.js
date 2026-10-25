/* из review-form.html (блок 1) */
// Спринт 6, Партия B: сессия и api — общий клиент js/api.js,
// toast/el/expWord — общие хелперы js/utils.js
import { api, toLogin, getToken, handleAuthFail } from './api.js';
import { toast as baseToast, el, expWord } from './utils.js';
// --- сессия ученика (единый паттерн кабинета, sdd §10.2–10.3) ---
if(!getToken()){toLogin()}
function toast(m){baseToast(m,3200)}
// ФИО/аватар ученика (FR-5)
api('/api/auth/me',{},function(res){
  if(handleAuthFail(res))return;
  if(!res.data||!res.data.ok)return;
  var u=res.data.user||{};
  var fio=[u.surname,u.name,u.patronymic].filter(Boolean).join(' ');
  if(fio){document.getElementById('uname').textContent=fio;
    document.getElementById('avatar').textContent=((u.surname||'')[0]||'')+((u.name||'')[0]||'');}
});
// toast/el/expWord — из js/utils.js (toast — 3200 мс, как было)
// el — из js/utils.js (textContent — stored XSS)

// --- цель отзыва: /review?instructor=<id> (переход из «Моих заявок») ---
var params=new URLSearchParams(location.search);
var instructorId=+(params.get('instructor')||0);
if(!instructorId){location.href='/my-requests'}
// контекст: GET /api/student/instructors/{id} (ФИО, стаж, авто, агрегат рейтинга)
api('/api/student/instructors/'+instructorId,{},function(res){
  if(handleAuthFail(res))return;
  if(!res.data||!res.data.ok){toast('Инструктор не найден');return}
  var i=res.data.instructor||{};
  var fio=i.full_name||'Инструктор';
  document.getElementById('i-name').textContent=fio;
  document.getElementById('i-ava').textContent=
    fio.split(' ').slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('');
  var sub='Стаж '+((i.experience_years!=null)?i.experience_years:0)+' '+expWord(+i.experience_years||0);
  var cars=(i.cars||[]).map(function(c){return [c.brand,c.model].filter(Boolean).join(' ')}).filter(Boolean);
  if(cars.length)sub+=' · '+cars.join(', ');
  document.getElementById('i-sub').textContent=sub;
  var r=i.rating,box=document.getElementById('i-rating');
  box.textContent='';
  if(r&&r.has_reviews!==false&&r.count){
    box.appendChild(document.createTextNode((+r.average).toFixed(1)+' ★'));
    box.appendChild(el('small',null,r.count+' отзывов учеников'));
  }else{
    box.appendChild(document.createTextNode('☆'));
    box.appendChild(el('small',null,'отзывов пока нет'));
  }
});

// --- звёзды: клик фиксирует оценку, hover — предпросмотр ---
var rating=0;
var LABELS={0:'Выберите оценку от 1 до 5',1:'1 — плохо',2:'2 — так себе',3:'3 — нормально',4:'4 — хорошо',5:'5 — отлично!'};
var stars=document.querySelectorAll('.star');
function paint(n){
  stars.forEach(function(s){s.classList.toggle('on',+s.dataset.v<=n)});
  var lab=document.getElementById('stars-lab');lab.textContent='';
  if(n){lab.appendChild(document.createTextNode('Оценка: '));
    lab.appendChild(el('b',null,LABELS[n]));}
  else{lab.textContent=LABELS[0]}
}
stars.forEach(function(s){
  s.addEventListener('mouseenter',function(){paint(+s.dataset.v)});
  s.addEventListener('mouseleave',function(){paint(rating)});
  s.addEventListener('click',function(){rating=+s.dataset.v;paint(rating);validate()});
});
var ta=document.getElementById('review-text');
ta.addEventListener('input',function(){
  var c=document.getElementById('counter'),len=ta.value.length;
  c.textContent=len+' / 1000';c.classList.toggle('over',len>1000);
  validate();
});
function validate(){
  var ok=rating>0&&ta.value.trim().length>0&&ta.value.length<=1000;
  document.getElementById('send').disabled=!ok;
}
// состояние «уже оставлен» (409) / «отправлен» (200) — данными сервера
function showDone(title){
  document.getElementById('done-title').textContent=title;
  document.getElementById('view-form').style.display='none';
  document.getElementById('view-done').style.display='block';
}
document.getElementById('send').addEventListener('click',function(){
  var btn=this;btn.disabled=true;
  api('/api/student/instructors/'+instructorId+'/reviews',{method:'POST',
    body:JSON.stringify({rating:rating,text:ta.value.trim()})},function(res){
    if(res.status===401){toLogin();return} // только 401 — сессия; 403 — бизнес-ошибка (NFR-2)
    if(res.status===200&&res.data&&res.data.ok){
      showDone('Отзыв отправлен');
      toast('Отзыв отправлен: оценка '+rating+' из 5. Спасибо — он появится в карточке инструктора.');
    }else if(res.status===409){
      showDone('Отзыв уже отправлен');
      btn.disabled=false;
      toast('Отзыв: вы уже оставляли отзыв этому инструктору.');
    }else{
      btn.disabled=false;
      toast((res.data&&res.data.error)||'Не удалось отправить отзыв');
    }
  });
});
paint(0);
