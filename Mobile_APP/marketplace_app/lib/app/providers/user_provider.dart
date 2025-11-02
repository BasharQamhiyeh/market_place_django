import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class UserProvider with ChangeNotifier {
  final _storage = const FlutterSecureStorage();
  String? _accessToken;

  String? get token => _accessToken;
  bool get isLoggedIn => _accessToken != null;

  Future<void> loadToken() async {
    _accessToken = await _storage.read(key: 'access');
    notifyListeners();
  }

  Future<void> saveToken(String token) async {
    _accessToken = token;
    await _storage.write(key: 'access', value: token);
    notifyListeners();
  }

  Future<void> logout() async {
    _accessToken = null;
    await _storage.deleteAll();
    notifyListeners();
  }
}
