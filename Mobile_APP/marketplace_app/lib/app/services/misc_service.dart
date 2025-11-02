import 'api_service.dart';

class MiscService {
  final ApiService api;

  MiscService(this.api);

  Future<void> reportIssue({
    required int itemId,
    required String message,
  }) async =>
      await api.postJson('/issue-reports/', {
        'item_id': itemId,
        'message': message,
      });

  Future<void> subscribe(String email) async =>
      await api.postJson('/subscribe/', {'email': email});
}
