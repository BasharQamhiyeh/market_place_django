import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import 'api_service.dart';

class ItemService {
  final ApiService api;

  ItemService(this.api);

  Future<Map<String, dynamic>> listItems({
    String? q,
    int? categoryId,
    int? cityId,
  }) async {
    final params = <String, dynamic>{};
    if (q != null && q.isNotEmpty) params['q'] = q;
    if (categoryId != null) params['category_id'] = categoryId;
    if (cityId != null) params['city_id'] = cityId;

    return await api.getJson('/items/', query: params);
  }

  Future<Map<String, dynamic>> getItem(int id) async =>
      await api.getJson('/items/$id/');

  /// ✅ Fixed image upload and attribute formatting
  Future<Map<String, dynamic>> createItem({
    required String title,
    required String condition,
    required String price,
    required String description,
    required int cityId,
    required int categoryId,
    required List<http.MultipartFile> images,
    List<Map<String, dynamic>> attributeValues = const [],
  }) async {
    final req = http.MultipartRequest('POST', Uri.parse('${_apiBase()}/items/'));

    // Headers
    req.headers.addAll(api.headers());

    // Regular fields
    req.fields.addAll({
      'title': title,
      'condition': condition,
      'price': price,
      'description': description,
      'city_id': '$cityId',
      'category_id': '$categoryId',
    });

    // Attributes
    for (int i = 0; i < attributeValues.length; i++) {
      final attr = attributeValues[i];
      if (attr.containsKey('attribute_id') && attr.containsKey('value')) {
        req.fields['attribute_values[$i][attribute_id]'] =
            '${attr['attribute_id']}';
        req.fields['attribute_values[$i][value]'] =
            '${attr['value']}';
      }
    }

    // ✅ Proper image attachment
    for (final file in images) {
      req.files.add(file);
    }

    // Debug print (optional, for local troubleshooting)
    print('Sending ${req.files.length} image(s)...');

    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw ApiError(res.statusCode, res.body);
  }

  /// ✅ Same fix for updateItem
  Future<Map<String, dynamic>> updateItem({
    required int id,
    String? title,
    String? condition,
    String? price,
    String? description,
    int? cityId,
    int? categoryId,
    List<http.MultipartFile> images = const [],
    List<Map<String, dynamic>>? attributeValues,
  }) async {
    final req =
        http.MultipartRequest('PUT', Uri.parse('${_apiBase()}/items/$id/'));
    req.headers.addAll(api.headers());

    if (title != null) req.fields['title'] = title;
    if (condition != null) req.fields['condition'] = condition;
    if (price != null) req.fields['price'] = price;
    if (description != null) req.fields['description'] = description;
    if (cityId != null) req.fields['city_id'] = '$cityId';
    if (categoryId != null) req.fields['category_id'] = '$categoryId';

    // Attributes
    if (attributeValues != null) {
      for (int i = 0; i < attributeValues.length; i++) {
        final attr = attributeValues[i];
        if (attr.containsKey('attribute_id')) {
          req.fields['attribute_values[$i][attribute_id]'] =
              attr['attribute_id'].toString();
        }
        if (attr.containsKey('value')) {
          req.fields['attribute_values[$i][value]'] =
              attr['value'].toString();
        }
      }
    }

    // ✅ Proper image attachment
    for (final file in images) {
      req.files.add(file);
    }

    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw ApiError(res.statusCode, res.body);
  }

  Future<void> deleteItem(int id) async => await api.delete('/items/$id/');

  Future<void> reactivate(int id) async =>
      await api.postJson('/items/$id/reactivate/', {});

  Future<void> markSold(int id) async =>
      await api.postJson('/items/$id/mark_sold/', {});

  Future<void> cancel(int id, String reason) async =>
      await api.postJson('/items/$id/cancel/', {'reason': reason});

  String _apiBase() => AppConfig.apiBaseUrl;
}
