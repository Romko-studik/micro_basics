#!/bin/bash

FACADE_URL="http://localhost:8001"

echo "Відправляємо 10 повідомлень через facade-service..."

for i in {1..10}
do
  MSG="msg$i"
  echo "Відправляємо: $MSG"
  curl -s -X POST "$FACADE_URL/post" -H "Content-Type: application/json" -d "{\"msg\":\"$MSG\"}" > /dev/null
done

echo ""
echo "Повідомлення відправлені."

echo ""
echo "Декілька разів отримуємо об'єднані повідомлення з facade-service..."

for i in {1..3}
do
  echo "Запит GET /get, спроба $i:"
  curl -s "$FACADE_URL/get"
  echo -e "\n---\n"
  sleep 1
done

echo "Перевірте логи logging-service та messages-service для отриманих повідомлень."
echo "У логах мають бути виведені всі повідомлення msg1...msg10 для кожного екземпляра."
