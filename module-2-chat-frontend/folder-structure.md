# ========== МОДУЛЬ 2 ==========

## Папка module-2-chat-frontend/

### Файлы:

- README.md
- package.json - Node.js/React проект
- Dockerfile
- docker-compose.module.yml

### Подпапки:

- **src/backend/** - Backend на Node.js
  - server.js - Express/WebSocket сервер
  - websocket/
    - connection_manager.js
    - message_handler.js
  - api/
    - messages.js
    - users.js
    - rooms.js
  - grpc_client/
    - orchestrator_client.js
  - config.js

- **src/frontend/** - Frontend на React
  - index.html
  - src/
    - App.jsx
    - components/
      - ChatWindow.jsx
      - MessageList.jsx
      - MessageInput.jsx
      - UserList.jsx
      - StyleSelector.jsx - Выбор стиля (Чехов и т.д.)
      - AdaptationIndicator.jsx
    - hooks/
      - useWebSocket.js
      - useMessages.js
    - services/
      - api.js
    - styles/
      - app.css
  - public/

- **tests/** - Тесты
  - unit/
    - websocket.test.js
  - integration/
    - grpc_integration.test.js
  - e2e/
    - chat_flow.spec.js - Playwright

- **config/** - Конфигурация
  - nginx.conf
  - env/
    - development.env
    - production.env

- **assets/** - Ассеты
  - default_avatar.png
  - sounds/
    - notification.mp3
