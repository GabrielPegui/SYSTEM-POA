import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../errors/failures.dart';
import '../models/orders_models.dart';
import '../network/api_client.dart';

class OrdersApiService {
  OrdersApiService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<OverviewSnapshot> loadOverview() async {
    try {
      final response = await _apiClient.get('/orders');
      final decoded = jsonDecode(response.body);
      final persistedOrders = [
        for (final item in (decoded as List<dynamic>))
          OrderListView.fromJson(Map<String, dynamic>.from(item as Map)),
      ];
      return OverviewSnapshot(
        persistedOrders: persistedOrders,
        sessionDocuments: const <ProcessedDocumentView>[],
        usingDemoData: false,
        bannerMessage: 'Datos reales cargados desde el backend',
      );
    } on Failure catch (error) {
      return _demoSnapshot(
        'No pudimos conectar con el servidor (${error.message}). '
        'Mostrando datos de demostración para revisar la interfaz.',
      );
    } catch (error) {
      return _demoSnapshot(
        'No pudimos conectar con el servidor ($error). '
        'Mostrando datos de demostración para revisar la interfaz.',
      );
    }
  }

  Future<ProcessedDocumentView> processPdfBytes({
    required Uint8List bytes,
    required String filename,
  }) async {
    if (bytes.isEmpty) {
      throw const UnknownFailure('El archivo PDF está vacío.');
    }

    final response = await _apiClient.postMultipart(
      '/orders/process',
      files: [
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename.isEmpty ? 'document.pdf' : filename,
        ),
      ],
    );
    final decoded = jsonDecode(response.body);
    return ProcessedDocumentView.fromJson(
      Map<String, dynamic>.from(decoded as Map),
      receivedAt: DateTime.now(),
    );
  }

  Future<ProcessedDocumentView> processPdfPath(String filePath) async {
    final file = File(filePath);
    if (!file.existsSync()) {
      throw UnknownFailure('El archivo no existe: $filePath');
    }
    final bytes = await file.readAsBytes();
    final filename = file.path.split(RegExp(r'[/\\]')).last;
    return processPdfBytes(bytes: bytes, filename: filename);
  }

  /// Marca una orden como validada tras la revisión humana.
  ///
  /// El backend solo expone ``PUT /orders/{order_number}/validate`` sin cuerpo:
  /// no persiste correcciones de campos. La corrección local se conserva en la
  /// sesión del frontend; la persistencia real de campos corregidos queda
  /// pendiente de capacidad backend.
  Future<void> validateOrder(String orderNumber) async {
    await _apiClient.put('/orders/$orderNumber/validate');
  }

  OverviewSnapshot _demoSnapshot(String message) {
    final persistedOrders = [
      OrderListView(
        id: 1,
        orderNumber: '4117171895',
        customerName: 'JUMBO HIGUEY',
        routeCode: 'PPN403',
        deliveryDate: DateTime(2026, 8, 12),
        status: 'processed',
        items: const [
          OrderItemView(
            description: 'PEPIN PAN HOT DOG 8/1',
            quantity: 27,
            pdfCode: '7461012345670',
          ),
        ],
      ),
      OrderListView(
        id: 2,
        orderNumber: '3846637',
        customerName: 'OPERADORA WESTPARK, SAS',
        routeCode: 'PPN001',
        deliveryDate: DateTime(2026, 8, 11),
        status: 'processed',
        items: const [
          OrderItemView(
            description: 'PEPIN VIGA MEDIANA BLANCO',
            quantity: 180,
            pdfCode: '7461012345687',
          ),
        ],
      ),
    ];

    return OverviewSnapshot(
      persistedOrders: persistedOrders,
      sessionDocuments: _demoSessionDocuments,
      usingDemoData: true,
      bannerMessage: message,
    );
  }

  /// Documentos de demostración que ilustran la consolidación Ruta + Fecha.
  ///
  /// Ruta 200 con entrega 12/08/2026: CLIENTE A pide Pan 20 / Queso 10 / Limón
  /// 5 y CLIENTE B pide Pan 20 / Queso 15, dejando totales Pan 40, Queso 25,
  /// Limón 5 y un total general de 70 unidades.
  static final List<ProcessedDocumentView> _demoSessionDocuments = [
    ProcessedDocumentView(
      sourceFilename: 'ruta_200_12ago_cliente_a.pdf',
      parserId: 'demo',
      documentType: 'purchase_order',
      status: OrderProcessingStatus.processed,
      orderNumber: 'DEMO-A-200',
      customerCode: 'CL-A',
      customerName: 'CLIENTE A',
      routeCode: '200',
      deliveryDate: DateTime(2026, 8, 12),
      routeReason: 'Ruta por defecto del cliente',
      reasons: const [],
      items: const [
        OrderLineView(description: 'PAN PEPIN 24/1', quantity: 20, pdfCode: '750101010001'),
        OrderLineView(description: 'QUESO CREMA 500G', quantity: 10, pdfCode: '750101010002'),
        OrderLineView(description: 'LIMON DE MESA', quantity: 5, pdfCode: '750101010003'),
      ],
      receivedAt: DateTime(2026, 8, 10, 9, 15),
    ),
    ProcessedDocumentView(
      sourceFilename: 'ruta_200_12ago_cliente_b.pdf',
      parserId: 'demo',
      documentType: 'purchase_order',
      status: OrderProcessingStatus.processed,
      orderNumber: 'DEMO-B-200',
      customerCode: 'CL-B',
      customerName: 'CLIENTE B',
      routeCode: '200',
      deliveryDate: DateTime(2026, 8, 12),
      routeReason: 'Ruta por defecto del cliente',
      reasons: const [],
      items: const [
        OrderLineView(description: 'PAN PEPIN 24/1', quantity: 20, pdfCode: '750101010004'),
        OrderLineView(description: 'QUESO CREMA 500G', quantity: 15, pdfCode: '750101010005'),
      ],
      receivedAt: DateTime(2026, 8, 10, 9, 18),
    ),
  ];
}
