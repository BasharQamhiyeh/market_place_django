import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/favorite_service.dart';
import '../home/item_card.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  bool loading = true;
  String? error;
  List<dynamic> favs = [];

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      favs = await FavoriteService(api).list();
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
      appBar: AppBar(title: const Text('Favorites')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    itemCount: favs.length,
                    itemBuilder: (_, i) {
                      final item = favs[i]['item'] as Map<String, dynamic>;
                      return ItemCard(item: item);
                    },
                  ),
                ),
    );
  }
}
