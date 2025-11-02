import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import '../core/config.dart';

class ItemService {
  static Future<List<dynamic>> fetchItems(String? token) async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/items/");
    final headers = {
      "Content-Type": "application/json",
      if (token != null) "Authorization": "Bearer $token",
    };
    final res = await http.get(url, headers: headers);
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return (data is List) ? data : (data['results'] ?? []);
    }
    throw Exception("Failed to load items");
  }

  static Future<List<dynamic>> fetchCities() async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/cities/");
    final res = await http.get(url);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception("Failed to load cities");
  }

  static Future<List<dynamic>> fetchCategories() async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/categories/");
    final res = await http.get(url);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception("Failed to load categories");
  }

  static Future<List<dynamic>> fetchCategoryAttributes(int categoryId) async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/categories/$categoryId/attributes/");
    final res = await http.get(url);
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw Exception("Failed to load attributes");
  }

  /// attributes payload example:
  /// [{"id": 12, "value": "Toyota"}, {"id": 15, "value": "2021"}]
  static Future<bool> createItem({
    required String token,
    required String title,
    required String condition,
    required String price,
    String description = "",
    int? categoryId,
    int? cityId,
    List<Map<String, dynamic>> attributes = const [],
    List<XFile> images = const [],
  }) async {
    final url = Uri.parse("${AppConfig.apiBaseUrl}/items/");
    final req = http.MultipartRequest('POST', url)
      ..headers['Authorization'] = 'Bearer $token'
      ..fields['title'] = title
      ..fields['condition'] = condition
      ..fields['price'] = price
      ..fields['description'] = description;

    if (categoryId != null) req.fields['category'] = categoryId.toString();
    if (cityId != null) req.fields['city'] = cityId.toString();
    if (attributes.isNotEmpty) {
      req.fields['attributes'] = jsonEncode(attributes);
    }

    for (final img in images) {
      req.files.add(await http.MultipartFile.fromPath('photos', img.path));
    }

    final res = await req.send();
    return res.statusCode == 201;
  }
}
