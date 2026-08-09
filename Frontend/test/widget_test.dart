import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:purchase_order_frontend/app.dart';
import 'package:purchase_order_frontend/core/models/orders_models.dart';
import 'package:purchase_order_frontend/core/router/app_router.dart';
import 'package:purchase_order_frontend/core/services/orders_api_service.dart';
import 'package:purchase_order_frontend/core/state/app_state.dart';

class _FakeService extends OrdersApiService {
  @override
  Future<OverviewSnapshot> loadOverview() async {
    return const OverviewSnapshot(
      persistedOrders: [],
      sessionDocuments: [],
      usingDemoData: false,
      bannerMessage: '',
    );
  }
}

void main() {
  setUp(() {
    appRouter.go('/dashboard');
  });

  testWidgets('app boots and shows the initial screen', (WidgetTester tester) async {
    final appState = AppState(service: _FakeService());
    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    expect(find.text('Grupo Bolin'), findsOneWidget);
    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('Recepción y procesamiento'), findsOneWidget);
  });

  testWidgets('navigation rail switches between features', (WidgetTester tester) async {
    final appState = AppState(service: _FakeService());
    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();

    expect(find.text('Consolidación'), findsNWidgets(2));
  });
}
