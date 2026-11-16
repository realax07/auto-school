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
        <template v-if="selected.desc">
          <div
            v-for="(item, pi) in selectedDescItems"
            :key="pi"
            class="zn-para"
            :class="'zn-para-' + item.type"
            data-test="pdd-desc"
          >
            <span class="zn-dot" :class="'zn-dot-' + item.type"></span>
            <p>{{ item.text }}</p>
          </div>
        </template>
        <div v-if="selected.fine" class="fine" data-test="pdd-fine">
          <div class="fine-head"><span class="fine-ico">⚖</span> Штраф и наказание</div>
          <p
            v-for="(line, li) in fineRenderLines"
            :key="li"
            class="fine-line"
            :class="line.itemCls"
            v-html="line.html"
          ></p>
          <a class="fine-link" href="#/pdd-fines">все штрафы →</a>
        </div>
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
    // абзацы описания по смыслу (замечание Заказчика 2026-11-15: «сплошным
    // текстом… сделать более читабельным», «табуляции, графику»):
    // назначение — 🛈, исключения — 🚫 (красная планка + отступ)
    selectedDescItems() {
      if (!this.selected || !this.selected.descParas) return [];
      return this.selected.descParas.map(function (text) {
        var exception = /^(Знак\s+не\s+(применяется|касается)|Однако\s+действие\s+знака\s+не\s+распространяется|Исключени)/.test(text.trim());
        return { text: text, type: exception ? 'exception' : 'info' };
      });
    },
    // суммы — акцентом (экранирование до обертки; v-html только на esc+regex)
    // строки штрафа: экранирование + суммы акцентом; перечни а)/б)/в)
    // (и 1./2./3.) — отдельными строками с табуляцией (замечание Заказчика)
    fineRenderLines() {
      if (!this.selected || !this.selected.fineLines) return [];
      var esc = function (t) {
        return String(t)
          .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      };
      return this.selected.fineLines.map(function (raw) {
        var line = raw.trim();
        var isItem = /^[а-дё]\)|^\d\.\s|^\d\)/.test(line);
        var html = esc(line).replace(
          /((?:от|до)\s+)?\d[\d\u00a0 ]*(?:₽|руб\S*)/gi,
          '<b class="fine-sum">$&</b>'
        );
        return { html: html, itemCls: isItem ? 'fine-item' : '' };
      });
    },
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
