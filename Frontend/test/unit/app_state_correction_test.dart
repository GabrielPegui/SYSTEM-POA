import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:purchase_order_frontend/core/models/orders_models.dart';
import 'package:purchase_order_frontend/core/services/orders_api_service.dart';
import 'package:purchase_order_frontend/core/state/app_state.dart';

class StubCorrectionService extends OrdersApiService {
  StubCorrectionService({this.onValidate, this.orderNumber});

  final Future<void> Function(String orderNumber)? onValidate;
  final String? orderNumber;

  @override
  Future<OverviewSnapshot> loadOverview() async {
    return OverviewSnapshot.empty;
  }

  @override
  Future<ProcessedDocumentView> processPdfBytes({
    required Uint8List bytes,
    required String filename,
  }) {
    return Future.value(
      ProcessedDocumentView(
        sourceFilename: filename,
        parserId: 'test',
        documentType: 'po',
        status: OrderProcessingStatus.reviewRequired,
        orderNumber: orderNumber,
        reasons: const ['Cliente con varias rutas posibles'],
        items: const [
          OrderLineView(
            description: 'PAN PEPIN HOT DOG 8/1',
            quantity: 30,
            matchStatus: 'review_required',
          ),
        ],
      ),
    );
  }

  @override
  Future<ProcessedDocumentView> processPdfPath(String path) {
    return processPdfBytes(bytes: Uint8List.fromList([1]), filename: path);
  }

  @override
  Future<void> validateOrder(String orderNumber) {
    final callback = onValidate;
    if (callback != null) {
      return callback(orderNumber);
    }
    return Future.value();
  }
}

void main() {
  group('AppState.applyCorrection', () {
    test('marks a reviewed document as processed and keeps it in session', () async {
      final state = AppState(service: StubCorrectionService());

      await state.processFiles([
        _file('orden_revision.pdf'),
      ]);

      final before = state.reviewQueue.single;
      expect(before.status, OrderProcessingStatus.reviewRequired);

      await state.applyCorrection(
        before,
        customerName: 'SUPERMERCADO CENTRAL',
        routeCode: 'PPN101',
        deliveryDate: DateTime(2026, 8, 12),
      );

      expect(state.reviewQueue, isEmpty);
      expect(state.processedDocuments, hasLength(1));
      final corrected = state.processedDocuments.single;
      expect(corrected.sourceFilename, 'orden_revision.pdf');
      expect(corrected.status, OrderProcessingStatus.processed);
      expect(corrected.customerName, 'SUPERMERCADO CENTRAL');
      expect(corrected.routeCode, 'PPN101');
      expect(corrected.deliveryDate, DateTime(2026, 8, 12));
      expect(corrected.reasons, isEmpty);
      expect(state.selectedDocument?.sourceFilename, 'orden_revision.pdf');
    });

    test('corrections reflect in consolidation', () async {
      final state = AppState(service: StubCorrectionService());

      await state.processFiles([
        _file('orden_revision.pdf'),
      ]);

      await state.applyCorrection(
        state.reviewQueue.single,
        customerName: 'SUPERMERCADO CENTRAL',
        routeCode: 'PPN101',
      );

      final byCustomer = state.consolidatedByCustomer;
      expect(byCustomer, hasLength(1));
      expect(byCustomer.single.label, 'SUPERMERCADO CENTRAL');
      expect(byCustomer.single.routes, contains('PPN101'));
      expect(byCustomer.single.totalQuantity, 30);
    });

    test('editing quantities updates the consolidated totals', () async {
      final state = AppState(service: StubCorrectionService());

      await state.processFiles([
        _file('orden_revision.pdf'),
      ]);

      await state.applyCorrection(
        state.reviewQueue.single,
        customerName: 'SUPERMERCADO CENTRAL',
        routeCode: 'PPN101',
        correctedItems: const [
          OrderLineView(
            description: 'PAN PEPIN HOT DOG 8/1',
            quantity: 45,
            matchStatus: 'matched',
          ),
        ],
      );

      expect(state.consolidatedByProduct.single.totalQuantity, 45);
    });

    test('trims whitespace and falls back to previous customer name', () async {
      final state = AppState(service: StubCorrectionService());

      await state.processFiles([
        _file('orden_revision.pdf'),
      ]);

      await state.applyCorrection(
        state.reviewQueue.single,
        customerName: '   ',
        routeCode: '  PPN999  ',
      );

      final corrected = state.processedDocuments.single;
      expect(corrected.customerName, isNull);
      expect(corrected.routeCode, 'PPN999');
    });

    test('notifies backend when the document has an order number', () async {
      final validated = <String>[];
      final state = AppState(
        service: StubCorrectionService(
          onValidate: (orderNumber) async {
            validated.add(orderNumber);
          },
          orderNumber: 'ORD-123',
        ),
      );

      await state.processFiles([
        _file('con_numero.pdf'),
      ]);

      await state.applyCorrection(
        state.reviewQueue.single,
        customerName: 'CLIENTE A',
      );

      expect(validated, ['ORD-123']);
    });

    test('keeps the local correction when backend validation fails', () async {
      final state = AppState(
        service: StubCorrectionService(
          onValidate: (orderNumber) async {
            throw Exception('Servidor no disponible');
          },
          orderNumber: 'ORD-123',
        ),
      );

      await state.processFiles([
        _file('con_numero.pdf'),
      ]);

      await state.applyCorrection(
        state.reviewQueue.single,
        customerName: 'CLIENTE A',
      );

      expect(state.processedDocuments, hasLength(1));
      expect(state.processedDocuments.single.customerName, 'CLIENTE A');
    });
  });
}

PlatformFile _file(String name) {
  return PlatformFile(name: name, size: 1, bytes: Uint8List.fromList([1]));
}
