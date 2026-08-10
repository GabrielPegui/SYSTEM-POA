import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../features/configuration/presentation/pages/configuration_page.dart';
import '../../features/customers/presentation/pages/customers_page.dart';
import '../../features/history/presentation/pages/history_page.dart';
import '../../features/order_processing/presentation/pages/order_processing_page.dart';
import '../../features/products/presentation/pages/products_page.dart';
import '../../features/routes/presentation/pages/routes_page.dart';
import '../../features/validation/presentation/pages/validation_page.dart';
import '../constants/app_constants.dart';
import '../state/app_state.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.dashboard,
  routes: [
    ShellRoute(
      builder: (context, state, child) => _AppShell(child: child),
      routes: [
        GoRoute(
          path: AppRoutes.dashboard,
          builder: (_, _) => const OrderProcessingPage(),
        ),
        GoRoute(
          path: AppRoutes.validation,
          builder: (_, _) => const ValidationPage(),
        ),
        GoRoute(
          path: AppRoutes.history,
          builder: (_, _) => const HistoryPage(),
        ),
        GoRoute(
          path: AppRoutes.customers,
          builder: (_, _) => const CustomersPage(),
        ),
        GoRoute(
          path: AppRoutes.products,
          builder: (_, _) => const ProductsPage(),
        ),
        GoRoute(
          path: AppRoutes.routes,
          builder: (_, _) => const RoutesPage(),
        ),
        GoRoute(
          path: AppRoutes.configuration,
          builder: (_, _) => const ConfigurationPage(),
        ),
      ],
    ),
  ],
);

class _AppShell extends StatelessWidget {
  const _AppShell({required this.child});

  final Widget child;

  static const _destinations = [
    (
      path: AppRoutes.dashboard,
      label: 'Inicio',
      icon: Icons.dashboard_outlined,
    ),
    (
      path: AppRoutes.validation,
      label: 'Revisión',
      icon: Icons.rule_outlined,
    ),
    (
      path: AppRoutes.history,
      label: 'Consolidación',
      icon: Icons.view_agenda_outlined,
    ),
    (
      path: AppRoutes.configuration,
      label: 'Configuración',
      icon: Icons.settings_outlined,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    final selectedIndex = _destinations.indexWhere((destination) => destination.path == location);
    final appState = context.watch<AppState>();

    return Scaffold(
      body: Row(
        children: [
          Container(
            width: 288,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              border: Border(
                right: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
              ),
            ),
            child: SafeArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
                    child: _BrandBlock(usingDemoData: appState.usingDemoData),
                  ),
                  if (appState.usingDemoData)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: _DemoBanner(message: appState.bannerMessage),
                    ),
                  const SizedBox(height: 8),
                  Expanded(
                    child: SingleChildScrollView(
                      child: IntrinsicHeight(
                        child: NavigationRail(
                          selectedIndex: selectedIndex < 0 ? 0 : selectedIndex,
                          onDestinationSelected: (index) => context.go(_destinations[index].path),
                          labelType: NavigationRailLabelType.all,
                          minWidth: 288,
                          destinations: [
                            for (final destination in _destinations)
                              NavigationRailDestination(
                                icon: Icon(destination.icon),
                                label: Text(destination.label),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(20),
                    child: _ShellFooter(appState: appState),
                  ),
                ],
              ),
            ),
          ),
          Expanded(child: child),
        ],
      ),
    );
  }
}

class _BrandBlock extends StatelessWidget {
  const _BrandBlock({required this.usingDemoData});

  final bool usingDemoData;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: theme.colorScheme.primary,
            borderRadius: BorderRadius.circular(8),
          ),
          alignment: Alignment.center,
          child: Text(
            'B',
            style: theme.textTheme.titleLarge?.copyWith(
              color: theme.colorScheme.onPrimary,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Grupo Bolin',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 2),
              Text(
                usingDemoData ? 'Vista de demostración' : 'Operación de pedidos',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DemoBanner extends StatelessWidget {
  const _DemoBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF4D6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE6C15D)),
      ),
      child: Text(
        message.isEmpty ? 'Datos de demostración locales activos.' : message,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _ShellFooter extends StatelessWidget {
  const _ShellFooter({required this.appState});

  final AppState appState;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Estado',
          style: theme.textTheme.labelLarge?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Icon(
              appState.loading ? Icons.cloud_sync_outlined : Icons.cloud_done_outlined,
              size: 18,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                appState.loading ? 'Sincronizando datos' : 'Listo para operar',
                style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
        if (appState.errorMessage != null) ...[
          const SizedBox(height: 8),
          Text(
            appState.errorMessage!,
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error),
          ),
        ],
      ],
    );
  }
}
