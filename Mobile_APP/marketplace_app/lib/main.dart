import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app/core/theme.dart';
import 'app/providers/user_provider.dart';
import 'app/screens/auth/login_screen.dart';
import 'app/screens/shell.dart';
void main() async {
WidgetsFlutterBinding.ensureInitialized();
final userProvider = UserProvider();
await userProvider.restoreSession();
runApp(MarketPlaceApp(userProvider: userProvider));
}
class MarketPlaceApp extends StatelessWidget {
final UserProvider userProvider;
const MarketPlaceApp({super.key, required this.userProvider});
@override
Widget build(BuildContext context) {
return MultiProvider(
providers: [
ChangeNotifierProvider<UserProvider>.value(value: userProvider),
],
child: MaterialApp(
title: 'Market Place',
debugShowCheckedModeBanner: false,
theme: buildTheme(),
home: Consumer<UserProvider>(
builder: (_, up, __) => up.isLoggedIn ? const AppShell() : const
LoginScreen(),
),
),
);
}
}