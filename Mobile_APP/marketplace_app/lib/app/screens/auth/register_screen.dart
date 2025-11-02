import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  String u = '', p = '', phone = '', email = '';
  bool _loading = false;
  String? _msg, _err;

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    _form.currentState!.save();
    setState(() => _loading = true);

    try {
      final api = ApiService();
      final auth = AuthService(api);
      await auth.register(
        username: u,
        phone: phone,
        password: p,
        email: email.isEmpty ? null : email,
      );
      setState(() => _msg = 'Registered! A verification code has been sent to your phone.');
    } catch (e) {
      setState(() => _err = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _form,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextFormField(
                      decoration: const InputDecoration(labelText: 'Username'),
                      onSaved: (v) => u = v!.trim(),
                      validator: (v) => v!.isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: 'Phone (07xxxxxxxx or 9627xxxxxxxx)',
                      ),
                      onSaved: (v) => phone = v!.trim(),
                      validator: (v) => v!.isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      decoration: const InputDecoration(labelText: 'Email (optional)'),
                      onSaved: (v) => email = v!.trim(),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Password'),
                      onSaved: (v) => p = v!.trim(),
                      validator: (v) => v!.length < 6 ? 'Min 6 chars' : null,
                    ),
                    const SizedBox(height: 16),
                    if (_err != null)
                      Text(
                        _err!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    if (_msg != null)
                      Text(
                        _msg!,
                        style: const TextStyle(color: Colors.green),
                      ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _loading ? null : _submit,
                        child: _loading
                            ? const CircularProgressIndicator()
                            : const Text('Register'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
