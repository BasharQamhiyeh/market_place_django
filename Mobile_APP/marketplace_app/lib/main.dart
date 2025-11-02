import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app/core/theme.dart';
import 'app/providers/user_provider.dart';
import 'app/screens/auth/login_screen.dart';
import 'app/screens/home/home_screen.dart';

void main() {
  runApp(const MarketplaceApp());
}

class MarketplaceApp extends StatelessWidget {
  const MarketplaceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => UserProvider()..loadToken(),
      child: Consumer<UserProvider>(
        builder: (context, user, _) {
          return MaterialApp(
            debugShowCheckedModeBanner: false,
            title: 'Marketplace',
            theme: AppTheme.lightTheme,
            home: user.isLoggedIn
                ? const HomeScreen()
                : LoginScreen(),
          );
        },
      ),
    );
  }
}
