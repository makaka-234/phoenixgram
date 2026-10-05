import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';
import '../models/message.dart';

typedef MessageCallback = void Function(Message message);
typedef EventCallback = void Function(Map<String, dynamic> event);

class WebSocketService {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  WebSocketChannel? _channel;
  bool _isConnected = false;
  
  final List<MessageCallback> _messageListeners = [];
  final List<EventCallback> _eventListeners = [];

  bool get isConnected => _isConnected;

  void addMessageListener(MessageCallback cb) => _messageListeners.add(cb);
  void removeMessageListener(MessageCallback cb) => _messageListeners.remove(cb);
  void addEventListener(EventCallback cb) => _eventListeners.add(cb);
  void removeEventListener(EventCallback cb) => _eventListeners.remove(cb);

  Future<void> connect() async {
    if (_isConnected) return;
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    if (token == null) return;

    try {
      final uri = Uri.parse('${AppConstants.wsUrl}?token=$token');
      _channel = WebSocketChannel.connect(uri);
      _isConnected = true;

      _channel!.stream.listen(
        (data) {
          try {
            final json = jsonDecode(data as String) as Map<String, dynamic>;
            _handleEvent(json);
          } catch (_) {}
        },
        onError: (_) {
          _isConnected = false;
          _scheduleReconnect();
        },
        onDone: () {
          _isConnected = false;
          _scheduleReconnect();
        },
      );
    } catch (_) {
      _isConnected = false;
    }
  }

  void _handleEvent(Map<String, dynamic> json) {
    final event = json['event'] as String?;
    final payload = json['payload'] as Map<String, dynamic>? ?? {};

    if (event == 'new_message') {
      try {
        final msg = Message.fromJson(payload);
        for (final cb in List.from(_messageListeners)) cb(msg);
      } catch (_) {}
    }

    for (final cb in List.from(_eventListeners)) cb(json);
  }

  void _scheduleReconnect() {
    Future.delayed(const Duration(seconds: 3), () => connect());
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
  }
}
