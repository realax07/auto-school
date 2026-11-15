<!-- Спринт 17 (change add-pdd-learning, задача 17.5.1): секция «Билеты» —
     тренажёр кабинета ученика, мокап design/mocks/pdd-bilety-trenazher.html
     ИСТОЧНИК ДИЗАЙНА (классы exam-bar/exam-meta/timer/score, q-card/q-num/
     q-text/q-img/answers/ans/tag/tip, q-nav/qn — дословно; стили — в конце
     styles.css). Lazy-чанк: App.vue монтирует через defineAsyncComponent
     с v-if="pddTicketsVisited" (NFR-26).
     Данные — pdd-bilety-index.json (static import, ~1 КБ gzip) + JSON
     билета — ДИНАМИЧЕСКИЙ import по выбору (чанк ~6–8 КБ gzip на билет,
     design «Бюджеты»: шардинг по билету вынуждает правило (г)).
     Автомат экранов (design «Решение 2»): выбор (категория abm|cd, билет
     1–40) → тренировка (таймер 20:00 обратный отсчет, авто-финиш на
     00:00; клик ответа ФИКСИРУЕТ его однократно: неверный — красный,
     верный — зеленый + блок пояснения; q-nav 1–20 со статусами;
     «Сдать» досрочно) → результат (счёт, статусы 1–20, «Пройти снова»/
     «Выбрать другой билет»). Состояние — Vue ref, БЕЗ персистентности
     (решение Заказчика). Чистая арифметика (часы/статусы/счёт) — в
     sections/pdd-logic.mjs (unit-носитель tests/unit/test_pdd_tickets_logic.py). -->
<template>
  <div>
    <!-- ЭКРАН ВЫБОРА: категории A/B/M и C/D, билеты 1–40 из pdd-bilety-index.json -->
    <div v-if="!ticketId" class="tk-cats" data-test="pdd-tk-pick">
      <div v-for="cat in categories" :key="cat.id" class="tk-cat" :data-test="'pdd-tk-cat-' + cat.id">
        <b>{{ catTitle(cat.id) }}</b>
        <div class="tk-tickets">
          <button v-for="t in cat.tickets" :key="t.id" type="button" class="tk-ticket"
                  :data-test="'pdd-tk-ticket-' + t.id" :disabled="loading" @click="startTicket(t.id)">
            {{ t.number }}
          </button>
        </div>
      </div>
      <div v-if="loadError" class="tk-loading" data-test="pdd-tk-error">Не удалось загрузить билет — попробуйте ещё раз.</div>
    </div>

    <!-- ТРЕНИРОВКА: экзамен-бар + карточка вопроса + сетка навигации -->
    <template v-else-if="!finished">
      <div class="exam-bar" data-test="pdd-exam-bar">
        <div class="exam-meta"><b>Билет {{ ticketNumber }}</b><span>{{ catTitle(category) }}</span></div>
        <div class="timer">⏱ <b data-test="pdd-timer">{{ clockText }}</b></div>
        <div class="score" data-test="pdd-score">Верных: <b class="g">{{ score.good }}</b> · Ошибок: <b class="r">{{ score.wrong }}</b></div>
        <button type="button" class="tk-finish" data-test="pdd-finish" @click="finish">Сдать</button>
      </div>
      <div v-if="questions.length" class="q-card" data-test="pdd-q-card">
        <div class="q-num" data-test="pdd-q-num">Вопрос {{ cur + 1 }} из {{ questions.length }}</div>
        <p class="q-text" data-test="pdd-q-text">{{ activeQuestion.text }}</p>
        <img v-if="activeQuestion.image" class="q-img" :src="activeQuestion.image"
             alt="ситуация вопроса" loading="lazy" data-test="pdd-q-img">
        <div class="answers" data-test="pdd-answers">
          <button v-for="(opt, i) in activeQuestion.options" :key="i" type="button" class="ans"
                  :class="ansClass(i)" :data-test="'pdd-ans-' + i" @click="pick(i)">
            {{ (i + 1) + '. ' + opt.text }}<span v-if="revealed && opt.correct" class="tag">Верный</span>
          </button>
        </div>
        <div v-if="revealed" class="tip" data-test="pdd-tip"><b>Пояснение:</b> {{ activeQuestion.explanation }}</div>
      </div>
      <div class="q-nav" data-test="pdd-q-nav">
        <button v-for="(st, i) in statuses" :key="i" type="button" class="qn"
                :class="[st, { cur: i === cur }]" :data-test="'pdd-qn-' + (i + 1)" @click="go(i)">{{ i + 1 }}</button>
      </div>
    </template>

    <!-- РЕЗУЛЬТАТ: балл, верных/всего, статусы 1–20, кнопки повтора/выбора -->
    <div v-else class="tk-result" data-test="pdd-result">
      <h2>Билет {{ ticketNumber }} — результат</h2>
      <div class="tk-res-score" data-test="pdd-res-score">{{ score.good }} из {{ questions.length }}</div>
      <div class="score" data-test="pdd-res-detail">Верных: <b class="g">{{ score.good }}</b> · Ошибок: <b class="r">{{ score.wrong }}</b> · Не отвечено: {{ questions.length - score.answered }}</div>
      <div class="q-nav" data-test="pdd-res-nav">
        <button v-for="(st, i) in statuses" :key="i" type="button" class="qn" :class="st">{{ i + 1 }}</button>
      </div>
      <div class="tk-actions">
        <button type="button" class="tk-btn primary" data-test="pdd-res-again" @click="again">Пройти снова</button>
        <button type="button" class="tk-btn" data-test="pdd-res-other" @click="other">Выбрать другой билет</button>
      </div>
    </div>
  </div>
</template>

<script>
import { onBeforeUnmount } from 'vue';
import {
  fmtClock, decClock, timeUp, isAnswered, fixAnswer, statusesOf, scoreOf,
} from './pdd-logic.mjs';

// Шардинг ПО БИЛЕТУ (design «Бюджеты»): import.meta.glob (lazy по
// умолчанию) код-сплитит каждый pdd-bilety-<cat>-<nn>.json в ОТДЕЛЬНЫЙ
// lazy-чанк ~6–8 КБ gzip — выбор билета тянет ровно один маленький чанк;
// переменный путь в голом import() rolldown не анализирует.
const TICKET_CHUNKS = import.meta.glob('../pdd-data/pdd-bilety-*.json');

var CATEGORY_TITLES = { abm: 'категория A/B/M', cd: 'категория C/D' };
var EXAM_SECONDS = 20 * 60; // таймер 20:00 — режим экзамена (мокап/design)

export default {
  name: 'PddTickets',
  data() {
    return {
      categories: [],
      // выбранный билет: id ('abm-01')/номер/категория и его вопросы
      ticketId: null,
      ticketNumber: 0,
      category: '',
      questions: [],
      loading: false,
      loadError: false,
      // тренировка: выбор на каждый вопрос (однократная фиксация),
      // текущий вопрос, часы; finished — экран результата
      picked: [],
      cur: 0,
      clock: EXAM_SECONDS,
      finished: false,
    };
  },
  computed: {
    activeQuestion() {
      return this.questions[this.cur] || null;
    },
    statuses() {
      return statusesOf(this.questions, this.picked);
    },
    score() {
      return scoreOf(this.statuses);
    },
    revealed() {
      return isAnswered(this.picked[this.cur]);
    },
    clockText() {
      return fmtClock(this.clock);
    },
  },
  mounted() {
    // индекс билетов из glob-карты (MIN-2: без статического импорта —
    // иначе дублирование + INEFFECTIVE_DYNAMIC_IMPORT паразитный чанк)
    var idxLoader = TICKET_CHUNKS['../pdd-data/pdd-bilety-index.json'];
    if (idxLoader) {
      var self = this;
      idxLoader().then(function (m) { self.categories = (m.default || m).categories; });
    }
  },
  beforeUnmount() {
    this.stopTimer();
  },
  methods: {
    catTitle(id) {
      return CATEGORY_TITLES[id] || id;
    },
    // выбор билета: JSON билета — lazy-чанк по билету (глоб-карта выше);
    // чанк тянется при ПЕРВОМ выборе билета и кэшируется модулем
    startTicket(id) {
      if (this.loading) return;
      var loader = TICKET_CHUNKS['../pdd-data/pdd-bilety-' + id + '.json'];
      if (!loader) {
        this.loadError = true;
        return;
      }
      this.loadError = false;
      this.loading = true;
      var self = this;
      loader()
        .then(function (mod) {
          var data = mod.default;
          self.ticketId = data.id;
          self.ticketNumber = data.number;
          self.category = data.category;
          self.questions = data.questions;
          self.loading = false;
          self.restartRun();
        })
        .catch(function () {
          self.loading = false;
          self.loadError = true;
        });
    },
    restartRun() {
      this.picked = this.questions.map(function () { return null; });
      this.cur = 0;
      this.clock = EXAM_SECONDS;
      this.finished = false;
      this.startTimer();
    },
    startTimer() {
      this.stopTimer();
      var self = this;
      this._timerId = setInterval(function () {
        self.clock = decClock(self.clock);
        if (timeUp(self.clock)) {
          // 00:00 — авто-финиш с подсчетом отвеченного (design «Решение 2»)
          self.stopTimer();
          self.finished = true;
        }
      }, 1000);
    },
    stopTimer() {
      if (this._timerId) {
        clearInterval(this._timerId);
        this._timerId = null;
      }
    },
    // клик по варианту ФИКСИРУЕТ ответ немедленно и ОДНОКРАТНО: повторный
    // клик (и клик по другому варианту) ответ не меняет (design «Решение 2»)
    pick(choice) {
      if (isAnswered(this.picked[this.cur])) return;
      this.picked[this.cur] = fixAnswer(this.picked[this.cur], choice);
    },
    ansClass(i) {
      var q = this.activeQuestion;
      if (!this.revealed) return {};
      return {
        good: !!q.options[i].correct,
        wrong: this.picked[this.cur] === i && !q.options[i].correct,
      };
    },
    go(i) {
      this.cur = i;
    },
    // «Сдать» досрочно — итог по отвеченному
    finish() {
      this.stopTimer();
      this.finished = true;
    },
    again() {
      this.restartRun();
    },
    other() {
      this.stopTimer();
      this.ticketId = null;
      this.questions = [];
      this.finished = false;
    },
  },
};
</script>
