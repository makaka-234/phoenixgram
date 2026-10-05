import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';
import '../models/user.dart';
import '../models/chat.dart';
import '../models/message.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  late Dio _dio;
  String? _accessToken;

  void init() {
    _dio = Dio(BaseOptions(
      baseUrl: '${AppConstants.baseUrl}/api/v1',
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final refreshed = await _tryRefresh();
          if (refreshed) {
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $_accessToken';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } catch (_) {}
          }
        }
        handler.next(error);
      },
    ));
  }

  Future<bool> _tryRefresh() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    if (refreshToken == null) return false;
    try {
      final res = await Dio().post(
        '${AppConstants.baseUrl}/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      _accessToken = res.data['access_token'];
      await prefs.setString('access_token', _accessToken!);
      await prefs.setString('refresh_token', res.data['refresh_token']);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> loadTokens() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString('access_token');
  }

  Future<void> saveTokens(String access, String refresh) async {
    _accessToken = access;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', access);
    await prefs.setString('refresh_token', refresh);
  }

  Future<void> clearTokens() async {
    _accessToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }

  bool get isLoggedIn => _accessToken != null;

  // ========== AUTH ==========

  Future<Map<String, dynamic>> login(String phoenixId, String code) async {
    final res = await _dio.post('/auth/login', data: {
      'phoenix_id': phoenixId,
      'code': code,
    });
    return res.data;
  }

  Future<User> getMe() async {
    final res = await _dio.get('/auth/me');
    return User.fromJson(res.data);
  }

  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } catch (_) {}
    await clearTokens();
  }

  // ========== CHATS ==========

  Future<List<Chat>> getChats() async {
    final res = await _dio.get('/chats');
    return (res.data as List).map((e) => Chat.fromJson(e)).toList();
  }

  Future<Chat> createPrivateChat(String peerPhoenixId) async {
    final res = await _dio.post('/chats', data: {
      'type': 'private',
      'peer_phoenix_id': peerPhoenixId,
    });
    return Chat.fromJson(res.data);
  }

  Future<Chat> createGroupChat(String title, List<int> memberIds) async {
    final res = await _dio.post('/chats', data: {
      'type': 'group',
      'title': title,
      'member_ids': memberIds,
    });
    return Chat.fromJson(res.data);
  }

  Future<Chat> getChat(int chatId) async {
    final res = await _dio.get('/chats/$chatId');
    return Chat.fromJson(res.data);
  }

  // ========== MESSAGES ==========

  Future<List<Message>> getMessages(int chatId, {int? beforeId, int limit = 50}) async {
    final params = <String, dynamic>{'limit': limit};
    if (beforeId != null) params['before_id'] = beforeId;
    final res = await _dio.get('/chats/$chatId/messages', queryParameters: params);
    final items = res.data['items'] as List;
    return items.map((e) => Message.fromJson(e)).toList();
  }

  Future<Message> sendMessage(int chatId, String text, {int? replyToId}) async {
    final data = <String, dynamic>{'text': text, 'type': 'text'};
    if (replyToId != null) data['reply_to_id'] = replyToId;
    final res = await _dio.post('/chats/$chatId/messages', data: data);
    return Message.fromJson(res.data);
  }

  Future<void> deleteMessage(int messageId) async {
    await _dio.delete('/messages/$messageId');
  }

  Future<void> markRead(int chatId, int messageId) async {
    await _dio.post('/chats/$chatId/read', queryParameters: {'message_id': messageId});
  }

  // ========== USER ==========

  Future<User> getUserByPhoenixId(String phoenixId) async {
    final res = await _dio.get('/users/$phoenixId');
    return User.fromJson(res.data);
  }

  Future<List<User>> searchUsers(String query) async {
    final res = await _dio.get('/users/search', queryParameters: {'q': query});
    return (res.data as List).map((e) => User.fromJson(e)).toList();
  }

  Future<User> updateProfile({String? firstName, String? lastName, String? bio}) async {
    final data = <String, dynamic>{};
    if (firstName != null) data['first_name'] = firstName;
    if (lastName != null) data['last_name'] = lastName;
    if (bio != null) data['bio'] = bio;
    final res = await _dio.patch('/users/me', data: data);
    return User.fromJson(res.data);
  }

  // ========== STARS ==========

  Future<Map<String, dynamic>> getStarsBalance() async {
    final res = await _dio.get('/stars/balance');
    return res.data;
  }

  Future<List<dynamic>> getStarProducts() async {
    final res = await _dio.get('/stars/products');
    return res.data;
  }

  // ========== SUBSCRIPTIONS ==========

  Future<List<dynamic>> getSubscriptionPlans() async {
    final res = await _dio.get('/subscriptions/plans');
    return res.data;
  }

  Future<Map<String, dynamic>> getMySubscription() async {
    final res = await _dio.get('/subscriptions/me');
    return res.data;
  }

  // ========== GIFTS ==========

  Future<List<dynamic>> getGiftCatalog() async {
    final res = await _dio.get('/gifts/catalog');
    return res.data;
  }

  Future<List<dynamic>> getMyGifts() async {
    final res = await _dio.get('/gifts/my');
    return res.data;
  }

  Future<Map<String, dynamic>> sendGift(int giftId, int recipientId) async {
    final res = await _dio.post('/gifts/send', data: {
      'gift_id': giftId,
      'recipient_id': recipientId,
    });
    return res.data;
  }
}
