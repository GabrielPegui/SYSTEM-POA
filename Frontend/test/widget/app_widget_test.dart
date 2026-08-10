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

  testWidgets('main navigation exposes only the operational destinations', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    final rail = find.byType(NavigationRail);
    for (final label in ['Inicio', 'Revisión', 'Consolidación', 'Configuración']) {
      expect(find.descendant(of: rail, matching: find.text(label)), findsOneWidget, reason: 'Falta destino $label');
    }
    // Clientes, Productos y Rutas ya no forman parte de la navegación principal.
    for (final label in ['Clientes', 'Productos', 'Rutas']) {
      expect(find.descendant(of: rail, matching: find.text(label)), findsNothing, reason: '$label no debería estar en la navegación');
    }
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

    // Navigate to Configuración
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Configuración')));
    await tester.pumpAndSettle();
    expect(find.text('Configuración'), findsWidgets);

    // Regresar a Inicio
    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Inicio')));
    await tester.pumpAndSettle();
    expect(find.text('Recepción y procesamiento'), findsOneWidget);
  });

  testWidgets('inicio exposes a single primary import action without development controls', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    // Una única acción primaria de importación.
    expect(find.widgetWithText(FilledButton, 'Importar órdenes PDF'), findsOneWidget);
    // El ruido de desarrollo ya no está en la operación normal.
    expect(find.text('Ruta manual o muestras (desarrollo)'), findsNothing);
    expect(find.text('Seleccionar y procesar PDF'), findsNothing);
    expect(find.widgetWithText(OutlinedButton, 'Sincronizar backend'), findsNothing);
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

    expect(find.text('Todavía no hay órdenes'), findsOneWidget);
  });

  testWidgets('review center lets the operator correct and save a document', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Revisión')));
    await tester.pumpAndSettle();

    // La orden pendiente muestra el detalle editable con sus motivos.
    expect(find.text('¿Qué requiere revisión?'), findsOneWidget);
    expect(find.text('Guardar corrección'), findsOneWidget);

    // La operadora corrige el cliente y guarda.
    final customerField = find.byWidgetPredicate(
      (widget) => widget is TextField && widget.decoration?.labelText == 'Cliente',
    );
    expect(customerField, findsOneWidget);
    await tester.enterText(customerField, 'Supermercado Central');
    await tester.tap(find.widgetWithText(FilledButton, 'Guardar corrección'));
    await tester.pumpAndSettle();

    // El documento sale de la bandeja de revisión y queda procesado.
    expect(find.text('No hay órdenes pendientes'), findsOneWidget);
    expect(appState.reviewQueue, isEmpty);
    final corrected = appState.processedDocuments
        .where((document) => document.sourceFilename == 'review_doc.pdf')
        .single;
    expect(corrected.customerName, 'Supermercado Central');
    expect(corrected.status, OrderProcessingStatus.processed);
  });
}
