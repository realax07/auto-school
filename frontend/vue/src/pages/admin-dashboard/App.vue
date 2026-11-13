<!-- Админка: дашборд с сайдбаром (заглушка). Раздел «Пользователи»: таблица + выгрузка CSV. Данные демо, в базе не хранятся
     Разметка — дословный перенос frontend/admin-dashboard.html (Спринт 15,
     change add-vue-s15-final-migration, задача 2.2; шаблон повторяет вход
     vue/admin-dashboard.html — «Разметку держать синхронной с App.vue»).
     Wiring — перенос js/admin/admin-dashboard.js 1:1 (плоский JS в
     onMounted): гвард admin_token (нет → /admin-login; 401 любого API →
     /admin-login), все запросы с X-Admin-Token; inline onclick разметки →
     @click-эквиваленты с теми же действиями (showSection/exportCsv/soon,
     logout), window.confirm('Одобрить заявку?…') — СОХРАНЕН (e2e
     page.on("dialog") без правок); deny #ic-deny-confirm disabled до
     непустого комментария (BUG-046/045-паттерн); хэш пароля в
     исходниках НЕТ (test_qa_instructor_flow). Фрагменты BUG-046 (thead без
     «Действия», rowhint, ic-deny-confirm disabled) — дословно. -->
<template>
<div class="app">
<aside>
  <div class="logo"><span class="check">✓</span><span><em>Сбер</em>Автошкола</span></div>
  <nav class="nav">
    <button class="active" @click="showSection('users', $event.currentTarget)">◉ Пользователи</button>
    <button @click="showSection('applications', $event.currentTarget)">⧉ Заявки инструкторов</button>
    <!-- Спринт 7 (ОВ-5): раздел «Автомобили» — ЕДИНСТВЕННЫЙ раздел про авто;
         старый админ-раздел /admin/cars (комплектность + блокировка, Спринт 5)
         слит в него и удален вместе с кнопкой блокировки. Заглушки
         «Отношения»/«Расписания» убраны (FR-58). -->
    <button @click="showSection('cars', $event.currentTarget)">🚗 Автомобили</button>
    <!-- Спринт 8 (change add-s8-cars-docs-booking, ОВ-1/ОВ-4): раздел
         «Документы» — верификация замененных версий ВУ и СТС
         (мокап design/mocks/admin-documents.html): ожидающие версии,
         предпросмотр (изображение ДОЛЖНО открываться), Подтвердить /
         Отклонить с ОБЯЗАТЕЛЬНОЙ причиной, фильтры, вкладка История. -->
    <button @click="showSection('documents', $event.currentTarget)">▤ Документы</button>
    <button class="soon" @click="soon()" title="Появится в следующем спринте">₽ Платежи</button>
    <button class="soon" @click="soon()" title="Появится в следующем спринте">✎ Настройки</button>
  </nav>
  <div class="side-foot">Спринт 7 · раздел «Автомобили»</div>
</aside>
<main>
  <div class="top"><h1>Пользователи</h1><div class="spacer"></div><span style="font-size:13px;color:#8ea4a8">admin</span><button class="logout" @click="adminLogout()">Выйти</button></div>
  <div class="toolbar">
    <span class="count" id="count"></span>
    <button class="btn-export" @click="exportCsv()">↓ Выгрузить CSV</button>
  </div>
  <table id="users-table">
    <thead><tr><th>ФИО</th><th>Email</th><th>Телефон</th><th>Роль</th><th>Дата регистрации</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <div class="empty" id="empty">Записей пока нет</div>

  <div id="sec-applications" style="display:none">
    <div class="top"><h1>Заявки инструкторов</h1><div class="spacer"></div></div>
    <div class="toolbar"><span class="count" id="app-count"></span></div>
    <table>
      <thead><tr><th>ФИО</th><th>Email</th><th>Телефон</th><th>Формат</th><th>ВУ</th><th>Стаж</th><th>Статус</th><th>Причина отказа</th></tr></thead>
      <tbody id="app-rows"></tbody>
    </table>
    <div class="rowhint">Строка кликабельна — откроется карточка заявки</div>
    <div class="empty" id="app-empty">Заявок пока нет</div>
  </div>

  <!-- Спринт 7 (change add-car-validation-booking, FR-66, мокап
       design/mocks/admin-cars.html): раздел «Автомобили» — все авто всех
       инструкторов (GET /api/admin/cars/completeness +status), фильтр
       «На валидации» (?status=validating), клик по строке — модалка с
       чек-листом комплектности; «Подтвердить» ЗАБЛОКИРОВАНО при <3 ракурсов
       или нет СТС (ОВ-4) — вызов POST /api/admin/cars/{id}/validate
       (серверная 409 — страховка). Кнопки блокировки больше нет (ОВ-5). -->
  <div id="sec-cars-admin" style="display:none">
    <div class="top"><h1>Автомобили</h1><div class="spacer"></div></div>
    <div class="ac-filters" id="ac-filters">
      <button class="on" data-f="all" type="button">Все</button>
      <button data-f="validating" type="button">На валидации <span class="n" id="ac-n-val"></span></button>
      <button data-f="validated" type="button">Проверено</button>
      <button data-f="draft" type="button">Черновики</button>
    </div>
    <div class="toolbar"><span class="count" id="ac-count"></span></div>
    <div class="ac-card">
      <table id="ac-table">
        <thead><tr><th>Инструктор</th><th>Марка / модель</th><th>Госномер</th><th>Статус</th><th>Комплектность</th></tr></thead>
        <tbody id="ac-rows"></tbody>
      </table>
      <div class="rowhint">Строка кликабельна — откроется карточка авто</div>
      <div class="empty" id="ac-empty">Автомобилей пока нет</div>
    </div>
  </div>

  <!-- Спринт 8 (change add-s8-cars-docs-booking, ОВ-1/ОВ-4; мокап
       design/mocks/admin-documents.html): раздел «Документы» — таблица
       ожидающих версий (тип; ВУ — ФИО инструктора; СТС — марка/модель/
       госномер + владелец; дата загрузки), вкладки «Ожидают»/«История»,
       фильтры по типу/решению, предпросмотр (изображение ОТКРЫВАЕТСЯ),
       «Подтвердить» и «Отклонить» (причина обязательна — кнопка
       заблокирована без текста; сервер 422 — страховка). После решения
       строка уходит из списка. -->
  <div id="sec-documents" style="display:none">
    <div class="top"><h1>Документы</h1><div class="spacer"></div></div>
    <p class="dc-sub">Замены документов инструкторов: водительские удостоверения (ВУ) и СТС автомобилей. До решения действует предыдущая версия — документ «не мигает». Подтверждение делает новую версию действующей; при отклонении обязательна причина отказа — её увидит инструктор, действующей останется предыдущая версия.</p>
    <div class="dc-tabs" id="dc-tabs">
      <button class="on" data-tab="pending" type="button">Ожидают <span class="n" id="dc-n-pending"></span></button>
      <button data-tab="history" type="button">История</button>
    </div>
    <div class="ac-filters" id="dc-filters">
      <button class="on" data-f="all" type="button">Все типы</button>
      <button data-f="license" type="button">ВУ</button>
      <button data-f="sts" type="button">СТС</button>
    </div>
    <div class="ac-filters" id="dc-filters-hist" style="display:none">
      <button class="on" data-fh="all" type="button">Все решения</button>
      <button data-fh="verified" type="button">Подтверждённые</button>
      <button data-fh="rejected" type="button">Отклонённые</button>
    </div>
    <div class="toolbar"><span class="count" id="dc-count"></span></div>
    <div class="ac-card">
      <div class="dc-list" id="dc-list"></div>
      <div class="dc-hist-note" id="dc-hist-note" style="display:none">История решений. Подтверждение: новая версия verified, предыдущая — архив. Отклонение: версия rejected с причиной, у инструктора действует предыдущая версия.</div>
      <div class="empty" id="dc-empty">Записей пока нет</div>
    </div>
  </div>
</main>
</div>

<!-- Спринт 7: карточка авто (модально, мокап admin-cars.html): чек-лист
     комплектности (5 ракурсов + СТС — флаги из completeness, изображения
     админу не выдаются: фото-эндпоинт доступен только владельцу и ученику
     пары), перечень недостающего, «Подтвердить» — активна только для авто
     «На валидации» с ≥3 ракурсами и СТС (ОВ-4). -->
<div class="ac-backdrop" id="ac-backdrop" role="dialog" aria-modal="true" aria-labelledby="ac-title">
  <div class="ac-modal">
    <div class="ic-head">
      <div><h2 id="ac-title">—</h2><div class="sub" id="ac-sub">—</div></div>
      <span class="badge wait" id="ac-status" style="margin-top:4px">—</span>
      <button class="ic-close" id="ac-close" aria-label="Закрыть">×</button>
    </div>
    <div class="ac-grid">
      <div class="ic-panel">
        <h3>Комплектность · 5 ракурсов + СТС</h3>
        <div class="ac-thumbs" id="ac-thumbs"></div>
        <div class="ic-note" id="ac-verdict">—</div>
      </div>
      <div class="ic-panel">
        <h3>Данные авто</h3>
        <div class="ic-rows">
          <div class="ic-row"><span>Инструктор</span><b id="ac-owner">—</b></div>
          <div class="ic-row"><span>Марка / модель</span><b id="ac-brand">—</b></div>
          <div class="ic-row"><span>Год выпуска</span><b id="ac-year">—</b></div>
          <div class="ic-row"><span>Госномер</span><b id="ac-plate">—</b></div>
          <div class="ic-row"><span>Коробка передач</span><b id="ac-trans">—</b></div>
          <div class="ic-row"><span>Комплектность</span><b id="ac-compl">—</b></div>
          <div class="ic-row"><span>Статус</span><b id="ac-status-row">—</b></div>
        </div>
        <div class="ic-note" style="margin-top:12px">Изображения ракурсов выдаются только владельцу и ученику пары — здесь видны флаги загрузки (✓/—). Подтверждение устанавливает статус «Проверено»: авто вернётся в каталог новых учеников с зелёной галочкой.</div>
      </div>
    </div>
    <div style="display:flex;gap:10px;margin-top:18px;flex-wrap:wrap">
      <button class="btn-export" id="ac-approve" style="flex:1">✓ Подтвердить авто</button>
      <button class="btn-export" id="ac-dummy" style="flex:0;background:transparent;border:1px solid rgba(238,249,249,.3);color:#cfdede">Закрыть</button>
    </div>
  </div>
</div>
<!-- тост раздела «Автомобили» (результат POST validate и серверных 409) -->
<div class="ac-toast" id="ac-toast"></div>

<!-- Спринт 8 (ОВ-4): предпросмотр документа — ИЗОБРАЖЕНИЕ ДОЛЖНО
     ОТКРЫВАТЬСЯ (проверка на приемке): GET /api/admin/documents/{version_id}/file
     с X-Admin-Token (fetch -> blob -> objectURL; у <img> нельзя задать заголовки). -->
<div class="dc-backdrop" id="dc-view" role="dialog" aria-modal="true" aria-labelledby="dc-view-title">
  <div class="dc-modal">
    <div class="ic-head">
      <div><h2 id="dc-view-title" style="font-size:18px;margin:0">—</h2><div class="sub" id="dc-view-sub">—</div></div>
      <button class="ic-close" id="dc-view-close" aria-label="Закрыть">×</button>
    </div>
    <div class="dc-preview" id="dc-view-full"><span>Загрузка…</span></div>
    <div class="dc-preview-foot">Изображение выдаёт авторизованный эндпоинт GET /api/admin/documents/{version_id}/file (X-Admin-Token, Content-Type image/*). Проверка на приёмке: предпросмотр обязан открываться (ОВ-4).</div>
  </div>
</div>

<!-- Спринт 8 (ОВ-1): отклонение замены — причина ОБЯЗАТЕЛЬНА: кнопка
     заблокирована без непустого текста (сервер 422 — страховка).
     Действующая (предыдущая) версия остается verified. -->
<div class="dc-backdrop" id="dc-deny" role="dialog" aria-modal="true" aria-labelledby="dc-deny-title">
  <div class="dc-modal small">
    <div class="ic-head">
      <div><h2 id="dc-deny-title" style="font-size:18px;margin:0">Отклонить замену</h2><div class="sub" id="dc-deny-sub">—</div></div>
      <button class="ic-close" id="dc-deny-close" aria-label="Закрыть">×</button>
    </div>
    <label class="dc-deny-lbl" for="dc-reason">Причина отказа <em>— обязательна</em></label>
    <textarea id="dc-reason" placeholder="Например: фото нечитаемо, документ обрезан — загрузите снимок целиком при дневном свете"></textarea>
    <div class="dc-deny-note">Причина будет показана инструктору в «Моих документах». Действующая (предыдущая) версия документа останется verified — инструктор не останется без документа и сможет загрузить замену заново.</div>
    <div class="dc-actions-m">
      <button class="dc-m-btn danger" id="dc-deny-go" disabled>Отклонить</button>
      <button class="dc-m-btn ghost" id="dc-deny-cancel">Отмена</button>
    </div>
  </div>
</div>

<!-- Карточка инструктора: открытие по клику на строку (FR-25). Изображение ВУ
     загружается с админ-токеном: GET /api/admin/instructor-applications/{id}/license-image
     c X-Admin-Token (blob -> objectURL; у <img> нельзя задать заголовки).
     Без токена/с неверным — 401, изображение не возвращается (FR-24, NFR-1). -->
<div class="ic-backdrop" id="ic-backdrop" role="dialog" aria-modal="true" aria-labelledby="ic-name">
  <div class="ic-modal">
    <div class="ic-head">
      <div><h2 id="ic-name">—</h2><div class="sub" id="ic-sub">Заявка инструктора № —</div></div>
      <button class="ic-close" id="ic-close" aria-label="Закрыть">×</button>
    </div>
    <div class="ic-grid2">
      <div class="ic-panel">
        <h3>Данные анкеты</h3>
        <div class="ic-rows">
          <div class="ic-row"><span>Фамилия</span><b id="ic-last">—</b></div>
          <div class="ic-row"><span>Имя</span><b id="ic-first">—</b></div>
          <div class="ic-row"><span>Отчество</span><b id="ic-pat">—</b></div>
          <div class="ic-row"><span>Email</span><b id="ic-email">—</b></div>
          <div class="ic-row"><span>Телефон</span><b id="ic-phone">—</b></div>
          <div class="ic-row"><span>Стаж вождения</span><b id="ic-exp">—</b></div>
          <div class="ic-row"><span>Автомобиль</span><b id="ic-car">—</b></div>
          <div class="ic-row"><span>Статус</span><b id="ic-status">—</b></div>
          <div class="ic-row"><span>Причина отказа</span><b id="ic-review">—</b></div>
        </div>
      </div>
      <div>
        <div class="ic-panel">
          <h3>Водительское удостоверение</h3>
          <div class="ic-img-ph" id="ic-license"><span>Загрузка…</span></div>
        </div>
        <div class="ic-note"><b>Доступ к изображению:</b> файл хранится вне раздаваемой статики и выдаётся только по эндпоинту с валидным админ-токеном. Без токена — отказ, изображение не возвращается.</div>
      </div>
    </div>
    <div style="display:flex;gap:10px;margin-top:18px;flex-wrap:wrap">
      <button class="btn-export" id="ic-approve" style="flex:1">✓ Одобрить заявку</button>
      <button class="btn-export" id="ic-deny" style="flex:1">✕ Отклонить</button>
    </div>
    <!-- Отклонение — только здесь, в модалке (BUG-046, решение Заказчика):
         причина отказа обязательна, подтверждение заблокировано до
         непустого комментария (паттерн BUG-045). -->
    <div id="ic-deny-box" style="display:none;margin-top:14px">
      <label style="display:block;font-size:12px;color:#9eabb4;margin-bottom:7px">Причина отказа (обязательно):</label>
      <textarea id="ic-deny-comment" rows="3" style="width:100%;background:#0a1117;border:1px solid #ffffff1c;color:#f1f5f6;border-radius:10px;padding:10px;font:inherit;font-size:13px;resize:vertical"></textarea>
      <div style="margin-top:10px;display:flex;gap:10px">
        <button class="btn-export" id="ic-deny-confirm" disabled>Отклонить</button>
        <button class="btn-export" id="ic-deny-cancel">Отмена</button>
      </div>
    </div>
  </div>
</div>
</template>

<style>
/* Design-guard якорь TC-UI-014 (BUG-046: желтый wait-бейдж «На рассмотрении»).
   Правило — вербатим из styles.css (дословный перенос <style> легаси) и
   design/mocks/admin-dashboard.html: test_ui_playwright сверяет фрагмент
   по носителям «вход + App.vue» — дубль идемпотентен (тот же селектор и
   свойства; CSS глобален). */
.badge.wait{background:#3a2f14;color:#ffc76e;border:1px solid #8a6d1f}
</style>

<script>
// Wiring — перенос js/admin/admin-dashboard.js 1:1 (плоский JS в
// onMounted, прецедент С14 documents — bridge для @click-эквивалентов
// inline onclick). БЕЗ импортов shared — свой fetch с X-Admin-Token,
// как legacy. Токен — sessionStorage 'admin_token' in-memory.
import { onMounted } from 'vue';

export default {
  name: 'AdminDashboardApp',
  setup: function () {
    // inline onclick разметки → эквиваленты с теми же действиями
    // (design.md «Границы правок тестов»); реализация — в onMounted ниже.
    var bridge = {};
    function showSection(name, btn){return bridge.showSection(name, btn)}
    function exportCsv(){return bridge.exportCsv()}
    function soon(){return bridge.soon()}
    function adminLogout(){
      sessionStorage.removeItem('admin_token');
      location.href='/admin-login';
    }

    onMounted(function(){
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
        return 'СТС · версия '+d.version+' · инструктор '+(d.instructor_full_name||'—')
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
      // onclick-эквиваленты в разметке — bridge (ES-модуль глобальные
      // объявления не создает — механика legacy window.showSection)
      bridge.showSection = showSection;
      bridge.exportCsv = exportCsv;
      bridge.soon = soon;
    });

    return {
      showSection: showSection,
      exportCsv: exportCsv,
      soon: soon,
      adminLogout: adminLogout,
    };
  },
};
</script>
