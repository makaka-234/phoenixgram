import 'user.dart';

class Message {
  final int id;
  final int chatId;
  final int? senderId;
  final String? text;
  final String type;
  final String? mediaUrl;
  final bool isDeleted;
  final int? replyToId;
  final String createdAt;
  final User? sender;

  Message({
    required this.id,
    required this.chatId,
    this.senderId,
    this.text,
    this.type = 'text',
    this.mediaUrl,
    this.isDeleted = false,
    this.replyToId,
    required this.createdAt,
    this.sender,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'],
      chatId: json['chat_id'],
      senderId: json['sender_id'],
      text: json['text'],
      type: json['type'] ?? 'text',
      mediaUrl: json['media_url'],
      isDeleted: json['is_deleted'] ?? false,
      replyToId: json['reply_to_id'],
      createdAt: json['created_at'] ?? '',
      sender: json['sender'] != null ? User.fromJson(json['sender']) : null,
    );
  }

  String get displayText {
    if (isDeleted) return '🗑 Сообщение удалено';
    return text ?? '[медиафайл]';
  }
}
