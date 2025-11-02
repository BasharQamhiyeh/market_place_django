import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../services/auth_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  String phone = '';
  String? error, msg;

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    _form.currentState!.save();

    try {
      final api = ApiService();
      final auth = AuthService(api);
      await auth.forgotPassword(phone);
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const VerifyResetCodeScreen()),
        );
      }
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot Password')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _form,
          child: Column(
            children: [
              TextFormField(
                decoration: const InputDecoration(labelText: 'Phone'),
                onSaved: (v) => phone = v!.trim(),
                validator: (v) => v!.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              if (error != null)
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red),
                ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _submit,
                child: const Text('Send Code'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class VerifyResetCodeScreen extends StatefulWidget {
  const VerifyResetCodeScreen({super.key});

  @override
  State<VerifyResetCodeScreen> createState() => _VerifyResetCodeScreenState();
}

class _VerifyResetCodeScreenState extends State<VerifyResetCodeScreen> {
  final _form = GlobalKey<FormState>();
  String code = '';
  String? error;

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    _form.currentState!.save();

    try {
      final api = ApiService();
      final auth = AuthService(api);
      await auth.verifyResetCode(code);
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const ResetPasswordScreen()),
        );
      }
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verify Code')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _form,
          child: Column(
            children: [
              TextFormField(
                decoration: const InputDecoration(labelText: 'Code'),
                onSaved: (v) => code = v!.trim(),
                validator: (v) => v!.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              if (error != null)
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red),
                ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _submit,
                child: const Text('Verify'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ResetPasswordScreen extends StatefulWidget {
  const ResetPasswordScreen({super.key});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _form = GlobalKey<FormState>();
  String pw = '';
  String? error, msg;

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    _form.currentState!.save();

    try {
      final api = ApiService();
      final auth = AuthService(api);
      await auth.resetPassword(pw);
      if (mounted) Navigator.popUntil(context, (r) => r.isFirst);
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reset Password')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _form,
          child: Column(
            children: [
              TextFormField(
                obscureText: true,
                decoration: const InputDecoration(labelText: 'New Password'),
                onSaved: (v) => pw = v!.trim(),
                validator: (v) => v!.length < 6 ? 'Min 6 chars' : null,
              ),
              const SizedBox(height: 12),
              if (error != null)
                Text(
                  error!,
                  style: const TextStyle(color: Colors.red),
                ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _submit,
                child: const Text('Reset'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
