<!-- Мокап: Личный кабинет ученика (Спринт 1). Стиль референса. Кнопка выхода ->
     admin/учетка сессии. Спринт 19 (add-ai-chat-home, 19.3.1): «Главная» —
     ИИ-чат по утвержденным макетам (design/mocks/mobile/mobile-home-chat.html
     ≤760px, design/mocks/home-chat-web.html >760px, аппрув Заказчика
     2026-11-18 «Вот теперь отлично. Так и делай»): .greet/.assistant/.quick/
     .services-title/.tiles удалены по решению Заказчика 2026-11-18 («Да,
     убираем все кнопки с этого экрана и оставь только гигагаишника. Не
     только в могилке, но и на веб версии тоже» — requirements-19,
     «Решения Заказчика»); ставший мертвым wiring заглушек (alert-обработчики
     .tile/.quick button/.send, App.vue onMounted) удален (arch-review 002
     MIN-3 — чтобы вербатим-гарды не считали его живым). ФИО остается
     в блоке учетки сайдбара и в «Профиле» таб-бара (MODIFIED cabinet, FR-5).
     Wiring (единственные отличия от мокапа): GET /api/auth/me с X-Session-Token
     из sessionStorage (401 -> редирект на главную, к модалке входа), 200 ->
     подстановка ФИО; «Выйти» -> POST /api/auth/logout -> очистка sessionStorage ->
     редирект на главную.
     BUG-047 (решение Заказчика 2026-10-17): кабинет ученика — ЕДИНЫЙ лейаут
     (сайдбар слева, контент справа, шапка сверху). Раздел «Мои заявки»
     перенесен из frontend/my-requests.html внутрь кабинета как таб.
     Замечание Заказчика 2026-11-15 №1: сайдбар — СТАТИЧНЫЙ ЕДИНЫЙ элемент;
     канонический список ученика («Главная, Мои заявки, Выбрать инструктора,
     Мои брони, Кошелек, Знаки, Правила, Билеты, Штрафы») — тот же состав и
     порядок на instructor-choice и лендинге (index.html).
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
<!-- Замечание Заказчика 2026-11-16: сайдбар — ОТДЕЛЬНЫЙ МОДУЛЬ
     StudentSidebar.vue (физически один элемент на всех ученических
     страницах): логотип/канонические 9 пунктов/учётка внизу слева; ФИО и
     «Выйти» — wiring ВНУТРИ компонента (GET /api/auth/me, POST
     /api/auth/logout). Активный пункт — props curTab; клик таба —
     @tab="navTo" (существующий механизм разделов и хешей). -->
<student-sidebar :active-tab="curTab" @tab="navTo" @me="onMe"></student-sidebar>
<!-- Спринт 18 (add-mobile-adaptive, 18.1.1): мобильный таб-бар снизу —
     показ ≤760px (matchMedia внутри компонента), активный по curTab;
     клик таба — тот же @tab="navTo" (SPA-механика разделов без изменений). -->
<mobile-tab-bar :active-tab="curTab" @tab="navTo"></mobile-tab-bar>
<!-- Замечание Заказчика №2 (2026-11-16): пустой <header> (наследник шапки
     мокапа, 45px+8px вертикали) убран — контент правой колонки начинается
     у верха, отступ = паддинг .frame (26px, синхронно с мокапом). -->
<div class="hero"><div class="frame">

<!-- раздел «Главная» (Спринт 19, add-ai-chat-home 19.3.1: ИИ-чат по макетам
     design/mocks/home-chat-web.html >760px / mobile/mobile-home-chat.html
     ≤760px — тексты и визуал дословно, FR-19.1). Пустой чат → приветствие
     по центру (spark/«Добрый день!»/подсказка); есть история → пузыри
     user/assistant вместо приветствия (FR-19.4). Композер прижат к низу:
     плейсхолдер дословно, «+» видима/неактивна с честной подписью «Скоро»
     (FR-19.7 — требование Заказчика, в макете подписи нет), рабочая кнопка
     отправки (стрелка вверх, как в макете). Wiring — 19.3.2/19.3.3:
     POST /api/ai/chat {message} → {reply} и GET /api/ai/chat/history
     (X-Session-Token из sessionStorage). Сайдбар/таб-бар — без изменений
     (FR-19.2); навигация «Найти водителя»/«Мои заявки» — через них. -->
<div id="sec-home" :class="aiMessages.length ? 'ai-has-msgs' : 'ai-empty'">
<div class="ai-greet" id="ai-greet" v-show="!aiMessages.length">
  <svg class="ai-spark" viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="1.6" stroke-linecap="round">
    <path d="M12 2v6M12 16v6M2 12h6M16 12h6"/>
    <path d="M4.9 4.9l4.2 4.2M14.9 14.9l4.2 4.2M19.1 4.9l-4.2 4.2M9.1 14.9l-4.2 4.2"/>
  </svg>
  <div class="ai-hello">Добрый день!</div>
  <div class="ai-hello-sub">Спроси что угодно про обучение, экзамен или ПДД — помогу подготовиться</div>
</div>
<div class="ai-msgs" id="ai-msgs">
  <div class="ai-msg" v-for="(m, i) in aiMessages" :key="i" :class="m.role === 'user' ? 'ai-msg-user' : 'ai-msg-bot'">
    <div class="ai-bubble">{{ m.text }}</div>
  </div>
  <div class="ai-typing" id="ai-typing" v-if="aiBusy" aria-label="Ассистент печатает"><i></i><i></i><i></i></div>
</div>
<div class="ai-composer" id="ai-composer">
  <div class="ai-input-box">
    <input class="ai-input" id="ai-input" type="text" placeholder="Спроси что угодно про обучение, экзамен или ПДД..." v-model="aiDraft" :disabled="aiBusy" @keydown.enter.prevent="aiSend">
    <div class="ai-error" id="ai-error" v-if="aiError">{{ aiError }}</div>
    <div class="ai-actions">
      <span class="ai-plus-wrap">
        <button class="ai-plus" id="ai-plus" type="button" disabled aria-label="Вложения — скоро">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9aa39d" stroke-width="2" stroke-linecap="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
        </button>
        <span class="ai-soon">Скоро</span>
      </span>
      <button class="ai-send" id="ai-send" type="button" aria-label="Отправить" :disabled="aiBusy" @click="aiSend">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0a130e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 19V5"/>
          <path d="M5 12l7-7 7 7"/>
        </svg>
      </button>
    </div>
  </div>
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
  <div class="no-req" id="noreq" :style="{display: viewReqs.length ? 'none' : 'block'}"><b>Заявок пока нет</b><span class="no-req-text">Найдите инструктора в каталоге и подайте первую заявку.</span><button id="go-catalog" type="button">Перейти к выбору инструктора</button></div>
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
        <button v-for="(cell, ix) in row.cells" :key="row.key + '-' + ix" type="button" :class="cell.cls" :title="cell.title" :disabled="cell.disabled" @click="cell.inst ? openBookModal(cell.inst) : null"><span class="bk-slot-lab">{{ cell.lab }}</span></button>
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
      <!-- Спринт 16 (16.4.1): спор по ПРОВЕДЕННОЙ брони с холдом (МАЖ-2:
           только тарифицированные брони; окно 24ч от «проведено» — вне
           окна API вернет ошибку, покажем тост) -->
      <div class="bk-actions" v-if="b.status === 'completed' && b.hold_amount_kop > 0">
        <button class="bk-act dispute" type="button" @click="openDispute(b)">⚠ Оспорить занятие</button>
      </div>
    </article>
  </div>
</div>

<!-- раздел «Кошелек» (Спринт 16, add-wallet-economy 16.4.1; мокап
     design/mocks/wallet-student.html — источник дизайна, якорь #sec-wallet):
     балансы — SUM по журналу (GET /api/wallet: available/frozen/total),
     «Пополнить» — модал с POST /api/wallet/topup (X-Idempotency-Key),
     история транзакций владельца (тип/дата/описание/сумма ±) -->
<div id="sec-wallet" style="display:none">
  <div class="page-head">
    <div>
      <div class="kicker">Кошелек</div>
      <h1>Мой кошелек</h1>
      <p>Деньги хранятся в копейках, баланс — по журналу транзакций. При бронировании занятия сумма блокируется: она уходит из «Доступно» в «Заморожено» и возвращается, если занятие отменили.</p>
    </div>
    <div class="wal-legenda">Заморожено — холды ваших броней</div>
  </div>

  <div class="wal-balances" id="balances">
    <div class="wal-bal"><small>Доступно</small><b id="b-avail">{{ rubFmt(walBalances.available_kop) }}<small>₽</small></b><div class="wal-hint">можно тратить на бронирования</div></div>
    <div class="wal-bal frozen"><small>Заморожено</small><b id="b-frozen">{{ rubFmt(walBalances.frozen_kop) }}<small>₽</small></b><div class="wal-hint">холды броней — до релиза или возврата</div></div>
    <div class="wal-bal"><small>Всего</small><b id="b-total">{{ rubFmt(walBalances.total_kop) }}<small>₽</small></b><div class="wal-hint">доступно + заморожено</div></div>
  </div>

  <div class="wal-actions">
    <button class="wal-btn primary" id="topup-open" type="button">＋ Пополнить</button>
    <button class="wal-btn ghost" id="to-bookings" type="button">Мои брони</button>
    <span class="wal-legenda" id="wal-count">Операций: {{ walletTxs.length }}</span>
  </div>

  <div class="wal-hist-title">История транзакций</div>
  <table class="wal-table">
    <thead><tr><th>Дата</th><th>Тип</th><th>Описание</th><th style="text-align:right">Сумма</th></tr></thead>
    <tbody id="hist">
      <tr v-for="t in walletTxs" :key="String(t.id)">
        <td class="wal-when">{{ walWhen(t.created_at) }}</td>
        <td><span class="wal-ttype" :class="txBadge(t.type)[1]">{{ txBadge(t.type)[0] }}</span></td>
        <td>{{ walDesc(t) }}</td>
        <td class="wal-amount" :class="t.sign > 0 ? 'plus' : 'minus'">{{ t.sign > 0 ? '+' : '−' }} {{ rubFmt(t.amount_kop) }} ₽</td>
      </tr>
      <tr v-if="!walletTxs.length"><td colspan="4" class="wal-empty">Операций пока нет — пополните кошелек, чтобы забронировать занятие.</td></tr>
    </tbody>
  </table>
</div>

<!-- Спринт 17 (add-pdd-learning, 17.3.1): раздел «Знаки» (мокап
     design/mocks/pdd-znaki-student.html): скелет — синхронно с cabinet.html;
     списки (чипы/сетка/деталь) — в PddSigns.vue (defineAsyncComponent,
     v-if="pddSignsVisited" — visited-загрузка: чанк при ПЕРВОМ открытии,
     остается смонтированным, NFR-26) -->
<div id="sec-pdd-signs" style="display:none">
  <div class="page-head">
    <div>
      <div class="kicker">Обучение · ПДД</div>
      <h1>Дорожные знаки</h1>
      <p>8 групп · 321 знак с описаниями. Выбери группу — внутри карточки знаков и их значение.</p>
    </div>
  </div>
  <pdd-signs v-if="pddSignsVisited"></pdd-signs>
</div>

<!-- Спринт 17 (add-pdd-learning, 17.4.1): раздел «Правила» (мокап
     design/mocks/pdd-pravila-student.html, two-column prav-wrap): скелет —
     синхронно с cabinet.html; toc/глава — в PddRules.vue
     (defineAsyncComponent, v-if="pddRulesVisited", NFR-26) -->
<div id="sec-pdd-rules" style="display:none">
  <div class="page-head">
    <div>
      <div class="kicker">Обучение · ПДД</div>
      <h1>Правила дорожного движения</h1>
      <p>26 глав действующей редакции. Глава раскрывается по клику; пункты — полный текст.</p>
    </div>
  </div>
  <pdd-rules v-if="pddRulesVisited"></pdd-rules>
</div>

<!-- Спринт 17 (add-pdd-learning, 17.5.1): раздел «Билеты» — тренажер
     (мокап design/mocks/pdd-bilety-trenazher.html): скелет — синхронно
     с cabinet.html; выбор/тренировка/результат — в PddTickets.vue
     (defineAsyncComponent, v-if="pddTicketsVisited", NFR-26) -->
<div id="sec-pdd-tickets" style="display:none">
  <div class="page-head">
    <div>
      <div class="kicker">Обучение · ПДД</div>
      <h1>Билеты ПДД — тренажер</h1>
      <p>Режим экзамена: 20 вопросов, 20 минут. Картинки вопросов — как на реальном экзамене ГИБДД.</p>
    </div>
  </div>
  <pdd-tickets v-if="pddTicketsVisited"></pdd-tickets>
</div>

<!-- Спринт 17 (add-pdd-learning, 17.6.1): раздел «Штрафы» (мокап
     design/mocks/pdd-shtrafi-student.html): скелет — синхронно с
     cabinet.html; поиск/таблица — в PddFines.vue
     (defineAsyncComponent, v-if="pddFinesVisited", NFR-26) -->
<div id="sec-pdd-fines" style="display:none">
  <div class="page-head">
    <div>
      <div class="kicker">Обучение · ПДД</div>
      <h1>Штрафы ГИБДД</h1>
      <p>Таблица нарушений главы 12 КоАП: статья, нарушение, наказание. Поиск — по любой колонке, без перезагрузки.</p>
    </div>
  </div>
  <pdd-fines v-if="pddFinesVisited"></pdd-fines>
</div>

<!-- модалка: пополнение кошелька (мок эквайринга; POST /api/wallet/topup
     с X-Idempotency-Key — повтор той же операции не удваивает зачисление) -->
<div class="wal-backdrop" id="m-backdrop" role="dialog" aria-modal="true" aria-labelledby="wal-topup-title">
  <div class="wal-modal">
    <h2 id="wal-topup-title">Пополнить кошелек</h2>
    <div class="wal-sub">Оплата на моках эквайринга (MVP): зачисление мгновенное, реальных списаний нет.</div>
    <div class="wal-presets">
      <button type="button" data-r="1000">1 000 ₽</button>
      <button type="button" class="on" data-r="3000">3 000 ₽</button>
      <button type="button" data-r="5000">5 000 ₽</button>
    </div>
    <input class="wal-input" id="m-amount" inputmode="numeric" value="3000" title="Сумма в рублях, целое число">
    <div class="wal-note">Сумма — целые рубли; зачисление происходит в копейках (× 100). Повторы той же операции не удваивают зачисление.</div>
    <div class="wal-mactions">
      <button class="wal-btn primary" id="m-confirm" type="button">Пополнить</button>
      <button class="wal-btn m-close" id="m-close" type="button">Отмена</button>
    </div>
  </div>
</div>

<!-- модалка: спор по проведенному занятию (POST /api/student/bookings/{id}/
     dispute) — комментарий обязателен (кнопка заблокирована без текста,
     прецедент BUG-046 deny); окно 24ч контролирует сервер -->
<div class="wal-backdrop" id="m-dispute" role="dialog" aria-modal="true" aria-labelledby="wal-dispute-title">
  <div class="wal-modal">
    <h2 id="wal-dispute-title">Оспорить занятие</h2>
    <div class="wal-sub" id="wal-dispute-sub">—</div>
    <label class="wal-label" for="wal-dispute-comment">Что произошло? — обязательно</label>
    <textarea class="wal-textarea" id="wal-dispute-comment" rows="3" placeholder="Например: инструктор отменил занятие по месту, откатал только час"></textarea>
    <div class="wal-note">Спор открывается в течение 24 часов после отметки занятия проведенным. Замороженная сумма не распределяется, пока спор не решит оператор.</div>
    <div class="wal-mactions">
      <button class="wal-btn primary" id="wal-dispute-go" type="button" disabled>Открыть спор</button>
      <button class="wal-btn m-close" id="wal-dispute-cancel" type="button">Отмена</button>
    </div>
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
    <!-- Спринт 16 (16.4.1): 402 «недостаточно средств» (холд не прошел) —
         честное сообщение + переход в «Кошелек» для пополнения -->
    <div class="bk-no-funds" id="bk-no-funds" style="display:none">
      <b>Недостаточно средств</b>
      <span id="bk-no-funds-msg">На кошельке не хватает суммы холда за это занятие.</span>
      <button class="bk-btn primary" id="bk-go-wallet" type="button">Пополнить кошелек</button>
    </div>
    <div class="bk-form-actions">
      <button class="bk-btn primary" id="bk-send" type="button">Отправить запрос</button>
      <button class="bk-btn ghost" data-close-book type="button">Отмена</button>
    </div>
  </div>
</div>

<footer><span>СберАвтошкола · кабинет ученика</span><span>Спринт 1 · визуал</span></footer>
</div></div>
</div>
</template>

<script>
// Wiring — перенос js/student/cabinet.js 1:1 (задача 4.2; фикс с15:
// hoist функций и плоского состояния в область setup). Раньше
// openBookModal/retryBooking и их зависимости (localApi, loadRequests,
// bk-*) объявлялись внутри onMounted-замыкания, а return setup ссылался
// на эти имена — ReferenceError при setup каскадом вало монтирование:
// пустой setupState в рендере (TypeError length в шаблоне) и
// императивные биндинги по null (.logout и др.). Теперь все функции,
// вызываемые шаблоном, и их зависимости — в setup-области; onMounted
// оставлен только для bootstrap-привязок к СУЩЕСТВУЮЩИМ элементам
// (токен, слушатели, стартовые загрузки) — реактивный порт вместо
// императивных биндингов на отсутствующий DOM.
// Токен — sessionStorage 'session_token' (свой clearSession/toLogin —
// как legacy); toast/fmtDate/nowMoscow — из vue/src/shared/utils.js
// (дословные переносы С14/С15; fioOf переехал в StudentSidebar вместе с
// ФИО-замечанием 2026-11-16); fetch-логика — локальная (как legacy).
import { onMounted, ref, computed, defineAsyncComponent, nextTick } from 'vue';
import { toast, fmtDate, nowMoscow } from '../../shared/utils.js';
// Замечание Заказчика 2026-11-16: сайдбар — ОТДЕЛЬНЫЙ МОДУЛЬ (общий чанк
// shared — vite.config.mjs manualChunks /src/components/)
import StudentSidebar from '../../components/StudentSidebar.vue';
// Спринт 18 (add-mobile-adaptive, 18.1.1): мобильный таб-бар (общий чанк
// shared — vite.config.mjs manualChunks /src/components/); показ ≤760px,
// активный по curTab, клик таба — тот же navTo
import MobileTabBar from '../../components/MobileTabBar.vue';

export default {
  name: 'CabinetApp',
  // Единый сайдбар ученика (физически один элемент; ФИО/«Выйти» — внутри)
  // + Спринт 17 (add-pdd-learning, 17.3.1): секции обучения ПДД — lazy-чанки
  // (NFR-26): defineAsyncComponent + v-if="pdd*-Visited" в шаблоне — чанк
  // грузится при ПЕРВОМ открытии раздела и остается смонтированным.
  components: {
    StudentSidebar,
    // Спринт 18 (18.1.1): мобильный таб-бар снизу (≤760px)
    MobileTabBar,
    PddSigns: defineAsyncComponent(function () {
      return import('./sections/PddSigns.vue');
    }),
    PddRules: defineAsyncComponent(function () {
      return import('./sections/PddRules.vue');
    }),
    PddTickets: defineAsyncComponent(function () {
      return import('./sections/PddTickets.vue');
    }),
    PddFines: defineAsyncComponent(function () {
      return import('./sections/PddFines.vue');
    }),
  },
  setup: function () {
    // --- сессия (sdd §10.2–10.4): токен сессии — sessionStorage, ключ
    // session_token (единый snake_case-паттерн с admin_token Спринта 0);
    // модалка входа (задача 2.2) пишет его в тот же ключ ---
    var TOKEN_KEY = 'session_token';
    var token = null;
    function clearSession() {
      try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
    }
    // 401 (нет токена / невалидный / истек / аннулирован) -> редирект на
    // главную, к модалке входа (FR-7)
    function toLogin() {
      clearSession();
      location.href = '/';
    }
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

    // --- сайдбар (StudentSidebar): активный таб + greet из @me ------------
    // Замечание Заказчика 2026-11-16: активный пункт сайдбара — props
    // curTab (истина последней инстанции: кабинет роутит разделы через
    // history.replaceState — hashchange не fireится, location-производная
    // протухла бы внутри SPA). navTo обновляет curTab; клики табов приходят
    // событием @tab от компонента (клик по «Выбрать инструктора» компонент
    // обрабатывает сам — переход на /instructor-choice).
    var curTab = ref('Главная');
    // Спринт 19 (19.3.1): greet «ЛИЧНЫЙ КАБИНЕТ / Добро пожаловать, {name}!»
    // удален вместе с .greet (макеты чата «Главной» его не содержат); ФИО —
    // в блоке учетки StudentSidebar и в «Профиле» таб-бара (FR-5 сохранен).
    // Обработчик @me оставлен (сайдбар эмитит его всегда) — безопасный no-op
    // с null-guard, чтобы не ронять эмиссию компонента.
    function onMe(u) {
      var el = document.querySelector('.greet b');
      if (el) el.textContent = 'Добро пожаловать, ' + u.name + '!';
    }

    // --- Спринт 19 (add-ai-chat-home, 19.3.1–19.3.3): ИИ-чат «Главной» ------
    // POST /api/ai/chat {message} → {reply} (19.3.1, рабочая отправка);
    // GET /api/ai/chat/history — подхват истории за 14 дней при открытии
    // раздела (19.3.2, FR-19.5). Токен — sessionStorage 'session_token'
    // (тот же, что у localApi выше); Promise-паттерн — как postJSON из
    // shared/loginWiring.js, но с заголовком сессии ученика.
    var aiMessages = ref([]);   // журнал чата: {role:'user'|'assistant', text, created_at}
    var aiDraft = ref('');
    // Волна 21.3 (add-roles-theme-landing): prefill вопроса из лендинг-блока
    // ГигаЧата (sessionStorage ai_prefill — ставит лендинг при send/quick
    // незалогиненному; подхват при входе в кабинет, затем очистка).
    try {
      var _prefill = sessionStorage.getItem('ai_prefill');
      if (_prefill) { aiDraft.value = String(_prefill).slice(0, 500);
        sessionStorage.removeItem('ai_prefill'); }
    } catch (e) {}
    var aiBusy = ref(false);    // отправка блокируется на время ответа (FR-19.3)
    var aiError = ref('');      // человеческий текст ошибки у поля

    function aiApi(path, method, payload) {
      var opts = {
        method: method || 'GET',
        headers: { 'X-Session-Token': token || '', 'Content-Type': 'application/json' },
      };
      if (payload !== undefined) opts.body = JSON.stringify(payload);
      return fetch(path, opts).then(function (r) {
        return r.json().then(function (d) { return { status: r.status, data: d }; },
          function () { return { status: r.status, data: null }; });
      }, function () { return { status: 0, data: null }; });
    }

    // Ошибки — человеческим текстом у поля, без кодов/стеков (FR-19.3).
    // Шейпы: контрактный {ok:false, error:"…"} (конвенция Sprint-0) И
    // машинный FastAPI-дефолт {detail:[…]} на 422 (MIN-3 review-19.2 —
    // глобального обработчика валидации в app.py нет). Фронт обрабатывает
    // ОБА: контрактному доверяем текст, машинному/сети — общий человеческий.
    function aiHumanError(res) {
      if (res.data && res.data.error) return String(res.data.error);
      return 'Не получилось отправить сообщение. Попробуйте еще раз чуть позже.';
    }

    function aiScrollBottom() {
      nextTick(function () {
        var box = document.getElementById('ai-msgs');
        if (box) box.scrollTop = box.scrollHeight;
      });
    }

    // Подхват истории при открытии/входе (FR-19.5): GET за последние 14 дней
    // (глубина — серверная, клиентской глубине не доверяем). Есть история →
    // пузыри вместо приветствия; пусто → приветствие из макета (FR-19.4).
    // Фоновый запрос: не-200/сеть — история просто не подхватилась, ошибку
    // у поля не ставим (она — про отправку, FR-19.3).
    function aiLoadHistory() {
      aiApi('/api/ai/chat/history').then(function (res) {
        if (handleAuthFail(res)) return;
        if (res.status === 200 && res.data && res.data.ok) {
          aiMessages.value = res.data.messages || [];
          aiScrollBottom();
        }
      });
    }

    function aiSend() {
      if (aiBusy.value) return;
      var text = (aiDraft.value || '').trim();
      if (!text) return;
      aiError.value = '';
      aiMessages.value.push({ role: 'user', text: text });
      aiDraft.value = '';
      aiBusy.value = true; // индикатор ожидания (NFR: не «висит» молча)
      aiScrollBottom();
      var at = aiMessages.value.length - 1;
      aiApi('/api/ai/chat', 'POST', { message: text }).then(function (res) {
        aiBusy.value = false;
        if (handleAuthFail(res)) { aiMessages.value.splice(at, 1); return; }
        if (res.status === 200 && res.data && res.data.ok) {
          aiMessages.value.push({ role: 'assistant', text: res.data.reply });
          aiScrollBottom();
        } else {
          // Ошибка/таймаут: пузырь пользователя убираем — сервер обмен НЕ
          // сохранял (история только из состоявшихся обменов); текст
          // возвращаем в поле для повторной отправки, ошибка — у поля.
          aiMessages.value.splice(at, 1);
          aiDraft.value = text;
          aiError.value = aiHumanError(res);
        }
      });
    }

    // --- раздел «Мои заявки» — реактивные данные (el()-отрисовка → v-for) ---
    var reqs = ref([]);
    var cur = ref('all');
    // Спринт 17 (17.3.1): visited-загрузка lazy-секций ПДД (NFR-26)
    var pddSignsVisited = ref(false);
    var pddRulesVisited = ref(false);
    var pddTicketsVisited = ref(false);
    var pddFinesVisited = ref(false);
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
            var cell = { cls: 'bk-slot off', title: '', disabled: true, inst: null, lab: '' };
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
              // Спринт 18 (18.2.3): короткая подпись слота «Пн 17.11 · 16:00–18:00»
              // — видима только на мобильной неделе-полосе (.bk-slot-lab,
              // styles.css media ≤760px); desktop показывает пустую ячейку
              // со статусом в :after — раскладка не меняется
              var lab = (BK_DAYS[inst.weekday] ? BK_DAYS[inst.weekday] + ' ' : '') +
                inst.date.slice(8, 10) + '.' + inst.date.slice(5, 7) + ' · ' +
                inst.start_time.slice(0, 5) + '–' + inst.end_time.slice(0, 5);
              cell = { cls: 'bk-slot ' + cls + (past ? ' past' : ''), title: title, disabled: !clickable, inst: clickable ? inst : null, lab: lab };
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
      // Спринт 16 (16.4.1): блок нехватки средств скрыт при новом открытии
      document.getElementById('bk-no-funds').style.display = 'none';
      document.getElementById('m-book').classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function closeBookModal() {
      document.getElementById('m-book').classList.remove('open');
      document.body.style.overflow = '';
    }
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

    // =====================================================================
    // Спринт 16 (add-wallet-economy, 16.4.1): раздел «Кошелек» — балансы
    // (SUM по журналу, GET /api/wallet), история транзакций, пополнение
    // (мок эквайринга, POST /api/wallet/topup с X-Idempotency-Key),
    // спор по проведенному занятию (POST …/{id}/dispute). Деньги —
    // целые копейки, в ₽ только ДЛЯ ПОКАЗА (целочисленное деление).
    var walBalances = ref({ available_kop: 0, frozen_kop: 0, total_kop: 0 });
    var walletTxs = ref([]);
    var walDisputeTarget = null;
    var WAL_TX_BADGES = {
      topup: ['Пополнение', 'wal-t-topup'],
      hold: ['Холд брони', 'wal-t-hold'],
      release: ['Оплата занятия', 'wal-t-release'],
      refund: ['Возврат холда', 'wal-t-refund'],
      payout: ['Выплата', 'wal-t-payout'],
    };
    function txBadge(type) { return WAL_TX_BADGES[type] || [type, '']; }
    // копейки → строка ₽ БЕЗ float (NFR-33-наследование: целые остаток/деление)
    function rubFmt(kop) {
      var a = Math.abs(Number(kop) || 0);
      return ((a - (a % 100)) / 100).toLocaleString('ru-RU');
    }
    function walWhen(iso) {
      var s = String(iso || ''), parts = s.split(' ');
      var d = (parts[0] || '').split('-'), t = parts[1] || '';
      return d.length === 3 ? d[2] + '.' + d[1] + '.' + d[0] + (t ? ' ' + t.slice(0, 5) : '') : s;
    }
    function walDesc(t) {
      var d = t.description || '';
      if (t.booking_id) d += ' (бронь №' + t.booking_id + ')';
      return d;
    }
    function loadWallet() {
      localApi('/api/wallet', {}, function (res) {
        if (handleAuthFail(res)) return;
        if (!res.data || !res.data.ok) {
          toast((res.data && res.data.error) || 'Не удалось загрузить кошелек');
          return;
        }
        walBalances.value = {
          available_kop: res.data.available_kop || 0,
          frozen_kop: res.data.frozen_kop || 0,
          total_kop: res.data.total_kop || 0,
        };
        walletTxs.value = res.data.transactions || [];
      });
    }
    function closeTopupModal() {
      document.getElementById('m-backdrop').classList.remove('wal-open');
      document.body.style.overflow = '';
    }
    function openTopupModal() {
      document.getElementById('bk-no-funds').style.display = 'none';
      document.getElementById('m-backdrop').classList.add('wal-open');
      document.body.style.overflow = 'hidden';
    }
    // пополнение: целые рубли → amount_kop ×100; ключ идемпотентности —
    // свежий на каждую операцию (повтор по сети вернул бы результат первой)
    function sendTopup(btn) {
      var raw = String(document.getElementById('m-amount').value || '').trim();
      var rubles = parseInt(raw, 10);
      if (!rubles || rubles <= 0 || String(rubles) !== raw) {
        toast('Сумма — целое положительное число рублей');
        return;
      }
      btn.disabled = true;
      var idem = (window.crypto && window.crypto.randomUUID)
        ? window.crypto.randomUUID()
        : 'topup-' + Date.now() + '-' + Math.floor(Math.random() * 1000000000);
      localApi('/api/wallet/topup', {
        method: 'POST',
        headers: { 'X-Idempotency-Key': idem },
        body: JSON.stringify({ amount_kop: rubles * 100 }),
      }, function (res) {
        btn.disabled = false;
        if (handleAuthFail(res)) return;
        if (res.status === 200 && res.data && res.data.ok) {
          closeTopupModal();
          toast('Зачислено ' + rubFmt(res.data.amount_kop) + ' ₽ (мок). Пополнение мгновенное.');
          loadWallet();
        } else {
          toast((res.data && res.data.error) || 'Не удалось пополнить кошелек');
        }
      });
    }
    function openDispute(b) {
      walDisputeTarget = b;
      document.getElementById('wal-dispute-sub').textContent =
        'Бронь ' + bookingTitle(b) + ' · заморожено ' + rubFmt(b.hold_amount_kop) + ' ₽';
      document.getElementById('wal-dispute-comment').value = '';
      document.getElementById('wal-dispute-go').disabled = true;
      document.getElementById('m-dispute').classList.add('wal-open');
      document.body.style.overflow = 'hidden';
    }
    function closeDispute() {
      walDisputeTarget = null;
      document.getElementById('wal-dispute-comment').value = '';
      document.getElementById('wal-dispute-go').disabled = true;
      document.getElementById('m-dispute').classList.remove('wal-open');
      document.body.style.overflow = '';
    }
    // спор: комментарий обязателен (кнопка блокируется без текста —
    // прецедент BUG-046 deny); 409 вне окна 24ч/уже открыт и 422 без
    // живого холда — честный тост с текстом ошибки API
    function sendDispute() {
      if (!walDisputeTarget) return;
      var comment = document.getElementById('wal-dispute-comment').value.trim();
      if (!comment) return;
      var btn = document.getElementById('wal-dispute-go');
      btn.disabled = true;
      localApi('/api/student/bookings/' + walDisputeTarget.id + '/dispute', {
        method: 'POST', body: JSON.stringify({ comment: comment }),
      }, function (res) {
        btn.disabled = false;
        if (handleAuthFail(res)) return;
        if (res.status === 200 && res.data && res.data.ok) {
          closeDispute();
          toast('Спор открыт. Холд заморожен, пока оператор не примет решение.');
        } else {
          toast((res.data && res.data.error) || 'Не удалось открыть спор');
        }
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
    // Замечание Заказчика 2026-11-16: navTo — ВЫШЕ onMounted (setup-область):
    // шаблон вызывает его напрямую как обработчик @tab StudentSidebar.
    function navTo(name) {
        // Замечание Заказчика 2026-11-16: активный пункт сайдбара — props
        // curTab компонента StudentSidebar (подсветка — :class в компоненте)
        curTab.value = name;
        var isReq = (name === 'Мои заявки');
        var isBk = (name === 'Мои брони');
        // Спринт 16 (16.4.1): «Кошелек» — третий реальный раздел кабинета
        var isWal = (name === 'Кошелек');
        // Спринт 17 (17.3.1): обучающие разделы ПДД — 4 пункта после «Кошелек»
        var isSigns = (name === 'Знаки');
        var isRules = (name === 'Правила');
        var isTickets = (name === 'Билеты');
        var isFines = (name === 'Штрафы');
        var isPdd = isSigns || isRules || isTickets || isFines;
        // Спринт 19 (19.3.1): «Главная» — flex-колонка чата (лейаут #sec-home
        // в styles.css): приветствие по центру, композер прижат к низу
        document.getElementById('sec-home').style.display = (isReq || isBk || isWal || isPdd) ? 'none' : 'flex';
        document.getElementById('sec-requests').style.display = isReq ? 'block' : 'none';
        document.getElementById('sec-bookings').style.display = isBk ? 'block' : 'none';
        document.getElementById('sec-wallet').style.display = isWal ? 'block' : 'none';
        // Спринт 17: div#sec-pdd-* добавляет задача своей секции (17.4.1 —
        // sec-pdd-rules; 17.5.1/17.6.1 — sec-pdd-tickets/sec-pdd-fines),
        // display переключается только для существующих носителей
        var signsSec = document.getElementById('sec-pdd-signs');
        if (signsSec) signsSec.style.display = isSigns ? 'block' : 'none';
        var rulesSec = document.getElementById('sec-pdd-rules');
        if (rulesSec) rulesSec.style.display = isRules ? 'block' : 'none';
        // Спринт 17 (17.5.1/17.6.1): sec-pdd-tickets/sec-pdd-fines —
        // носители появляются в этой же волне; display — только для
        // существующих (тот же guard-паттерн)
        var ticketsSec = document.getElementById('sec-pdd-tickets');
        if (ticketsSec) ticketsSec.style.display = isTickets ? 'block' : 'none';
        var finesSec = document.getElementById('sec-pdd-fines');
        if (finesSec) finesSec.style.display = isFines ? 'block' : 'none';
        // Замечание Заказчика 2026-11-16: подсветка активного пункта — в
        // StudentSidebar (props curTab); прежний classList-цикл по .snav
        // button удален вместе с локальным aside
        // BUG-047: хеш раздела синхронизируется с табом — reload не сбрасывает
        // раздел, старые ссылки #/my-requests открывают его напрямую;
        // Спринт 16: #/wallet — раздел «Кошелек»;
        // Спринт 17: #/pdd-signs #/pdd-rules #/pdd-tickets #/pdd-fines
        var wantHash = isReq ? '#/my-requests'
          : isBk ? '#/my-bookings'
          : isWal ? '#/wallet'
          : isSigns ? '#/pdd-signs'
          : isRules ? '#/pdd-rules'
          : isTickets ? '#/pdd-tickets'
          : isFines ? '#/pdd-fines'
          : '';
        if (location.hash !== wantHash) {
          try { history.replaceState(null, '', location.pathname + location.search + (wantHash || '')); } catch (e) {}
        }
        if (isReq) loadRequests();
        if (isBk) loadBookingsSection();
        if (isWal) loadWallet();
        // Спринт 19 (19.3.2): возврат на «Главную» — подхват истории чата
        if (!isReq && !isBk && !isWal && !isPdd) aiLoadHistory();
        // Спринт 17 (NFR-26): чанк секции грузится при ПЕРВОМ открытии
        if (isSigns) pddSignsVisited.value = true;
        if (isRules) pddRulesVisited.value = true;
        if (isTickets) pddTicketsVisited.value = true;
        if (isFines) pddFinesVisited.value = true;
      }

    onMounted(function(){
      // Bootstrap-привязки к СУЩЕСТВУЮЩИМ элементам (после монтирования):
      // токен, слушатели, стартовые загрузки. Все функции объявлены в
      // setup-области выше — шаблон вызывает их напрямую (реактивный порт).
      // Замечание Заказчика 2026-11-16: ФИО (.uname) и «Выйти» — wiring
      // ВНУТРИ StudentSidebar (компонент тянет /api/auth/me сам и шлет
      // @me — greet обновляет onMe выше); клики .snav — тоже компонент
      // (@tab="navTo", «Выбрать инструктора» — переход внутри компонента).

      // GET /api/auth/me: guard страницы — без токена редирект на главную
      // (FR-7); подстановка ФИО/greet — событие @me сайдбара (выше)
      try { token = sessionStorage.getItem(TOKEN_KEY); } catch (e) { token = null; }
      if (!token) {
        toLogin();
      }

      // Спринт 19 (19.3.1): плитки «Найти водителя»/«Мои заявки» удалены
      // (решение Заказчика 2026-11-18, design «Решение 3») вместе с их
      // клик-wiring и alert-заглушками .tile/.quick button/.send
      // (arch-review 002 MIN-3: мертвый wiring не оставляем). Навигация
      // «Найти водителя»/«Мои заявки» — через сайдбар/таб-бар (FR-19.2).

      // хеш-бутстрап BUG-047/Спринт 16/17/замечание 2026-11-16: ссылки вида
      // /cabinet#/pdd-* работают И вживую (hashchange), а не только при загрузке
      function routeHash() {
        if (location.hash === '#/my-requests') navTo('Мои заявки');
        else if (location.hash === '#/my-bookings') navTo('Мои брони');
        else if (location.hash === '#/wallet') navTo('Кошелек');
        else if (location.hash === '#/pdd-signs') navTo('Знаки');
        else if (location.hash === '#/pdd-rules') navTo('Правила');
        else if (location.hash === '#/pdd-tickets') navTo('Билеты');
        else if (location.hash === '#/pdd-fines') navTo('Штрафы');
      }
      routeHash();
      window.addEventListener('hashchange', routeHash);

      // Спринт 19 (19.3.2): «Главная» — раздел по умолчанию, история чата
      // подхватывается при входе (GET /api/ai/chat/history, 14 дней — FR-19.5)
      aiLoadHistory();

      // --- Раздел «Мои заявки»: bootstrap-привязки (данные/функции —
      //     setup-область выше: loadRequests/renderFilters/retry) ---
      document.getElementById('go-catalog').onclick=function(){location.href='/instructor-choice'};
      document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){
        document.querySelectorAll('.filters button').forEach(function(x){x.classList.remove('on')});
        b.classList.add('on');cur.value=b.dataset.f;
      })});

      // =====================================================================
      // Спринт 5 (change add-booking-docs): раздел «Мои брони» (мокап
      // booking-student.html). Слоты — GET /api/student/instructors/{id}/slots
      // (СЕРВЕРНАЯ проверка пары, иначе 403); бронь — POST /api/student/bookings
      // {availability_id} (гонки: занято → 409); календарь — GET
      // /api/student/bookings; «Повторить» после отклонения (ОВ-5) — повторный
      // POST по слоту, найденному в текущем графике. Bootstrap-привязки ниже;
      // данные/отрисовка — функции setup-области (выше).
      document.getElementById('bk-prev').addEventListener('click', function () { bkNavWeek(-7); });
      document.getElementById('bk-next').addEventListener('click', function () { bkNavWeek(7); });
      document.getElementById('bk-this').addEventListener('click', function () {
        bkMonday = bkMondayOf(nowMoscow());
        bkRenderNav();
        bkInstances = [];
        bkRenderGrid();
        bkLoadInstances();
      });
      document.querySelectorAll('[data-close-book]').forEach(function (b) {
        b.addEventListener('click', closeBookModal);
      });
      document.getElementById('m-book').addEventListener('click', function (e) {
        if (e.target === this) closeBookModal();
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          closeBookModal();
          // Спринт 16 (16.4.1): Esc закрывает и модалки кошелька
          closeTopupModal();
          closeDispute();
        }
      });
      document.getElementById('bk-send').addEventListener('click', function () {
        if (!bkPicked) return;
        var btn = this, inst = bkPicked;
        btn.disabled = true;
        // бронь на КОНКРЕТНЫЙ экземпляр: availability_id + date (Спринт 10)
        localApi('/api/student/bookings', {method: 'POST', body: JSON.stringify({availability_id: inst.availability_id, date: inst.date})}, function (res) {
          btn.disabled = false;
          if (handleAuthFail(res)) { closeBookModal(); return; }
          if (res.status === 200 && res.data && res.data.ok) {
            closeBookModal();
            toast('Запрос отправлен (статус «на рассмотрении»). Инструктор получит его в разделе «Бронирования».');
          } else if (res.status === 402) {
            // Спринт 16 (16.4.1): холд не прошел — недостаточно средств.
            // Бронь НЕ создана (ROLLBACK); модал остаётся открытым с блоком
            // «Пополнить кошелек» — переход в раздел для пополнения.
            var need = res.data && res.data.need_kop, avail = res.data && res.data.available_kop;
            document.getElementById('bk-no-funds-msg').textContent =
              (res.data && res.data.error) ||
              ('На кошельке не хватает суммы холда за это занятие' +
                (need ? (' — нужно ' + rubFmt(need) + ' ₽, доступно ' + rubFmt(avail || 0) + ' ₽.') : '.'));
            document.getElementById('bk-no-funds').style.display = 'block';
          } else {
            closeBookModal();
            if (res.status === 409) {
              // NFR-8: слот уже занят (гонки/повтор на свой активный запрос)
              toast((res.data && res.data.error) || 'Слот уже занят — выберите другой');
            } else {
              // в т.ч. 422 «Слот уже начался или прошел» — сервер проверяет всегда
              toast((res.data && res.data.error) || 'Не удалось отправить запрос');
            }
          }
          loadSlotsAndBookings();
        });
      });
      document.getElementById('bk-go-choice').addEventListener('click', function () {
        location.href = '/instructor-choice';
      });

      // =====================================================================
      // Спринт 16 (add-wallet-economy, 16.4.1): bootstrap-привязки кошелька
      // (данные/функции — setup-область: loadWallet/sendTopup/sendDispute).
      document.getElementById('topup-open').addEventListener('click', openTopupModal);
      document.getElementById('to-bookings').addEventListener('click', function () { navTo('Мои брони'); });
      document.getElementById('m-close').addEventListener('click', closeTopupModal);
      document.getElementById('m-backdrop').addEventListener('click', function (e) {
        if (e.target === this) closeTopupModal();
      });
      document.querySelectorAll('#m-backdrop .wal-presets button').forEach(function (b) {
        b.addEventListener('click', function () {
          document.querySelectorAll('#m-backdrop .wal-presets button').forEach(function (x) { x.classList.remove('on'); });
          b.classList.add('on');
          document.getElementById('m-amount').value = b.dataset.r;
        });
      });
      document.getElementById('m-confirm').addEventListener('click', function () {
        sendTopup(this);
      });
      document.getElementById('wal-dispute-comment').addEventListener('input', function () {
        document.getElementById('wal-dispute-go').disabled = !this.value.trim();
      });
      document.getElementById('wal-dispute-go').addEventListener('click', sendDispute);
      document.getElementById('wal-dispute-cancel').addEventListener('click', closeDispute);
      document.getElementById('m-dispute').addEventListener('click', function (e) {
        if (e.target === this) closeDispute();
      });
      // 402 «недостаточно средств» → переход в раздел «Кошелек» (пополнение)
      document.getElementById('bk-go-wallet').addEventListener('click', function () {
        closeBookModal();
        navTo('Кошелек');
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
      // «Кошелек» (Спринт 16, 16.4.1)
      walBalances: walBalances, walletTxs: walletTxs,
      rubFmt: rubFmt, walWhen: walWhen, walDesc: walDesc,
      txBadge: txBadge, openDispute: openDispute,
      // Спринт 17 (17.3.1): visited-загрузка lazy-секций ПДД
      pddSignsVisited: pddSignsVisited, pddRulesVisited: pddRulesVisited,
      // Спринт 17 (17.5.1/17.6.1): секции «Билеты»/«Штрафы»
      pddTicketsVisited: pddTicketsVisited, pddFinesVisited: pddFinesVisited,
      // Замечание Заказчика 2026-11-16: сайдбар (StudentSidebar) — активный
      // таб + обработчики событий компонента
      curTab: curTab, navTo: navTo, onMe: onMe,
      // Спринт 19 (add-ai-chat-home): ИИ-чат «Главной»
      aiMessages: aiMessages, aiDraft: aiDraft, aiBusy: aiBusy, aiError: aiError, aiSend: aiSend,
    };
  },
};
</script>
