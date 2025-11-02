import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/message_service.dart';

class ChatScreen extends StatefulWidget {
  final Map<String, dynamic> conversation;

  const ChatScreen({super.key, required this.conversation});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  bool loading = true;
  String? error;
  List<dynamic> messages = [];
  final ctrl = TextEditingController();

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      messages = await MessageService(api)
          .messages(conversationId: widget.conversation['id'] as int);
      setState(() {});
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
    }
  }

  Future<void> _send() async {
    final text = ctrl.text.trim();
    if (text.isEmpty) return;
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final svc = MessageService(api);
      final msg = await svc.send(widget.conversation['id'] as int, text);
      ctrl.clear();
      setState(() => messages.add(msg));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.conversation['item']?['title'] ?? 'Chat'),
      ),
      body: Column(
        children: [
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: messages.length,
                    itemBuilder: (_, i) {
                      final m = messages[i] as Map<String, dynamic>;
                      final me = context.read<UserProvider>().user?['user_id'] ==
                          m['sender']?['user_id'];
                      return Align(
                        alignment: me
                            ? Alignment.centerRight
                            : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color:
                                me ? Colors.black87 : Colors.grey.shade200,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            m['text'] ?? '',
                            style: TextStyle(
                              color:
                                  me ? Colors.white : Colors.black87,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
          SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: ctrl,
                    decoration: const InputDecoration(
                      hintText: 'Type a message',
                      contentPadding: EdgeInsets.all(12),
                    ),
                  ),
                ),
                IconButton(
                  onPressed: _send,
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
