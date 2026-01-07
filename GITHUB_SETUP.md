# Инструкция по созданию репозитория на GitHub

## Способ 1: Использование скрипта (рекомендуется)

1. Получите GitHub Personal Access Token:
   - Перейдите на https://github.com/settings/tokens
   - Нажмите "Generate new token" -> "Generate new token (classic)"
   - Выберите права: `repo` (полный доступ к репозиториям)
   - Скопируйте токен

2. Запустите скрипт:
   ```bash
   ./create-github-repo.sh YOUR_GITHUB_TOKEN
   ```

## Способ 2: Через веб-интерфейс GitHub

1. Перейдите на https://github.com/new
2. Заполните форму:
   - **Repository name**: `traffic-hud`
   - **Description**: `TRAFFIC HUD - система отображения информации о дорожном движении`
   - **Visibility**: Public (или Private, по вашему выбору)
   - **НЕ** создавайте README, .gitignore или лицензию (они уже есть)
3. Нажмите "Create repository"

4. После создания репозитория выполните команды:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/traffic-hud.git
   git branch -M main
   git push -u origin main
   ```

## Способ 3: Установка GitHub CLI

1. Установите GitHub CLI:
   ```bash
   # macOS (через Homebrew)
   brew install gh
   
   # Или скачайте с https://cli.github.com/
   ```

2. Авторизуйтесь:
   ```bash
   gh auth login
   ```

3. Создайте репозиторий:
   ```bash
   gh repo create traffic-hud --public --description "TRAFFIC HUD - система отображения информации о дорожном движении" --source=. --remote=origin --push
   ```

