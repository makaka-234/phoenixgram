import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/auth_provider.dart';
import '../../services/api_service.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});
  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> with SingleTickerProviderStateMixin {
  late TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() { _tabs.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('Магазин', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: const Color(0xFF2AABEE),
          labelColor: const Color(0xFF2AABEE),
          unselectedLabelColor: Colors.white54,
          tabs: const [
            Tab(text: 'Звёзды'),
            Tab(text: 'Premium'),
            Tab(text: 'Юзернеймы'),
            Tab(text: 'NFT'),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 12),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0xFF17212B),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              children: [
                const Text('⭐', style: TextStyle(fontSize: 16)),
                const SizedBox(width: 4),
                Text('${user?.starsBalance ?? 0}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabs,
        children: const [
          _StarsTab(),
          _PremiumTab(),
          _UsernamesTab(),
          _NftTab(),
        ],
      ),
    );
  }
}

// ===== ЗВЁЗДЫ =====
class _StarsTab extends StatelessWidget {
  const _StarsTab();

  static const _packs = [
    {'stars': 100, 'price': 1, 'label': '⭐ 100 звёзд', 'popular': false},
    {'stars': 500, 'price': 4, 'label': '⭐ 500 звёзд', 'popular': false},
    {'stars': 1000, 'price': 7, 'label': '⭐ 1000 звёзд', 'popular': true},
    {'stars': 2500, 'price': 15, 'label': '⭐ 2500 звёзд', 'popular': false},
    {'stars': 5000, 'price': 25, 'label': '⭐ 5000 звёзд', 'popular': false},
    {'stars': 10000, 'price': 45, 'label': '⭐ 10000 звёзд', 'popular': false},
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _infoCard(),
          const SizedBox(height: 16),
          const Text('Пакеты звёзд', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.4,
            ),
            itemCount: _packs.length,
            itemBuilder: (_, i) => _PackCard(pack: _packs[i]),
          ),
        ],
      ),
    );
  }

  Widget _infoCard() => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      gradient: const LinearGradient(colors: [Color(0xFF2AABEE), Color(0xFF1580B5)]),
      borderRadius: BorderRadius.circular(16),
    ),
    child: const Row(
      children: [
        Text('⭐', style: TextStyle(fontSize: 40)),
        SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Звёзды Феникс', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              SizedBox(height: 4),
              Text('Внутренняя валюта. Покупайте за Telegram Stars через бота.',
                  style: TextStyle(color: Colors.white70, fontSize: 12)),
            ],
          ),
        ),
      ],
    ),
  );
}

class _PackCard extends StatelessWidget {
  final Map<String, dynamic> pack;
  const _PackCard({required this.pack});

  @override
  Widget build(BuildContext context) {
    final popular = pack['popular'] as bool;
    return Stack(
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: popular ? const Color(0xFF2B5278) : const Color(0xFF232E3C),
            borderRadius: BorderRadius.circular(16),
            border: popular ? Border.all(color: const Color(0xFF2AABEE), width: 1.5) : null,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(pack['label'] as String, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Text('${pack['price']} ⭐ Telegram', style: const TextStyle(color: Color(0xFF2AABEE), fontSize: 12)),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => _showBotInfo(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2AABEE),
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text('Купить', style: TextStyle(color: Colors.white, fontSize: 13)),
                ),
              ),
            ],
          ),
        ),
        if (popular) Positioned(
          top: 8, right: 8,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: const Color(0xFF2AABEE), borderRadius: BorderRadius.circular(6)),
            child: const Text('Хит', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  void _showBotInfo(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF232E3C),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Покупка через бота', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            const Text('Для покупки звёзд перейдите в Telegram-бот PhoenixGram и используйте раздел 🛒 Магазин',
                style: TextStyle(color: Colors.white70), textAlign: TextAlign.center),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2AABEE)),
                child: const Text('Понятно', style: TextStyle(color: Colors.white)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ===== PREMIUM =====
class _PremiumTab extends StatelessWidget {
  const _PremiumTab();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFFFFD700), Color(0xFFFF8C00)]),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              children: [
                const Text('👑', style: TextStyle(fontSize: 52)),
                const SizedBox(height: 12),
                const Text('PhoenixGram Premium', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('Разблокируй все возможности', style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 14)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ..._features.map((f) => _FeatureRow(icon: f[0], title: f[1], desc: f[2])),
          const SizedBox(height: 20),
          _PlanCard(title: 'Месяц', price: '299 ⭐', period: 'в месяц', highlighted: false),
          const SizedBox(height: 12),
          _PlanCard(title: 'Год', price: '2490 ⭐', period: 'в год • экономия 30%', highlighted: true),
        ],
      ),
    );
  }

  static const _features = [
    ['🚀', 'Без ограничений', 'Отправляй любые файлы до 4 ГБ'],
    ['🎨', 'Уникальные темы', 'Эксклюзивные цветовые схемы'],
    ['⭐', 'Двойные звёзды', 'Получай в 2× больше бонусных звёзд'],
    ['🔖', 'Сохранённые чаты', 'До 10 закреплённых чатов'],
    ['📢', 'Приоритет поддержки', 'Быстрые ответы от команды'],
  ];
}

class _FeatureRow extends StatelessWidget {
  final String icon, title, desc;
  const _FeatureRow({required this.icon, required this.title, required this.desc});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(
      children: [
        Text(icon, style: const TextStyle(fontSize: 28)),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 15)),
              Text(desc, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
            ],
          ),
        ),
        const Icon(Icons.check_circle, color: Color(0xFF2AABEE), size: 20),
      ],
    ),
  );
}

class _PlanCard extends StatelessWidget {
  final String title, price, period;
  final bool highlighted;
  const _PlanCard({required this.title, required this.price, required this.period, required this.highlighted});

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: highlighted ? const Color(0xFF2B5278) : const Color(0xFF232E3C),
      borderRadius: BorderRadius.circular(16),
      border: highlighted ? Border.all(color: const Color(0xFF2AABEE), width: 1.5) : null,
    ),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
              Text(price, style: const TextStyle(color: Color(0xFFFFD700), fontSize: 22, fontWeight: FontWeight.bold)),
              Text(period, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12)),
            ],
          ),
        ),
        ElevatedButton(
          onPressed: () {},
          style: ElevatedButton.styleFrom(
            backgroundColor: highlighted ? const Color(0xFF2AABEE) : const Color(0xFF17212B),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          child: Text(highlighted ? 'Выбрать' : 'Купить', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ),
      ],
    ),
  );
}

// ===== ЮЗЕРНЕЙМЫ =====
class _UsernamesTab extends StatelessWidget {
  const _UsernamesTab();
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🔤', style: TextStyle(fontSize: 60)),
          const SizedBox(height: 16),
          const Text('Красивые юзернеймы', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text('Получите короткий или уникальный ID через Telegram-бот',
              style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 14), textAlign: TextAlign.center),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            icon: const Icon(Icons.open_in_new, color: Colors.white, size: 18),
            label: const Text('Открыть бота', style: TextStyle(color: Colors.white)),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2AABEE),
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
            onPressed: () {},
          ),
        ],
      ),
    ),
  );
}

// ===== NFT =====
class _NftTab extends StatelessWidget {
  const _NftTab();

  static const _nfts = [
    {'name': 'Phoenix Fire #001', 'price': '500 ⭐', 'rarity': 'Редкий', 'emoji': '🔥'},
    {'name': 'Crystal Wings #042', 'price': '1200 ⭐', 'rarity': 'Эпический', 'emoji': '💎'},
    {'name': 'Shadow Wolf #007', 'price': '300 ⭐', 'rarity': 'Обычный', 'emoji': '🐺'},
    {'name': 'Golden Crown #099', 'price': '5000 ⭐', 'rarity': 'Легендарный', 'emoji': '👑'},
    {'name': 'Ice Storm #015', 'price': '800 ⭐', 'rarity': 'Редкий', 'emoji': '❄️'},
    {'name': 'Dark Matter #033', 'price': '2500 ⭐', 'rarity': 'Эпический', 'emoji': '🌌'},
  ];

  @override
  Widget build(BuildContext context) => GridView.builder(
    padding: const EdgeInsets.all(16),
    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
      crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 0.8,
    ),
    itemCount: _nfts.length,
    itemBuilder: (_, i) => _NftCard(nft: _nfts[i]),
  );
}

class _NftCard extends StatelessWidget {
  final Map<String, String> nft;
  const _NftCard({required this.nft});

  Color get _rarityColor {
    switch (nft['rarity']) {
      case 'Легендарный': return const Color(0xFFFFD700);
      case 'Эпический': return const Color(0xFF9B59B6);
      case 'Редкий': return const Color(0xFF2AABEE);
      default: return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(
      color: const Color(0xFF232E3C),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: _rarityColor.withOpacity(0.3)),
    ),
    child: Column(
      children: [
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [_rarityColor.withOpacity(0.3), const Color(0xFF17212B)],
                  begin: Alignment.topCenter, end: Alignment.bottomCenter),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            ),
            child: Center(child: Text(nft['emoji']!, style: const TextStyle(fontSize: 52))),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(nft['name']!, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: _rarityColor.withOpacity(0.2), borderRadius: BorderRadius.circular(6)),
                child: Text(nft['rarity']!, style: TextStyle(color: _rarityColor, fontSize: 10)),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(nft['price']!, style: const TextStyle(color: Color(0xFFFFD700), fontWeight: FontWeight.bold, fontSize: 13)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: const Color(0xFF2AABEE), borderRadius: BorderRadius.circular(8)),
                    child: const Text('Купить', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    ),
  );
}
