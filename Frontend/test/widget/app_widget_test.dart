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
              customerName: 'Supermercado Central',
              routeCode: 'PPN101',
              deliveryDate: DateTime(2026, 8, 15),
              status: 'processed',
              items: const [
                OrderItemView(
                  description: 'Pan Pepin Blanco',
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
    expect(find.text('Revisión de órdenes'), findsOneWidget);
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

  testWidgets('consolidation page shows the Ruta + Fecha distribution with selectors and totals', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();

    // Dimensión única Ruta + Fecha: distribución por cliente y total por producto.
    expect(find.text('Distribución por cliente'), findsOneWidget);
    expect(find.text('Total por producto'), findsOneWidget);
    expect(find.textContaining('Ruta PPN101'), findsOneWidget);
    expect(find.text('Total general'), findsOneWidget);
    // El total se repite en los tres niveles: subtotal cliente, total producto y barra general.
    expect(find.text('50 unidades'), findsNWidgets(3));

    // Selector combinado de ruta: filtrar por PPN101 conserva el grupo.
    await tester.tap(find.text('Todas las rutas'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('PPN101').last);
    await tester.pumpAndSettle();
    expect(find.textContaining('Ruta PPN101'), findsOneWidget);

    // El botón de exportación está deshabilitado (exportación pendiente).
    final exportButton = tester.widget<OutlinedButton>(
      find.widgetWithText(OutlinedButton, 'Exportar'),
    );
    expect(exportButton.onPressed, isNull);
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

  testWidgets('review center lets the operator correct and approve a document', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Revisión')));
    await tester.pumpAndSettle();

    // La orden pendiente muestra la alerta operativa y las acciones accionables.
    expect(find.text('Revisión pendiente'), findsOneWidget);
    expect(find.text('Aprobar y enviar a consolidación'), findsOneWidget);
    expect(find.text('Descartar orden'), findsOneWidget);

    // La operadora selecciona el cliente en el desplegable y aprueba la orden.
    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supermercado Central').last);
    await tester.pumpAndSettle();

    final approveButton = find.widgetWithText(FilledButton, 'Aprobar y enviar a consolidación');
    await tester.ensureVisible(approveButton);
    await tester.pumpAndSettle();
    await tester.tap(approveButton);
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

  testWidgets('consolidation defaults to the most recent date and never mixes dates', (WidgetTester tester) async {
    setupDesktopView(tester);
    final snapshot = _multiDateSnapshot();
    final appState = AppState(service: FakeOrdersApiService(snapshot: snapshot));

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();

    // No existe la opción "Todas las fechas": la fecha siempre viene seleccionada.
    expect(find.text('Todas las fechas'), findsNothing);

    // La fecha más reciente (12/08) está activa por defecto: las dos rutas de
    // esa fecha se ven juntas y el grupo de la fecha anterior (10/08) no.
    expect(find.textContaining('Ruta R1'), findsOneWidget);
    expect(find.textContaining('Ruta R2'), findsOneWidget);
    expect(find.text('10 unidades'), findsNothing);
    expect(find.text('12 unidades'), findsOneWidget);
  });

  testWidgets('changing the delivery date updates routes and totals without mixing', (WidgetTester tester) async {
    setupDesktopView(tester);
    final snapshot = _multiDateSnapshot();
    final appState = AppState(service: FakeOrdersApiService(snapshot: snapshot));

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Consolidación')));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<DateTime>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Aug 10, 2026').last);
    await tester.pumpAndSettle();

    // Solo existe la ruta R1 en la fecha anterior; R2 y sus unidades desaparecen.
    expect(find.textContaining('Ruta R1'), findsOneWidget);
    expect(find.textContaining('Ruta R2'), findsNothing);
    expect(find.text('10 unidades'), findsWidgets);
  });

  testWidgets('configuration lists processed PDFs and clears the session after confirmation', (WidgetTester tester) async {
    setupDesktopView(tester);
    final fakeService = FakeOrdersApiService();
    final appState = AppState(service: fakeService);

    await tester.pumpWidget(PurchaseOrderApp(appState: appState));
    await tester.pumpAndSettle();

    await tester.tap(find.descendant(of: find.byType(NavigationRail), matching: find.text('Configuración')));
    await tester.pumpAndSettle();

    expect(find.text('PDFs procesados'), findsOneWidget);
    expect(find.text('review_doc.pdf'), findsWidgets);

    // Cancelar conserva la sesión.
    await tester.tap(find.widgetWithText(OutlinedButton, 'Vaciar data'));
    await tester.pumpAndSettle();
    expect(find.text('¿Vaciar la sesión?'), findsOneWidget);
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
    expect(find.text('review_doc.pdf'), findsWidgets);
    expect(appState.documents, isNotEmpty);

    // Confirmar vacía la sesión pero conserva lo persistido en el backend.
    await tester.tap(find.widgetWithText(OutlinedButton, 'Vaciar data'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Vaciar'));
    await tester.pumpAndSettle();

    expect(find.text('Aún no se procesaron PDFs'), findsOneWidget);
    expect(find.text('review_doc.pdf'), findsNothing);
    expect(appState.snapshot.sessionDocuments, isEmpty);
    expect(appState.persistedOrders, isNotEmpty);
  });
}

OverviewSnapshot _multiDateSnapshot() {
  ProcessedDocumentView doc(String file, String route, DateTime date, int qty) {
    return ProcessedDocumentView(
      sourceFilename: file,
      parserId: 'p1',
      documentType: 'po',
      status: OrderProcessingStatus.processed,
      customerName: 'Cliente X',
      routeCode: route,
      deliveryDate: date,
      reasons: const [],
      items: [OrderLineView(description: 'Pan Pepin Blanco', quantity: qty)],
    );
  }

  return OverviewSnapshot(
    persistedOrders: const [],
    sessionDocuments: [
      doc('older.pdf', 'R1', DateTime(2026, 8, 10), 10),
      doc('recent_r1.pdf', 'R1', DateTime(2026, 8, 12), 5),
      doc('recent_r2.pdf', 'R2', DateTime(2026, 8, 12), 7),
    ],
    usingDemoData: false,
    bannerMessage: 'Multi-fecha para testing',
  );
}
