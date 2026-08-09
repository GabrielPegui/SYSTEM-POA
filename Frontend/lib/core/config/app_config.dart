/// Application-wide configuration.
///
/// Values can be overridden at build/run time with:
/// `--dart-define=API_BASE_URL=https://api.example.com`
class AppConfig {
  AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const Duration connectionTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
}
