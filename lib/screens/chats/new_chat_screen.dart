import 'package:flutter/material.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../widgets/avatar_widget.dart';
import 'chat_screen.dart';

class NewChatScreen extends StatefulWidget {
  const NewChatScreen({super.key});
  @override
  State<NewChatScreen> createState() => _NewChatScreenState();
}

class _NewChatScreenState extends State<NewChatScreen> {
  final _searchCtrl = TextEditingController();
  List<User> _results = [];
  bool _loading = false;
  String? _error;

  Future<void> _search(String q) async {
    if (q.trim().length < 2) { setState(() => _results = []); return; }
    setState(() { _loading = true; _error = null; });
    try {
      final users = await ApiService().searchUsers(q.trim());
      if (mounted) setState(() { _results = users; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = 'Ошибка поиска'; });
    }
  }

  Future<void> _startChat(User user) async {
    try {
      final chat = await ApiService().createPrivateChat(user.phoenixId);
      if (mounted) {
        Navigator.pop(context);
        Navigator.push(context, MaterialPageRoute(builder: (_) => ChatScreen(chat: chat)));
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Не удалось открыть чат')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('Новый чат', style: TextStyle(color: Colors.white)),
        leading: IconButton(icon: const Icon(Icons.arrow_back, color: Colors.white), onPressed: () => Navigator.pop(context)),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Поиск по ID или имени',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                prefixIcon: const Icon(Icons.search, color: Colors.white54),
                filled: true,
                fillColor: const Color(0xFF232E3C),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
              onChanged: _search,
            ),
          ),
          if (_loading) const LinearProgressIndicator(color: Color(0xFF2AABEE), backgroundColor: Colors.transparent),
          if (_error != null) Padding(
            padding: const EdgeInsets.all(16),
            child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: _results.length,
              itemBuilder: (_, i) {
                final u = _results[i];
                return ListTile(
                  leading: AvatarWidget(initials: u.initials, size: 46, isPremium: u.isPremium, isVerified: u.isVerified),
                  title: Text(u.displayName, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                  subtitle: Text('@${u.phoenixId}', style: const TextStyle(color: Color(0xFF2AABEE), fontSize: 13)),
                  onTap: () => _startChat(u),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
