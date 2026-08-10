import 'dart:async';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../errors/failures.dart';

/// Prepared HTTP client for the backend REST API.
///
/// All communication with the backend must go through repositories that use
/// this client (see Frontend/AGENTS.md). No business logic lives here.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('${AppConfig.apiBaseUrl}$path')
        .replace(queryParameters: query);
  }

  Future<http.Response> get(String path, {Map<String, String>? query}) {
    return _send(
      () => _client.get(_uri(path, query)).timeout(AppConfig.receiveTimeout),
    );
  }

  Future<http.Response> post(String path, {Object? body}) {
    return _send(
      () => _client.post(_uri(path), body: body).timeout(AppConfig.receiveTimeout),
    );
  }

  Future<http.Response> put(String path, {Object? body}) {
    return _send(
      () => _client.put(_uri(path), body: body).timeout(AppConfig.receiveTimeout),
    );
  }

  Future<http.Response> postMultipart(
    String path, {
    Map<String, String>? fields,
    List<http.MultipartFile>? files,
  }) {
    return _send(() async {
      final request = http.MultipartRequest('POST', _uri(path));
      if (fields != null) {
        request.fields.addAll(fields);
      }
      if (files != null) {
        request.files.addAll(files);
      }
      final streamed = await request.send().timeout(AppConfig.receiveTimeout);
      return http.Response.fromStream(streamed);
    });
  }

  Future<http.Response> _send(Future<http.Response> Function() request) async {
    try {
      final response = await request();
      if (response.statusCode >= 400) {
        throw ServerFailure(
          'El servidor respondió con código ${response.statusCode}.',
        );
      }
      return response;
    } on Failure {
      rethrow;
    } on http.ClientException catch (error) {
      throw NetworkFailure('No se pudo conectar con el servidor: ${error.message}');
    } on TimeoutException {
      throw TimeoutFailure('El servidor tardó demasiado en responder.');
    } catch (error) {
      throw UnknownFailure('Error inesperado: $error');
    }
  }
}
