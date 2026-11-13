<!-- Мокап: Личный кабинет ученика (Спринт 1). Стиль референса, чат-бар как на лендинге.
     Плитки-сервисы — заглушки (визуал). Кнопка выхода -> admin/учетка сессии.
     Wiring (единственные отличия от мокапа): GET /api/auth/me с X-Session-Token
     из sessionStorage (401 -> редирект на главную, к модалке входа), 200 ->
     подстановка ФИО; «Выйти» -> POST /api/auth/logout -> очистка sessionStorage ->
     редирект на главную. Плитки/чат-бар/quick — заглушки (alert из мокапа).
     BUG-047 (решение Заказчика 2026-10-17): кабинет ученика — ЕДИНЫЙ лейаут
     (сайдбар слева: «Главная», «Мои заявки», «Выбрать инструктора»; контент
     справа; шапка сверху). Раздел «Мои заявки» перенесен из frontend/
     my-requests.html внутрь кабинета как таб (бейджи желтый/зеленый/красный,
     комментарии отказов, «Повторить заявку», переход на /review — форма отзыва
     остается отдельной целевой страницей). Отдельной страницы /my-requests
     больше нет: 301 → /cabinet#/my-requests открывает этот же раздел.
     Стили мокапа не изменялись (design-guard test_cabinet_page.py) —
     новые правила только добавлены в конце <style>.
     Разметка — дословный перенос frontend/cabinet.html (Спринт 15,
     change add-vue-s15-final-migration, задача 4.2; шаблон повторяет вход
     vue/cabinet.html — «Разметку держать синхронной с App.vue»; у сетки
     #bk-grid угловая метка «время» в шаблоне статична — во входе та же).
     Wiring — перенос js/student/cabinet.js 1:1 (плоский JS в onMounted,
     реактивные списки — design.md «Границы правок тестов»): el()-отрисовка
     карточек/сеток → интерполяция {{ }} (текстовые узлы — XSS-правило
     выполняется построением); style.display/innerHTML списков → v-if/v-for/
     :style-эквиваленты с теми же значениями; модалки/тосты/хеш-навигация —
     flat DOM как legacy. Хелперы — из vue/src/shared/ (toast/fmtDate/
     nowMoscow/fioOf; el/initials не переносятся — инициалы инлайном). -->
<template>
<div class="app">
<aside class="side">
  <div class="side-brand"><span class="check">✓</span><div><em>Сбер</em>Автошкола<small>Кабинет ученика</small></div></div>
  <!-- BUG-047: примитивная навигация ученика; активный раздел подсвечивается.
       Спринт 5: добавлен раздел «Мои брони» (booking-student.html) -->
  <nav class="snav">
    <button class="on" data-tab="Главная" type="button"><span class="ico">⌂</span>Главная</button>
    <button data-tab="Мои заявки" type="button"><span class="ico">✉</span>Мои заявки</button>
    <button data-goto="/instructor-choice" type="button"><span class="ico">▤</span>Выбрать инструктора</button>
    <button data-tab="Мои брони" type="button"><span class="ico">◷</span>Мои брони</button>
  </nav>
</aside>
<div class="hero"><div class="frame">
<header>
  <div class="user"><span class="uname">Иван Иванов</span><button class="logout">Выйти</button></div>
</header>

<!-- раздел «Главная» (единственный контент кабинета до BUG-047) -->
<div id="sec-home">
<div class="greet">ЛИЧНЫЙ КАБИНЕТ<b>Добро пожаловать, Иван!</b></div>

<!-- чат-бар (как на главной) -->
<section class="assistant">
  <div class="ai-head"><div class="avatar"></div><div><b>Гига ГАИшник</b><span>Твой AI-помощник в обучении и на дороге</span></div></div>
  <div class="prompt"><span>Спроси что угодно про обучение, экзамен или ПДД...</span><button class="send" title="Открыть чат с AI">↑</button></div>
  <div class="quick">
    <button>▢ <span>Когда экзамен?</span></button>
    <button>☷ <span>Мой прогресс</span></button>
    <button>♧ <span>Готов ли я<br>к экзамену?</span></button>
  </div>
</section>

<p class="services-title">СЕРВИСЫ</p>
<div class="tiles">
  <button class="tile"><span class="soon">СКОРО</span>
    <div class="tile-icon">◈</div><b>Обучение ПДД</b>
    <p>Теория по блокам, тренировочные вопросы и разбор ошибок перед экзаменом.</p>
    <span class="go">→</span>
  </button>
  <button class="tile"><span class="soon">СКОРО</span>
    <div class="tile-icon">◉</div><b>Онлайн экзамен</b>
    <p>Пробный экзамен в формате ГИБДД: 20 вопросов, те же правила оценки.</p>
    <span class="go">→</span>
  </button>
  <button class="tile" id="tile-instructor">
    <div class="tile-icon">▤</div><b>Найти водителя</b>
    <p>Подбор инструктора: рейтинги, отзывы и свободные окна расписания.</p>
    <span class="go">→</span>
  </button>
  <button class="tile" id="tile-requests">
    <div class="tile-icon">✉</div><b>Мои заявки</b>
    <p>Статусы заявок инструкторам, комментарий отказа и повторная подача.</p>
    <span class="go">→</span>
  </button>
</div>
</div>

<!-- раздел «Мои заявки» (BUG-047: перенесен из frontend/my-requests.html;
     бейджи статусов желтый/зеленый/красный, комментарии отказов,
     «Повторить заявку», «Оставить отзыв» → /review — отдельная форма) -->
<div id="sec-requests" style="display:none">
  <div class="page-head">
    <div class="kicker">Мои заявки</div>
    <h1>Заявки инструкторам</h1>
    <p>Инструктор рассматривает заявку сам: у отказа обязателен комментарий — вы увидите его здесь. Повторить заявку отказанному инструктору можно в любой момент.</p>
  </div>

  <div class="filters">
    <button class="on" data-f="all" type="button">Все</button>
    <button data-f="new" type="button">На рассмотрении <span class="n" id="n-new"></span></button>
    <button data-f="accepted" type="button">Принятые <span class="n" id="n-accepted"></span></button>
    <button data-f="denied" type="button">Отказанные <span class="n" id="n-denied"></span></button>
  </div>

  <div class="list" id="list">
    <article class="req" v-for="r in viewReqs" :key="String(r.id)">
      <div class="req-top">
        <span class="sic">{{ initialsOf(r.instructor_full_name || 'Инструктор') }}</span>
        <div>
          <b>{{ r.instructor_full_name || 'Инструктор' }}</b>
          <small>{{ 'заявка от ' + fmtDate(r.created_at) }}</small>
        </div>
        <span class="status" :class="reqStatus(r)[1]">{{ reqStatus(r)[0] }}</span>
      </div>
      <div class="meta-pills" v-if="r.car">
        <span class="pill">Автомобиль занятий:</span>
        <span class="pill car">{{ '🚗 ' + carText(r.car) }}</span>
      </div>
      <div class="note" v-if="r.status === 'new'">Заявка ждёт решения инструктора. Пока она активна, новую этому же инструктору подать нельзя.</div>
      <div class="note" v-if="r.status === 'accepted'">Вы приняты{{ r.decided_at ? ' ' + fmtDate(r.decided_at) : '' }}. Отзыв можно оставить один раз: <a :href="'/review?instructor=' + (r.instructor_id || '')">оставить отзыв →</a></div>
      <div class="actions" v-if="r.status === 'accepted'">
        <button class="act review" type="button" @click="goReview(r)">★ Оставить отзыв</button>
      </div>
      <div class="comment" v-if="r.status === 'denied'" :class="{'system': r.deny_comment === SYSTEM_COMMENT}">
        <span>{{ r.deny_comment === SYSTEM_COMMENT ? 'Системный комментарий' : 'Комментарий инструктора' }}</span>{{ r.deny_comment || '' }}
      </div>
      <div class="actions" v-if="r.status === 'denied'">
        <button class="act retry" type="button" :data-rid="String(r.id)" @click="retry(r, $event.currentTarget)">↻ Повторить заявку</button>
      </div>
    </article>
  </div>
  <div class="no-req" id="noreq" :style="{display: viewReqs.length ? 'none' : 'block'}"><b>Заявок пока нет</b>Найдите инструктора в каталоге и подайте первую заявку.<button id="go-catalog" type="button">Перейти к выбору инструктора</button></div>
</div>

<!-- раздел «Мои брони» (Спринт 5, change add-booking-docs; мокап
     booking-student.html): расписание инструктора по принятой паре —
     свободные слоты кликабельны, занятые приглушены без раскрытия кем,
     свой запрос «на рассмотрении» жёлтый; ниже — «Мои брони» со статусами,
     комментарием отказа и «Повторить» -->
<div id="sec-bookings" style="display:none">
  <div class="page-head bk-head">
    <div class="kicker">Бронирование занятий</div>
    <h1>Расписание инструктора</h1>
    <p>Выберите свободный слот из графика вашего инструктора и отправьте запрос брони. Инструктор подтвердит или отклонит его — с комментарием при отказе.</p>
  </div>

  <!-- пара (серверная проверка student_requests accepted; без пары слоты недоступны — 403) -->
  <div class="bk-pair" id="bk-pair" style="display:none">
    <span class="sic" id="bk-pair-sic">—</span>
    <div><b id="bk-pair-name">—</b><small id="bk-pair-sub">ваш инструктор</small></div>
    <span class="car" id="bk-pair-car">—</span>
    <!-- Спринт 7 (ОВ-2): бейдж статуса авто пары — validated «Проверено» +
         галочка / validating желтый «Не проверено»; draft — бейдж скрыт -->
    <span class="car-badge" id="bk-pair-badge" style="display:none"></span>
  </div>
  <div class="bk-none" id="bk-nopair" style="display:none">
    <!-- BUG-049: была одна слипшаяся строка — теперь вертикальный блок -->
    <h3>Нет принятого инструктора</h3>
    <p>Расписание доступно после того, как инструктор примет вашу заявку.</p>
    <button id="bk-go-choice" type="button">Перейти к выбору инструктора</button>
  </div>

  <div class="bk-cal" id="bk-cal" style="display:none">
    <!-- Спринт 7 (задача 6.2): карточка прикрепленного авто рядом со слотами:
         фото по авторизованному photo_url (плейсхолдер при отсутствии/draft/
         удаленном авто), бейдж статуса по ОВ-2 -->
    <div class="bk-car-card" id="bk-car-card" style="display:none">
      <div class="bk-car-photo" id="bk-car-photo"><span class="ph">🚗</span></div>
      <div class="bk-car-info">
        <b id="bk-car-name">Автомобиль инструктора</b>
        <small id="bk-car-sub">Автомобиль занятий — он закрепляется за бронями этой пары.</small>
        <span class="car-badge" id="bk-car-badge" style="display:none"></span>
      </div>
    </div>
    <div class="bk-cal-head">
      <div><b>График на неделю</b><div class="sub">Слоты целиком, без нарезки · прошедшее — только просмотр</div></div>
      <div class="bk-nav">
        <button id="bk-prev" type="button" aria-label="Предыдущая неделя">‹</button>
        <button id="bk-this" type="button">Эта неделя</button>
        <button id="bk-next" type="button" aria-label="Следующая неделя">›</button>
        <span id="bk-range"></span>
      </div>
    </div>
    <div class="bk-legend">
      <span><i class="lg-free"></i>свободно — клик для брони</span>
      <span><i class="lg-busy"></i>занято</span>
      <span><i class="lg-mine"></i>ваш запрос на рассмотрении</span>
    </div>
    <div class="bk-grid" id="bk-grid">
      <span class="bk-corner">время</span>
      <div v-for="d in gridHead" :key="d.iso" :class="d.today ? 'bk-dh today' : 'bk-dh'"><small>{{ d.day }}</small><b>{{ d.date }}</b></div>
      <div class="bk-week-empty" v-if="!gridRows.length">На выбранной неделе слотов нет — листайте другие недели.</div>
      <template v-for="row in gridRows" :key="row.key">
        <span class="bk-tlabel">{{ row.label }}</span>
        <button v-for="(cell, ix) in row.cells" :key="row.key + '-' + ix" type="button" :class="cell.cls" :title="cell.title" :disabled="cell.disabled" @click="cell.inst ? openBookModal(cell.inst) : null"></button>
      </template>
    </div>
    <div class="bk-hint">Бронь ставится на конкретную дату экземпляра — слот целиком. Будущие слоты кликабельны; прошедшие и уже начавшиеся — только просмотр. Повторяющиеся слоты инструктора показаны в каждой неделе, разовые — только на своей дате. Занятые слоты скрыты от раскрытия, кем занято. Если слот займут раньше вас, вернётся ошибка «Слот уже занят» — выберите другой.</div>
  </div>

  <div class="bk-sect-head"><b>Мои брони</b><span class="n" id="bk-count">0</span></div>
  <div class="bk-list" id="bk-list">
    <div class="bk-none" v-if="!bookingsList.length">Броней пока нет — выберите свободный слот в графике инструктора.</div>
    <article class="bk-req" v-for="b in bookingsList" :key="String(b.id)">
      <div class="bk-req-top">
        <div>
          <b>{{ bookingTitle(b) }}</b>
          <small>{{ (b.instructor_full_name || '') + ' · авто: ' + bkCarText(b.car) }}</small>
        </div>
        <span v-if="b.car && b.car.car_status === 'validating'" class="car-badge val">Не проверено</span>
        <span v-else-if="b.car && b.car.car_status === 'validated'" class="car-badge ok">Проверено</span>
        <span class="bk-status" :class="bkStatus(b)[1]">{{ bkStatus(b)[0] }}</span>
      </div>
      <div class="bk-comment" v-if="b.status === 'rejected' && b.reject_comment">
        <span>Комментарий инструктора</span>{{ b.reject_comment }}
      </div>
      <div class="bk-actions" v-if="b.status === 'rejected'">
        <button class="bk-act retry" type="button" @click="retryBooking(b, $event.currentTarget)">↻ Повторить запрос</button>
      </div>
    </article>
  </div>
</div>

<!-- модалка: подтверждение запроса брони (POST /api/student/bookings) -->
<div class="backdrop" id="m-book" role="dialog" aria-modal="true" aria-labelledby="bk-title">
  <div class="bk-modal">
    <div class="bk-modal-head">
      <div><h2 id="bk-title">Забронировать занятие?</h2><div class="sub">Запрос уйдёт инструктору; слот закрепится за вами до решения.</div></div>
      <button class="close" data-close-book aria-label="Закрыть">×</button>
    </div>
    <div class="bk-slotbox">
      <div class="row"><span>Инструктор</span><b id="bk-instr">—</b></div>
      <div class="row"><span>День недели</span><b id="bk-day">—</b></div>
      <div class="row"><span>Время</span><b id="bk-time">—</b></div>
      <div class="row"><span>Автомобиль</span><b id="bk-car">—</b></div>
    </div>
    <div class="bk-form-note">Слот бронируется целиком (availability_id). Если инструктор отклонит запрос — слот освободится, и вы сможете отправить его снова; комментарий отказа будет виден здесь, в «Моих бронях».</div>
    <div class="bk-form-actions">
      <button class="bk-btn primary" id="bk-send" type="button">Отправить запрос</button>
      <button class="bk-btn ghost" data-close-book type="button">Отмена</button>
    </div>
  </div>
</div>

<footer><span>СберАвтошкола · кабинет ученика</span><span>Спринт 1 · визуал</span></footer>
</div></div>
</div>
<div class="toast" id="toast"></div>
</template>

<script>
// Wiring — перенос js/student/cabinet.js 1:1 (задача 4.2). Токен —
// sessionStorage 'session_token' (свой clearSession/toLogin — как legacy);
// toast/fmtDate/nowMoscow/fioOf — из vue/src/shared/utils.js (дословные
// переносы С14/С15); fetch-логика — локальная (как legacy).
import { onMounted, ref, computed } from 'vue';
import { toast, fmtDate, nowMoscow, fioOf } from '../../shared/utils.js';

export default {
  name: 'CabinetApp',
  setup: function () {
    // --- раздел «Мои заявки» — реактивные данные (el()-отрисовка → v-for) ---
    var reqs = ref([]);
    var cur = ref('all');
    var STATUS = {new:['На рассмотрении','st-new'],accepted:['Принята','st-acc'],denied:['Отказана','st-den']};
    // системный комментарий автозакрытия (ОВ-1) — тот же текст, что в бэкенде
    var SYSTEM_COMMENT = 'Заявка закрыта: ученик принят другим инструктором';
    function reqStatus(r){return STATUS[r.status]||['?','st-new']}
    function initialsOf(fio){return fio.split(' ').slice(0,2).map(function(w){return (w[0]||'').toUpperCase()}).join('')}
    function carText(c){
      if(!c)return '';
      var tr=c.transmission==='automatic'?'автомат':c.transmission==='manual'?'механика':(c.transmission||'');
      return [c.brand,c.model].filter(Boolean).join(' ')+(c.year?' '+c.year:'')+(tr?' · '+tr:'');
    }
    var viewReqs = computed(function(){
      return reqs.value.filter(function(r){return cur.value==='all'||r.status===cur.value});
    });
    function goReview(r){location.href='/review?instructor='+(r.instructor_id||'')}
    // «Повторить заявку» (ОВ-2): POST /api/student/requests {instructor_id}
    function retry(r,btn){
      btn.disabled=true;
      localApi('/api/student/requests',{method:'POST',body:JSON.stringify({instructor_id:r.instructor_id})},function(res){
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

    // --- раздел «Мои брони» — реактивные данные (список + сетка недели) ---
    var bookingsList = ref([]);   // «Мои брони» (renderMyBookings → v-for)
    var gridHead = ref([]);       // шапка сетки недели (bkRenderGrid → v-for)
    var gridRows = ref([]);       // строки сетки недели (bkRenderGrid → v-for)
    var BK_DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    var BK_ST = {new: ['Запрос отправлен', 'bk-st-new'],
                 confirmed: ['Подтверждена', 'bk-st-ok'],
                 rejected: ['Отклонена', 'bk-st-den']};
    function bkStatus(b){return BK_ST[b.status]||BK_ST.new}
    function bookingTitle(b){
      var dayName = BK_DAYS[b.weekday] ? BK_DAYS[b.weekday] + ', ' : '';  // N-9: день недели читаемо
      return dayName + (b.lesson_date || '') + ' · ' + (b.start_time || '') + '–' + (b.end_time || '');
    }
    function bkCarText(c) {
      if (!c) return '—';
      var tr = c.transmission === 'automatic' ? 'автомат' : c.transmission === 'manual' ? 'механика' : (c.transmission || '');
      return [c.brand, c.model].filter(Boolean).join(' ') + (c.year ? ' ' + c.year : '') + (tr ? ' · ' + tr : '');
    }

    // --- состояние раздела броней (плоские переменные — как legacy) ---
    var bkInstances = [];  // экземпляры ОТОБРАЖАЕМОЙ недели (GET slots?date=)
    var bkPair = null;     // {instructor_id, instructor_full_name, car, decided_at}
    var bkPicked = null;   // экземпляр, выбранный для брони
    var bkMonday = null;   // понедельник отображаемой недели (Date с полями МСК)
    var bkRows = [];       // уникальные интервалы недели [[start,end]...] — решетка
    var bkHasSchedule = false; // график инструктора непуст (скрытие пустого календаря)

    onMounted(function(){
      // Wiring Спринта 1 (sdd §10.2–10.4): токен сессии — sessionStorage,
      // ключ session_token (единый snake_case-паттерн с admin_token
      // Спринта 0); модалка входа (задача 2.2) пишет его в тот же ключ.
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
      function localApi(path,opts,cb){
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

      // данные: GET /api/student/requests (реальный шейп backend/student_requests.py)
      function loadRequests(){
        localApi('/api/student/requests',{},function(res){
          if(handleAuthFail(res))return;
          if(!res.data||!res.data.ok){toast((res.data&&res.data.error)||'Не удалось загрузить заявки');return}
          reqs.value=res.data.requests||[];
          renderFilters();
        });
      }
      function renderFilters(){
        document.getElementById('n-new').textContent=reqs.value.filter(function(r){return r.status==='new'}).length?'·'+reqs.value.filter(function(r){return r.status==='new'}).length:'';
        document.getElementById('n-accepted').textContent=reqs.value.filter(function(r){return r.status==='accepted'}).length?'·'+reqs.value.filter(function(r){return r.status==='accepted'}).length:'';
        document.getElementById('n-denied').textContent=reqs.value.filter(function(r){return r.status==='denied'}).length?'·'+reqs.value.filter(function(r){return r.status==='denied'}).length:'';
      }
      document.getElementById('go-catalog').onclick=function(){location.href='/instructor-choice'};
      document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
        document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});
        b.classList.add('on');cur.value=b.dataset.f;
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
      // draft/удален/нет статуса — скрыт (бейдж не показывается).
      // Плоский аналог carBadgeNode — setBadgeEl для бейджей пары/авто
      // (реактивный эквивалент carBadgeNode — v-if/v-else-if в шаблоне
      // карточек «Моих броней» с теми же классами/текстами).
      function setBadgeEl(elm, status) {
        var cls, text;
        if (status === 'validating') { cls = 'car-badge val'; text = 'Не проверено'; }
        else if (status === 'validated') { cls = 'car-badge ok'; text = 'Проверено'; }
        else { cls = null; text = null; }
        if (cls) {
          elm.className = cls;
          elm.textContent = text;
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
          var ph = document.createElement('span'); ph.className = 'ph'; ph.textContent = '🚗';
          photo.appendChild(ph);
        }
        document.getElementById('bk-car-name').textContent = bkCarText(car);
        setBadgeEl(document.getElementById('bk-car-badge'), car.car_status);
        // бейдж статуса авто у пары (задача 2.1/6.2, ОВ-2)
        setBadgeEl(document.getElementById('bk-pair-badge'), car.car_status);
      }
      function loadBookingsSection() {
        localApi('/api/student/requests', {}, function (res) {
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
        localApi('/api/student/bookings', {}, function (res2) {
          if (handleAuthFail(res2)) return;
          var bks = res2 && res2.data && res2.data.ok ? (res2.data.bookings || []) : [];
          renderPairCarCard(bks);
          renderMyBookings(bks);
        });
      }
      function bkLoadInstances() {
        localApi('/api/student/instructors/' + bkPair.instructor_id + '/slots?date=' + bkIso(bkMonday), {}, function (res) {
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
      // (подпись атомарна с колонками); экземпляры — ровно на своих датах.
      // Реактивный эквивалент legacy-отрисовки через el(): строим структуру
      // {gridHead, gridRows} — шаблон рендерит те же классы/тексты/титулы.
      function bkRenderGrid() {
        var now = nowMoscow();
        var todayIso = bkIso(bkStartOfDay(now));
        var head = [];
        for (var d = 0; d < 7; d++) {
          var dt = bkAddDays(bkMonday, d);
          head.push({ iso: bkIso(dt), day: BK_DAYS[d], date: String(dt.getDate()), today: bkIso(dt) === todayIso });
        }
        var rowsOut = [];
        if (bkRows.length) {
          bkRows.forEach(function (row) {
            var label = row[0].slice(0, 5) + '–' + row[1].slice(0, 5);
            var cells = [];
            for (var d2 = 0; d2 < 7; d2++) {
              var iso = bkIso(bkAddDays(bkMonday, d2));
              // каждый экземпляр ячейки — свой объект (клик по ячейке видит
              // СВОЙ экземпляр — эквивалент legacy let-цикла)
              var inst = null;
              bkInstances.forEach(function (s) {
                if (s.date === iso && s.start_time === row[0] && s.end_time === row[1]) inst = s;
              });
              var cell = { cls: 'bk-slot off', title: '', disabled: true, inst: null };
              if (inst) {
                // состояния бэкенда free/busy/pending → классы мокапа free/taken/mine;
                // прошедший/начавшийся экземпляр (начало ≤ NOW, МСК) — просмотр
                // без брони (FR-96), прошлые недели — вся сетка просмотр
                var past = !bkIsFuture(inst.date, inst.start_time);
                var cls = inst.state === 'pending' ? 'mine'
                          : inst.state === 'busy' ? 'taken' : 'free';
                var title = BK_DAYS[inst.weekday] + ', ' + inst.date.split('-').reverse().join('.') + ', ' +
                  inst.start_time.slice(0, 5) + '–' + inst.end_time.slice(0, 5) + ' — ' +
                  (past ? 'прошедшее — только просмотр'
                        : inst.state === 'free' ? 'свободно, нажмите для брони'
                        : inst.state === 'pending' ? 'ваш запрос на рассмотрении' : 'занято');
                var clickable = (inst.state === 'free' && !past);
                cell = { cls: 'bk-slot ' + cls + (past ? ' past' : ''), title: title, disabled: !clickable, inst: clickable ? inst : null };
              }
              cells.push(cell);
            }
            rowsOut.push({ key: row[0], label: label, cells: cells });
          });
        }
        gridHead.value = head;
        gridRows.value = rowsOut;
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
        localApi('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: inst.availability_id, date: inst.date})}, function (res) {
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
        document.getElementById('bk-count').textContent = bookings.length;
        bookingsList.value = bookings;
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
        localApi('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: inst.availability_id, date: inst.date})}, function (res) {
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
    });

    return {
      // «Мои заявки»
      viewReqs: viewReqs, SYSTEM_COMMENT: SYSTEM_COMMENT,
      fmtDate: fmtDate, reqStatus: reqStatus, initialsOf: initialsOf,
      carText: carText, goReview: goReview, retry: retry,
      // «Мои брони»
      bookingsList: bookingsList, gridHead: gridHead, gridRows: gridRows,
      bkStatus: bkStatus, bookingTitle: bookingTitle, bkCarText: bkCarText,
      openBookModal: openBookModal, retryBooking: retryBooking,
    };
  },
};
</script>
