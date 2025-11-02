import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/notification_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool loading = true;
  String? error;
  List<dynamic> notes = [];

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      notes = await NotificationService(api).list();
      setState(() {});
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
    }
  }

  Future<void> _markRead(int id) async {
    final api = ApiService(token: context.read<UserProvider>().token);
    await NotificationService(api).markRead(id);
    _load();
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    itemCount: notes.length,
                    itemBuilder: (_, i) {
                      final n = notes[i] as Map<String, dynamic>;
                      return ListTile(
                        title: Text(n['message'] ?? ''),
                        subtitle: Text(
                          n['is_read'] == true ? 'Read' : 'Unread',
                        ),
                        trailing: n['is_read'] == true
                            ? null
                            : TextButton(
                                onPressed: () => _markRead(n['id'] as int),
                                child: const Text('Mark read'),
                              ),
                      );
                    },
                  ),
                ),
    );
  }
}
