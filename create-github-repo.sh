#!/bin/bash

# Скрипт для создания репозитория на GitHub
# Использование: ./create-github-repo.sh [GITHUB_TOKEN]

REPO_NAME="traffic-hud"
DESCRIPTION="TRAFFIC HUD - система отображения информации о дорожном движении"

if [ -z "$1" ]; then
    echo "Использование: $0 <GITHUB_TOKEN>"
    echo ""
    echo "Для получения токена:"
    echo "1. Перейдите на https://github.com/settings/tokens"
    echo "2. Создайте новый токен (New token -> Generate new token (classic))"
    echo "3. Выберите права: repo (полный доступ к репозиториям)"
    echo "4. Скопируйте токен и используйте его в команде"
    exit 1
fi

GITHUB_TOKEN=$1

# Получаем имя пользователя GitHub
USERNAME=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -o '"login":"[^"]*' | cut -d'"' -f4)

if [ -z "$USERNAME" ]; then
    echo "Ошибка: Не удалось получить информацию о пользователе. Проверьте токен."
    exit 1
fi

echo "Создание репозитория $REPO_NAME для пользователя $USERNAME..."

# Создаем репозиторий
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"$DESCRIPTION\",
    \"private\": false
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo "✓ Репозиторий успешно создан!"
    echo ""
    echo "Добавляем remote и отправляем код..."
    
    # Добавляем remote
    git remote add origin https://github.com/$USERNAME/$REPO_NAME.git
    
    # Отправляем код
    git branch -M main
    git push -u origin main
    
    echo ""
    echo "✓ Готово! Репозиторий доступен по адресу:"
    echo "  https://github.com/$USERNAME/$REPO_NAME"
else
    echo "Ошибка при создании репозитория (HTTP $HTTP_CODE):"
    echo "$BODY"
    exit 1
fi

