import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class UserProvider extends ChangeNotifier {
  static const _storage = FlutterSecureStorage();

  String? _accessToken;
  Map<String, dynamic>? _user;

  bool get isLoggedIn => _accessToken != null;
  String? get token => _accessToken;
  Map<String, dynamic>? get user => _user;

  Future<void> restoreSession() async {
    _accessToken = await _storage.read(key: 'access');
    final u = await _storage.read(key: 'user');
    _user = u == null ? null : jsonDecode(u);
    notifyListeners();
  }

  Future<void> saveSession(String access, Map<String, dynamic> user) async {
    _accessToken = access;
    _user = user;
    await _storage.write(key: 'access', value: access);
    await _storage.write(key: 'user', value: jsonEncode(user));
    notifyListeners();
  }

  Future<void> clearSession() async {
    _accessToken = null;
    _user = null;
    await _storage.delete(key: 'access');
    await _storage.delete(key: 'user');
    notifyListeners();
  }
}
