import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/auth_provider.dart';
import '../../utils/constants.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notifications = true;
  bool _soundMessages = true;
  bool _darkMode = true;
  bool _autoDownload = false;

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    return Scaffold(
      backgroundColor: const Color(0xFF17212B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('Настройки', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        children: [
          // Профиль
          _buildProfileTile(user?.displayName ?? 'Пользователь', '@${user?.phoenixId ?? ''}', user?.avatarUrl),
          _sep,
          _section('Уведомления'),
          _toggle(Icons.notifications_outlined, 'Уведомления', _notifications, (v) => setState(() => _notifications = v)),
          _toggle(Icons.volume_up_outlined, 'Звук сообщений', _soundMessages, (v) => setState(() => _soundMessages = v)),
          _sep,
          _section('Внешний вид'),
          _toggle(Icons.dark_mode_outlined, 'Тёмная тема', _darkMode, (v) => setState(() => _darkMode = v)),
          _sep,
          _section('Медиа'),
          _toggle(Icons.download_outlined, 'Автозагрузка медиа', _autoDownload, (v) => setState(() => _autoDownload = v)),
          _sep,
          _section('Конфиденциальность'),
          _tile(Icons.lock_outline, 'Пароль и безопасность', () {}),
          _tile(Icons.block_outlined, 'Заблокированные', () {}),
          _sep,
          _section('О приложении'),
          _tile(Icons.info_outline, 'О PhoenixGram', () => _showAbout(context)),
          _tile(Icons.policy_outlined, 'Политика конфиденциальности', () {}),
          _tile(Icons.description_outlined, 'Условия использования', () {}),
          _sep,
          Padding(
            padding: const EdgeInsets.all(16),
            child: OutlinedButton.icon(
              icon: const Icon(Icons.logout, color: Colors.redAccent),
              label: const Text('Выйти', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Colors.redAccent),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              onPressed: () => context.read<AuthProvider>().logout(),
            ),
          ),
          Center(
            child: Text('PhoenixGram v${AppConstants.appVersion}',
                style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 12)),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildProfileTile(String name, String id, String? avatar) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(
        radius: 28,
        backgroundColor: const Color(0xFF2AABEE),
        backgroundImage: avatar != null && avatar.isNotEmpty ? NetworkImage(avatar) : null,
        child: avatar == null || avatar.isEmpty
            ? Text(name.isNotEmpty ? name[0].toUpperCase() : '?',
                style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold))
            : null,
      ),
      title: Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17)),
      subtitle: Text(id, style: const TextStyle(color: Color(0xFF2AABEE), fontSize: 13)),
      trailing: const Icon(Icons.chevron_right, color: Colors.white38),
      onTap: () {},
    );
  }

  Widget _section(String title) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
    child: Text(title.toUpperCase(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11, letterSpacing: 1.2)),
  );

  Widget _toggle(IconData icon, String title, bool val, void Function(bool) onChanged) => SwitchListTile(
    secondary: Icon(icon, color: const Color(0xFF2AABEE)),
    title: Text(title, style: const TextStyle(color: Colors.white)),
    value: val,
    onChanged: onChanged,
    activeColor: const Color(0xFF2AABEE),
  );

  Widget _tile(IconData icon, String title, VoidCallback onTap) => ListTile(
    leading: Icon(icon, color: const Color(0xFF2AABEE)),
    title: Text(title, style: const TextStyle(color: Colors.white)),
    trailing: const Icon(Icons.chevron_right, color: Colors.white38),
    onTap: onTap,
  );

  Widget get _sep => Divider(height: 1, color: Colors.white.withOpacity(0.07), indent: 16);

  void _showAbout(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF232E3C),
        title: const Text('PhoenixGram', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Center(child: Text('🔥', style: TextStyle(fontSize: 52))),
            const SizedBox(height: 12),
            Text('Версия: ${AppConstants.appVersion}', style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 4),
            const Text('Мессенджер с внутренней валютой Звёзды Феникс.',
                style: TextStyle(color: Colors.white54, fontSize: 13)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Закрыть', style: TextStyle(color: Color(0xFF2AABEE)))),
        ],
      ),
    );
  }
}
