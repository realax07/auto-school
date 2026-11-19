# Пакет tests/api (change add-ai-chat-home, волна 19.4, qa_automation):
# pytest (prepend) импортирует тесты API как api.test_* — иначе ДВА файла с
# базовым именем test_s19_ai_chat.py (tests/unit — юнит-носитель dev-волны
# 19.2, tests/api — API-носитель задачи 19.2.5) дают «import file mismatch»
# при полном сьюте `pytest tests/`. Внутрипакетные перекрестные импорты
# (test_instructor_admin, test_qa_instructor_flow) переведены на
# относительные. Node-id тестов не меняются (tests/api/test_x.py::test).
