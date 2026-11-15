<!-- Спринт 17 (change add-pdd-learning, задача 17.4.1): секция «Правила»
     кабинета ученика — мокап design/mocks/pdd-pravila-student.html ИСТОЧНИК
     ДИЗАЙНА (two-column prav-wrap по правке Заказчика; классы toc/toc-item/
     chapter — дословно, стили — в конце styles.css). Lazy-чанк: App.vue
     монтирует через defineAsyncComponent с v-if="pddRulesVisited" (NFR-26).
     Данные — pdd-pravila.json генератора 17.2.1 (26 глав: id, заголовок
     = H1-блок корпуса, html-блоки пунктов — белая конвертация генератора с
     экранированием; v-html ТОЛЬКО для этих сгенерированных полей — контент
     корпуса доверенный, пользовательского ввода в секции нет).
     Оглавление — 26 пунктов ПО КОРПУСУ (toc мокапа из 29 пунктов —
     иллюстрация, proposal «Сверка»); переход по клику — клиентский,
     без перезагрузки; активный toc-item подсвечен. -->
<template>
  <div class="prav-wrap" data-test="pdd-prav-wrap">
    <div class="toc" data-test="pdd-toc">
      <button v-for="c in chapters" :key="c.id" type="button" class="toc-item"
              :class="{ on: c.id === activeId }" :data-test="'pdd-toc-item-' + c.id"
              @click="openChapter(c.id)">{{ c.title }}</button>
    </div>
    <article class="chapter" data-test="pdd-chapter">
      <div class="kicker">Глава {{ activeChapter.id }}</div>
      <h2>{{ activeChapter.title }}</h2>
      <div class="chapter-body" v-html="activeHtml" data-test="pdd-chapter-body"></div>
    </article>
  </div>
</template>

<script>
// Данные всей книги (~90 КБ gzip) в одном чанке — одноцелевая lazy-загрузка
// допустима (design «Решение 5»); переходы по toc — клиентский стейт.
import pravilaData from '../pdd-data/pdd-pravila.json';

export default {
  name: 'PddRules',
  data() {
    return {
      chapters: pravilaData,
      activeId: pravilaData.length ? pravilaData[0].id : 1,
    };
  },
  computed: {
    activeChapter() {
      return this.chapters.find(function (c) { return c.id === this.activeId; }, this) || this.chapters[0];
    },
    activeHtml() {
      return this.activeChapter.html.join('\n');
    },
  },
  methods: {
    openChapter(id) {
      this.activeId = id;
    },
  },
};
</script>
