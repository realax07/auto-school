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
     #/pdd-fines (design «Решение 4»).
     Замечание Заказчика 2026-11-15 №2: деталь знака — МОДАЛЬНОЕ окно
     ПОВЕРХ страницы (было: блок внизу .zn-detail): fixed overlay с блюром
     фона (backdrop-filter: blur(8px) + затемнение — канон модалок входа
     LoginModal/RegisterModal, мокап-источник обновлен тем же решением),
     центрированная карточка zn-detail/zn-modal (крупная картинка знака,
     номер+название, описание, блок штрафа при наличии). Закрытие: ✕,
     ESC, клик по бэкдропу (@click.self); на время модалки скролл страницы
     заблокирован (document.body.style.overflow — прецедент модалок
     кабинета в App.vue). -->
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
    <!-- модалка детали знака (замечание 2026-11-15 №2): overlay поверх
         страницы; клик по карточке НЕ закрывает (@click.self), по бэкдропу —
         закрывает; ✕/ESC — тоже (watch selected + onKeydown) -->
    <div v-if="selected" class="zn-overlay" data-test="pdd-modal" @click.self="closeSign">
      <button type="button" class="zn-close" data-test="pdd-close" aria-label="Закрыть" title="Закрыть" @click="closeSign">×</button>
      <div class="zn-detail zn-modal" data-test="pdd-detail" role="dialog" aria-modal="true" :aria-label="'Знак ' + selected.number">
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
      </div>
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
  watch: {
    // модалка: ESC-закрытие + блокировка скролла страницы, пока открыта
    // (снятие блокировки — и при закрытии, и при размонтировании чанка)
    selected(open) {
      if (open) {
        document.addEventListener('keydown', this.onKeydown);
        document.body.style.overflow = 'hidden';
      } else {
        document.removeEventListener('keydown', this.onKeydown);
        document.body.style.overflow = '';
      }
    },
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.onKeydown);
    document.body.style.overflow = '';
  },
  methods: {
    onKeydown(e) {
      if (e.key === 'Escape') this.closeSign();
    },
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
