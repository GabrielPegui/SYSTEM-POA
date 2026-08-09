/// Global constants shared across the application.
class AppConstants {
  AppConstants._();

  static const String appName = 'Purchase Order Automation';
  static const String appVersion = '0.1.0';
}

/// Route paths for the application navigation.
///
/// The GoRouter graph lives in `core/router/app_router.dart`; these constants
/// keep the navigation paths in a single, shared place so the shell and the
/// router cannot drift apart.
class AppRoutes {
  AppRoutes._();

  static const String dashboard = '/dashboard';
  static const String validation = '/validation';
  static const String history = '/history';
  static const String customers = '/customers';
  static const String products = '/products';
  static const String routes = '/routes';
  static const String configuration = '/configuration';
}
