import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/websocket_service.dart';
import 'chats/chats_screen.dart';
import 'shop/shop_screen.dart';
import 'gifts/gifts_screen.dart';
import 'profile/profile_screen.dart';
import 'settings/settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    WebSocketService().connect();
  }

  static const _screens = [
    ChatsScreen(),
    ShopScreen(),
    GiftsScreen(),
    ProfileScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _tab, children: _screens),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF232E3C),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, -2))],
        ),
        child: NavigationBar(
          backgroundColor: const Color(0xFF232E3C),
          indicatorColor: const Color(0xFF2AABEE).withOpacity(0.2),
          selectedIndex: _tab,
          onDestinationSelected: (i) => setState(() => _tab = i),
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.chat_bubble_outline, color: Colors.white54),
              selectedIcon: Icon(Icons.chat_bubble, color: Color(0xFF2AABEE)),
              label: 'Чаты',
            ),
            NavigationDestination(
              icon: Icon(Icons.store_outlined, color: Colors.white54),
              selectedIcon: Icon(Icons.store, color: Color(0xFF2AABEE)),
              label: 'Магазин',
            ),
            NavigationDestination(
              icon: Icon(Icons.card_giftcard_outlined, color: Colors.white54),
              selectedIcon: Icon(Icons.card_giftcard, color: Color(0xFF2AABEE)),
              label: 'Подарки',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline, color: Colors.white54),
              selectedIcon: Icon(Icons.person, color: Color(0xFF2AABEE)),
              label: 'Профиль',
            ),
            NavigationDestination(
              icon: Icon(Icons.settings_outlined, color: Colors.white54),
              selectedIcon: Icon(Icons.settings, color: Color(0xFF2AABEE)),
              label: 'Настройки',
            ),
          ],
        ),
      ),
    );
  }
}
