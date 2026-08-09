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
        'match_status': 'exact_match',
        'product_code': '01010101',
        'product_description': 'PEPIN VIGA MEDIANA BLANCO',
        'confidence': 0.98,
        'reason': 'Exact match',
        'candidates': [
          {'code': '01010101', 'description': 'PEPIN VIGA MEDIANA BLANCO'}
        ],
      };

      final line = OrderLineView.fromProcessedJson(json);
      expect(line.description, 'PAN PEPIN BLANCO 24/1');
      expect(line.quantity, 50);
      expect(line.pdfCode, '7461234567890');
      expect(line.matchStatus, 'exact_match');
      expect(line.productCode, '01010101');
      expect(line.productDescription, 'PEPIN VIGA MEDIANA BLANCO');
      expect(line.confidence, 0.98);
      expect(line.reason, 'Exact match');
      expect(line.candidates, hasLength(1));
      expect(line.candidates.first, contains('01010101'));
    });

    test('handles missing or nullable fields gracefully', () {
      final json = <String, dynamic>{};
      final line = OrderLineView.fromProcessedJson(json);
      expect(line.description, '');
      expect(line.quantity, 0);
      expect(line.productCode, isNull);
      expect(line.confidence, isNull);
      expect(line.candidates, isEmpty);
    });
  });

  group('OrderListView', () {
    test('parses delivery_date into nullable DateTime', () {
      final json = {
        'id': 1,
        'order_number': 'ORD-1',
        'customer_code': 'CL001',
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
        'customer_code': 'CL002',
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
            'match_status': 'matched',
            'product_code': '02010101',
            'product_description': 'PEPIN PAN HOT DOG 8/1',
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

    test('consolidates processed documents across 4 perspectives', () {
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
            matchStatus: 'matched',
            productCode: 'P01',
            productDescription: 'Pan Pepin 8/1',
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
            matchStatus: 'matched',
            productCode: 'P01',
            productDescription: 'Pan Pepin 8/1',
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
      expect(byProd.containsKey('P01'), isTrue);
      expect(byProd['P01']!.totalQuantity, 50);
      expect(byProd['P01']!.customers, containsAll(['Cliente A', 'Cliente B']));
      expect(byProd['P01']!.routes, contains('R01'));

      // By Customer
      final byCust = snapshot.consolidateByCustomer();
      expect(byCust.keys, containsAll(['C1', 'C2']));
      expect(byCust['C1']!.totalQuantity, 30);
      expect(byCust['C2']!.totalQuantity, 20);

      // By Route
      final byRoute = snapshot.consolidateByRoute();
      expect(byRoute.containsKey('R01'), isTrue);
      expect(byRoute['R01']!.totalQuantity, 50);

      // By Date
      final byDate = snapshot.consolidateByDate();
      expect(byDate.containsKey('2026-08-12'), isTrue);
      expect(byDate['2026-08-12']!.totalQuantity, 50);
    });
  });
}
