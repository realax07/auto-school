<!-- Спринт 17 (change add-pdd-learning, задача 17.3.1): секция «Знаки»
     кабинета ученика — мокап design/mocks/pdd-znaki-student.html ИСТОЧНИК
     ДИЗАЙНА (классы chips/chip, zn-grid/zn, zn-detail/zd-head/fine —
     дословно; стили — в конце styles.css). Lazy-чанк секции: App.vue
     монтирует через defineAsyncComponent с v-if="visited" — чанк грузится
     при ПЕРВОМ открытии раздела и остается смонтированным (NFR-26).
     Данные — pdd-znaki.json генератора 17.2.1 (static import — инлайнится
     в чанк секции, ~61 КБ gzip ≤ 150: чипы 8 групп со счётчиками корпуса,
     321 знак: номер/название/группа/image=/pdd-assets/znaki/<номер>small.png
     (native lazy)/desc/fine). Блок штрафа — УСЛОВНЫЙ рендер по корпусу
     (fine у 166/321); у 5.33.1/5.34.1 desc пуст — блок описания не
     рендерится (гейт-допуск генератора). Кросс-ссылка fine-блока —
     #/pdd-fines (design «Решение 4»). -->
<template>
  <div>
    <div class="chips" data-test="pdd-chips">
      <button v-for="g in groups" :key="g.id" type="button" class="chip"
              :class="{ on: g.id === activeGroup }" :data-test="'pdd-chip-' + g.id"
              @click="selectGroup(g.id)">{{ g.name }} <b>{{ g.count }}</b></button>
    </div>
    <div class="zn-grid" data-test="pdd-grid">
      <figure v-for="s in groupSigns" :key="s.number" class="zn" data-test="pdd-card"
              @click="openSign(s)">
        <img :src="s.image" :alt="s.number" loading="lazy">
        <figcaption><b>{{ s.number }}</b> {{ s.name }}</figcaption>
      </figure>
    </div>
    <div v-if="selected" class="zn-detail" data-test="pdd-detail">
      <div class="zd-head">
        <img :src="selected.image" :alt="selected.number">
        <div>
          <div class="kicker">Знак {{ selected.number }}</div>
          <b>{{ selected.name }}</b>
          <small class="zn-group">{{ groupName(selected.group) }}</small>
        </div>
      </div>
      <p v-if="selected.desc" data-test="pdd-desc">{{ selected.desc }}</p>
      <div v-if="selected.fine" class="fine" data-test="pdd-fine">⚠ {{ selected.fine }}<a class="fine-link" href="#/pdd-fines">все штрафы →</a></div>
      <button type="button" class="zn-back" data-test="pdd-back" @click="closeSign">← назад к группе</button>
    </div>
  </div>
</template>

<script>
// Данные всей выборки (321 знак) уже в чанке — фильтр группы/деталь
// клиентские, без запросов (design «Решение 4»).
import znakiData from '../pdd-data/pdd-znaki.json';

export default {
  name: 'PddSigns',
  data() {
    return {
      groups: znakiData.groups,
      signs: znakiData.signs,
      // мокап начинает с активной первой группы («Все» не вводится)
      activeGroup: znakiData.groups.length ? znakiData.groups[0].id : 't1',
      selected: null,
    };
  },
  computed: {
    groupSigns() {
      return this.signs.filter(function (s) { return s.group === this.activeGroup; }, this);
    },
  },
  methods: {
    selectGroup(id) {
      this.activeGroup = id;
      this.selected = null;
    },
    openSign(sign) {
      this.selected = sign;
    },
    closeSign() {
      this.selected = null;
    },
    groupName(id) {
      const g = this.groups.find(function (x) { return x.id === id; });
      return g ? g.name : '';
    },
  },
};
</script>
