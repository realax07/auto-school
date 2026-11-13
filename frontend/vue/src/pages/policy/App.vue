<!-- «Политика персональных данных» — публичная страница /policy
     (оболочка БЕЗ текста политики — NFR-25: исходник страницы текста не
     содержит; grep-контроль test_policy зелен).
     Разметка — дословный перенос frontend/policy.html (Спринт 15,
     change add-vue-s15-final-migration, задача 3.1; шаблон повторяет вход
     vue/policy.html — «Разметку держать синхронной с App.vue»).
     Логика — перенос js/policy.js 1:1 (Спринт 9, задача 2.1,
     FR-76/NFR-25): fetch GET /api/policy → «Версия: X от Y» (строковая
     конкатенация дословно — MIN-2 С11); абзацы split(/\n\s*\n/) →
     интерполяция Vue = текстовые узлы (textContent-семантика, НЕ
     innerHTML — XSS-гигиена); 500/битый JSON/сеть → честное сообщение
     p.policy-error «Политика временно недоступна. Попробуйте позже» +
     пустой #policy-meta. Текст политики в этом компоненте ОТСУТСТВУЕТ
     (приходит только из API). -->
<template>
<div class="frame">
<header class="top"><a class="brand" href="/"><span class="check">✓</span><span><b>Сбер</b>Автошкола</span></a><a class="back" href="/">← Назад</a></header>
<h1>Политика персональных данных</h1>
<p class="meta" id="policy-meta">{{ metaText }}</p>
<div class="policy-text" id="policy-text"><p v-for="(p, ix) in paras" :key="ix">{{ p }}</p><p v-if="errShow" class="policy-error">{{ errorMessage }}</p></div>
</div>
</template>

<script>
// Логика — перенос js/policy.js 1:1 (fetch + split абзацев + текстовые
// узлы; design.md «Судьба каталога js/», задача 3.1).
import { onMounted, ref } from 'vue';

export default {
  name: 'PolicyApp',
  setup: function () {
    var metaText = ref('');
    var paras = ref([]);
    var errShow = ref(false);
    var errorMessage = 'Политика временно недоступна. Попробуйте позже';

    function showError() {
      metaText.value = '';
      paras.value = [];
      errShow.value = true;
    }

    onMounted(function () {
      fetch('/api/policy')
        .then(function(r) {
          return r.json().then(function(d) {
            return {status: r.status, data: d};
          }).catch(function() {
            return {status: r.status, data: null}; // ответ не JSON — честная ошибка
          });
        })
        .then(function(res) {
          if (!(res.status === 200 && res.data && res.data.ok && res.data.text)) {
            showError();
            return;
          }
          metaText.value = 'Версия: ' + res.data.version + ' от ' + res.data.date;
          String(res.data.text).split(/\n\s*\n/).forEach(function(chunk) {
            var p = chunk.replace(/^\s+|\s+$/g, '');
            if (!p) return;
            paras.value.push(p); // интерполяция = только текстовые узлы, без HTML-инъекций
          });
        })
        .catch(showError);
    });

    return { metaText: metaText, paras: paras, errShow: errShow, errorMessage: errorMessage };
  },
};
</script>
