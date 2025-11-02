import 'api_service.dart';

class NotificationService {
  final ApiService api;

  NotificationService(this.api);

  Future<List<dynamic>> list() async {
    final data = await api.getJson('/notifications/');
    return (data['results'] as List?) ?? [];
  }

  Future<void> markRead(int id) async =>
      await api.postJson('/notifications/$id/read/', {});
}
