import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../models/user.dart';
import '../../services/auth_provider.dart';
import '../../widgets/avatar_widget.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    if (user == null) return const SizedBox();

    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      body: CustomScrollView(
        slivers: [
          _buildHeader(user),
          SliverToBoxAdapter(child: _buildBody(user, context)),
        ],
      ),
    );
  }

  SliverAppBar _buildHeader(User user) {
    return SliverAppBar(
      expandedHeight: 220,
      pinned: true,
      backgroundColor: const Color(0xFF232E3C),
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF2AABEE), Color(0xFF1A1F2E)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              AvatarWidget(
                imageUrl: user.avatarUrl,
                initials: user.initials,
                size: 80,
                isPremium: user.isPremium,
                isVerified: user.isVerified,
              ),
              const SizedBox(height: 12),
              Text(user.displayName,
                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              GestureDetector(
                onTap: () {
                  Clipboard.setData(ClipboardData(text: user.phoenixId));
                },
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('@${user.phoenixId}',
                        style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 14)),
                    const SizedBox(width: 4),
                    Icon(Icons.copy, size: 14, color: Colors.white.withOpacity(0.5)),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBody(User user, BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Баланс
          _card(
            child: Row(
              children: [
                _statItem('⭐', '${user.starsBalance}', 'Звёзды'),
                _divider,
                _statItem(user.isPremium ? '👑' : '🆓', user.isPremium ? 'Premium' : 'Базовый', 'Подписка'),
                _divider,
                _statItem(user.isVerified ? '✅' : '❌', user.isVerified ? 'Да' : 'Нет', 'Верификация'),
              ],
            ),
          ),
          const SizedBox(height: 12),
          // Инфо
          if (user.bio != null && user.bio!.isNotEmpty) ...[
            _sectionTitle('О себе'),
            _card(child: Text(user.bio!, style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 14))),
            const SizedBox(height: 12),
          ],
          _sectionTitle('Аккаунт'),
          _card(
            child: Column(
              children: [
                _infoRow(Icons.alternate_email, 'PhoenixGram ID', user.phoenixId),
                _sep,
                _infoRow(Icons.calendar_today_outlined, 'Регистрация', _formatDate(user.createdAt)),
                _sep,
                _infoRow(Icons.devices_outlined, 'Устройства', 'Управление'),
              ],
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.logout, color: Colors.redAccent),
              label: const Text('Выйти из аккаунта', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Colors.redAccent),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              onPressed: () => _confirmLogout(context),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Future<void> _confirmLogout(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('Выход', style: TextStyle(color: Colors.white)),
        content: const Text('Вы уверены, что хотите выйти?', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Отмена')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Выйти', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) context.read<AuthProvider>().logout();
  }

  Widget _card({required Widget child}) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: const Color(0xFF232E3C),
      borderRadius: BorderRadius.circular(16),
    ),
    child: child,
  );

  Widget _statItem(String emoji, String val, String label) => Expanded(
    child: Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 22)),
        const SizedBox(height: 4),
        Text(val, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11)),
      ],
    ),
  );

  Widget get _divider => Container(width: 1, height: 48, color: Colors.white.withOpacity(0.1));
  Widget get _sep => Divider(height: 1, color: Colors.white.withOpacity(0.08));

  Widget _infoRow(IconData icon, String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 10),
    child: Row(
      children: [
        Icon(icon, size: 18, color: const Color(0xFF2AABEE)),
        const SizedBox(width: 12),
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13)),
        const Spacer(),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
      ],
    ),
  );

  Widget _sectionTitle(String t) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(t, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12, letterSpacing: 0.8)),
  );

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso);
      return '${dt.day}.${dt.month.toString().padLeft(2, '0')}.${dt.year}';
    } catch (_) { return iso; }
  }
}
