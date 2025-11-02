import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';

class ApiService {
  final String? token;

  ApiService({this.token});

  // Private headers builder (kept as-is)
  Map<String, String> _headers({Map<String, String>? extra}) {
    final h = <String, String>{'Accept': 'application/json'};
    if (token != null) h['Authorization'] = 'Bearer $token';
    if (extra != null) h.addAll(extra);
    return h;
  }

  // Public wrapper so other files can access headers safely
  Map<String, String> headers({Map<String, String>? extra}) =>
      _headers(extra: extra);

  Uri _u(String path, [Map<String, dynamic>? q]) =>
      Uri.parse("${AppConfig.apiBaseUrl}$path").replace(
        queryParameters: q?.map((k, v) => MapEntry(k, '$v')),
      );

  Future<Map<String, dynamic>> getJson(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    final r = await http.get(_u(path, query), headers: _headers());
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return jsonDecode(utf8.decode(r.bodyBytes));
    }
    throw ApiError(r.statusCode, r.body);
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    final r = await http.post(
      _u(path),
      headers: _headers(extra: {'Content-Type': 'application/json'}),
      body: jsonEncode(body),
    );
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return jsonDecode(utf8.decode(r.bodyBytes));
    }
    throw ApiError(r.statusCode, r.body);
  }

  Future<Map<String, dynamic>> putJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    final r = await http.put(
      _u(path),
      headers: _headers(extra: {'Content-Type': 'application/json'}),
      body: jsonEncode(body),
    );
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return jsonDecode(utf8.decode(r.bodyBytes));
    }
    throw ApiError(r.statusCode, r.body);
  }

  Future<void> delete(String path) async {
    final r = await http.delete(_u(path), headers: _headers());
    if (r.statusCode >= 200 && r.statusCode < 300) return;
    throw ApiError(r.statusCode, r.body);
  }
}

class ApiError implements Exception {
  final int statusCode;
  final String body;

  ApiError(this.statusCode, this.body);

  @override
  String toString() => 'ApiError($statusCode): $body';
}
