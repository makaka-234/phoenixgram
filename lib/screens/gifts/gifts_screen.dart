import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class GiftsScreen extends StatefulWidget {
  const GiftsScreen({super.key});
  @override
  State<GiftsScreen> createState() => _GiftsScreenState();
}

class _GiftsScreenState extends State<GiftsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabs;
  List<dynamic> _catalog = [];
  List<dynamic> _myGifts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _load();
  }

  @override
  void dispose() { _tabs.dispose(); super.dispose(); }

  Future<void> _load() async {
    try {
      final catalog = await ApiService().getGiftCatalog().catchError((_) => <dynamic>[]);
      final myGifts = await ApiService().getMyGifts().catchError((_) => <dynamic>[]);
      if (mounted) setState(() { _catalog = catalog; _myGifts = myGifts; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  static const _demoGifts = [
    {'emoji': '🌹', 'name': 'Роза', 'price': 50, 'desc': 'Символ любви'},
    {'emoji': '💎', 'name': 'Алмаз', 'price': 500, 'desc': 'Редкий подарок'},
    {'emoji': '🎂', 'name': 'Торт', 'price': 100, 'desc': 'С днём рождения!'},
    {'emoji': '🏆', 'name': 'Кубок', 'price': 200, 'desc': 'Ты победитель'},
    {'emoji': '🎁', 'name': 'Сюрприз', 'price': 75, 'desc': 'Неожиданный подарок'},
    {'emoji': '❤️', 'name': 'Сердце', 'price': 30, 'desc': 'Просто так'},
    {'emoji': '⭐', 'name': 'Звезда', 'price': 150, 'desc': 'Звёздный подарок'},
    {'emoji': '🦋', 'name': 'Бабочка', 'price': 80, 'desc': 'Лёгкий и нежный'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('Подарки', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: const Color(0xFF2AABEE),
          labelColor: const Color(0xFF2AABEE),
          unselectedLabelColor: Colors.white54,
          tabs: const [Tab(text: 'Каталог'), Tab(text: 'Мои подарки')],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2AABEE)))
          : TabBarView(
              controller: _tabs,
              children: [
                _buildCatalog(),
                _buildMyGifts(),
              ],
            ),
    );
  }

  Widget _buildCatalog() {
    final gifts = _catalog.isEmpty ? _demoGifts : _catalog;
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.1,
      ),
      itemCount: gifts.length,
      itemBuilder: (_, i) {
        final g = gifts[i];
        return _GiftCard(
          emoji: g['emoji'] as String? ?? '🎁',
          name: g['name'] as String? ?? 'Подарок',
          price: (g['price'] as num?)?.toInt() ?? 0,
          desc: g['desc'] as String? ?? '',
          onSend: () => _showSendDialog(g),
        );
      },
    );
  }

  Widget _buildMyGifts() {
    if (_myGifts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('🎁', style: TextStyle(fontSize: 64)),
            const SizedBox(height: 16),
            Text('У вас пока нет подарков', style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 16)),
            const SizedBox(height: 8),
            Text('Отправляйте подарки друзьям из каталога', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 13)),
          ],
        ),
      );
    }
    return ListView.builder(
      itemCount: _myGifts.length,
      itemBuilder: (_, i) {
        final g = _myGifts[i];
        return ListTile(
          leading: Text(g['emoji'] ?? '🎁', style: const TextStyle(fontSize: 32)),
          title: Text(g['name'] ?? 'Подарок', style: const TextStyle(color: Colors.white)),
          subtitle: Text('От: ${g['sender'] ?? 'Неизвестно'}', style: const TextStyle(color: Color(0xFF2AABEE))),
        );
      },
    );
  }

  void _showSendDialog(Map gift) {
    final ctrl = TextEditingController();
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF232E3C),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(gift['emoji'] ?? '🎁', style: const TextStyle(fontSize: 52)),
            const SizedBox(height: 8),
            Text('Отправить ${gift['name']}', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            Text('${gift['price']} ⭐', style: const TextStyle(color: Color(0xFFFFD700), fontSize: 16)),
            const SizedBox(height: 16),
            TextField(
              controller: ctrl,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'ID получателя',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                filled: true,
                fillColor: const Color(0xFF17212B),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () { Navigator.pop(context); },
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2AABEE),
                    padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                child: const Text('Отправить', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _GiftCard extends StatelessWidget {
  final String emoji, name, desc;
  final int price;
  final VoidCallback onSend;
  const _GiftCard({required this.emoji, required this.name, required this.price, required this.desc, required this.onSend});

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onSend,
    child: Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: const Color(0xFF232E3C), borderRadius: BorderRadius.circular(16)),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 40)),
          const SizedBox(height: 8),
          Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
          Text(desc, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11), textAlign: TextAlign.center),
          const SizedBox(height: 6),
          Text('$price ⭐', style: const TextStyle(color: Color(0xFFFFD700), fontWeight: FontWeight.bold)),
        ],
      ),
    ),
  );
}
