<!-- «Мои документы» /instructor/documents — НОВАЯ страница (Спринт 14,
     change add-vue-s14-instructor-loop, задача 3.3; design.md «Страница
     /instructor/documents на Vue»): функциональность — вынос раздела
     «Мои документы» кабинета (С8) на отдельный маршрут. Оболочка —
     минимальная, в стиле кабинета (бренд → /instructor/dashboard,
     «← В кабинет», «Выйти» — механика dashboard-logout → /instructors);
     контент — перенос карточной модели раздела 1:1 (функции docName/
     docMetaText/docVersionLine/docSubverNodes/docCardNode/openDocs —
     дословно из dashboard-instructor.js): ВУ + СТС по каждому авто,
     бейдж «Действует»/«нет СТС» (.ds-*), блок «Ожидает проверки замены»
     (.subver.pend), «Отклонено» с причиной (.subver.rej — ОВ-1/ОВ-7),
     docVersionLine «версия N · загружено …»; просмотр — модалка #m-view
     (BUG-054: стрелки над фото, Esc, клик по фону закрывает); кнопки
     Загрузить/Заменить — диалог #m-replace с предупреждением FR-71 и
     ЯВНОЙ кнопкой «Заменить» (первая загрузка — без предупреждения);
     дозагрузка СТС авто без документа (GET /api/instructor/cars + merge
     как openDocs — FR-69); клиентская валидация JPEG/PNG ≤5 МБ
     (mcValidatePhoto — тексты = серверным); тосты legacy дословно
     («Замена ВУ отправлена на проверку администратору…» и др.);
     перезагрузка списка после успешной загрузки (FR-72).
     Гвард — как в кабинете (GET /api/instructor/me НЕ существует —
     сверка design.md «Сверка контрактов решения»): fetch('/api/auth/me',
     X-Session-Token) → 401 → location.href='/'; данные — GET
     /api/instructor/documents (401/403 → '/'); контракты БЕЗ ИЗМЕНЕНИЙ:
     GET /api/instructor/documents, GET …/{doc_id}/file (только владелец),
     POST /api/instructor/documents/license ('file'), POST
     /api/instructor/cars/{id}/photo/sts ('photo'). Виджетов в разделе
     нет (FR-73); ссылок из кабинета НЕ добавляется (сайдбар «ровно
     перечень» — TC-UI-028). Разметку держать синхронной с входом
     vue/documents.html (id-якоря раздела: #lic-docs/#sts-docs/#lic-n/
     #sts-count/#no-license*/#upload-license/#m-view/#m-replace/#doc-file). -->
<template>
<div class="app">
<aside class="sidebar">
  <a class="brand" href="/instructor/dashboard"><div class="check">✓</div><div>СберАвтошкола<small>Кабинет инструктора</small></div></a>
  <div class="nav-label">Рабочее пространство</div>
  <nav class="nav">
    <button class="active" type="button"><span class="ico">▤</span>Мои документы</button>
  </nav>
  <div class="side-bottom"><strong>Раздел кабинета</strong><p>Та же функциональность, что и в разделе «Профиль и документы» кабинета, — на отдельном маршруте (прямой URL).</p></div>
</aside>

<main>
  <div class="topbar"><div><div class="crumb">Рабочее пространство</div><h1 id="page-title">Мои документы</h1></div><div class="top-actions"><a class="back-btn" href="/instructor/dashboard">← В кабинет</a><div class="user"><div class="avatar" id="avatar">—</div><div><b id="user-fio">…</b><small>Инструктор</small></div></div><button class="icon-btn" @click="logout()" title="Выйти">⎋</button></div></div>

  <section class="card panel">
    <section class="sect">
      <div class="sect-head"><b>Водительское удостоверение</b><span class="n" id="lic-n">0</span><span class="hint">личный документ · из анкеты инструктора</span></div>
      <div class="docs" id="lic-docs"></div>
      <div class="no-license" id="no-license"><b>ВУ не загружено</b><span id="no-license-hint">В вашей анкете не было фото водительского удостоверения.</span><div class="doc-actions" style="justify-content:center;margin-top:14px"><button class="btn-u" id="upload-license" type="button" style="flex:0 0 auto;padding:10px 22px">Загрузить ВУ</button></div></div>
    </section>
    <section class="sect">
      <div class="sect-head"><b>СТС автомобилей</b><span class="n" id="sts-count">0</span><span class="hint">по одному на каждый автомобиль · замена — после проверки администратором</span></div>
      <div class="docs" id="sts-docs"></div>
    </section>
  </section>

  <div class="backdrop" id="m-view" role="dialog" aria-modal="true" aria-labelledby="view-title">
    <div class="viewer">
      <div class="viewer-head">
        <div><h2 id="view-title">Документ</h2><small id="view-sub"></small></div>
        <button class="close" id="view-close" aria-label="Закрыть">×</button>
      </div>
      <div class="full" id="view-full">
        <img id="view-img" alt="">
        <button class="navarrow prev" id="view-prev" type="button" aria-label="Предыдущее фото" style="display:none">‹</button>
        <button class="navarrow next" id="view-next" type="button" aria-label="Следующее фото" style="display:none">›</button>
      </div>
      <div class="viewer-foot">Выдача — авторизованный эндпоинт GET /api/instructor/documents/{doc_id}/file (Content-Type image/*). Чужой или несуществующий документ вернёт 404 — документы других инструкторов недоступны.</div>
    </div>
  </div>

  <div class="backdrop" id="m-replace" role="dialog" aria-modal="true" aria-labelledby="rep-title">
    <div class="viewer" style="width:min(520px,100%)">
      <div class="viewer-head">
        <div><h2 id="rep-title">Заменить документ?</h2><small id="rep-sub">—</small></div>
        <button class="close" id="rep-close" aria-label="Закрыть">×</button>
      </div>
      <div class="warnbox"><b>Замена не вступает в силу сразу.</b> Замена вступит в силу только после проверки администратором: до подтверждения действует предыдущая версия — документ «не мигает». Повторная загрузка до решения заменит ожидающую версию.</div>
      <p class="m-rep-txt">Если администратор отклонит замену, вы увидите причину отказа, а действующей останется текущая версия — документ не будет утерян.</p>
      <div class="form-actions">
        <button class="btn primary" id="rep-go" type="button">Заменить</button>
        <button class="btn ghost" id="rep-cancel" type="button">Отмена</button>
      </div>
    </div>
  </div>
  <input type="file" id="doc-file" accept="image/jpeg,image/png" style="display:none">

  <footer><span>СберАвтошкола · Мои документы</span><span>Документы проверяет администратор — статусы обновляются здесь</span></footer>
</main>
</div>
<div class="toast" id="toast"></div>
</template>

<script>
// Wiring — перенос раздела документов кабинета (dashboard-instructor.js)
// 1:1: blob-загрузка авторизованных фото (mcLoadImg, XHR с
// X-Session-Token), карточки docCardNode (textContent — XSS-гигиена
// review-001), диалог FR-71 (#m-replace) и скрытый input #doc-file,
// multipart mcUpload на контрактные эндпоинты, тосты дословно.
// Отличия от кабинета — только оболочка/гвард (design.md 3.3): гвард
// страницы fetch('/api/auth/me') → 401 → '/'; данные GET
// /api/instructor/documents — 401/403 → location.href='/' (роль
// гарантируют 401/403 инструкторских эндпоинтов, FR-18).
import { onMounted } from 'vue';
import { toast as baseToast } from '../../shared/utils.js';
import { apiGet, clearSession } from '../../shared/api.js';

export default {
  name: 'DocumentsApp',
  setup: function () {
    var bridge = {};
    function logout(){return bridge.logout()}

    onMounted(function(){
      function toast(msg){baseToast(msg,2600)}
      // DOM-хелпер: пользовательские строки — только через textContent
      // (code-review review-001 #1: stored XSS через innerHTML запрещен)
      function node(tag,cls,text){var n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n}
      function el(id){return document.getElementById(id)}
      // --- Wiring кабинета (Токен — sessionStorage, ключ session_token):
      function toLogin(){clearSession();location.href='/'}
      var TOKEN_KEY='session_token';
      var token=null;
      try{token=sessionStorage.getItem(TOKEN_KEY)}catch(e){}
      // Гвард страницы (FR-18): GET /api/auth/me (X-Session-Token) →
      // 401 → «/»; ФИО/инициалы шапки из ответа (FR-20) — как в кабинете.
      if(!token){location.href='/'}else{
      fetch('/api/auth/me',{headers:{'X-Session-Token':token}})
        .then(function(r){if(!r.ok){location.href='/';return;}return r.json();})
        .then(function(d){if(!d||!d.ok){return;}
          var u=d.user||{};
          var fio=[u.surname,u.name,u.patronymic].filter(Boolean).join(' ');
          el('user-fio').textContent=fio||'Инструктор';
          var ini=((u.surname||'')[0]||'')+((u.name||'')[0]||'');
          el('avatar').textContent=ini||'—';
        }).catch(function(){location.href='/';});
      }
      // Загрузка авторизованного изображения в blob (X-Session-Token);
      // кэш по URL (как mcLoadImg кабинета)
      var mcObjectUrls={};
      function mcLoadImg(url,img){
        if(!url)return;
        if(mcObjectUrls[url]){img.src=mcObjectUrls[url];return}
        var xhr=new XMLHttpRequest();
        xhr.open('GET',url);
        xhr.setRequestHeader('X-Session-Token',token||'');
        xhr.responseType='blob';
        xhr.onload=function(){
          if(xhr.status!==200)return; // 404 «не загружено» — плейсхолдер, не битая картинка
          mcObjectUrls[url]=URL.createObjectURL(xhr.response);
          img.src=mcObjectUrls[url];
        };
        xhr.send();
      }
      function mcPurgeCarUrls(carId){
        var pfx='/api/instructor/cars/'+carId+'/';
        Object.keys(mcObjectUrls).forEach(function(u){
          if(u.indexOf(pfx)===0){URL.revokeObjectURL(mcObjectUrls[u]);delete mcObjectUrls[u]}
        });
      }
      // Клиентская предварительная проверка (как на бэкенде): JPEG/PNG, <=5 МБ.
      function mcValidatePhoto(file){
        if(file.size>5*1024*1024)return 'Файл: изображение больше 5 МБ';
        if(file.type!=='image/jpeg'&&file.type!=='image/png')return 'Фото: допустимы только изображения JPEG или PNG';
        return null;
      }
      function mcShowPhotoError(msg){toast(msg)}
      // multipart-загрузка с прогрессом; 413 (размер) / 415 (формат) / 422 — тосты
      function mcUpload(path,fieldName,file,bar,lab,onDone){
        var fd=new FormData();fd.append(fieldName,file);
        var xhr=new XMLHttpRequest();
        xhr.open('POST',path);
        xhr.setRequestHeader('X-Session-Token',token||'');
        xhr.upload.onprogress=function(e){
          if(!e.lengthComputable)return;
          var v=Math.round(e.loaded/e.total*100);
          if(bar)bar.style.width=v+'%';
          if(lab)lab.textContent='Загрузка… '+v+'%';
        };
        xhr.onload=function(){
          if(xhr.status===200){
            if(lab)lab.textContent='Фото загружено ✓';
            onDone(null);
          }else{
            var msg='';
            try{var d=JSON.parse(xhr.responseText);if(d&&d.error)msg=d.error}catch(e){}
            if(xhr.status===413)msg=msg||'Файл: изображение больше 5 МБ';
            if(xhr.status===415)msg=msg||'Фото: допустимы только изображения JPEG или PNG';
            toast(msg||'Не удалось загрузить фото ('+xhr.status+')');
            onDone(msg||'error');
          }
        };
        xhr.onerror=function(){toast('Не удалось загрузить фото');onDone('network')};
        xhr.send(fd);
      }
      // --- Раздел «Мои документы» (С8) — перенос карточной модели 1:1 ---
      var docTarget=null; // цель загрузки/замены {kind:'license'|'car_sts', carId, name, wasMissing}
      function docName(d){
        if(d.type==='license')return 'Водительское удостоверение';
        var c=d.car||{};
        return 'СТС · '+[c.brand,c.model].filter(Boolean).join(' ');
      }
      function docMetaText(d){
        if(d.type==='license')return d.license_number?('ВУ № '+d.license_number):(d.meta||'');
        var c=d.car||{};
        return [c.brand,c.model].filter(Boolean).join(' ')+(c.plate?' · '+c.plate:'');
      }
      function docVersionLine(d){
        if(d.active_version&&d.active_version.version!=null){
          return 'версия '+d.active_version.version
            +' · загружено '+((d.active_version.uploaded_at||d.uploaded_at||'').split(' ')[0]||'—');
        }
        if(d.uploaded_at)return 'загружено '+String(d.uploaded_at).split(' ')[0];
        return 'документ не загружен';
      }
      function docSubverNodes(d){
        var out=[];
        if(d.pending){
          var p=node('div','subver pend');
          p.appendChild(node('b',null,'Ожидает проверки замены'));
          var pt=node('span',null,'Загружена новая версия ('
            +((d.pending.uploaded_at||'').split(' ')[0]||'дата неизвестна')
            +'). Пока администратор её не подтвердил, действует текущая версия — документ «не мигает».');
          p.appendChild(pt);
          out.push(p);
        }
        if(d.last_rejected){
          var r=node('div','subver rej');
          r.appendChild(node('b',null,'Причина отказа от администратора'));
          // причина — пользовательский текст: только textContent (XSS-гигиена)
          r.appendChild(node('span',null,d.last_rejected.reject_reason||''));
          r.appendChild(node('br'));
          r.appendChild(node('span','look','решение '+((d.last_rejected.decided_at||'').split(' ')[0]||'—')
            +' · действует предыдущая версия, можно загрузить заново'));
          out.push(r);
        }
        return out;
      }
      // просмотр документа в полном размере (BUG-054: стрелки НАД фото,
      // обе стороны всегда в разметке; одиночный документ — скрыты;
      // цикличное листание; клик по стрелке окно не закрывает; Esc закрывает)
      var mcViewPhotos=[],mcViewIx=0;
      function mcOpenView(doc){
        mcViewPhotos=(doc.photos&&doc.photos.length?doc.photos:[doc]).map(function(p){
          return {url:p.url,title:p.title,
            sub:(p.sub!=null?p.sub:(doc.sub||'')),
            doc_id:(p.doc_id!=null?p.doc_id:(doc.doc_id||''))};
        });
        mcViewIx=0;
        mcShowViewPhoto();
        el('m-view').classList.add('open');document.body.style.overflow='hidden';
      }
      function mcShowViewPhoto(){
        var p=mcViewPhotos[mcViewIx];
        el('view-title').textContent=p.title;
        el('view-sub').textContent=(p.sub||'')+(p.doc_id?(' · doc_id '+p.doc_id):'');
        var many=mcViewPhotos.length>1;
        el('view-prev').style.display=many?'':'none';
        el('view-next').style.display=many?'':'none';
        var img=el('view-img');img.alt=p.title;
        mcLoadImg(p.url,img);
      }
      function mcNavView(dir){
        mcViewIx=(mcViewIx+dir+mcViewPhotos.length)%mcViewPhotos.length;
        mcShowViewPhoto();
      }
      function mcCloseView(){el('m-view').classList.remove('open');document.body.style.overflow=''}
      function docCardNode(d){
        var hasFile=!!d.doc_id;
        var card=node('article','doc');
        card.dataset.docId=d.doc_id||'';
        card.dataset.kind=d.type;
        card.dataset.car=String((d.car&&d.car.id)||0);
        var thumb=node('span','thumb');
        if(hasFile){
          thumb.style.cursor='zoom-in';
          var img=document.createElement('img');img.alt=docName(d);
          thumb.appendChild(img);
          thumb.appendChild(node('span','zoom','⤢ Смотреть'));
          mcLoadImg('/api/instructor/documents/'+d.doc_id+'/file',img);
          if(d.pending)thumb.appendChild(node('span','pendtag','замена на проверке'));
          var open=function(){mcOpenView({
            title:docName(d),doc_id:d.doc_id,
            url:'/api/instructor/documents/'+d.doc_id+'/file',sub:docMetaText(d)})};
          thumb.addEventListener('click',open);
          card._open=open;
        }else{
          thumb.appendChild(node('span','ph','🚗'));
        }
        card.appendChild(thumb);
        card.appendChild(node('b','name',docName(d)));
        var meta=node('small','meta');
        meta.appendChild(document.createTextNode(docMetaText(d)));
        meta.appendChild(document.createElement('br'));
        var ver=node('span','ver',docVersionLine(d));
        meta.appendChild(ver);
        card.appendChild(meta);
        if(hasFile){
          card.appendChild(node('span','ds-badge ds-verified','Действует'));
        }else{
          card.appendChild(node('span','ds-badge ds-pending','нет СТС'));
        }
        docSubverNodes(d).forEach(function(s){card.appendChild(s)});
        var act=node('div','doc-actions');
        if(hasFile){
          var view=node('button','btn-u ghost','Открыть');view.type='button';
          view.addEventListener('click',function(){if(card._open)card._open()});
          act.appendChild(view);
        }
        var main=node('button','btn-u',hasFile?'Заменить':'Загрузить');main.type='button';
        main.dataset.uploadDoc='1';main.dataset.kind=d.type;
        main.dataset.car=String((d.car&&d.car.id)||0);
        main.addEventListener('click',function(){
          var t={kind:d.type,carId:(d.car&&d.car.id)||0,name:docName(d),wasMissing:!hasFile};
          if(hasFile){docsAskReplace(t)}else{docsStartUpload(t)} // первая загрузка — без предупреждения FR-71
        });
        act.appendChild(main);
        card.appendChild(act);
        return card;
      }
      // Список документов: ВУ + СТС по КАЖДОМУ авто (FR-69/FR-72 — merge
      // как openDocs кабинета). Гвард данных: 401/403 → «/» (FR-18).
      function openDocs(){
        if(!token)return;
        fetch('/api/instructor/documents',{headers:{'X-Session-Token':token}})
          .then(function(r){
            if(r.status===401||r.status===403){location.href='/';return null;}
            return r.json().then(function(d){return {status:r.status,data:d};});
          })
          .then(function(res){
            if(!res)return;
            if(!res.data||!res.data.ok){toast((res.data&&res.data.error)||'Не удалось загрузить документы');return}
            var docs=res.data.documents||[];
            var lic=docs.filter(function(d){return d.type==='license'});
            var stsDocs=docs.filter(function(d){return d.type==='car_sts'});
            var licBox=el('lic-docs');licBox.innerHTML='';
            lic.forEach(function(d){licBox.appendChild(docCardNode(d))});
            el('lic-n').textContent=lic.length;
            el('no-license').style.display=lic.length?'none':'block';
            if(!lic.length&&res.data.license_hint)el('no-license-hint').textContent=res.data.license_hint;
            apiGet('/api/instructor/cars',function(cres){
              var cars=cres?(cres.cars||[]):[];
              var withDoc={};
              stsDocs.forEach(function(d){if(d.car&&d.car.id!=null)withDoc[d.car.id]=1});
              cars.forEach(function(c){
                if(c.has_sts||withDoc[c.id])return;
                stsDocs.push({doc_id:null,type:'car_sts',title:'СТС автомобиля',
                  car:{id:c.id,brand:c.brand,model:c.model,plate:c.plate},uploaded_at:null});
              });
              stsDocs.sort(function(a,b){
                return ((a.car&&a.car.id)||0)-((b.car&&b.car.id)||0);
              });
              var stsBox=el('sts-docs');stsBox.innerHTML='';
              stsDocs.forEach(function(d){stsBox.appendChild(docCardNode(d))});
              el('sts-count').textContent=stsDocs.length;
            });
          })
          .catch(function(){toast('Не удалось загрузить документы')});
      }
      // ── загрузка/замена документов (FR-71/FR-72): единый flow с модалкой
      // предупреждения #m-replace и скрытым input #doc-file; multipart на
      // контрактные эндпоинты; ошибка сервера — честный тост, список
      // не меняется до успешной загрузки (после нее — перезагрузка). ---
      function docsAskReplace(t){
        docTarget=t;
        el('rep-sub').textContent=t.name;
        el('m-replace').classList.add('open');
        document.body.style.overflow='hidden';
      }
      function docsCloseReplace(){
        docTarget=null;
        el('m-replace').classList.remove('open');
        document.body.style.overflow='';
      }
      function docsPickFile(){el('doc-file').value='';el('doc-file').click()}
      function docsStartUpload(t){
        docTarget=t; // первая загрузка (нет предыдущей версии) — без предупреждения
        docsPickFile();
      }
      function docsCloseReplaceSilent(){
        el('m-replace').classList.remove('open');
        document.body.style.overflow='';
      }
      // --- wiring (DOM существует после монтирования шаблона) ---
      el('view-prev').addEventListener('click',function(e){e.stopPropagation();mcNavView(-1)});
      el('view-next').addEventListener('click',function(e){e.stopPropagation();mcNavView(1)});
      el('view-close').addEventListener('click',mcCloseView);
      el('m-view').addEventListener('click',function(e){if(e.target===this)mcCloseView()}); // фон закрывает (BUG-054)
      el('rep-go').addEventListener('click',function(){
        if(!docTarget)return;
        docsPickFile(); // диалог закрывается в обработчике change по результату
      });
      el('rep-cancel').addEventListener('click',docsCloseReplace);
      el('rep-close').addEventListener('click',docsCloseReplace);
      el('m-replace').addEventListener('click',function(e){if(e.target===this)docsCloseReplace()});
      el('upload-license').addEventListener('click',function(){
        docsStartUpload({kind:'license',carId:0,name:'Водительское удостоверение',wasMissing:true});
      });
      el('doc-file').addEventListener('change',function(){
        var t=docTarget;docTarget=null;
        docsCloseReplaceSilent();
        if(!t||!this.files.length)return;
        var file=this.files[0];
        var err=mcValidatePhoto(file); // JPEG/PNG ≤5 МБ — как на бэкенде (NFR-9)
        if(err){mcShowPhotoError(err);return}
        if(t.kind==='license'){
          mcUpload('/api/instructor/documents/license','file',file,null,null,function(e){
            if(e)return;
            // review-005 MINOR: первичная загрузка — не «замена»
            toast(t.wasMissing
              ?'ВУ отправлено на проверку администратору: документ появится после подтверждения.'
              :'Замена ВУ отправлена на проверку администратору: до подтверждения действует предыдущая версия.');
            openDocs(); // перезагрузка списка с актуальными статусами (FR-72)
          });
        }else{
          mcUpload('/api/instructor/cars/'+t.carId+'/photo/sts','photo',file,null,null,function(e){
            if(e)return;
            mcPurgeCarUrls(t.carId);
            toast(t.wasMissing
              ?'Фото СТС загружено — документ появился в списке.'
              :'Замена СТС отправлена на проверку администратору: действует предыдущая версия, статус авто не изменился (ОВ-6).');
            openDocs();
          });
        }
      });
      // Esc закрывает просмотр (BUG-054) и диалог замены (как в кабинете)
      document.addEventListener('keydown',function(e){if(e.key==='Escape'){mcCloseView();docsCloseReplaceSilent()}});
      // Выход (FR-22, механика dashboard-logout): POST /api/auth/logout ->
      // по любому ответу очистка sessionStorage -> лендинг инструкторов.
      function logout(){
      fetch('/api/auth/logout',{method:'POST',headers:{'X-Session-Token':token||''}})
        .catch(function(){})
        .then(function(){clearSession();location.href='/instructors'});
      }
      bridge.logout = logout;
      openDocs();
    });

    return {
      logout: logout,
    };
  },
};
</script>
