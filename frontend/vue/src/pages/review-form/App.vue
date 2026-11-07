<!-- «Оставить отзыв» (/review) — кабинет ученика.
     Разметка — перенос 1:1 из legacy frontend/review-form.html (change
     add-vue-s11-status-forms, задача 2.2; FR-5/FR-34/FR-35, без редизайна;
     задокументированные отклонения от мокапа наследуются: в done-состоянии
     нет done-stars/done-text/даты — свой отзыв из API не возвращается;
     ссылка «Вернуться к моим заявкам»; back-ссылки шапки убраны — BUG-047).
     Стили — подключаемый css styles.css (перенос дословный).
     Держать синхронной со статической разметкой review-form.html.
     Поведение — wiring legacy js/review-form.js 1:1 (onMounted): нет
     токена → toLogin; GET /api/auth/me → #uname/#avatar (FR-5);
     ?instructor= → числовой id, 0/нет → location.href='/my-requests'
     (301 → /cabinet#/my-requests — BUG-047); GET
     /api/student/instructors/{id} → карточка (#i-name/#i-ava/#i-sub —
     стаж+авто, #i-rating — агрегат FR-35; not ok → тост «Инструктор не
     найден»); звёзды hover/click + LABELS + #stars-lab; #review-text
     maxlength 1000 + #counter «N / 1000» (класс over); #send активна при
     rating>0 И текст непустой И ≤1000; POST /api/student/instructors/{id}/reviews
     — ТОЛЬКО 401 → toLogin (403 — тост, NFR-2), 200 → «Отзыв отправлен» +
     тост, 409 → «Отзыв уже отправлен» + тост + кнопка активна, прочие →
     тост ошибки; состояние — данными сервера при каждой загрузке (reload
     показывает форму заново — TC-UI-017). URL вызовов — СТРОКОВОЙ
     КОНКАТЕНАЦИЕЙ как в legacy (needle TC-S3BE-041
     instructors/'+instructorId+'/reviews проверяется дословно; template
     literals НЕ вводить). Тосты — #toast 3200 мс (shared/utils.js).
     XSS: пользовательские строки — только интерполяция {{ }} (экранирование
     по умолчанию); v-html ЗАПРЕЩЕН. Id-якоря e2e дословно (#view-form/
     #view-done/#done-title/#send/#review-text/#i-name/#i-ava/#i-sub/
     #i-rating/#stars-lab/#counter/#uname/#avatar, .star[data-v]). -->
<template>
  <div class="frame">
  <header>
    <div class="hgroup">
      <div class="brand"><span class="check">✓</span><span><em>Сбер</em>Автошкола<small>Кабинет ученика</small></span></div>
      <div class="crumb">Отзыв об инструкторе</div>
    </div>
    <div class="user"><span class="uname" id="uname">{{ unameText }}</span><span class="avatar" id="avatar">{{ avaText }}</span><button class="logout" id="logout">Выйти</button></div>
  </header>

  <div class="page-head">
    <div class="kicker">Отзывы</div>
    <h1>Оставить отзыв</h1>
    <p>Рейтинг и текст отзыва видны другим ученикам в карточке инструктора и влияют на фильтр «рейтинг не ниже».</p>
  </div>

  <!-- контекст: инструктор, о котором отзыв -->
  <div class="icard">
    <span class="iava" id="i-ava">{{ iAva }}</span>
    <div><b id="i-name">{{ iName }}</b><small id="i-sub">{{ iSub }}</small></div>
    <div class="irating" id="i-rating"><template v-if="instructor">{{ iRatingMain }}<small>{{ iRatingSub }}</small></template><template v-else><small>отзывы учеников</small></template></div>
  </div>

  <!-- СОСТОЯНИЕ 1: форма отзыва -->
  <section class="form-card" id="view-form" :style="{display: done ? 'none' : 'block'}">
    <h2>Как прошли занятия?</h2>
    <div class="sub">Оцените инструктора и поделитесь опытом — отзыв публикуется под вашим именем.</div>
    <div class="stars" id="stars">
      <button class="star" data-v="1" aria-label="1 звезда" :class="{on: painted>=1}" @mouseenter="previewStar(1)" @mouseleave="leaveStar" @click="fixRating(1)">★</button>
      <button class="star" data-v="2" aria-label="2 звезды" :class="{on: painted>=2}" @mouseenter="previewStar(2)" @mouseleave="leaveStar" @click="fixRating(2)">★</button>
      <button class="star" data-v="3" aria-label="3 звезды" :class="{on: painted>=3}" @mouseenter="previewStar(3)" @mouseleave="leaveStar" @click="fixRating(3)">★</button>
      <button class="star" data-v="4" aria-label="4 звезды" :class="{on: painted>=4}" @mouseenter="previewStar(4)" @mouseleave="leaveStar" @click="fixRating(4)">★</button>
      <button class="star" data-v="5" aria-label="5 звёзд" :class="{on: painted>=5}" @mouseenter="previewStar(5)" @mouseleave="leaveStar" @click="fixRating(5)">★</button>
    </div>
    <div class="stars-lab" id="stars-lab"><template v-if="painted">Оценка: <b>{{ LABELS[painted] }}</b></template><template v-else>{{ LABELS[0] }}</template></div>
    <textarea id="review-text" maxlength="1000" placeholder="Что понравилось? Чему научились? Что стоит знать будущим ученикам…" v-model="text"></textarea>
    <div class="ta-row">
      <span>Текст отзыва обязателен (непустой)</span>
      <span class="counter" id="counter" :class="{over: text.length>1000}">{{ text.length }} / 1000</span>
    </div>
    <button class="send" id="send" :disabled="!canSend || sending" @click="submit">Отправить отзыв</button>
    <a class="back" href="/my-requests">← Назад к заявкам</a>
    <div class="hint">🔒 Отзыв может оставить только ученик с принятой заявкой у этого инструктора. Повторный отзыв оставить нельзя.</div>
  </section>

  <!-- СОСТОЯНИЕ 2: отзыв уже отправлен / повтор → 409 (UNIQUE пара).
       Показ/скрытие — inline display, как legacy showDone
       (style.display='none'/'block'): класс .done-card имеет
       display:none — v-show (display='') вернул бы скрытие классом. -->
  <section class="done-card" id="view-done" :style="{display: done ? 'block' : 'none'}">
    <h2><span class="ok">✓</span><span id="done-title">{{ doneTitle }}</span></h2>
    <div class="done-note">Вы уже оценили этого инструктора. Один отзыв на пару «ученик ↔ инструктор» — изменить или дополнить его нельзя.</div>
    <div class="done-date">Отображается в карточке инструктора</div>
  </section>

  <footer><span>СберАвтошкола · «Оставить отзыв»</span><span>Кабинет ученика</span></footer>
  </div>
</template>

<script>
// Контракты вызовов — через общий клиент shared/api.js (перенос
// frontend/js/api.js, без изменений); toast/expWord — shared/utils.js.
import { computed, onMounted, ref } from 'vue';
import { api, getToken, handleAuthFail, toLogin } from '../../shared/api.js';
import { expWord, toast as baseToast } from '../../shared/utils.js';

var LABELS = {0:'Выберите оценку от 1 до 5',1:'1 — плохо',2:'2 — так себе',3:'3 — нормально',4:'4 — хорошо',5:'5 — отлично!'};

export default {
  setup: function () {
    // состояние (данными сервера при каждой загрузке — reload показывает
    // форму заново, поведение TC-UI-017)
    var user = ref(null);
    var instructor = ref(null);
    var rating = ref(0);
    var preview = ref(null); // hover-предпросмотр (null — нет)
    var text = ref('');
    var done = ref(false);
    var doneTitle = ref('Отзыв отправлен');
    var sending = ref(false);
    var instructorId = 0;

    // toast — 3200 мс (baseToast review-form), как legacy
    function toast(m) { baseToast(m, 3200); }

    // --- звёзды: hover — предпросмотр, mouseleave — возврат, click —
    // фиксация (paint legacy: painted = preview ?? rating) ---
    var painted = computed(function () {
      return preview.value !== null ? preview.value : rating.value;
    });
    function previewStar(n) { preview.value = n; }
    function leaveStar() { preview.value = null; }
    function fixRating(n) { rating.value = n; preview.value = null; }

    var canSend = computed(function () {
      return rating.value > 0
        && text.value.trim().length > 0
        && text.value.length <= 1000;
    });

    // --- ФИО/аватар ученика (FR-5): ставятся только при непустом ФИО,
    // как legacy (если ФИО нет — плейсхолдеры «…»/«—») ---
    var userFio = computed(function () {
      var u = user.value;
      if (!u) return '';
      return [u.surname, u.name, u.patronymic].filter(Boolean).join(' ');
    });
    var unameText = computed(function () { return userFio.value || '…'; });
    var avaText = computed(function () {
      var u = user.value;
      if (!u || !userFio.value) return '—';
      return ((u.surname || '')[0] || '') + ((u.name || '')[0] || '');
    });

    // --- карточка инструктора: дефолты разметки до загрузки, как legacy ---
    var iName = computed(function () {
      return instructor.value ? (instructor.value.full_name || 'Инструктор') : '…';
    });
    var iAva = computed(function () {
      if (!instructor.value) return '—';
      var fio = instructor.value.full_name || 'Инструктор';
      return fio.split(' ').slice(0, 2).map(function (w) {
        return (w[0] || '').toUpperCase();
      }).join('');
    });
    var iSub = computed(function () {
      if (!instructor.value) return '';
      var i = instructor.value;
      var sub = 'Стаж ' + ((i.experience_years != null) ? i.experience_years : 0)
        + ' ' + expWord(+i.experience_years || 0);
      var cars = (i.cars || []).map(function (c) {
        return [c.brand, c.model].filter(Boolean).join(' ');
      }).filter(Boolean);
      if (cars.length) sub += ' · ' + cars.join(', ');
      return sub;
    });
    // агрегат FR-35: «X.X ★» + «N отзывов учеников» либо «☆» + «отзывов пока нет»
    var iRatingMain = computed(function () {
      var r = instructor.value && instructor.value.rating;
      return (r && r.has_reviews !== false && r.count)
        ? (+r.average).toFixed(1) + ' ★' : '☆';
    });
    var iRatingSub = computed(function () {
      var r = instructor.value && instructor.value.rating;
      return (r && r.has_reviews !== false && r.count)
        ? r.count + ' отзывов учеников' : 'отзывов пока нет';
    });

    // состояние «уже оставлен» (409) / «отправлен» (200) — данными сервера
    function showDone(title) {
      doneTitle.value = title;
      done.value = true;
    }

    function submit() {
      sending.value = true; // кнопка блокируется сразу, как legacy btn.disabled=true
      // URL — строковой конкатенацией (needle TC-S3BE-041 дословно)
      api('/api/student/instructors/'+instructorId+'/reviews', {
        method: 'POST',
        body: JSON.stringify({ rating: rating.value, text: text.value.trim() })
      }, function (res) {
        // только 401 — сессия; 403 — бизнес-ошибка тостом (NFR-2)
        if (res.status === 401) { toLogin(); return; }
        if (res.status === 200 && res.data && res.data.ok) {
          showDone('Отзыв отправлен');
          toast('Отзыв отправлен: оценка ' + rating.value + ' из 5. Спасибо — он появится в карточке инструктора.');
        } else if (res.status === 409) {
          showDone('Отзыв уже отправлен');
          sending.value = false; // кнопка обратно активна
          toast('Отзыв: вы уже оставляли отзыв этому инструктору.');
        } else {
          sending.value = false;
          toast((res.data && res.data.error) || 'Не удалось отправить отзыв');
        }
      });
    }

    onMounted(function () {
      // --- сессия ученика (единый паттерн кабинета, sdd §10.2–10.3) ---
      if (!getToken()) { toLogin(); }
      // ФИО/аватар ученика (FR-5)
      api('/api/auth/me', {}, function (res) {
        if (handleAuthFail(res)) return;
        if (!res.data || !res.data.ok) return;
        user.value = res.data.user || {};
      });

      // --- цель отзыва: /review?instructor=<id> (переход из «Моих заявок») ---
      var params = new URLSearchParams(location.search);
      instructorId = +(params.get('instructor') || 0);
      if (!instructorId) { location.href = '/my-requests'; }
      // контекст: GET /api/student/instructors/{id} (ФИО, стаж, авто, агрегат)
      api('/api/student/instructors/'+instructorId, {}, function (res) {
        if (handleAuthFail(res)) return;
        if (!res.data || !res.data.ok) { toast('Инструктор не найден'); return; }
        instructor.value = res.data.instructor || {};
      });

      // paint(0) legacy — эквивалентен начальному состоянию (rating=0,
      // preview=null, подпись LABELS[0] в статической разметке).
    });

    return {
      LABELS: LABELS,
      painted: painted,
      previewStar: previewStar,
      leaveStar: leaveStar,
      fixRating: fixRating,
      text: text,
      canSend: canSend,
      sending: sending,
      submit: submit,
      done: done,
      doneTitle: doneTitle,
      unameText: unameText,
      avaText: avaText,
      instructor: instructor,
      iName: iName,
      iAva: iAva,
      iSub: iSub,
      iRatingMain: iRatingMain,
      iRatingSub: iRatingSub,
    };
  },
};
</script>
