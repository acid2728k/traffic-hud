#!/bin/bash

# Скрипт для запуска серверов TRAFFIC HUD

echo "🚀 Запуск TRAFFIC HUD серверов..."
echo ""

# Backend
echo "Запуск backend на http://localhost:8000"
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo "Запуск frontend на http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Серверы запущены!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Для остановки: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Откройте http://localhost:3000 в браузере"
