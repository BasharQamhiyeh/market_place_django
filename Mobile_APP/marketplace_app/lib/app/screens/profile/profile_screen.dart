import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/user_provider.dart';
import '../../services/api_service.dart';
import '../../services/auth_service.dart';
import '../../services/misc_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? profile;
  String? error;
  bool loading = true;

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final token = context.read<UserProvider>().token;
      final api = ApiService(token: token);
      final auth = AuthService(api);
      final p = await auth.profile();
      setState(() => profile = p);
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      setState(() => loading = false);
    }
  }

  Future<void> _changePassword() async {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Change Password'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: oldCtrl,
              decoration: const InputDecoration(labelText: 'Old password'),
              obscureText: true,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: newCtrl,
              decoration: const InputDecoration(labelText: 'New password'),
              obscureText: true,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Save'),
          ),
        ],
      ),
    );

    if (ok != true) return;

    try {
      final api = ApiService(token: context.read<UserProvider>().token);
      final auth = AuthService(api);
      await auth.changePassword(oldCtrl.text.trim(), newCtrl.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Password changed')),
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

  Future<void> _sendVerifyCode() async {
    final api = ApiService(token: context.read<UserProvider>().token);
    await AuthService(api).sendVerifyCode();

    if (!mounted) return;

    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Verify Phone'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(labelText: 'Code'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Verify'),
          ),
        ],
      ),
    );

    if (ok == true) {
      await AuthService(api).verifyPhone(ctrl.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Phone verified')),
        );
      }
    }
  }

  Future<void> _subscribe() async {
    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Subscribe to newsletter'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(labelText: 'Email'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Subscribe'),
          ),
        ],
      ),
    );

    if (ok == true) {
      final api = ApiService(token: context.read<UserProvider>().token);
      await MiscService(api).subscribe(ctrl.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Subscribed')),
        );
      }
    }
  }

  void _logout() async => context.read<UserProvider>().clearSession();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Username: ${profile?['username'] ?? ''}'),
                      Text('Phone: ${profile?['phone'] ?? ''}'),
                      Text('Email: ${profile?['email'] ?? ''}'),
                      Text(
                        'Name: ${profile?['first_name'] ?? ''} ${profile?['last_name'] ?? ''}',
                      ),
                      const SizedBox(height: 20),
                      Wrap(
                        spacing: 8,
                        children: [
                          ElevatedButton(
                            onPressed: _changePassword,
                            child: const Text('Change Password'),
                          ),
                          OutlinedButton(
                            onPressed: _sendVerifyCode,
                            child: const Text('Verify Phone'),
                          ),
                          TextButton(
                            onPressed: _subscribe,
                            child: const Text('Subscribe'),
                          ),
                          TextButton(
                            onPressed: _logout,
                            child: const Text('Logout'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
    );
  }
}
