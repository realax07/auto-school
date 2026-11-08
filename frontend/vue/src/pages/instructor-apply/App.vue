<!-- Анкета инструктора «/instructors/apply» (Спринт 12, change
     add-vue-s12-landing-apply, задача 3.1). Разметка — перенос 1:1 из
     legacy frontend/instructor-apply.html (тексты/CSS мокапа
     registration-instructor дословно, без редизайна; стили —
     styles.css, перенос дословный). Держать синхронной со статической
     разметкой instructor-apply.html (носитель §4.2 test_instructor_pages).
     Поведение — wiring legacy js/apply.js 1:1: формат own/sber —
     эквивалент updateFormat реактивной связью (госномер disabled/очистка/
     приглушение — семантика мокапа сохранена); выбор ВУ → миниатюра
     objectURL / клиентская ошибка (JPEG/PNG ≤5 МБ — тексты совпадают с
     серверными, BUG-048); consent-гейт кнопки (FR-77); сабмит — FormData
     построчно как legacy (15 fd.append-строк: 14 полей + consent
     'true'/'false', + условный license_photo — arch-review-001 MIN-1),
     fetch('/api/instructors/apply', method:'POST') — СТРОКОВО как в
     legacy; 200 → localStorage application_poll_token/
     application_exchange_token ДО редиректа /instructors/pending; 413/
     415/422-файловые → #license-error + #notice; согласие — 422 позиция
     1a (сервер, «Согласие: поле обязательно») → #notice; сеть → #notice
     «Ошибка сети». Сессия по заявке не выдается — хранение сессии на
     странице НЕ используется. Id-якоря e2e дословно (#registration,
     #license-file, .checkline, #notice и др. — TC-UI-004-серия). -->
<template>
<header class="wrap"><a class="brand" href="/instructors"><span class="check">✓</span><span><b>Сбер</b>Автошкола</span></a><a class="back" href="/instructors">← Вернуться на лендинг</a></header>
<main class="wrap layout"><aside class="intro"><div class="eyebrow">Подключение инструкторов</div><h1>Начнём<br>с <span style="color:#70efa5">простого.</span></h1><p>Оставь данные, выбери формат работы — команда СберАвтошколы свяжется с тобой и расскажет о следующих шагах.</p><div class="path"><div class="path-row"><div class="path-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></div><div><strong>01 · Анкета</strong><span>Контакты и информация об автомобиле</span></div></div><div class="path-row"><div class="path-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M12 3 20 6v5c0 5-3.5 8.3-8 10-4.5-1.7-8-5-8-10V6l8-3Z" stroke="currentColor" stroke-width="1.5"/><path d="m8 12 2.5 2.5L16 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></div><div><strong>02 · Проверка</strong><span>Квалификация и документы</span></div></div><div class="path-row"><div class="path-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16v13H4zM8 7V4h8v3M8 12h8" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg></div><div><strong>03 · Подключение</strong><span>Согласование условий сотрудничества</span></div></div></div><div class="side-note"><b>Важно:</b> заполняй только свои данные. Документы и сведения будут использоваться для рассмотрения заявки после настройки защищённого процесса обработки данных.</div></aside>
<section class="form-card"><div class="form-head"><div><h2>Заявка инструктора</h2><p>Заполни поля, отмеченные звёздочкой. Остальные данные можно уточнить позднее.</p></div><div class="badge">Этап 1 из 2</div></div><div class="progress"><span></span><span></span><span></span></div>
<form id="registration" @submit.prevent="submit"><div class="section-title"><em>01</em> Личные данные</div><div class="grid">
<div class="field"><label for="surname">Фамилия <span class="req">*</span></label><input id="surname" name="surname" autocomplete="family-name" placeholder="Иванов" required></div>
<div class="field"><label for="name">Имя <span class="req">*</span></label><input id="name" name="name" autocomplete="given-name" placeholder="Иван" required></div>
<div class="field full"><label for="patronymic">Отчество <span class="req">*</span></label><input id="patronymic" name="patronymic" autocomplete="additional-name" placeholder="Иванович" required></div>
<div class="field"><label for="phone">Номер телефона <span class="req">*</span></label><input id="phone" name="phone" type="tel" autocomplete="tel" placeholder="+7 900 000-00-00" required></div>
<div class="field"><label for="email">Электронная почта <span class="req">*</span></label><input id="email" name="email" type="email" autocomplete="email" placeholder="name@example.ru" required></div>
<div class="field full"><label for="address">Адрес фактического проживания <span class="req">*</span></label><input id="address" name="address" autocomplete="street-address" placeholder="Город, улица, дом, квартира" required><div class="hint">Укажи адрес, по которому фактически проживаешь. Не обязательно совпадает с регистрацией по месту жительства.</div></div>
</div>
<div class="section-title"><em>02</em> Формат работы и автомобиль</div><div class="choice"><label><input type="radio" name="format" value="own" checked v-model="format"> У меня есть свой автомобиль</label><label><input type="radio" name="format" value="sber" v-model="format"> Хочу работать на автомобиле Сбера</label></div>
<div class="grid" style="margin-top:14px"><div class="field full" id="plate-wrap" :style="{opacity: format==='own' ? '1' : '.55'}"><label for="plate">Государственный регистрационный номер автомобиля</label><input id="plate" name="plate" placeholder="Например, А123АА 777" v-model="plate" :disabled="plateDisabled"><div class="hint">Если автомобиля нет, оставь поле пустым.</div></div><div class="field"><label for="license-number">Номер водительского удостоверения <span class="req">*</span></label><input id="license-number" name="license-number" placeholder="Серия и номер" required></div><div class="field"><label for="license-date">Дата выдачи удостоверения</label><input id="license-date" name="license-date" type="date"></div><div class="field"><label for="license-category">Категория прав <span class="req">*</span></label><select id="license-category" name="license-category" required><option value="">Выбери категорию</option><option>B</option><option>A</option><option>C</option><option>D</option><option>BE</option><option>Другая</option></select></div><div class="field"><label for="experience">Стаж вождения</label><select id="experience" name="experience"><option value="">Выбери стаж</option><option>3–4 года</option><option>5–9 лет</option><option>10 лет и больше</option></select></div></div>
<div class="section-title"><em>02.1</em> Пароль для входа</div><div class="grid"><div class="field"><label for="password">Пароль <span class="req">*</span></label><input id="password" name="password" type="password" autocomplete="new-password" placeholder="Минимум 8 символов" required><div class="hint">Понадобится для входа и проверки статуса заявки.</div></div><div class="field"><label for="password-confirm">Подтверждение пароля <span class="req">*</span></label><input id="password-confirm" name="password-confirm" type="password" autocomplete="new-password" placeholder="Повтори пароль" required></div></div>
<div class="section-title"><em>03</em> Документы</div><div class="grid"><div class="field full"><label>Водительское удостоверение</label><label class="upload" for="license-file" :class="{'has-file': hasFile}"><span class="upload-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v4h16v-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="upload-text" style="flex:1"><strong id="file-name">{{ fileName }}</strong><span>JPG или PNG · до 5 МБ</span></span><button type="button" id="pick-file" @click="pickFile">Выбрать файл</button><img id="license-thumb" alt="Миниатюра водительского удостоверения" :src="licenseThumbSrc"><input type="file" id="license-file" accept="image/jpeg,image/png" @change="onLicenseChange"></label><div class="upload-error" id="license-error" role="alert" :class="{show: licenseErrorText}">{{ licenseErrorText }}</div><div class="hint">Дополнительные документы о квалификации и праве обучать вождению можно запросить на следующем этапе.</div></div></div>
<label class="checkline"><input type="checkbox" required v-model="consentChecked"><span>Я подтверждаю, что указал(а) корректные данные, и соглашаюсь на обработку персональных данных для рассмотрения заявки. Согласен(на) с <a href="/policy" target="_blank" rel="noopener">политикой персональных данных</a>. <span class="req">*</span></span></label>
<div class="submit-row"><button class="submit" type="submit" :disabled="!consentChecked">Продолжить →</button><div class="secure">После анкеты — проверка данных и документов.<br>Заявка уйдет на рассмотрение сразу после отправки.</div></div><div class="notice" id="notice" :class="{show: noticeShow}">{{ noticeText }}</div></form></section></main><footer><div class="wrap foot"><span>© СберАвтошкола · Концепция экрана регистрации</span><span>Защита персональных данных должна быть настроена до запуска</span></div></footer>
</template>

<script>
// Контракты вызовов — плоский JS как в legacy apply.js (дословные
// фрагменты: fetch('/api/instructors/apply', method:'POST', new FormData(),
// все fd.append, 5*1024*1024, validateLicenseFile,
// location.href='/instructors/pending'); хранение сессии НЕ используется.
import { computed, ref, watch } from 'vue';

export default {
  name: 'InstructorApplyApp',
  setup: function () {
    // --- формат own/sber: эквивалент updateFormat legacy — реактивная
    // связь radio формата с полем госномера (disabled/очистка/
    // приглушение opacity .55 — семантика мокапа сохранена) ---
    var format = ref('own');
    var plate = ref('');
    var plateDisabled = computed(function () { return format.value !== 'own'; });
    watch(format, function (v) { if (v !== 'own') { plate.value = ''; } });

    // --- consent-гейт кнопки (FR-77): «Продолжить →» недоступна до
    // установки чекбокса согласия; required — второй рубеж ---
    var consentChecked = ref(false);

    // --- BUG-048: выбор файла ВУ → миниатюра objectURL / клиентская
    // ошибка (тексты совпадают с серверными — 422 контракт) ---
    var licenseFileError = null;
    var licenseObjectUrl = null;
    var fileName = ref('Прикрепить фото или скан');
    var licenseThumbSrc = ref(null);
    var hasFile = ref(false);
    var licenseErrorText = ref('');

    function validateLicenseFile(file){
     if(file.size>5*1024*1024)return 'Файл: изображение больше 5 МБ';
     var type=(file.type||'').toLowerCase(),ext=(file.name.split('.').pop()||'').toLowerCase();
     var okType=['image/jpeg','image/jpg','image/png'].indexOf(type)!==-1;
     var okExt=['jpg','jpeg','png'].indexOf(ext)!==-1;
     if(!okType&&!okExt)return 'Файл: допустимы только изображения JPEG или PNG';
     return null;
    }
    // resetLicensePreview legacy: скрыть миниатюру, освободить objectURL
    function resetLicensePreview(){
     hasFile.value=false;
     if(licenseObjectUrl){URL.revokeObjectURL(licenseObjectUrl);licenseObjectUrl=null;}
    }
    function onLicenseChange(e){
     var input=e.target,file=input.files[0];
     resetLicensePreview();licenseFileError=null;licenseErrorText.value='';
     if(!file){fileName.value='Прикрепить фото или скан';return;}
     var err=validateLicenseFile(file);
     if(err){ // красный текст ошибки, миниатюры нет, отправка блокируется
       licenseFileError=err;licenseErrorText.value=err;input.value='';
       fileName.value='Прикрепить фото или скан';return;
     }
     fileName.value=file.name;
     licenseObjectUrl=URL.createObjectURL(file);
     licenseThumbSrc.value=licenseObjectUrl;
     hasFile.value=true;
    }
    // клик по «Выбрать файл» открывает выбор (как и клик по миниатюре —
    // label for=license-file, разметка legacy)
    function pickFile(){document.getElementById('license-file').click();}

    // --- notice под формой: эквивалент notice.classList.add('show') —
    // класс show из реактивного состояния ---
    var noticeShow = ref(false);
    var noticeText = ref('Не удалось отправить заявку. Проверь заполнение полей и попробуй ещё раз.');

    // --- сабмит: POST /api/instructors/apply, multipart/form-data (все
    // поля анкеты + license_photo). Токен сессии не используется: сессия
    // по этой заявке не выдается. 200 → токены заявки в localStorage ДО
    // редиректа (application_poll_token / application_exchange_token);
    // 413/415/422 → сообщение от сервера видно у поля загрузки ВУ и под
    // формой; клиентская ошибка файла блокирует отправку. ---
    function submit(){
      var notice=document.getElementById('notice');
      noticeShow.value=false;
      if(licenseFileError){ // валидный файл не выбран — отправка заблокирована
        licenseErrorText.value=licenseFileError;
        document.getElementById('license-error').scrollIntoView({behavior:'smooth',block:'nearest'});
        return;
      }
      licenseErrorText.value='';
      // Явный набор полей (name-атрибуты макета используют дефисы,
      // контракту нужны snake_case ключи) + license_photo.
      function val(id){return document.getElementById(id).value.trim();}
      var fd=new FormData();
      fd.append('surname',val('surname'));
      fd.append('name',val('name'));
      fd.append('patronymic',val('patronymic'));
      fd.append('phone',val('phone'));
      fd.append('email',val('email'));
      fd.append('address',val('address'));
      fd.append('work_format',document.querySelector('input[name="format"]:checked').value);
      fd.append('plate',val('plate'));
      fd.append('license_number',val('license-number'));
      fd.append('license_date',document.getElementById('license-date').value);
      fd.append('license_category',document.getElementById('license-category').value);
      fd.append('experience',document.getElementById('experience').value);
      fd.append('password',document.getElementById('password').value);
      fd.append('password_confirm',document.getElementById('password-confirm').value);
      fd.append('consent',document.querySelector('.checkline input').checked?'true':'false');
      var lf=document.getElementById('license-file').files[0];
      if(lf)fd.append('license_photo',lf,lf.name);
      fetch('/api/instructors/apply',{method:'POST',body:fd})
        .then(function(r){return r.text().then(function(t){var d=null;try{d=t?JSON.parse(t):null}catch(err){}return {status:r.status,data:d};})})
        .then(function(res){
          if(res.status===200&&res.data&&res.data.ok){
            // Токены заявки из ответа apply — в localStorage ДО редиректа
            // на экран ожидания (хранение в localStorage осознанно —
            // обязано переживать перезагрузки экрана). Ошибка записи
            // localStorage не мешает редиректу. При 422/ошибке токены не
            // сохраняются — эта ветка не выполняется.
            try{
              if(res.data.poll_token){localStorage.setItem('application_poll_token',res.data.poll_token);}
              if(res.data.exchange_token){localStorage.setItem('application_exchange_token',res.data.exchange_token);}
            }catch(err){}
            location.href='/instructors/pending';
          }
          else{
            var msg=(res.data&&res.data.error)
              ||(res.status===413?'Файл: изображение больше 5 МБ'
              :res.status===415?'Файл: допустимы только изображения JPEG или PNG'
              :'Ошибка отправки заявки');
            if(res.status===413||res.status===415||(res.status===422&&msg.indexOf('Файл')===0)){
              licenseErrorText.value=msg; // только файловые ошибки — у поля загрузки
            }
            noticeText.value=msg;
            noticeShow.value=true;
            notice.scrollIntoView({behavior:'smooth',block:'nearest'});
          }
        })
        .catch(function(){
          noticeText.value='Ошибка сети';
          noticeShow.value=true;
        });
    }

    return {
      format: format,
      plate: plate,
      plateDisabled: plateDisabled,
      consentChecked: consentChecked,
      fileName: fileName,
      licenseThumbSrc: licenseThumbSrc,
      hasFile: hasFile,
      licenseErrorText: licenseErrorText,
      noticeShow: noticeShow,
      noticeText: noticeText,
      pickFile: pickFile,
      onLicenseChange: onLicenseChange,
      submit: submit,
    };
  },
};
</script>
