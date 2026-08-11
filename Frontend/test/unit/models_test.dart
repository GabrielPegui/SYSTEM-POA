import 'package:flutter_test/flutter_test.dart';
import 'package:purchase_order_frontend/core/models/orders_models.dart';

void main() {
  group('OrderProcessingStatusX', () {
    test('parses API status strings correctly', () {
      expect(OrderProcessingStatusX.fromApi('processed'), OrderProcessingStatus.processed);
      expect(OrderProcessingStatusX.fromApi('review_required'), OrderProcessingStatus.reviewRequired);
      expect(OrderProcessingStatusX.fromApi('no_match'), OrderProcessingStatus.noMatch);
      expect(OrderProcessingStatusX.fromApi('error'), OrderProcessingStatus.error);
      expect(OrderProcessingStatusX.fromApi('invalid'), OrderProcessingStatus.unknown);
      expect(OrderProcessingStatusX.fromApi(null), OrderProcessingStatus.unknown);
    });

    test('returns correct user-facing labels', () {
      expect(OrderProcessingStatus.processed.label, 'Procesada');
      expect(OrderProcessingStatus.reviewRequired.label, 'Requiere revisión');
      expect(OrderProcessingStatus.noMatch.label, 'Sin coincidencia');
      expect(OrderProcessingStatus.error.label, 'Error');
      expect(OrderProcessingStatus.unknown.label, 'Desconocido');
    });
  });

  group('OrderLineView', () {
    test('parses processed line JSON with complete data', () {
      final json = {
        'description': 'PAN PEPIN BLANCO 24/1',
        'quantity': 50,
        'pdf_code': '7461234567890',
        'ean': '07461234567890',
      };

      final line = OrderLineView.fromProcessedJson(json);
      expect(line.description, 'PAN PEPIN BLANCO 24/1');
      expect(line.quantity, 50);
      expect(line.pdfCode, '7461234567890');
      expect(line.ean, '07461234567890');
    });

    test('handles missing or nullable fields gracefully', () {
      final json = <String, dynamic>{};
      final line = OrderLineView.fromProcessedJson(json);
      expect(line.description, '');
      expect(line.quantity, 0);
      expect(line.pdfCode, isNull);
      expect(line.ean, isNull);
    });
  });

  group('OrderListView', () {
    test('parses delivery_date into nullable DateTime', () {
      final json = {
        'id': 1,
        'order_number': 'ORD-1',
        'customer_name': 'Cliente A',
        'route_code': 'R01',
        'delivery_date': '2026-08-15',
        'status': 'processed',
        'items': <Map<String, dynamic>>[],
      };

      final order = OrderListView.fromJson(json);
      expect(order.deliveryDate, DateTime(2026, 8, 15));
    });

    test('deliveryDate is null when delivery_date is missing or invalid', () {
      final json = {
        'id': 2,
        'order_number': 'ORD-2',
        'customer_name': 'Cliente B',
        'route_code': 'R02',
        'status': 'review_required',
        'items': <Map<String, dynamic>>[],
      };

      final order = OrderListView.fromJson(json);
      expect(order.deliveryDate, isNull);

      final invalid = OrderListView.fromJson({...json, 'delivery_date': 'no-es-una-fecha'});
      expect(invalid.deliveryDate, isNull);
    });

    test('parses items without product codes', () {
      final json = {
        'id': 3,
        'order_number': 'ORD-3',
        'customer_name': 'Cliente C',
        'route_code': 'R03',
        'delivery_date': '2026-08-15',
        'status': 'processed',
        'items': [
          {'description': 'PAN PEPIN HOT DOG 8/1', 'quantity': 27, 'pdf_code': '7461', 'ean': '007461'},
        ],
      };

      final order = OrderListView.fromJson(json);
      expect(order.items, hasLength(1));
      expect(order.items.first.description, 'PAN PEPIN HOT DOG 8/1');
      expect(order.items.first.quantity, 27);
      expect(order.items.first.pdfCode, '7461');
      expect(order.items.first.ean, '007461');
    });
  });

  group('ProcessedDocumentView', () {
    test('parses full ProcessOrderResponse JSON correctly', () {
      final json = {
        'source_filename': 'orden_123.pdf',
        'parser_id': 'sirena_v1',
        'document_type': 'purchase_order',
        'status': 'processed',
        'processed_at': '2026-08-08T15:30:00',
        'order_number': 'ORD-999',
        'delivery_date': '2026-08-12',
        'customer_code': 'CL001',
        'customer_name': 'SUPERMERCADO NACIONAL',
        'route_code': 'PPN101',
        'route_reason': 'Matched via customer default route',
        'reasons': ['Valid order'],
        'items': [
          {
            'description': 'PAN PEPIN HOT DOG 8/1',
            'quantity': 100,
            'pdf_code': '7461123456',
          }
        ],
      };

      final doc = ProcessedDocumentView.fromJson(json);
      expect(doc.sourceFilename, 'orden_123.pdf');
      expect(doc.parserId, 'sirena_v1');
      expect(doc.status, OrderProcessingStatus.processed);
      expect(doc.orderNumber, 'ORD-999');
      expect(doc.customerCode, 'CL001');
      expect(doc.customerName, 'SUPERMERCADO NACIONAL');
      expect(doc.routeCode, 'PPN101');
      expect(doc.items, hasLength(1));
      expect(doc.items.first.quantity, 100);
    });
  });

  group('OverviewSnapshot & Consolidation', () {
    test('calculates correct state metrics', () {
      final snapshot = OverviewSnapshot(
        persistedOrders: const [],
        sessionDocuments: [
          ProcessedDocumentView(
            sourceFilename: 'a.pdf',
            parserId: 'p1',
            documentType: 'po',
            status: OrderProcessingStatus.processed,
            items: const [],
            reasons: const [],
          ),
          ProcessedDocumentView(
            sourceFilename: 'b.pdf',
            parserId: 'p1',
            documentType: 'po',
            status: OrderProcessingStatus.reviewRequired,
            items: const [],
            reasons: const ['No customer match'],
          ),
          ProcessedDocumentView(
            sourceFilename: 'c.pdf',
            parserId: 'p1',
            documentType: 'po',
            status: OrderProcessingStatus.error,
            items: const [],
            reasons: const ['Corrupted PDF'],
          ),
        ],
        usingDemoData: false,
        bannerMessage: '',
      );

      expect(snapshot.processedCount, 1);
      expect(snapshot.reviewRequiredCount, 1);
      expect(snapshot.errorCount, 1);
      expect(snapshot.totalIncoming, 3);
    });

    test('consolidates processed documents across perspectives', () {
      final doc1 = ProcessedDocumentView(
        sourceFilename: 'doc1.pdf',
        parserId: 'p1',
        documentType: 'po',
        status: OrderProcessingStatus.processed,
        customerCode: 'C1',
        customerName: 'Cliente A',
        routeCode: 'R01',
        deliveryDate: DateTime(2026, 8, 12),
        reasons: const [],
        items: const [
          OrderLineView(
            description: 'Pan Pepin 8/1',
            quantity: 30,
          ),
        ],
      );

      final doc2 = ProcessedDocumentView(
        sourceFilename: 'doc2.pdf',
        parserId: 'p1',
        documentType: 'po',
        status: OrderProcessingStatus.processed,
        customerCode: 'C2',
        customerName: 'Cliente B',
        routeCode: 'R01',
        deliveryDate: DateTime(2026, 8, 12),
        reasons: const [],
        items: const [
          OrderLineView(
            description: 'Pan Pepin 8/1',
            quantity: 20,
          ),
        ],
      );

      final snapshot = OverviewSnapshot(
        persistedOrders: const [],
        sessionDocuments: [doc1, doc2],
        usingDemoData: false,
        bannerMessage: '',
      );

      // By Product
      final byProd = snapshot.consolidateByProduct();
      expect(byProd.containsKey('pan pepin 8/1'), isTrue);
      expect(byProd['pan pepin 8/1']!.totalQuantity, 50);
      expect(byProd['pan pepin 8/1']!.customers, containsAll(['Cliente A', 'Cliente B']));
      expect(byProd['pan pepin 8/1']!.routes, contains('R01'));

      // By Customer
      final byCust = snapshot.consolidateByCustomer();
      expect(byCust.keys, containsAll(['C1', 'C2']));
      expect(byCust['C1']!.totalQuantity, 30);
      expect(byCust['C2']!.totalQuantity, 20);

      // By Route
      final byRoute = snapshot.consolidateByRoute();
      expect(byRoute.containsKey('R01'), isTrue);
      expect(byRoute['R01']!.totalQuantity, 50);

      // By Route + Date
      final groups = snapshot.consolidateByRouteAndDate();
      expect(groups, hasLength(1));
      final group = groups.single;
      expect(group.routeCode, 'R01');
      expect(group.deliveryDate, DateTime(2026, 8, 12));
      expect(group.customers, hasLength(2));
      expect(group.totalQuantity, 50);
      expect(group.orderCount, 2);
      final productTotal = group.productTotals.single;
      expect(productTotal.productLabel, 'Pan Pepin 8/1');
      expect(productTotal.quantity, 50);
    });

    test('route+date consolidation breaks down per customer with totals', () {
      ProcessedDocumentView doc(String file, String customer, List<OrderLineView> items) {
        return ProcessedDocumentView(
          sourceFilename: file,
          parserId: 'p1',
          documentType: 'po',
          status: OrderProcessingStatus.processed,
          customerName: customer,
          routeCode: '200',
          deliveryDate: DateTime(2026, 8, 12),
          reasons: const [],
          items: items,
        );
      }

      final snapshot = OverviewSnapshot(
        persistedOrders: const [],
        sessionDocuments: [
          doc('a.pdf', 'Cliente A', const [
            OrderLineView(description: 'Pan', quantity: 20),
            OrderLineView(description: 'Queso', quantity: 10),
            OrderLineView(description: 'Limón', quantity: 5),
          ]),
          doc('b.pdf', 'Cliente B', const [
            OrderLineView(description: 'Pan', quantity: 20),
            OrderLineView(description: 'Queso', quantity: 15),
          ]),
        ],
        usingDemoData: false,
        bannerMessage: '',
      );

      final groups = snapshot.consolidateByRouteAndDate();
      expect(groups, hasLength(1));
      final group = groups.single;

      final totals = {for (final p in group.productTotals) p.productLabel: p.quantity};
      expect(totals, {'Pan': 40, 'Queso': 25, 'Limón': 5});
      expect(group.totalQuantity, 70);
      expect(group.customers, hasLength(2));

      final customerA = group.customers.singleWhere((c) => c.customerName == 'Cliente A');
      expect(customerA.totalQuantity, 35);
      expect(customerA.orderCount, 1);
    });

    test('counts each order once across session documents and persisted orders', () {
      final sessionDoc = ProcessedDocumentView(
        sourceFilename: 'a.pdf',
        parserId: 'p1',
        documentType: 'po',
        status: OrderProcessingStatus.processed,
        orderNumber: 'ORD-1',
        customerName: 'Cliente A',
        routeCode: 'R1',
        deliveryDate: DateTime(2026, 8, 12),
        reasons: const [],
        items: const [OrderLineView(description: 'Pan', quantity: 10)],
      );
      final persistedOrder = OrderListView(
        id: 1,
        orderNumber: 'ORD-1',
        customerName: 'Cliente A',
        routeCode: 'R1',
        deliveryDate: DateTime(2026, 8, 12),
        status: 'processed',
        items: const [OrderItemView(description: 'Pan', quantity: 10)],
      );

      final snapshot = OverviewSnapshot(
        persistedOrders: [persistedOrder],
        sessionDocuments: [sessionDoc],
        usingDemoData: false,
        bannerMessage: '',
      );

      expect(snapshot.documents, hasLength(1));
      final group = snapshot.consolidateByRouteAndDate().single;
      expect(group.totalQuantity, 10);
      expect(group.orderCount, 1);
      expect(group.customers.single.orderCount, 1);
    });

    test('the same route splits into separate groups per delivery date', () {
      ProcessedDocumentView doc(String file, DateTime date, int qty) {
        return ProcessedDocumentView(
          sourceFilename: file,
          parserId: 'p1',
          documentType: 'po',
          status: OrderProcessingStatus.processed,
          customerName: 'Cliente X',
          routeCode: 'R1',
          deliveryDate: date,
          reasons: const [],
          items: [OrderLineView(description: 'Pan', quantity: qty)],
        );
      }

      final snapshot = OverviewSnapshot(
        persistedOrders: const [],
        sessionDocuments: [
          doc('older.pdf', DateTime(2026, 8, 10), 10),
          doc('recent.pdf', DateTime(2026, 8, 12), 5),
        ],
        usingDemoData: false,
        bannerMessage: '',
      );

      final groups = snapshot.consolidateByRouteAndDate();
      expect(groups, hasLength(2));
      final groupsByDate = {
        for (final g in groups) g.deliveryDate: g,
      };
      expect(groupsByDate[DateTime(2026, 8, 12)]!.totalQuantity, 5);
      expect(groupsByDate[DateTime(2026, 8, 10)]!.totalQuantity, 10);
    });

    test('two routes on the same delivery date stay in separate route groups', () {
      ProcessedDocumentView doc(String file, String route, int qty) {
        return ProcessedDocumentView(
          sourceFilename: file,
          parserId: 'p1',
          documentType: 'po',
          status: OrderProcessingStatus.processed,
          customerName: 'Cliente X',
          routeCode: route,
          deliveryDate: DateTime(2026, 8, 12),
          reasons: const [],
          items: [OrderLineView(description: 'Pan', quantity: qty)],
        );
      }

      final snapshot = OverviewSnapshot(
        persistedOrders: const [],
        sessionDocuments: [
          doc('r1.pdf', 'R1', 5),
          doc('r2.pdf', 'R2', 7),
        ],
        usingDemoData: false,
        bannerMessage: '',
      );

      final groups = snapshot.consolidateByRouteAndDate();
      expect(groups, hasLength(2));
      final totals = {
        for (final g in groups) g.routeCode: g.totalQuantity,
      };
      expect(totals, {'R1': 5, 'R2': 7});
    });
  });
}
