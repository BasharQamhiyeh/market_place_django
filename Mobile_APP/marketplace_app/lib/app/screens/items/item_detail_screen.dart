import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/favorite_service.dart';
import '../../services/item_service.dart';
import '../../services/misc_service.dart';
import '../../services/message_service.dart';
import '../inbox/chat_screen.dart';

class ItemDetailScreen extends StatefulWidget {
  final int itemId;

  const ItemDetailScreen({super.key, required this.itemId});

  @override
  State<ItemDetailScreen> createState() => _ItemDetailScreenState();
}

class _ItemDetailScreenState extends State<ItemDetailScreen> {
  bool loading = true;
  String? error;
  Map<String, dynamic>? item;
  bool favWorking = false;

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final svc = ItemService(api);
      final it = await svc.getItem(widget.itemId);
      setState(() => item = it);
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

  Future<void> _addFavorite() async {
    setState(() => favWorking = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      await FavoriteService(api).add(widget.itemId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Added to favorites')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    } finally {
      setState(() => favWorking = false);
    }
  }

  Future<void> _report() async {
    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Report Issue'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(hintText: 'Message'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Send'),
          ),
        ],
      ),
    );

    if (ok != true) return;

    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      await MiscService(api).reportIssue(
        itemId: widget.itemId,
        message: ctrl.text.trim(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Reported')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  Future<void> _startChat() async {
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final conv = await MessageService(api).startConversation(widget.itemId);
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ChatScreen(conversation: conv),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final photos = (item?['photos'] as List?) ?? [];
    return Scaffold(
      appBar: AppBar(title: const Text('Item')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (photos.isNotEmpty)
                        SizedBox(
                          height: 280,
                          child: PageView(
                            children: photos
                                .map<Widget>(
                                  (p) => CachedNetworkImage(
                                    imageUrl: p['image'],
                                    fit: BoxFit.cover,
                                  ),
                                )
                                .toList(),
                          ),
                        )
                      else
                        const SizedBox(
                          height: 120,
                          child: Center(
                            child: Icon(Icons.image, size: 64),
                          ),
                        ),
                      const SizedBox(height: 12),
                      Text(
                        item?['title'] ?? '',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '${item?['price']} JOD',
                        style: const TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 12),
                      Text(item?['description'] ?? ''),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          ElevatedButton.icon(
                            onPressed: favWorking ? null : _addFavorite,
                            icon: const Icon(Icons.favorite_border),
                            label: const Text('Favorite'),
                          ),
                          const SizedBox(width: 8),
                          OutlinedButton.icon(
                            onPressed: _startChat,
                            icon: const Icon(Icons.chat),
                            label: const Text('Chat'),
                          ),
                          const SizedBox(width: 8),
                          TextButton(
                            onPressed: _report,
                            child: const Text('Report'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
    );
  }
}
