import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/chat.dart';
import '../../models/message.dart';
import '../../services/api_service.dart';
import '../../services/auth_provider.dart';
import '../../services/websocket_service.dart';
import '../../widgets/avatar_widget.dart';

class ChatScreen extends StatefulWidget {
  final Chat chat;
  const ChatScreen({super.key, required this.chat});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Message> _messages = [];
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _loading = true;
  bool _sending = false;
  Message? _replyTo;

  @override
  void initState() {
    super.initState();
    _loadMessages();
    WebSocketService().addMessageListener(_onNewMessage);
  }

  @override
  void dispose() {
    WebSocketService().removeMessageListener(_onNewMessage);
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onNewMessage(Message msg) {
    if (msg.chatId == widget.chat.id && mounted) {
      setState(() => _messages.add(msg));
      _scrollToBottom();
    }
  }

  Future<void> _loadMessages() async {
    try {
      final msgs = await ApiService().getMessages(widget.chat.id);
      if (mounted) {
        setState(() {
          _messages.clear();
          _messages.addAll(msgs.reversed);
          _loading = false;
        });
        _scrollToBottom();
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    _textCtrl.clear();
    final reply = _replyTo;
    setState(() => _replyTo = null);
    try {
      final msg = await ApiService().sendMessage(widget.chat.id, text, replyToId: reply?.id);
      if (mounted) {
        setState(() => _messages.add(msg));
        _scrollToBottom();
      }
    } catch (_) {
      _textCtrl.text = text;
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Не удалось отправить'), backgroundColor: Colors.red),
      );
    }
    if (mounted) setState(() => _sending = false);
  }

  @override
  Widget build(BuildContext context) {
    final me = context.read<AuthProvider>().user;
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF232E3C),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Row(
          children: [
            AvatarWidget(imageUrl: widget.chat.displayAvatar, initials: widget.chat.initials, size: 38),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.chat.displayName,
                      style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                  Text(widget.chat.type == 'private' ? 'в сети' : 'группа',
                      style: const TextStyle(color: Color(0xFF2AABEE), fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.more_vert, color: Colors.white), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF2AABEE)))
                : _messages.isEmpty
                    ? Center(
                        child: Text('Нет сообщений\nНапишите первым!',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 14)),
                      )
                    : ListView.builder(
                        controller: _scrollCtrl,
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
                        itemCount: _messages.length,
                        itemBuilder: (_, i) {
                          final msg = _messages[i];
                          final isMe = msg.senderId == me?.id;
                          return _MessageBubble(
                            message: msg,
                            isMe: isMe,
                            onReply: () => setState(() => _replyTo = msg),
                          );
                        },
                      ),
          ),
          if (_replyTo != null) _replyBar,
          _inputBar,
        ],
      ),
    );
  }

  Widget get _replyBar => Container(
    color: const Color(0xFF232E3C),
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    child: Row(
      children: [
        Container(width: 3, height: 36, color: const Color(0xFF2AABEE)),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Ответить', style: TextStyle(color: Color(0xFF2AABEE), fontSize: 12, fontWeight: FontWeight.w600)),
              Text(_replyTo!.displayText, style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13), maxLines: 1),
            ],
          ),
        ),
        IconButton(
          icon: const Icon(Icons.close, color: Colors.white54, size: 18),
          onPressed: () => setState(() => _replyTo = null),
        ),
      ],
    ),
  );

  Widget get _inputBar => Container(
    color: const Color(0xFF232E3C),
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
    child: Row(
      children: [
        IconButton(
          icon: const Icon(Icons.attach_file, color: Colors.white54),
          onPressed: () {},
        ),
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF17212B),
              borderRadius: BorderRadius.circular(24),
            ),
            child: TextField(
              controller: _textCtrl,
              style: const TextStyle(color: Colors.white, fontSize: 15),
              maxLines: 4,
              minLines: 1,
              decoration: const InputDecoration(
                hintText: 'Сообщение...',
                hintStyle: TextStyle(color: Colors.white38),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              onSubmitted: (_) => _send(),
            ),
          ),
        ),
        const SizedBox(width: 8),
        GestureDetector(
          onTap: _send,
          child: Container(
            width: 44,
            height: 44,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: Color(0xFF2AABEE),
            ),
            child: _sending
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                  )
                : const Icon(Icons.send_rounded, color: Colors.white, size: 20),
          ),
        ),
      ],
    ),
  );
}

class _MessageBubble extends StatelessWidget {
  final Message message;
  final bool isMe;
  final VoidCallback onReply;

  const _MessageBubble({required this.message, required this.isMe, required this.onReply});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onLongPress: onReply,
      child: Align(
        alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
          margin: const EdgeInsets.symmetric(vertical: 2),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: isMe ? const Color(0xFF2B5278) : const Color(0xFF232E3C),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(18),
              topRight: const Radius.circular(18),
              bottomLeft: Radius.circular(isMe ? 18 : 4),
              bottomRight: Radius.circular(isMe ? 4 : 18),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!isMe && message.sender != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text(
                    message.sender!.displayName,
                    style: const TextStyle(color: Color(0xFF2AABEE), fontSize: 13, fontWeight: FontWeight.w600),
                  ),
                ),
              Text(
                message.displayText,
                style: TextStyle(
                  color: message.isDeleted ? Colors.white38 : Colors.white,
                  fontSize: 15,
                  fontStyle: message.isDeleted ? FontStyle.italic : FontStyle.normal,
                ),
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.bottomRight,
                child: Text(
                  _formatTime(message.createdAt),
                  style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '';
    }
  }
}
