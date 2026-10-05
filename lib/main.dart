import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'services/auth_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthProvider()..init(),
      child: const PhoenixGramApp(),
    ),
  );
}

class PhoenixGramApp extends StatelessWidget {
  const PhoenixGramApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PhoenixGram',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF2AABEE),
          secondary: const Color(0xFF229ED9),
          surface: const Color(0xFF232E3C),
          background: const Color(0xFF17212B),
          onPrimary: Colors.white,
          onSurface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFF17212B),
        useMaterial3: true,
        fontFamily: 'Roboto',
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Color(0xFF232E3C),
          labelTextStyle: WidgetStatePropertyAll(TextStyle(color: Colors.white, fontSize: 11)),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF232E3C),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        dialogTheme: const DialogTheme(backgroundColor: Color(0xFF232E3C)),
        snackBarTheme: const SnackBarThemeData(backgroundColor: Color(0xFF232E3C)),
      ),
      home: const _RootRouter(),
    );
  }
}

class _RootRouter extends StatelessWidget {
  const _RootRouter();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.initialized) {
      return const Scaffold(
        backgroundColor: Color(0xFF17212B),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('🔥', style: TextStyle(fontSize: 64)),
              SizedBox(height: 16),
              Text('PhoenixGram', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
              SizedBox(height: 24),
              CircularProgressIndicator(color: Color(0xFF2AABEE)),
            ],
          ),
        ),
      );
    }
    return auth.isLoggedIn ? const HomeScreen() : const LoginScreen();
  }
}
