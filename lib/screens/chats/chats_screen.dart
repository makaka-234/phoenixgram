import 'package:flutter/material.dart';
import 'package:timeago/timeago.dart' as timeago;
import '../../models/chat.dart';
import '../../services/api_service.dart';
import '../../widgets/avatar_widget.dart';
import 'chat_screen.dart';
import 'new_chat_screen.dart';

class ChatsScreen extends StatefulWidget {
  const ChatsScreen({super.key});
  @override
  State<ChatsScreen> createState() => _ChatsScreenState();
}

class _ChatsScreenState extends State<ChatsScreen> {
  List<Chat> _chats = [];
  bool _loading = true;
  final _search = TextEditingController();
  String _query = '';

  @override
  void initState() {
    super.initState();
    _load();
    // Настройка русского языка для timeago
    timeago.setLocaleMessages('ru', timeago.RuMessages());
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final chats = await ApiService().getChats();
      if (mounted) setState(() { _chats = chats; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Chat> get _filtered {
    if (_query.isEmpty) return _chats;
    final q = _query.toLowerCase();
    return _chats.where((c) => c.displayName.toLowerCase().contains(q)).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF17212B),
        elevation: 0,
        title: const Text('PhoenixGram', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20)),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined, color: Colors.white),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NewChatScreen())).then((_) => _load()),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(52),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              controller: _search,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Поиск чатов',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                prefixIcon: const Icon(Icons.search, color: Colors.white54, size: 20),
                filled: true,
                fillColor: Colors.white.withOpacity(0.08),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.symmetric(vertical: 10),
              ),
              onChanged: (v) => setState(() => _query = v),
            ),
          ),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2AABEE)))
          : RefreshIndicator(
              color: const Color(0xFF2AABEE),
              onRefresh: _load,
              child: _filtered.isEmpty
                  ? _empty
                  : ListView.separated(
                      itemCount: _filtered.length,
                      separatorBuilder: (_, __) => Divider(
                        height: 1,
                        indent: 80,
                        color: Colors.white.withOpacity(0.06),
                      ),
                      itemBuilder: (ctx, i) => _ChatTile(
                        chat: _filtered[i],
                        onTap: () => Navigator.push(
                          ctx,
                          MaterialPageRoute(builder: (_) => ChatScreen(chat: _filtered[i])),
                        ).then((_) => _load()),
                      ),
                    ),
            ),
    );
  }

  Widget get _empty => Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.chat_bubble_outline, size: 64, color: Colors.white.withOpacity(0.2)),
        const SizedBox(height: 16),
        Text(
          _query.isNotEmpty ? 'Чатов не найдено' : 'У вас пока нет чатов',
          style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16),
        ),
        if (_query.isEmpty) ...[
          const SizedBox(height: 8),
          Text('Нажмите ✏️ чтобы начать переписку', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 13)),
        ],
      ],
    ),
  );
}

class _ChatTile extends StatelessWidget {
  final Chat chat;
  final VoidCallback onTap;
  const _ChatTile({required this.chat, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final hasUnread = chat.unreadCount > 0;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            AvatarWidget(
              imageUrl: chat.displayAvatar,
              initials: chat.initials,
              size: 52,
              isPremium: chat.peer?.isPremium ?? false,
              isVerified: chat.peer?.isVerified ?? false,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          chat.displayName,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 15),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (chat.updatedAt != null)
                        Text(
                          _formatTime(chat.updatedAt!),
                          style: TextStyle(
                            color: hasUnread ? const Color(0xFF2AABEE) : Colors.white.withOpacity(0.4),
                            fontSize: 12,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          chat.lastMessageText ?? 'Нет сообщений',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                            fontSize: 13,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (hasUnread)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF2AABEE),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            chat.unreadCount > 99 ? '99+' : '${chat.unreadCount}',
                            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(String iso) {
    try {
      final dt = DateTime.parse(iso);
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inDays == 0) {
        return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
      } else if (diff.inDays < 7) {
        const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
        return days[dt.weekday - 1];
      } else {
        return '${dt.day}.${dt.month.toString().padLeft(2, '0')}';
      }
    } catch (_) {
      return '';
    }
  }
}
