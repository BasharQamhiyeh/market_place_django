import 'api_service.dart';

class MessageService {
  final ApiService api;

  MessageService(this.api);

  Future<List<dynamic>> conversations() async {
    final data = await api.getJson('/conversations/');
    return (data['results'] as List?) ?? [];
  }

  Future<Map<String, dynamic>> startConversation(int itemId) async =>
      await api.postJson('/conversations/', {'item_id': itemId});

  Future<List<dynamic>> messages({int? conversationId}) async {
    final data = await api.getJson('/messages/');
    final results = (data['results'] as List?) ?? [];
    if (conversationId == null) return results;
    return results
        .where((m) => m['conversation_id'] == conversationId)
        .toList();
  }

  Future<Map<String, dynamic>> send(int conversationId, String text) async =>
      await api.postJson('/messages/', {
        'conversation_id': conversationId,
        'text': text,
      });
}
