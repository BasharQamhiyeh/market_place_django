import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/config.dart';
import '../../providers/user_provider.dart';
import '../../services/item_service.dart';
import '../auth/login_screen.dart';
import '../items/create_item_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<dynamic> items = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadItems();
  }

  Future<void> _loadItems() async {
    try {
      final token = context.read<UserProvider>().token;
      final data = await ItemService.fetchItems(token);
      setState(() {
        items = data;
        loading = false;
      });
    } catch (e) {
      setState(() {
        error = e.toString();
        loading = false;
      });
    }
  }

  void _logout() {
    final u = context.read<UserProvider>();
    u.logout();
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => LoginScreen()),
    );
  }

  String _fullUrl(String path) =>
      path.startsWith('http') ? path : "${AppConfig.baseUrl}$path";

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Marketplace"),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _loadItems,
                  child: GridView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: items.length,
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 0.8,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                    ),
                    itemBuilder: (context, i) {
                      final item = items[i];
                      final photos = item['photos'] ?? [];
                      final img = photos.isNotEmpty
                          ? _fullUrl(photos[0]['image'])
                          : null;
                      final title = item['title'] ?? '';
                      final price = item['price']?.toString() ?? '';
                      final cond = item['condition'] ?? '';

                      return Card(
                        elevation: 2,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              child: ClipRRect(
                                borderRadius: const BorderRadius.vertical(
                                    top: Radius.circular(8)),
                                child: img != null
                                    ? Image.network(img, fit: BoxFit.cover)
                                    : Container(
                                        color: Colors.grey.shade200,
                                        child: const Icon(Icons.image,
                                            size: 50, color: Colors.grey),
                                      ),
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(title,
                                      style: const TextStyle(
                                          fontWeight: FontWeight.bold),
                                      overflow: TextOverflow.ellipsis),
                                  const SizedBox(height: 4),
                                  Text("$price JOD",
                                      style: const TextStyle(
                                          color: Colors.green,
                                          fontWeight: FontWeight.w500)),
                                  Text(
                                    cond == 'new' ? "New" : "Used",
                                    style: const TextStyle(
                                        fontSize: 12, color: Colors.grey),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CreateItemScreen()),
          );
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
