import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';

class CategoryService {
  static Future<List<dynamic>> fetchCategories() async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/categories/");
    final response = await http.get(url);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Failed to load categories");
    }
  }
}
