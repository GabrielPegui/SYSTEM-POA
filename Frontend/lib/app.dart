import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_constants.dart';
import 'core/router/app_router.dart';
import 'core/state/app_state.dart';
import 'core/theme/app_theme.dart';

/// Root application widget.
class PurchaseOrderApp extends StatelessWidget {
  const PurchaseOrderApp({super.key, this.appState});

  final AppState? appState;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<AppState>(
      create: (_) => appState ?? AppState(),
      child: MaterialApp.router(
        title: AppConstants.appName,
        theme: AppTheme.light,
        routerConfig: appRouter,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
