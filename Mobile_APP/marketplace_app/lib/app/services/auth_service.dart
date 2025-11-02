import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';

class AuthService {
  static Future<String?> login(String username, String password) async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/auth/login/");
    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"username": username, "password": password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['access']; // return JWT access token
    }
    return null;
  }
}
