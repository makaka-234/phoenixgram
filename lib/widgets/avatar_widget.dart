import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

class AvatarWidget extends StatelessWidget {
  final String? imageUrl;
  final String initials;
  final double size;
  final Color? color;
  final bool isPremium;
  final bool isVerified;

  const AvatarWidget({
    super.key,
    this.imageUrl,
    required this.initials,
    this.size = 48,
    this.color,
    this.isPremium = false,
    this.isVerified = false,
  });

  static const List<Color> _colors = [
    Color(0xFF2AABEE), Color(0xFF229ED9), Color(0xFF5B99C2),
    Color(0xFFE74C3C), Color(0xFF9B59B6), Color(0xFF27AE60),
    Color(0xFFF39C12), Color(0xFF1ABC9C), Color(0xFF34495E),
  ];

  Color get _avatarColor {
    if (color != null) return color!;
    final idx = initials.isNotEmpty ? initials.codeUnitAt(0) % _colors.length : 0;
    return _colors[idx];
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _avatarColor,
          ),
          child: imageUrl != null && imageUrl!.isNotEmpty
              ? ClipOval(
                  child: CachedNetworkImage(
                    imageUrl: imageUrl!,
                    fit: BoxFit.cover,
                    errorWidget: (_, __, ___) => _initials,
                  ),
                )
              : _initials,
        ),
        if (isPremium)
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              width: size * 0.35,
              height: size * 0.35,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFFFFD700),
              ),
              child: Icon(Icons.star, size: size * 0.22, color: Colors.white),
            ),
          ),
        if (isVerified && !isPremium)
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              width: size * 0.35,
              height: size * 0.35,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFF2AABEE),
              ),
              child: Icon(Icons.verified, size: size * 0.22, color: Colors.white),
            ),
          ),
      ],
    );
  }

  Widget get _initials => Center(
    child: Text(
      initials.isEmpty ? '?' : initials[0],
      style: TextStyle(
        color: Colors.white,
        fontSize: size * 0.4,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}
