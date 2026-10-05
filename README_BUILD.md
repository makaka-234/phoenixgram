# PhoenixGram — Инструкция по сборке APK

## ШАГ 0: Настройка сервера

Перед сборкой откройте файл:
`lib/utils/constants.dart`

Замените `your-server.com` на реальный IP/домен вашего сервера:
```dart
static const String baseUrl = 'https://ВАШ_СЕРВЕР';
static const String wsUrl = 'wss://ВАШ_СЕРВЕР/api/v1/ws';
```

---

## ВАРИАНТ А: Сборка на ПК (рекомендуется)

### 1. Установите Flutter
- Скачайте: https://docs.flutter.dev/get-started/install/windows
- Распакуйте в `C:\flutter`
- Добавьте `C:\flutter\bin` в PATH

### 2. Установите Android Studio
- Скачайте: https://developer.android.com/studio
- Установите Android SDK через SDK Manager

### 3. Настройте путь к Android SDK
```
flutter config --android-sdk C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Android\Sdk
```

### 4. Соберите APK
```bash
cd phoenixgram_flutter
flutter pub get
flutter build apk --release --split-per-abi
```

APK будет в: `build/app/outputs/flutter-apk/app-arm64-v8a-release.apk`

---

## ВАРИАНТ Б: Онлайн-сборка через Codemagic (бесплатно)

1. Зарегистрируйтесь на https://codemagic.io
2. Загрузите весь проект на GitHub
3. Подключите репозиторий в Codemagic
4. Выберите "Flutter App" → "Android APK"
5. Нажмите "Start build"
6. Скачайте готовый APK из артефактов

---

## ВАРИАНТ В: Онлайн через GitHub Actions

Создайте файл `.github/workflows/build.yml`:

```yaml
name: Build APK
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.0'
      - run: flutter pub get
      - run: flutter build apk --release
      - uses: actions/upload-artifact@v3
        with:
          name: phoenixgram-apk
          path: build/app/outputs/flutter-apk/app-release.apk
```

---

## Установка APK на телефон

1. **Разрешить установку из неизвестных источников:**
   - Android 8+: Настройки → Приложения → Особые разрешения → Установка неизвестных приложений → Выберите браузер/файловый менеджер → Разрешить
   - Android 7 и ниже: Настройки → Безопасность → Неизвестные источники → Включить

2. **Скопируйте APK на телефон** (через USB, Telegram, Google Drive)

3. **Откройте APK** через файловый менеджер и нажмите "Установить"

4. **Запустите PhoenixGram**
