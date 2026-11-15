<!-- Спринт 17 (change add-pdd-learning, задача 17.6.1): секция «Штрафы»
     кабинета ученика — мокап design/mocks/pdd-shtrafi-student.html ИСТОЧНИК
     ДИЗАЙНА (классы search/fines — дословно; стили — в конце styles.css).
     Lazy-чанк: App.vue монтирует через defineAsyncComponent с
     v-if="pddFinesVisited" (NFR-26).
     Данные — pdd-shtrafi.json генератора 17.2.1 (static import, ~6 КБ
     gzip — инлайнится в чанк секции): все строки корпуса (сейчас 58;
     мокап-63 — иллюстрация, proposal «Сверка»). Поиск — клиентская
     фильтрация-подстрока по статье/нарушению/наказанию без учета
     регистра (чистая функция filterFines в sections/pdd-logic.mjs,
     unit-носитель tests/unit/test_pdd_tickets_logic.py); пустой
     результат — строка-заглушка (design «Решение 6»). Заголовок первого
     столбца — «Пункт КоАП» (tasks.md 17.6.1 / design «Решение 6», как в
     источнике корпуса; «Статья» мокапа — иллюстрация). Блок «Популярные
     штрафы» источника не рендерится (навигационный блок сайта, не данные). -->
<template>
  <div>
    <div class="search" data-test="pdd-search">
      <input v-model="query" type="text" data-test="pdd-search-input"
             placeholder="Поиск по статье или нарушению… (например: скорость, переезд, пешеход)">
      <button type="button">Найти</button>
    </div>
    <table class="fines" data-test="pdd-fines-table">
      <thead>
        <tr><th>Пункт КоАП</th><th>Нарушение</th><th>Наказание</th></tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in filtered" :key="i" :data-test="'pdd-fines-row-' + (i + 1)">
          <td>{{ r.article }}</td>
          <td>{{ r.violation }}</td>
          <td>{{ r.penalty }}</td>
        </tr>
        <tr v-if="!filtered.length">
          <td colspan="3" class="fines-empty" data-test="pdd-fines-empty">Ничего не найдено по запросу «{{ query }}» — сократите запрос или проверьте раскладку.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import shtrafiData from '../pdd-data/pdd-shtrafi.json';
import { filterFines } from './pdd-logic.mjs';

export default {
  name: 'PddFines',
  data() {
    return {
      rows: shtrafiData,
      query: '',
    };
  },
  computed: {
    filtered() {
      return filterFines(this.rows, this.query);
    },
  },
};
</script>
