import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:purchase_order_frontend/app.dart';
import 'package:purchase_order_frontend/core/models/orders_models.dart';
import 'package:purchase_order_frontend/core/router/app_router.dart';
import 'package:purchase_order_frontend/core/services/orders_api_service.dart';
import 'package:purchase_order_frontend/core/state/app_state.dart';

class FakeOrdersApiService extends OrdersApiService {
  FakeOrdersApiService({this.snapshot, this.shouldThrow = false});

  final OverviewSnapshot? snapshot;
  final bool shouldThrow;

  @override
  Future<OverviewSnapshot> loadOverview() async {
    if (shouldThrow) {
      throw Exception('Unreachable backend');
    }
    return snapshot ??
        OverviewSnapshot(
          persistedOrders: [
            OrderListView(
              id: 1,
              orderNumber: 'ORD-999',
              customerCode: 'CL001',
              customerName: 'Supermercado Central',
              routeCode: 'PPN101',
              deliveryDate: DateTime(2026, 8, 15),
              status: 'processed',
              items: const [
                OrderItemView(
                  productCode: 'P01',
                  productDescription: 'Pan Pepin Blanco',
                  quantity: 50,
                ),
              ],
            ),
          ],
          sessionDocuments: [
            ProcessedDocumentView(
              sourceFilename: 'review_doc.pdf',
              parserId: 'sirena_v1',
              documentType: 'po',
              status: OrderProcessingStatus.reviewRequired,
              reasons: const ['Múltiples clientes candidatos'],
              items: const [
                OrderLineView(
                  description: 'PAN PEPIN HOT DOG 8/1',
                  quantity: 30,
                  matchStatus: 'review_required',
                  reason: 'Low confidence match',
                ),
              ],
              receivedAt: DateTime(2026, 8, 8, 14, 0),
            ),
          ],
          usingDemoData: false,
          bannerMessage: 'Respuesta determinista para testing',
        );
  }
}

void main() {
  setUp(() {
    appRouter.go('/dashboard');
  });

  WidgetTester setupDesktopView(WidgetTester tester) {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    return tester;
  }

  testWidgets('app boots and displays shell with navigation rail', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    expect(find.text('Grupo Bolin'), findsOneWidget);
    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('Recepción y procesamiento'), findsOneWidget);
  });

  testWidgets('navigates through all views via navigation rail', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    // Navigate to Revisión
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Revisión')));
    await tester.pumpAndSettle();
    expect(find.text('Centro de revisión'), findsOneWidget);
    expect(find.text('review_doc.pdf'), findsWidgets);

    // Navigate to Consolidación
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();
    expect(find.text('Consolidación'), findsWidgets);

    // Navigate to Clientes
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Clientes')));
    await tester.pumpAndSettle();
    expect(find.text('Clientes'), findsWidgets);

    // Navigate to Productos
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Productos')));
    await tester.pumpAndSettle();
    expect(find.text('Productos'), findsWidgets);

    // Navigate to Rutas
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Rutas')));
    await tester.pumpAndSettle();
    expect(find.text('Rutas'), findsWidgets);

    // Navigate to Configuración
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Configuración')));
    await tester.pumpAndSettle();
    expect(find.text('Configuración'), findsWidgets);
  });

  testWidgets('consolidation page toggles between product, customer, route, date tabs', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();

    // Switch to Cliente tab
    await tester.tap(find.text('Cliente'));
    await tester.pumpAndSettle();
    expect(find.text('Agrupación por cliente'), findsOneWidget);

    // Switch to Ruta tab
    await tester.tap(find.text('Ruta'));
    await tester.pumpAndSettle();
    expect(find.text('Agrupación por ruta'), findsOneWidget);

    // Switch to Fecha tab
    await tester.tap(find.text('Fecha'));
    await tester.pumpAndSettle();
    expect(find.text('Agrupación por fecha'), findsOneWidget);
  });

  testWidgets('displays empty state panels when snapshot has no documents', (WidgetTester tester) async {
    setupDesktopView(tester);
    final emptySnapshot = OverviewSnapshot.empty;
    final fakeService = FakeOrdersApiService(snapshot: emptySnapshot);
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    expect(find.text('La bandeja está vacía'), findsOneWidget);
  });
}
