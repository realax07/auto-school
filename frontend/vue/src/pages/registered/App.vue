<!-- Страница после регистрации (заглушка): инфо об успешной регистрации, данные никуда не ушли
     Разметка — дословный перенос frontend/registered.html (Спринт 15,
     change add-vue-s15-final-migration, задача 3.1; шаблон повторяет вход
     vue/registered.html — «Разметку держать синхронной с App.vue»).
     Заглушка С0 сохраняется КАК ЕСТЬ (design.md «Сознательные
     ограничения»): alert «Заглушка: личный кабинет появится в следующем
     спринте» и href="landing-students.html" (файла нет; переход никогда не
     выполняется) — в Vue-эквиваленте inline onclick переносится как
     @click.prevent с тем же alert (named stack-эквивалент: preventDefault
     вместо return false — поведение legacy «переход не выполняется
     никогда» воспроизведено честно). Сервиса за кнопкой НЕ изобретается. -->
<template>
<div class="hero"><div class="card">
  <div class="check">✓</div>
  <h1>Регистрация завершена</h1>
  <p>Вы зарегистрированы как ученик. Мы свяжемся с вами по указанным контакту — расскажем расписание и подберем инструктора.</p>
  <div class="note">Это демонстрационная страница спринта-0: данные формы никуда не отправлялись, база учеников появится вместе с бэкендом.</div>
  <div class="actions">
    <a class="btn btn-primary" href="/">На главную</a>
    <a class="btn btn-ghost" href="landing-students.html" @click.prevent="stubCabinet">Личный кабинет</a>
  </div>
  <div class="brand">СберАвтошкола</div>
</div></div>
</template>

<script>
// Wiring — эквивалент inline onclick легаса 1:1 по поведению:
// alert('Заглушка: личный кабинет появится в следующем спринте');
// return false (переход никогда не выполняется). Никакой другой логики
// страница не имеет (заглушка С0 — перенос дословный).
export default {
  name: 'RegisteredApp',
  setup: function () {
    function stubCabinet(){
      alert('Заглушка: личный кабинет появится в следующем спринте');
      return false;
    }
    return { stubCabinet: stubCabinet };
  },
};
</script>
