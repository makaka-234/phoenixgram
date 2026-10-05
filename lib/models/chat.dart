import 'user.dart';

class Chat {
  final int id;
  final String type;
  final String? title;
  final String? avatarUrl;
  final int? lastMessageId;
  final String? lastMessageText;
  final int unreadCount;
  final String? updatedAt;
  final User? peer;

  Chat({
    required this.id,
    required this.type,
    this.title,
    this.avatarUrl,
    this.lastMessageId,
    this.lastMessageText,
    this.unreadCount = 0,
    this.updatedAt,
    this.peer,
  });

  factory Chat.fromJson(Map<String, dynamic> json) {
    return Chat(
      id: json['id'],
      type: json['type'] ?? 'private',
      title: json['title'],
      avatarUrl: json['avatar_url'],
      lastMessageId: json['last_message_id'],
      lastMessageText: json['last_message_text'],
      unreadCount: json['unread_count'] ?? 0,
      updatedAt: json['updated_at'],
      peer: json['peer'] != null ? User.fromJson(json['peer']) : null,
    );
  }

  String get displayName {
    if (type == 'private' && peer != null) return peer!.displayName;
    return title ?? 'Чат #$id';
  }

  String get displayAvatar {
    if (type == 'private' && peer != null) return peer?.avatarUrl ?? '';
    return avatarUrl ?? '';
  }

  String get initials {
    final name = displayName;
    final words = name.trim().split(' ');
    if (words.length >= 2) return '${words[0][0]}${words[1][0]}'.toUpperCase();
    if (name.isNotEmpty) return name[0].toUpperCase();
    return '?';
  }
}
