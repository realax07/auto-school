/* из cabinet.html (блок 1) */
// Спринт 6, Партия B: toast/el/fmtDate/nowMoscow/fioOf — общие хелперы
// js/utils.js; fetch-логика (своя очистка сессии) — локальная.
import { toast, el, fmtDate, nowMoscow, fioOf } from './utils.js';
(function(){
  // Wiring Спринта 1 (sdd §10.2–10.4): токен сессии — sessionStorage,
  // ключ session_token (единый snake_case-паттерн с admin_token Спринта 0);
  // модалка входа (задача 2.2) пишет его в тот же ключ.
  var TOKEN_KEY = 'session_token';
  var token = null;
  try { token = sessionStorage.getItem(TOKEN_KEY); } catch (e) {}

  function clearSession() {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
  }
  // 401 (нет токена / невалидный / истек / аннулирован) -> редирект на
  // главную, к модалке входа (FR-7)
  function toLogin() {
    clearSession();
    location.href = '/';
  }

  // GET /api/auth/me (X-Session-Token): 200 -> подстановка ФИО (FR-5)
  if (!token) {
    toLogin();
  } else {
    fetch('/api/auth/me', { headers: { 'X-Session-Token': token } })
      .then(function (r) {
        return r.json().then(function (d) { return { status: r.status, data: d }; });
      })
      .then(function (res) {
        if (res.status === 401 || !res.data || !res.data.ok) { toLogin(); return; }
        var u = res.data.user || {};
        var fio = fioOf(u);
        document.querySelector('.uname').textContent = fio;
        document.querySelector('.greet b').textContent = 'Добро пожаловать, ' + u.name + '!';
      })
      .catch(function () { /* сеть: остаемся на странице без подстановки */ });
  }

  // «Выйти» -> POST /api/auth/logout -> очистка sessionStorage ->
  // редирект на главную (FR-8); редирект после любого ответа (design, поток 3)
  document.querySelector('.logout').addEventListener('click', function () {
    fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'X-Session-Token': token || '' }
    })
      .catch(function () {})
      .then(function () {
        clearSession();
        location.href = '/';
      });
  });

  // Плитка «Найти водителя» (спринт 3, change add-instructor-student-loop):
  // переход в раздел «Выбор инструктора» (страница /instructor-choice —
  // по решению BUG-047 остается отдельной целевой страницей)
  var tileInstructor = document.getElementById('tile-instructor');
  if (tileInstructor) {
    tileInstructor.addEventListener('click', function () {
      location.href = '/instructor-choice';
    });
  }

  // =====================================================================
  // BUG-047: единый лейаут кабинета — переключение разделов «Главная» /
  // «Мои заявки»; «Выбрать инструктора» — переход на /instructor-choice.
  // Спринт 5 (change add-booking-docs): раздел «Мои брони» — тоже ВНУТРИ
  // кабинета (BUG-047-прецедент: standalone-страницы запрещены).
  // Активный пункт сайдбара подсвечивается. Хвост старых ссылок:
  // /my-requests теперь 301 на /cabinet#/my-requests — хеш открывает
  // раздел напрямую.
  function navTo(name) {
    var isReq = (name === 'Мои заявки');
    var isBk = (name === 'Мои брони');
    document.getElementById('sec-home').style.display = (isReq || isBk) ? 'none' : 'block';
    document.getElementById('sec-requests').style.display = isReq ? 'block' : 'none';
    document.getElementById('sec-bookings').style.display = isBk ? 'block' : 'none';
    document.querySelectorAll('.snav button[data-tab]').forEach(function (b) {
      b.classList.toggle('on', b.dataset.tab === name);
    });
    // BUG-047: хеш раздела синхронизируется с табом — reload не сбрасывает
    // раздел, старые ссылки #/my-requests открывают его напрямую
    var wantHash = isReq ? '#/my-requests' : isBk ? '#/my-bookings' : '';
    if (location.hash !== wantHash) {
      try { history.replaceState(null, '', location.pathname + location.search + (wantHash || '')); } catch (e) {}
    }
    if (isReq) loadRequests();
    if (isBk) loadBookingsSection();
  }
  document.querySelectorAll('.snav button[data-tab]').forEach(function (b) {
    b.addEventListener('click', function () { navTo(b.dataset.tab); });
  });
  document.querySelectorAll('.snav button[data-goto]').forEach(function (b) {
    b.addEventListener('click', function () { location.href = b.dataset.goto; });
  });
  if (location.hash === '#/my-requests') navTo('Мои заявки');
  if (location.hash === '#/my-bookings') navTo('Мои брони');

  // --- Раздел «Мои заявки» (перенесен из my-requests.html) --------------
  // сессия ученика — токен/clearSession/toLogin выше (единый паттерн)
  function api(path,opts,cb){
    opts=opts||{};
    opts.headers=Object.assign({'X-Session-Token':token||''},opts.headers||{});
    if(opts.body)opts.headers['Content-Type']='application/json';
    fetch(path,opts).then(function(r){
      return r.json().then(function(d){cb({status:r.status,data:d})},function(){cb({status:r.status,data:null})});
    },function(){cb({status:0,data:null})});
  }
  function handleAuthFail(res){
    if(res.status===401||res.status===403){toLogin();return true}
    return false;
  }
  // toast/el — общие хелперы (js/utils.js)
  // el — из js/utils.js (textContent — stored XSS)

  // данные: GET /api/student/requests (реальный шейп backend/student_requests.py)
  var reqs=[];
  var STATUS={new:['На рассмотрении','st-new'],accepted:['Принята','st-acc'],denied:['Отказана','st-den']};
  // системный комментарий автозакрытия (ОВ-1) — тот же текст, что в бэкенде
  var SYSTEM_COMMENT='Заявка закрыта: ученик принят другим инструктором';
  // fmtDate — из js/utils.js: '2026-10-16 10:22:00' → '16.10.2026'
  function loadRequests(){
    api('/api/student/requests',{},function(res){
      if(handleAuthFail(res))return;
      if(!res.data||!res.data.ok){toast((res.data&&res.data.error)||'Не удалось загрузить заявки');return}
      reqs=res.data.requests||[];
      renderFilters();
      render(cur);
    });
  }
  function renderFilters(){
    document.getElementById('n-new').textContent=reqs.filter(function(r){return r.status==='new'}).length?'·'+reqs.filter(function(r){return r.status==='new'}).length:'';
    document.getElementById('n-accepted').textContent=reqs.filter(function(r){return r.status==='accepted'}).length?'·'+reqs.filter(function(r){return r.status==='accepted'}).length:'';
    document.getElementById('n-denied').textContent=reqs.filter(function(r){return r.status==='denied'}).length?'·'+reqs.filter(function(r){return r.status==='denied'}).length:'';
  }
  function carText(c){
    if(!c)return '';
    var tr=c.transmission==='automatic'?'автомат':c.transmission==='manual'?'механика':(c.transmission||'');
    return [c.brand,c.model].filter(Boolean).join(' ')+(c.year?' '+c.year:'')+(tr?' · '+tr:'');
  }
  function render(filter){
    var box=document.getElementById('list');box.innerHTML='';
    var list=reqs.filter(function(r){return filter==='all'||r.status===filter});
    document.getElementById('noreq').style.display=list.length?'none':'block';
    list.forEach(function(r){
      var instructor=r.instructor_full_name||'Инструктор';
      var art=el('article','req');
      var top=el('div','req-top');
      top.appendChild(el('span','sic',instructor.split(' ').slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('')));
      var who=el('div');
      who.appendChild(el('b',null,instructor));
      who.appendChild(el('small',null,'заявка от '+fmtDate(r.created_at)));
      top.appendChild(who);
      var st=STATUS[r.status]||['?','st-new'];
      top.appendChild(el('span','status '+st[1],st[0]));
      art.appendChild(top);
      if(r.car) {
        var pills=el('div','meta-pills');
        pills.appendChild(el('span','pill','Автомобиль занятий:'));
        pills.appendChild(el('span','pill car','🚗 '+carText(r.car)));
        art.appendChild(pills);
      }
      if(r.status==='new'){
        art.appendChild(el('div','note','Заявка ждёт решения инструктора. Пока она активна, новую этому же инструктору подать нельзя.'));
      }
      if(r.status==='accepted'){
        var note=el('div','note');
        note.appendChild(document.createTextNode('Вы приняты'+(r.decided_at?' '+fmtDate(r.decided_at):'')+'. Отзыв можно оставить один раз: '));
        var a=el('a',null,'оставить отзыв →');
        a.href='/review?instructor='+(r.instructor_id||'');
        note.appendChild(a);
        art.appendChild(note);
        var act=el('div','actions');
        var rv=el('button','act review','★ Оставить отзыв');rv.type='button';
        rv.addEventListener('click',function(){location.href='/review?instructor='+(r.instructor_id||'')});
        act.appendChild(rv);
        art.appendChild(act);
      }
      if(r.status==='denied'){
        var isSystem=r.deny_comment===SYSTEM_COMMENT;
        var com=el('div','comment'+(isSystem?' system':''));
        com.appendChild(el('span',null,isSystem?'Системный комментарий':'Комментарий инструктора'));
        com.appendChild(document.createTextNode(r.deny_comment||''));
        art.appendChild(com);
        var act2=el('div','actions');
        var rt=el('button','act retry','↻ Повторить заявку');rt.type='button';
        rt.dataset.rid=String(r.id);
        rt.addEventListener('click',function(){retry(r,rt)});
        act2.appendChild(rt);
        art.appendChild(act2);
      }
      box.appendChild(art);
    });
    bind();
  }
  function bind(){
    document.getElementById('go-catalog').onclick=function(){location.href='/instructor-choice'};
  }
  // «Повторить заявку» (ОВ-2): POST /api/student/requests {instructor_id}
  function retry(r,btn){
    btn.disabled=true;
    api('/api/student/requests',{method:'POST',body:JSON.stringify({instructor_id:r.instructor_id})},function(res){
      if(handleAuthFail(res)){btn.disabled=false;return}
      if(res.status===200&&res.data&&res.data.ok){
        toast('Заявка отправлена повторно: инструктор увидит её в своём кабинете.');
        loadRequests();
      }else if(res.status===409){
        btn.disabled=false;
        toast('У вас уже есть активная заявка этому инструктору.');
      }else{
        btn.disabled=false;
        toast((res.data&&res.data.error)||'Не удалось отправить заявку');
      }
    });
  }
  var cur='all';
  document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});
    b.classList.add('on');cur=b.dataset.f;render(cur);
  })});

  // Плитка «Мои заявки» (BUG-047): открывает раздел внутри кабинета
  // (отдельной страницы /my-requests больше нет — 301 на /cabinet#/my-requests)
  var tileRequests = document.getElementById('tile-requests');
  if (tileRequests) {
    tileRequests.addEventListener('click', function () {
      navTo('Мои заявки');
    });
  }

  // =====================================================================
  // Спринт 5 (change add-booking-docs): раздел «Мои брони» (мокап
  // booking-student.html). Слоты — GET /api/student/instructors/{id}/slots
  // (СЕРВЕРНАЯ проверка пары, иначе 403); бронь — POST /api/student/bookings
  // {availability_id} (гонки: занято → 409); календарь — GET
  // /api/student/bookings; «Повторить» после отклонения (ОВ-5) — повторный
  // POST по слоту, найденному в текущем графике.
  var BK_DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  var BK_ST = {new: ['Запрос отправлен', 'bk-st-new'],
               confirmed: ['Подтверждена', 'bk-st-ok'],
               rejected: ['Отклонена', 'bk-st-den']};
  var bkSlots = [];      // ответ slots-эндпоинта: {id,weekday,start_time,end_time,state}
  var bkPair = null;     // {instructor_id, instructor_full_name, car, decided_at}
  var bkPicked = null;   // слот, выбранный для брони
  function bkCarText(c) {
    if (!c) return '—';
    var tr = c.transmission === 'automatic' ? 'автомат' : c.transmission === 'manual' ? 'механика' : (c.transmission || '');
    return [c.brand, c.model].filter(Boolean).join(' ') + (c.year ? ' ' + c.year : '') + (tr ? ' · ' + tr : '');
  }
  function loadBookingsSection() {
    api('/api/student/requests', {}, function (res) {
      if (handleAuthFail(res)) return;
      if (!res.data || !res.data.ok) { toast((res.data && res.data.error) || 'Не удалось загрузить заявку пары'); return; }
      bkPair = null;
      (res.data.requests || []).forEach(function (r) {
        if (r.status === 'accepted') bkPair = r;
      });
      var pairBox = document.getElementById('bk-pair');
      var nopair = document.getElementById('bk-nopair');
      var cal = document.getElementById('bk-cal');
      if (!bkPair) {
        pairBox.style.display = 'none';
        nopair.style.display = 'block';
        cal.style.display = 'none';
        renderMyBookings([]);
        return;
      }
      nopair.style.display = 'none';
      pairBox.style.display = 'flex';
      var fio = bkPair.instructor_full_name || 'Инструктор';
      document.getElementById('bk-pair-sic').textContent =
        fio.split(' ').slice(0, 2).map(function (w) { return (w[0] || '').toUpperCase(); }).join('');
      document.getElementById('bk-pair-name').textContent = fio;
      document.getElementById('bk-pair-sub').textContent =
        'ваш инструктор' + (bkPair.decided_at ? ' с ' + fmtDate(bkPair.decided_at) : '');
      document.getElementById('bk-pair-car').textContent = bkCarText(bkPair.car);
      loadSlotsAndBookings();
    });
  }
  function loadSlotsAndBookings() {
    api('/api/student/instructors/' + bkPair.instructor_id + '/slots', {}, function (res) {
      if (handleAuthFail(res)) return;
      if (!res.data || !res.data.ok) {
        toast((res.data && res.data.error) || 'Не удалось загрузить график');
        return;
      }
      bkSlots = res.data.slots || [];
      api('/api/student/bookings', {}, function (res2) {
        if (handleAuthFail(res2)) return;
        renderSchedule(res2 && res2.data && res2.data.ok ? (res2.data.bookings || []) : []);
        renderMyBookings(res2 && res2.data && res2.data.ok ? (res2.data.bookings || []) : []);
      });
    });
  }
  function renderSchedule() {
    var cal = document.getElementById('bk-cal');
    var grid = document.getElementById('bk-grid');
    if (!bkSlots.length) { cal.style.display = 'none'; return; }
    cal.style.display = 'block';
    grid.innerHTML = '';
    var now = nowMoscow();
    var todayIdx = (now.getDay() + 6) % 7;
    grid.appendChild(el('span', 'bk-corner', 'время'));
    for (var d = 0; d < 7; d++) {
      var dh = el('div', 'bk-dh' + (d === todayIdx ? ' today' : ''));
      dh.appendChild(el('small', null, BK_DAYS[d]));
      grid.appendChild(dh);
    }
    // строки — уникальные интервалы графика, столбцы — дни недели
    var rows = {};
    bkSlots.forEach(function (s) { rows[s.start_time + '-' + s.end_time] = 1; });
    Object.keys(rows).sort().forEach(function (k) {
      var parts = k.split('-');
      var start = parts[0], end = parts[1];
      grid.appendChild(el('span', 'bk-tlabel', start.slice(0, 5) + '–' + end.slice(0, 5)));
      for (var d2 = 0; d2 < 7; d2++) {
        // let (не var): замыкание клика должно видеть СВОЙ слот строки
        let slot = null;
        bkSlots.forEach(function (s) {
          if (s.weekday === d2 && s.start_time === start && s.end_time === end) slot = s;
        });
        var btn = document.createElement('button');
        btn.type = 'button';
        // состояния бэкенда free/busy/pending → классы мокапа free/taken/mine
        var cls = slot ? (slot.state === 'pending' ? 'mine'
                        : slot.state === 'busy' ? 'taken' : slot.state) : 'off';
        btn.className = 'bk-slot ' + cls;
        btn.title = BK_DAYS[d2] + ', ' + start + '–' + end + ' — ' +
          (slot ? (slot.state === 'free' ? 'свободно, нажмите для брони'
                : slot.state === 'pending' ? 'ваш запрос на рассмотрении' : 'занято')
               : 'не в графике');
        if (slot && slot.state === 'free') {
          btn.addEventListener('click', function () { openBookModal(slot); });
        } else {
          btn.disabled = true;
        }
        grid.appendChild(btn);
      }
    });
  }
  function openBookModal(slot) {
    bkPicked = slot;
    document.getElementById('bk-instr').textContent = bkPair.instructor_full_name || '—';
    document.getElementById('bk-day').textContent = BK_DAYS[slot.weekday] || '—';
    document.getElementById('bk-time').textContent = slot.start_time.slice(0, 5) + '–' + slot.end_time.slice(0, 5);
    document.getElementById('bk-car').textContent = bkCarText(bkPair.car);
    document.getElementById('m-book').classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeBookModal() {
    document.getElementById('m-book').classList.remove('open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-close-book]').forEach(function (b) {
    b.addEventListener('click', closeBookModal);
  });
  document.getElementById('m-book').addEventListener('click', function (e) {
    if (e.target === this) closeBookModal();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeBookModal(); });
  document.getElementById('bk-send').addEventListener('click', function () {
    if (!bkPicked) return;
    var btn = this, slot = bkPicked;
    btn.disabled = true;
    api('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: slot.id})}, function (res) {
      btn.disabled = false;
      closeBookModal();
      if (handleAuthFail(res)) return;
      if (res.status === 200 && res.data && res.data.ok) {
        toast('Запрос отправлен (статус «на рассмотрении»). Инструктор получит его в разделе «Бронирования».');
      } else if (res.status === 409) {
        // NFR-8: слот уже занят (гонки/повтор на свой активный запрос)
        toast((res.data && res.data.error) || 'Слот уже занят — выберите другой');
      } else {
        toast((res.data && res.data.error) || 'Не удалось отправить запрос');
      }
      loadSlotsAndBookings();
    });
  });
  function renderMyBookings(bookings) {
    var box = document.getElementById('bk-list');
    box.innerHTML = '';
    document.getElementById('bk-count').textContent = bookings.length;
    if (!bookings.length) {
      box.appendChild(el('div', 'bk-none', 'Броней пока нет — выберите свободный слот в графике инструктора.'));
      return;
    }
    bookings.forEach(function (b) {
      var st = BK_ST[b.status] || BK_ST.new;
      var art = el('article', 'bk-req');
      var top = el('div', 'bk-req-top');
      var who = el('div');
      var dayName = BK_DAYS[b.weekday] ? BK_DAYS[b.weekday] + ', ' : '';  // N-9: день недели читаемо
      who.appendChild(el('b', null, dayName + (b.lesson_date || '') + ' · ' + (b.start_time || '') + '–' + (b.end_time || '')));
      who.appendChild(el('small', null, (b.instructor_full_name || '') + ' · авто: ' + bkCarText(b.car)));
      top.appendChild(who);
      top.appendChild(el('span', 'bk-status ' + st[1], st[0]));
      art.appendChild(top);
      if (b.status === 'rejected' && b.reject_comment) {
        var com = el('div', 'bk-comment');
        com.appendChild(el('span', null, 'Комментарий инструктора'));
        com.appendChild(document.createTextNode(b.reject_comment));
        art.appendChild(com);
      }
      if (b.status === 'rejected') {
        // ОВ-5: после отклонения запрос можно повторить (слот освобождён)
        var act = el('div', 'bk-actions');
        var rt = el('button', 'bk-act retry', '↻ Повторить запрос');
        rt.type = 'button';
        rt.addEventListener('click', function () { retryBooking(b, rt); });
        act.appendChild(rt);
        art.appendChild(act);
      }
      box.appendChild(art);
    });
  }
  function retryBooking(b, btn) {
    if (!bkPair) { toast('Нет принятой пары с инструктором'); return; }
    // availability_id в ответе броней нет — ищем слот графика по
    // (weekday, start_time, end_time); нет слота — запросить нечего
    var slotId = null;
    bkSlots.forEach(function (s) {
      if (s.weekday === b.weekday && s.start_time === b.start_time && s.end_time === b.end_time) slotId = s.id;
    });
    if (!slotId) {
      toast('Этого слота больше нет в графике инструктора — выберите другой');
      return;
    }
    btn.disabled = true;
    api('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: slotId})}, function (res) {
      btn.disabled = false;
      if (handleAuthFail(res)) return;
      if (res.status === 200 && res.data && res.data.ok) {
        toast('Запрос отправлен повторно (статус «на рассмотрении»).');
      } else if (res.status === 409) {
        toast((res.data && res.data.error) || 'Слот уже занят — выберите другой');
      } else {
        toast((res.data && res.data.error) || 'Не удалось отправить запрос');
      }
      loadSlotsAndBookings();
    });
  }
  document.getElementById('bk-go-choice').addEventListener('click', function () {
    location.href = '/instructor-choice';
  });

  // заглушки спринта-1 (как в мокапе, FR-6): плитки и чат не подключены;
  // .logout выведен из заглушек — у него реальный wiring выше;
  // плитки «Найти водителя»/«Мои заявки» — реальные переходы/раздел
  document.querySelectorAll('.tile:not(#tile-instructor):not(#tile-requests),.quick button,.send').forEach(function (b) {
    b.addEventListener('click', function () { alert('Заглушка: сервис появится в следующем спринте'); });
  });
})();
