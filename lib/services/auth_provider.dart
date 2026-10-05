import 'package:flutter/foundation.dart';
import '../models/user.dart';
import 'api_service.dart';

class AuthProvider extends ChangeNotifier {
  User? _user;
  bool _loading = false;
  bool _initialized = false;
  String? _error;

  User? get user => _user;
  bool get loading => _loading;
  bool get isLoggedIn => _user != null;
  bool get initialized => _initialized;
  String? get error => _error;

  final ApiService _api = ApiService();

  Future<void> init() async {
    _api.init();
    await _api.loadTokens();
    if (_api.isLoggedIn) {
      try {
        _user = await _api.getMe();
      } catch (_) {
        await _api.clearTokens();
      }
    }
    _initialized = true;
    notifyListeners();
  }

  Future<bool> login(String phoenixId, String code) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final result = await _api.login(phoenixId, code);
      await _api.saveTokens(result['access_token'], result['refresh_token']);
      _user = await _api.getMe();
      _loading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _loading = false;
      _error = _parseError(e);
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _api.logout();
    _user = null;
    notifyListeners();
  }

  Future<void> refreshUser() async {
    try {
      _user = await _api.getMe();
      notifyListeners();
    } catch (_) {}
  }

  String _parseError(dynamic e) {
    if (e.toString().contains('401')) return 'Неверный ID или код';
    if (e.toString().contains('SocketException')) return 'Нет подключения к интернету';
    return 'Ошибка входа. Попробуйте ещё раз';
  }
}
