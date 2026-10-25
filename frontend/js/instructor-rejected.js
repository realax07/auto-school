/* из instructor-rejected.html (блок 1) */
// Экран отказа (задача 4.3, FR-17/FR-13): причина — из ответа логина (sdd §15.5,
// ключ reason, ключ sessionStorage 'instructor_rejected_reason' — пишет модалка
// входа при route=rejected, задача 4.5). Статус при загрузке НЕ проверяется.
// Пусто/нет ключа — экран без персональной причины (чужую не раскрываем, design).
try {
  var reason = sessionStorage.getItem('instructor_rejected_reason');
  if (reason) {
    document.getElementById('reason-text').textContent = reason;
    document.getElementById('reason-block').style.display = '';
  }
} catch (e) { /* sessionStorage недоступен — без причины */ }
