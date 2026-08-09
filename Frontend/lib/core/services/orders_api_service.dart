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

  OverviewSnapshot _demoSnapshot(String message) {
    final persistedOrders = [
      OrderListView(
        id: 1,
        orderNumber: '4117171895',
        customerCode: 'CL000002-009',
        customerName: 'JUMBO HIGUEY',
        routeCode: 'PPN403',
        deliveryDate: DateTime(2026, 8, 12),
        status: 'processed',
        items: const [
          OrderItemView(
            productCode: '02010101',
            productDescription: 'PEPIN PAN HOT DOG 8/1',
            quantity: 27,
          ),
        ],
      ),
      OrderListView(
        id: 2,
        orderNumber: '3846637',
        customerCode: 'CL001686',
        customerName: 'OPERADORA WESTPARK, SAS',
        routeCode: 'PPN001',
        deliveryDate: DateTime(2026, 8, 11),
        status: 'processed',
        items: const [
          OrderItemView(
            productCode: '01010101',
            productDescription: 'PEPIN VIGA MEDIANA BLANCO',
            quantity: 180,
          ),
        ],
      ),
    ];

    return OverviewSnapshot(
      persistedOrders: persistedOrders,
      sessionDocuments: const <ProcessedDocumentView>[],
      usingDemoData: true,
      bannerMessage: message,
    );
  }
}
