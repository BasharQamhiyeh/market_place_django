import 'api_service.dart';

class FavoriteService {
  final ApiService api;

  FavoriteService(this.api);

  Future<List<dynamic>> list() async {
    final data = await api.getJson('/favorites/');
    return (data['results'] as List?) ?? [];
  }

  Future<void> add(int itemId) async =>
      await api.postJson('/favorites/', {'item_id': itemId});

  Future<void> remove(int favoriteId) async =>
      await api.delete('/favorites/$favoriteId/');
}
