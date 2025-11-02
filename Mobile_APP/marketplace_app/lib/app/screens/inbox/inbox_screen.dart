import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/message_service.dart';
import 'chat_screen.dart';

class InboxScreen extends StatefulWidget {
  const InboxScreen({super.key});

  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  bool loading = true;
  String? error;
  List<dynamic> conversations = [];

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      conversations = await MessageService(api).conversations();
      setState(() {});
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
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
      appBar: AppBar(title: const Text('Inbox')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    itemCount: conversations.length,
                    itemBuilder: (_, i) {
                      final c = conversations[i] as Map<String, dynamic>;
                      final itemTitle = c['item']?['title'] ?? '';
                      return ListTile(
                        title: Text(itemTitle),
                        subtitle: const Text('Buyer & Seller chat'),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                ChatScreen(conversation: c),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
