class User {
  final int id;
  final String phoenixId;
  final String? firstName;
  final String? lastName;
  final String? username;
  final String? avatarUrl;
  final int starsBalance;
  final bool isPremium;
  final bool isVerified;
  final bool isBanned;
  final String? bio;
  final String createdAt;

  User({
    required this.id,
    required this.phoenixId,
    this.firstName,
    this.lastName,
    this.username,
    this.avatarUrl,
    this.starsBalance = 0,
    this.isPremium = false,
    this.isVerified = false,
    this.isBanned = false,
    this.bio,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      phoenixId: json['phoenix_id'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      username: json['username'],
      avatarUrl: json['avatar_url'],
      starsBalance: json['stars_balance'] ?? 0,
      isPremium: json['is_premium'] ?? false,
      isVerified: json['is_verified'] ?? false,
      isBanned: json['is_banned'] ?? false,
      bio: json['bio'],
      createdAt: json['created_at'] ?? '',
    );
  }

  String get displayName {
    if (firstName != null && firstName!.isNotEmpty) {
      return lastName != null ? '$firstName $lastName' : firstName!;
    }
    return '@$phoenixId';
  }

  String get initials {
    if (firstName != null && firstName!.isNotEmpty) {
      final f = firstName![0].toUpperCase();
      final l = lastName != null && lastName!.isNotEmpty ? lastName![0].toUpperCase() : '';
      return '$f$l';
    }
    return phoenixId[0].toUpperCase();
  }
}
