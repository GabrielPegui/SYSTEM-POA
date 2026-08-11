import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:purchase_order_frontend/core/errors/failures.dart';
import 'package:purchase_order_frontend/core/models/orders_models.dart';
import 'package:purchase_order_frontend/core/services/orders_api_service.dart';
import 'package:purchase_order_frontend/core/state/app_state.dart';

/// Servicio fake que permite controlar el resultado de cada archivo procesado.
class StubOrdersApiService extends OrdersApiService {
  StubOrdersApiService(this._handler);

  final Future<ProcessedDocumentView> Function(String filename) _handler;

  @override
  Future<OverviewSnapshot> loadOverview() async {
    return OverviewSnapshot.empty;
  }

  @override
  Future<ProcessedDocumentView> processPdfBytes({
    required Uint8List bytes,
    required String filename,
  }) {
    return _handler(filename);
  }

  @override
  Future<ProcessedDocumentView> processPdfPath(String path) {
    return _handler(path);
  }
}

ProcessedDocumentView _doc(String filename, OrderProcessingStatus status) {
  return ProcessedDocumentView(
    sourceFilename: filename,
    parserId: 'test',
    documentType: 'po',
    status: status,
    items: const [],
    reasons: const [],
  );
}

void main() {
  group('AppState batch processing', () {
    test('empty batch is a no-op and clears progress', () async {
      final service = StubOrdersApiService((_) async => _doc('x.pdf', OrderProcessingStatus.processed));
      final state = AppState(service: service);

      await state.processFiles(const []);
      expect(state.busy, isFalse);
      expect(state.batchTotal, 0);
      expect(state.batchSummary, isNull);
      expect(state.documents, isEmpty);
    });

    test('batch of successful files populates documents and summary', () async {
      final service = StubOrdersApiService(
        (filename) async => _doc(filename, OrderProcessingStatus.processed),
      );
      final state = AppState(service: service);

      final files = [
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'b.pdf', size: 1, bytes: Uint8List.fromList([2])),
        PlatformFile(name: 'c.pdf', size: 1, bytes: Uint8List.fromList([3])),
      ];
      await state.processFiles(files);

      expect(state.busy, isFalse);
      expect(state.batchSummary?.total, 3);
      expect(state.batchSummary?.processed, 3);
      expect(state.batchSummary?.needsAttention, 0);
      expect(state.documents, hasLength(3));
      expect(state.selectedDocument?.sourceFilename, 'c.pdf');
    });

    test('batch reports each status bucket correctly', () async {
      final service = StubOrdersApiService(
        (filename) async => switch (filename) {
          'ok.pdf' => _doc(filename, OrderProcessingStatus.processed),
          'review.pdf' => _doc(filename, OrderProcessingStatus.reviewRequired),
          'nomatch.pdf' => _doc(filename, OrderProcessingStatus.noMatch),
          _ => _doc(filename, OrderProcessingStatus.error),
        },
      );
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'ok.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'review.pdf', size: 1, bytes: Uint8List.fromList([2])),
        PlatformFile(name: 'nomatch.pdf', size: 1, bytes: Uint8List.fromList([3])),
        PlatformFile(name: 'error.pdf', size: 1, bytes: Uint8List.fromList([4])),
      ]);

      expect(state.batchSummary?.total, 4);
      expect(state.batchSummary?.processed, 1);
      expect(state.batchSummary?.reviewRequired, 1);
      expect(state.batchSummary?.noMatch, 1);
      expect(state.batchSummary?.errors, 1);
      expect(state.batchSummary?.needsAttention, 3);
    });

    test('a failing file becomes a visible ERROR document', () async {
      final service = StubOrdersApiService(
        (filename) async {
          if (filename == 'broken.pdf') {
            throw const UnknownFailure('El archivo PDF está corrupto.');
          }
          return _doc(filename, OrderProcessingStatus.processed);
        },
      );
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'ok.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'broken.pdf', size: 1, bytes: Uint8List.fromList([2])),
      ]);

      expect(state.batchSummary?.processed, 1);
      expect(state.batchSummary?.errors, 1);
      final broken = state.documents.where((d) => d.sourceFilename == 'broken.pdf').single;
      expect(broken.status, OrderProcessingStatus.error);
      expect(broken.reasons.single, contains('El archivo PDF está corrupto'));
    });

    test('unreadable file (no bytes, no path) becomes an ERROR document', () async {
      final service = StubOrdersApiService((_) async => _doc('x.pdf', OrderProcessingStatus.processed));
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'nodata.pdf', size: 0),
      ]);

      expect(state.batchSummary?.errors, 1);
      expect(state.documents.single.status, OrderProcessingStatus.error);
    });

    test('re-processing the same filename replaces the session document', () async {
      final service = StubOrdersApiService(
        (filename) async => _doc(filename, OrderProcessingStatus.processed),
      );
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([2])),
      ]);

      expect(state.documents, hasLength(1));
      expect(state.documents.single.sourceFilename, 'a.pdf');
    });

    test('re-importing the same filename replaces its quantities in consolidation', () async {
      var callCount = 0;
      final service = StubOrdersApiService((filename) async {
        callCount++;
        return ProcessedDocumentView(
          sourceFilename: filename,
          parserId: 'test',
          documentType: 'po',
          status: OrderProcessingStatus.processed,
          customerName: 'Cliente A',
          routeCode: 'R1',
          deliveryDate: DateTime(2026, 8, 12),
          reasons: const [],
          items: [OrderLineView(description: 'Pan', quantity: callCount * 10)],
        );
      });
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([2])),
      ]);

      expect(state.documents, hasLength(1));
      final groups = state.consolidatedByRouteAndDate;
      expect(groups, hasLength(1));
      expect(groups.single.totalQuantity, 20);
      expect(groups.single.orderCount, 1);
    });

    test('importing different filenames keeps separate orders and sums quantities', () async {
      final quantities = <String, int>{'a.pdf': 10, 'b.pdf': 20};
      final service = StubOrdersApiService((filename) async {
        return ProcessedDocumentView(
          sourceFilename: filename,
          parserId: 'test',
          documentType: 'po',
          status: OrderProcessingStatus.processed,
          customerName: 'Cliente A',
          routeCode: 'R1',
          deliveryDate: DateTime(2026, 8, 12),
          reasons: const [],
          items: [OrderLineView(description: 'Pan', quantity: quantities[filename]!)],
        );
      });
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'b.pdf', size: 1, bytes: Uint8List.fromList([2])),
      ]);

      expect(state.documents, hasLength(2));
      final groups = state.consolidatedByRouteAndDate;
      expect(groups, hasLength(1));
      expect(groups.single.totalQuantity, 30);
      expect(groups.single.orderCount, 2);
    });

    test('clearing the session empties documents but keeps persisted orders', () async {
      final service = StubOrdersApiService(
        (filename) async => _doc(filename, OrderProcessingStatus.processed),
      );
      final state = AppState(service: service);

      await state.processFiles([
        PlatformFile(name: 'a.pdf', size: 1, bytes: Uint8List.fromList([1])),
        PlatformFile(name: 'b.pdf', size: 1, bytes: Uint8List.fromList([2])),
      ]);

      expect(state.documents, hasLength(2));

      state.clearSession();

      expect(state.documents, isEmpty);
      expect(state.snapshot.sessionDocuments, isEmpty);
      expect(state.selectedDocument, isNull);
      expect(state.batchSummary, isNull);
    });
  });
}
