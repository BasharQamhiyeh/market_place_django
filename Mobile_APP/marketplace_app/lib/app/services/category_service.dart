import 'api_service.dart';

class CategoryService {
  final ApiService api;

  CategoryService(this.api);

  Future<Object> getCategoriesTree() async {
    final data = await api.getJson('/categories/');
    if (data is List) {
      return data;
    } else if (data is Map<String, dynamic> && data.containsKey('results')) {
      return (data['results'] as List?) ?? [];
    } else {
      return [];
    }
  }

  Future<Object> getCities() async {
    final data = await api.getJson('/cities/');
    if (data is List) {
      return data;
    } else if (data is Map<String, dynamic> && data.containsKey('results')) {
      return (data['results'] as List?) ?? [];
    } else {
      return [];
    }
  }
}
