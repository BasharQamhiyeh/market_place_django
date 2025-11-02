import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/user_provider.dart';
import 'api_service.dart';

class AuthService {
  final ApiService api;

  AuthService(this.api);

  Future<void> login(
    BuildContext context, {
    required String username,
    required String password,
  }) async {
    final data = await api.postJson('/auth/login/', {
      'username': username,
      'password': password,
    });

    final access = data['token']['access'] as String;
    final user = data['user'] as Map<String, dynamic>;

    await context.read<UserProvider>().saveSession(access, user);
  }

  Future<void> register({
    required String username,
    required String phone,
    required String password,
    String? email,
    String? firstName,
    String? lastName,
    bool showPhone = false,
  }) async {
    await api.postJson('/auth/register/', {
      'username': username,
      'phone': phone,
      'password': password,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'show_phone': showPhone,
    });
  }

  Future<Map<String, dynamic>> profile() async =>
      await api.getJson('/auth/profile/');

  Future<Map<String, dynamic>> changePassword(
    String oldPw,
    String newPw,
  ) async =>
      await api.putJson('/auth/change-password/', {
        'old_password': oldPw,
        'new_password': newPw,
      });

  Future<void> sendVerifyCode() async =>
      await api.postJson('/auth/send-verify-code/', {});

  Future<void> verifyPhone(String code) async =>
      await api.postJson('/auth/verify-phone/', {'code': code});

  Future<void> forgotPassword(String phone) async =>
      await api.postJson('/auth/forgot-password/', {'phone': phone});

  Future<void> verifyResetCode(String code) async =>
      await api.postJson('/auth/verify-reset-code/', {'code': code});

  Future<void> resetPassword(String newPw) async =>
      await api.postJson('/auth/reset-password/', {'new_password': newPw});
}
