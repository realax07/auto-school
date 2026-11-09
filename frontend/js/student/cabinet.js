/* из cabinet.html (блок 1) */
// Спринт 6, Партия B: toast/el/fmtDate/nowMoscow/fioOf — общие хелперы
// js/utils.js; fetch-логика (своя очистка сессии) — локальная.
import { toast, el, fmtDate, nowMoscow, fioOf } from '../shared/utils.js';
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
  var bkInstances = [];  // экземпляры ОТОБРАЖАЕМОЙ недели (GET slots?date=)
  var bkPair = null;     // {instructor_id, instructor_full_name, car, decided_at}
  var bkPicked = null;   // экземпляр, выбранный для брони
  var bkMonday = null;   // понедельник отображаемой недели (Date с полями МСК)
  var bkRows = [];       // уникальные интервалы недели [[start,end]...] — решетка
  var bkHasSchedule = false; // график инструктора непуст (скрытие пустого календаря)
  // Спринт 10 (задача 6.1, FR-87/FR-94): реальный календарь ученика —
  // та же арифметика дат, что у инструктора; «сейчас» — МСК (UTC+3,
  // nowMoscow), локальная таймзона браузера не используется
  function bkPad(n) { return (n < 10 ? '0' : '') + n; }
  function bkIso(d) { return d.getFullYear() + '-' + bkPad(d.getMonth() + 1) + '-' + bkPad(d.getDate()); }
  function bkAddDays(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function bkMondayOf(d) { return bkAddDays(d, -((d.getDay() + 6) % 7)); }
  function bkStartOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  // бронирование ТОЛЬКО будущих (FR-96/NFR-31, граница MIN-1 единая с
  // сервером): начало экземпляра (date + start_time) СТРОГО больше NOW (МСК)
  function bkIsFuture(dateIso, startTime) {
    var p = dateIso.split('-'), sp = startTime.split(':');
    var t = new Date(+p[0], +p[1] - 1, +p[2], +sp[0], +sp[1] || 0, 0);
    return t.getTime() > nowMoscow().getTime();
  }
  // подпись диапазона (D9): обе части месяца/года при пересечении
  var BK_MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                   'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  function bkRangeLabel() {
    var a = bkMonday, b = bkAddDays(bkMonday, 6);
    if (a.getFullYear() !== b.getFullYear())
      return a.getDate() + ' ' + BK_MONTHS[a.getMonth()] + ' ' + a.getFullYear() + ' — ' + b.getDate() + ' ' + BK_MONTHS[b.getMonth()] + ' ' + b.getFullYear();
    if (a.getMonth() !== b.getMonth())
      return a.getDate() + ' ' + BK_MONTHS[a.getMonth()] + ' — ' + b.getDate() + ' ' + BK_MONTHS[b.getMonth()] + ' ' + a.getFullYear();
    return a.getDate() + ' – ' + b.getDate() + ' ' + BK_MONTHS[a.getMonth()] + ' ' + a.getFullYear();
  }
  function bkRenderNav() {
    document.getElementById('bk-range').textContent = bkRangeLabel();
    var diff = Math.round((bkMonday - bkMondayOf(nowMoscow())) / 864e5);
    document.getElementById('bk-prev').disabled = diff <= -364; // горизонт ±12 месяцев
    document.getElementById('bk-next').disabled = diff >= 364;
  }
  function bkNavWeek(n) {
    bkMonday = bkAddDays(bkMonday, n);
    bkRenderNav();
    bkInstances = [];
    // решетка и подпись — локально мгновенно (NFR-32); экземпляры недели —
    // GET slots?date= асинхронно, без перезагрузки страницы
    bkRenderGrid();
    bkLoadInstances();
  }
  document.getElementById('bk-prev').addEventListener('click', function () { bkNavWeek(-7); });
  document.getElementById('bk-next').addEventListener('click', function () { bkNavWeek(7); });
  document.getElementById('bk-this').addEventListener('click', function () {
    bkMonday = bkMondayOf(nowMoscow());
    bkRenderNav();
    bkInstances = [];
    bkRenderGrid();
    bkLoadInstances();
  });
  function bkCarText(c) {
    if (!c) return '—';
    var tr = c.transmission === 'automatic' ? 'автомат' : c.transmission === 'manual' ? 'механика' : (c.transmission || '');
    return [c.brand, c.model].filter(Boolean).join(' ') + (c.year ? ' ' + c.year : '') + (tr ? ' · ' + tr : '');
  }
  // Спринт 7 (задачи 2.1/6.2, ОВ-2): авторизованная загрузка фото авто
  // (обычный <img src> получит 401 — токен уходит заголовком, ответ -> blob)
  function loadImgAuth(url, img) {
    if (!url) return;
    fetch(url, { headers: { 'X-Session-Token': token || '' } })
      .then(function (r) { return r.ok ? r.blob() : null; })
      .then(function (blob) {
        if (!blob) return;
        // NIT-1 (review-001): revoke прежнего blob-URL перед заменой —
        // перерисовки раздела не копят объектные URL
        if (img._blobUrl) URL.revokeObjectURL(img._blobUrl);
        img._blobUrl = URL.createObjectURL(blob);
        img.src = img._blobUrl;
      })
      .catch(function () { /* 404/сеть: остается плейсхолдер, не битая картинка */ });
  }
  // бейдж статуса авто (ОВ-2): validating — желтый «Не проверено»,
  // validated — зеленый «Проверено» + галочка (:before в CSS);
  // draft/удален/нет статуса — null (бейдж скрыт)
  function carBadgeNode(status) {
    if (status === 'validating') return el('span', 'car-badge val', 'Не проверено');
    if (status === 'validated') return el('span', 'car-badge ok', 'Проверено');
    return null;
  }
  function setBadgeEl(elm, status) {
    var badge = carBadgeNode(status);
    if (badge) {
      elm.className = badge.className;
      elm.textContent = badge.textContent;
      elm.style.display = '';
    } else {
      elm.style.display = 'none';
      elm.textContent = '';
    }
  }
  // карточка прикрепленного авто рядом со слотами (задача 6.2): фото +
  // название + бейдж; данные — car из броней (photo_url приоритет front;
  // draft -> у ученика без photo_url — плейсхолдер, ОВ-2)
  function renderPairCarCard(bookings) {
    var card = document.getElementById('bk-car-card');
    var car = null;
    bookings.forEach(function (b) { if (!car && b.car && b.car.id) car = b.car; });
    if (!car && bkPair && bkPair.car && bkPair.car.id) car = bkPair.car;
    if (!car) { card.style.display = 'none'; setBadgeEl(document.getElementById('bk-pair-badge'), null); return; }
    card.style.display = 'flex';
    var photo = document.getElementById('bk-car-photo');
    photo.innerHTML = '';
    if (car.photo_url) {
      var img = document.createElement('img');
      img.alt = 'Фото автомобиля инструктора';
      photo.appendChild(img);
      loadImgAuth(car.photo_url, img);
    } else {
      photo.appendChild(el('span', 'ph', '🚗'));
    }
    document.getElementById('bk-car-name').textContent = bkCarText(car);
    setBadgeEl(document.getElementById('bk-car-badge'), car.car_status);
    // бейдж статуса авто у пары (задача 2.1/6.2, ОВ-2)
    setBadgeEl(document.getElementById('bk-pair-badge'), car.car_status);
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
      // при открытии — неделя текущей даты (МСК); колонки и подпись
      // отрисовываются локально, экземпляры — асинхронно (FR-94/NFR-32)
      bkMonday = bkMondayOf(nowMoscow());
      bkRenderNav();
      loadSlotsAndBookings();
    });
  }
  function loadSlotsAndBookings() {
    // экземпляры недели — GET slots?date= (D7: разворот серий на сервере);
    // свои брони/список «Мои брони» — независимо от недели
    bkLoadInstances();
    api('/api/student/bookings', {}, function (res2) {
      if (handleAuthFail(res2)) return;
      var bks = res2 && res2.data && res2.data.ok ? (res2.data.bookings || []) : [];
      renderPairCarCard(bks);
      renderMyBookings(bks);
    });
  }
  function bkLoadInstances() {
    api('/api/student/instructors/' + bkPair.instructor_id + '/slots?date=' + bkIso(bkMonday), {}, function (res) {
      if (handleAuthFail(res)) return;
      if (!res.data || !res.data.ok) {
        toast((res.data && res.data.error) || 'Не удалось загрузить график');
        return;
      }
      bkInstances = res.data.instances || [];
      if (bkInstances.length) bkHasSchedule = true;
      bkCollectRows();
      var cal = document.getElementById('bk-cal');
      if (!bkInstances.length && !bkHasSchedule) {
        // график пуст (первая загрузка без слотов) — прежнее поведение
        cal.style.display = 'none';
        return;
      }
      cal.style.display = 'block';
      bkRenderGrid();
    });
  }
  function bkCollectRows() {
    var seen = {};
    bkRows = [];
    bkInstances.forEach(function (s) {
      var k = s.start_time + '|' + s.end_time;
      if (seen[k]) return;
      seen[k] = 1;
      bkRows.push([s.start_time, s.end_time]);
    });
    bkRows.sort(function (a, b) { return a[0] < b[0] ? -1 : 1; });
  }
  // решетка: колонки — 7 РЕАЛЬНЫХ дат от понедельника отображаемой недели
  // (подпись атомарна с колонками); экземпляры — ровно на своих датах
  function bkRenderGrid() {
    var grid = document.getElementById('bk-grid');
    grid.innerHTML = '';
    var now = nowMoscow();
    var todayIso = bkIso(bkStartOfDay(now));
    grid.appendChild(el('span', 'bk-corner', 'время'));
    for (var d = 0; d < 7; d++) {
      var dt = bkAddDays(bkMonday, d);
      var dh = el('div', 'bk-dh' + (bkIso(dt) === todayIso ? ' today' : ''));
      dh.appendChild(el('small', null, BK_DAYS[d]));
      dh.appendChild(el('b', null, String(dt.getDate())));
      grid.appendChild(dh);
    }
    if (!bkRows.length) {
      var note = el('div', 'bk-week-empty', 'На выбранной неделе слотов нет — листайте другие недели.');
      grid.appendChild(note);
      return;
    }
    bkRows.forEach(function (row) {
      grid.appendChild(el('span', 'bk-tlabel', row[0].slice(0, 5) + '–' + row[1].slice(0, 5)));
      for (var d2 = 0; d2 < 7; d2++) {
        var iso = bkIso(bkAddDays(bkMonday, d2));
        // let (не var): замыкание клика должно видеть СВОЙ экземпляр ячейки
        let inst = null;
        bkInstances.forEach(function (s) {
          if (s.date === iso && s.start_time === row[0] && s.end_time === row[1]) inst = s;
        });
        var btn = document.createElement('button');
        btn.type = 'button';
        if (inst) {
          // состояния бэкенда free/busy/pending → классы мокапа free/taken/mine;
          // прошедший/начавшийся экземпляр (начало ≤ NOW, МСК) — просмотр
          // без брони (FR-96), прошлые недели — вся сетка просмотр
          var past = !bkIsFuture(inst.date, inst.start_time);
          var cls = inst.state === 'pending' ? 'mine'
                    : inst.state === 'busy' ? 'taken' : 'free';
          btn.className = 'bk-slot ' + cls + (past ? ' past' : '');
          btn.title = BK_DAYS[inst.weekday] + ', ' + inst.date.split('-').reverse().join('.') + ', ' +
            inst.start_time.slice(0, 5) + '–' + inst.end_time.slice(0, 5) + ' — ' +
            (past ? 'прошедшее — только просмотр'
                  : inst.state === 'free' ? 'свободно, нажмите для брони'
                  : inst.state === 'pending' ? 'ваш запрос на рассмотрении' : 'занято');
          if (inst.state === 'free' && !past) {
            btn.addEventListener('click', function () { openBookModal(inst); });
          } else {
            btn.disabled = true;
          }
        } else {
          btn.className = 'bk-slot off';
          btn.disabled = true;
        }
        grid.appendChild(btn);
      }
    });
  }
  function openBookModal(inst) {
    bkPicked = inst;
    document.getElementById('bk-instr').textContent = bkPair.instructor_full_name || '—';
    // бронь фиксируется на КОНКРЕТНОЙ дате экземпляра (FR-96)
    document.getElementById('bk-day').textContent =
      (BK_DAYS[inst.weekday] ? BK_DAYS[inst.weekday] + ', ' : '') +
      inst.date.split('-').reverse().join('.');
    document.getElementById('bk-time').textContent = inst.start_time.slice(0, 5) + '–' + inst.end_time.slice(0, 5);
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
    var btn = this, inst = bkPicked;
    btn.disabled = true;
    // бронь на КОНКРЕТНЫЙ экземпляр: availability_id + date (Спринт 10)
    api('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: inst.availability_id, date: inst.date})}, function (res) {
      btn.disabled = false;
      closeBookModal();
      if (handleAuthFail(res)) return;
      if (res.status === 200 && res.data && res.data.ok) {
        toast('Запрос отправлен (статус «на рассмотрении»). Инструктор получит его в разделе «Бронирования».');
      } else if (res.status === 409) {
        // NFR-8: слот уже занят (гонки/повтор на свой активный запрос)
        toast((res.data && res.data.error) || 'Слот уже занят — выберите другой');
      } else {
        // в т.ч. 422 «Слот уже начался или прошел» — сервер проверяет всегда
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
      // Спринт 7 (ОВ-2): бейдж статуса авто брони (validated «Проверено» +
      // галочка / validating желтый «Не проверено»; draft — без бейджа)
      var carBadge = carBadgeNode(b.car && b.car.car_status);
      if (carBadge) top.appendChild(carBadge);
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
    // экземпляр графика по (weekday, время) отклоненной брони; при наличии
    // lesson_date — ровно её неделя среди загруженных экземпляров
    var inst = null, fallback = null;
    bkInstances.forEach(function (s) {
      if (s.weekday !== b.weekday || s.start_time !== b.start_time || s.end_time !== b.end_time) return;
      if (b.lesson_date && s.date === b.lesson_date) inst = s;
      if (!fallback) fallback = s;
    });
    if (!inst) inst = b.lesson_date ? null : fallback;
    if (!inst) {
      toast('Этого слота больше нет в графике инструктора — выберите другой');
      return;
    }
    if (!bkIsFuture(inst.date, inst.start_time)) {
      // бронирование только будущих (FR-96): прошедший/начавшийся — просмотр
      toast('Слот уже начался или прошел — бронирование недоступно');
      return;
    }
    btn.disabled = true;
    api('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: inst.availability_id, date: inst.date})}, function (res) {
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
