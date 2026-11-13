<!-- «Выбор инструктора» — кабинет ученика. Вариант A (согласованный мокап
     design/mocks/choice-instructor-a.html): фильтры колонкой слева.
     Разметка — дословный перенос frontend/instructor-choice.html (Спринт 15,
     change add-vue-s15-final-migration, задача 4.1; шаблон повторяет вход
     vue/instructor-choice.html — «Разметку держать синхронной с App.vue»).
     Wiring — перенос js/student/instructor-choice.js 1:1 (стековые
     эквиваленты именованные — design.md «Границы правок тестов»): el()/
     innerHTML-отрисовка списков → реактивные списки/интерполяция
     {{ }} (текстовые узлы — XSS-гигиена по построению: пользовательские
     строки ФИО/брендов никогда не проходят через HTML); отрисовка
     ratingNode → v-if/v-else («☆ Нет отзывов», «★ X.Y», «N отзывов»);
     #empty display:block/none → :style-эквивалент с теми же значениями
     (класс .empty содержит display:none — v-show здесь не эквивалент);
     fetchSeq-гонка фильтров, sent-кэш («✓ Заявка отправлена»), 409-тост
     БЕЗ кэширования (review-001 #14), сортировка localeCompare 'ru',
     empty-состояние, logout, сайдбар ученика — дословно.
     Гвард без токена → toLogin; ФИО (#uname из /api/auth/me) — FR-5. -->
<template>
<div class="app">
<!-- BUG-047: единый сайдбар ученика; «Выбрать инструктора» — активный раздел,
     остальные пункты ведут в кабинет (отдельной кнопки «← В кабинет» больше нет) -->
<aside class="side">
  <div class="side-brand"><span class="check">✓</span><div><em>Сбер</em>Автошкола<small>Кабинет ученика</small></div></div>
  <nav class="snav">
    <a href="/cabinet"><span class="ico">⌂</span>Главная</a>
    <a href="/cabinet#/my-requests"><span class="ico">✉</span>Мои заявки</a>
    <a class="on" href="/instructor-choice"><span class="ico">▤</span>Выбрать инструктора</a>
    <a href="/cabinet#/my-bookings"><span class="ico">◷</span>Мои брони</a>
  </nav>
</aside>
<div class="frame">
<header>
  <div class="user"><span class="uname" id="uname">…</span><button class="logout" id="logout">Выйти</button></div>
</header>

<div class="page-head">
  <div class="kicker">Выбор инструктора</div>
  <h1>Найдите своего инструктора</h1>
  <p>Одобренные инструкторы школы: рейтинг, стаж, автомобили и свободные часы. Подайте заявку — инструктор увидит её в своём кабинете.</p>
</div>

<div class="layout">
  <!-- ВАРИАНТ A: фильтры колонкой слева -->
  <aside class="filters">
    <h2>Фильтры</h2>
    <p class="sub">Сузьте подбор под ваш график</p>
    <div class="fgroup">
      <span>Автомобиль (КПП)</span>
      <div class="seg" id="f-trans">
        <button class="on" data-v="">Любая</button>
        <button data-v="manual">Механика</button>
        <button data-v="automatic">Автомат</button>
      </div>
    </div>
    <div class="fgroup">
      <span>Рейтинг не ниже</span>
      <div class="range-lab"><b id="rating-val">0</b><span>из 5</span></div>
      <input type="range" id="f-rating" min="0" max="5" step="0.5" value="0">
    </div>
    <div class="fgroup">
      <span>Стаж от</span>
      <div class="chips" id="f-exp">
        <button class="chip on" data-v="0">Любой</button>
        <button class="chip" data-v="3">3 года</button>
        <button class="chip" data-v="5">5 лет</button>
        <button class="chip" data-v="10">10 лет</button>
      </div>
    </div>
    <div class="fgroup">
      <span>Свободное время</span>
      <div class="chips" id="f-day">
        <button class="chip on" data-v="">Любой день</button>
        <button class="chip" data-v="0">Пн</button>
        <button class="chip" data-v="2">Ср</button>
        <button class="chip" data-v="5">Сб</button>
        <button class="chip" data-v="6">Вс</button>
      </div>
      <div class="frow">
        <select id="f-from" aria-label="Время от">
          <option value="">с …</option><option>08:00</option><option>10:00</option><option>12:00</option><option>14:00</option><option>16:00</option><option>18:00</option>
        </select>
        <select id="f-to" aria-label="Время до">
          <option value="">до …</option><option>12:00</option><option>14:00</option><option>16:00</option><option>18:00</option><option>20:00</option><option>22:00</option>
        </select>
      </div>
    </div>
    <button class="reset" id="reset">Сбросить фильтры</button>
  </aside>

  <section>
    <div class="cards-top">
      <b id="found">{{ foundText }}</b>
      <label class="sort">Сортировка
        <select id="sort"><option value="rating">по рейтингу</option><option value="exp">по стажу</option><option value="name">по фамилии</option></select>
      </label>
    </div>
    <div class="cards" id="cards">
      <article class="card" v-for="i in view" :key="String(cardId(i))" :data-id="String(cardId(i))">
        <div class="card-top">
          <span class="icard">{{ initialsOf(i) }}</span>
          <div>
            <b>{{ instFio(i) }}</b>
            <small>Стаж: {{ instExp(i) }} {{ expWord(instExp(i)) }}</small>
          </div>
          <div class="rating" v-if="hasRating(i)">
            <b>{{ '★ ' + (+i.rating.average).toFixed(1) }}</b>
            <small>{{ String(i.rating.count) + ' отзывов' }}</small>
          </div>
          <div class="rating none" v-else>
            <b>☆ Нет отзывов</b>
            <small>новый инструктор</small>
          </div>
        </div>
        <div class="meta">
          <span class="pill green">{{ 'Авто: ' + (i.cars||[]).length }}</span>
          <span class="pill" v-for="(c, cx) in (i.cars||[])" :key="cx">{{ carPillText(c) }}</span>
        </div>
        <div class="hours">
          <span>Свободные часы</span>
          <div class="slotrow">
            <span class="slot" v-for="(s, sx) in (i.availability||[])" :key="sx">{{ slotText(s) }}</span>
          </div>
        </div>
        <div class="warn-note" v-if="sent[cardId(i)]">Заявка подана — статус появится в разделе «Мои заявки»</div>
        <button class="apply" :class="{'sent': !!sent[cardId(i)]}" type="button" @click="applyClick(i)">{{ sent[cardId(i)] ? '✓ Заявка отправлена' : 'Подать заявку' }}</button>
      </article>
    </div>
    <div class="empty" id="empty" :style="{display: view.length ? 'none' : 'block'}"><b>Под фильтры никто не подошёл</b>Попробуйте ослабить условия: снизить рейтинг или расширить время.<br><button id="empty-reset">Сбросить фильтры</button></div>
  </section>
</div>

<footer><span>СберАвтошкола · «Выбор инструктора», вариант A</span><span>Кабинет ученика</span></footer>
</div>
</div>
<div class="toast" id="toast"></div>
</template>

<script>
// Wiring — перенос js/student/instructor-choice.js 1:1 (задача 4.1):
// сессия/api — общий клиент vue/src/shared/api.js (телa дословны с С9),
// toast/expWord — из vue/src/shared/utils.js; el() не переносится —
// карточки рендерятся реактивным списком (интерполяция = текстовые узлы).
import { onMounted, reactive, ref, computed } from 'vue';
import { api, toLogin, clearSession, getToken } from '../../shared/api.js';
import { toast, expWord } from '../../shared/utils.js';

export default {
  name: 'InstructorChoiceApp',
  setup: function () {
    // --- поля карточки (реальный шейп GET /api/student/instructors,
    //     backend/student_marketplace.py; code-review review-001 #2/#5:
    //     нормализация по «догадкам» удалена) ---
    var DAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
    function instFio(i){return i.full_name||'Инструктор'}
    function instExp(i){return +i.experience_years||0}
    function slotText(s){return DAYS[s.weekday]+' '+s.start_time+'–'+s.end_time}
    function cardId(i){return i.id||i.instructor_id}
    // инициалы — инлайн (перенос 1:1; el/initials из js/shared/utils.js
    // НЕ переносятся — design.md «Судьба каталога js/»)
    function initialsOf(i){return instFio(i).split(' ').slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('')}
    function carPillText(c){
      var tr=c.transmission==='automatic'?'автомат':c.transmission==='manual'?'механика':(c.transmission||'');
      return [c.brand,c.model].filter(Boolean).join(' ')+' · '+(c.year||'')+(tr?' · '+tr:'');
    }
    // рейтинг — узел (агрегат {average,count} / {has_reviews:false}, FR-35);
    // v-if/v-else эквивалент ratingNode
    function hasRating(i){
      var r=i.rating;
      return !(!r||r.has_reviews===false||!r.count);
    }

    // --- состояние фильтров -> query-параметры (фильтрует сервер, FR-32) ---
    var state=reactive({transmission:'',min_rating:0,min_experience:0,free_weekday:'',free_from:'',free_to:''});
    var sent=reactive({});       // instructor_id -> заявка подана (в этой сессии страницы)
    var instructors=ref([]);// последний ответ API
    var fetchSeq=0;
    var sortBy=ref('rating');
    var view=computed(function(){
      var list=instructors.value.slice();
      var sort=sortBy.value;
      list.sort(function(a,b){
        if(sort==='exp')return instExp(b)-instExp(a);
        if(sort==='name')return instFio(a).localeCompare(instFio(b),'ru');
        var ra=a.rating&&a.rating.average!=null?+a.rating.average:-1;
        var rb=b.rating&&b.rating.average!=null?+b.rating.average:-1;
        return rb-ra;
      });
      return list;
    });
    var foundText=computed(function(){return 'Найдено: '+view.value.length});
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
        instructors.value=res.data.instructors||[];
      });
    }
    // «Подать заявку» (эквивалент click-обработчика кнопки apply 1:1)
    function applyClick(i){
      var id=cardId(i);
      if(sent[id])return;
      api('/api/student/requests',{method:'POST',body:JSON.stringify({instructor_id:+id})},function(res){
        if(res.status===401||res.status===403){toLogin();return}
        if(res.status===200&&res.data&&res.data.ok){
          sent[id]=true;
          toast('Заявка отправлена инструктору. Ответ появится в разделе «Мои заявки».');
        }else if(res.status===409){
          // 409 не кэшируем в sent (review-001 #14): состояние «подано»
          // знает только сервер
          toast('У вас уже есть активная заявка этому инструктору.');
        }else{
          toast((res.data&&res.data.error)||'Не удалось отправить заявку');
        }
      });
    }

    onMounted(function(){
      // --- сессия ученика (единый паттерн кабинета, sdd §10.2–10.3) ---
      if(!getToken()){toLogin()}
      // ФИО ученика (FR-5)
      api('/api/auth/me',{},function(res){
        if(res.status===401||res.status===403||!res.data||!res.data.ok){toLogin();return}
        var u=res.data.user||{};
        var fio=[u.surname,u.name,u.patronymic].filter(Boolean).join(' ');
        if(fio){document.getElementById('uname').textContent=fio;}
      });

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
      document.getElementById('sort').addEventListener('change',function(){sortBy.value=this.value});
      function reset(){
        Object.assign(state,{transmission:'',min_rating:0,min_experience:0,free_weekday:'',free_from:'',free_to:''});
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
    });

    return {
      view: view, foundText: foundText, sent: sent,
      cardId: cardId, instFio: instFio, instExp: instExp, expWord: expWord,
      slotText: slotText, initialsOf: initialsOf, carPillText: carPillText,
      hasRating: hasRating, applyClick: applyClick,
    };
  },
};
</script>
