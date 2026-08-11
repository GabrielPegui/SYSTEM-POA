import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:purchase_order_frontend/core/errors/failures.dart';
import 'package:purchase_order_frontend/core/network/api_client.dart';
import 'package:purchase_order_frontend/core/services/orders_api_service.dart';

void main() {
  group('ApiClient', () {
    test('returns response when status code is 200', () async {
      final mockHttpClient = MockClient((request) async {
        expect(request.url.path, '/orders');
        return http.Response(jsonEncode([]), 200);
      });

      final apiClient = ApiClient(client: mockHttpClient);
      final response = await apiClient.get('/orders');
      expect(response.statusCode, 200);
    });

    test('throws ServerFailure when status code >= 400', () async {
      final mockHttpClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Not found'}), 404);
      });

      final apiClient = ApiClient(client: mockHttpClient);
      expect(
        () => apiClient.get('/orders/nonexistent'),
        throwsA(isA<ServerFailure>()),
      );
    });

    test('sends PUT requests with the expected path and method', () async {
      final mockHttpClient = MockClient((request) async {
        expect(request.method, 'PUT');
        expect(request.url.path, '/orders/ORD-1/validate');
        return http.Response(jsonEncode({}), 200);
      });

      final apiClient = ApiClient(client: mockHttpClient);
      final response = await apiClient.put('/orders/ORD-1/validate');
      expect(response.statusCode, 200);
    });
  });

  group('OrdersApiService', () {
    test('loadOverview parses persisted orders on success', () async {
      final mockHttpClient = MockClient((request) async {
        final body = jsonEncode([
          {
            'id': 10,
            'order_number': '4117171895',
            'customer_name': 'JUMBO HIGUEY',
            'route_code': 'PPN403',
            'delivery_date': '2026-08-12',
            'status': 'processed',
            'items': [
              {
                'description': 'PEPIN PAN HOT DOG 8/1',
                'quantity': 27,
                'pdf_code': '7461012345670',
              }
            ],
          }
        ]);
        return http.Response(body, 200);
      });

      final service = OrdersApiService(apiClient: ApiClient(client: mockHttpClient));
      final snapshot = await service.loadOverview();

      expect(snapshot.usingDemoData, isFalse);
      expect(snapshot.persistedOrders, hasLength(1));
      expect(snapshot.persistedOrders.first.orderNumber, '4117171895');
      expect(snapshot.persistedOrders.first.customerName, 'JUMBO HIGUEY');
      expect(snapshot.persistedOrders.first.items.single.description, 'PEPIN PAN HOT DOG 8/1');
    });

    test('loadOverview falls back to demo snapshot on network error', () async {
      final mockHttpClient = MockClient((request) async {
        return http.Response('Server error', 500);
      });

      final service = OrdersApiService(apiClient: ApiClient(client: mockHttpClient));
      final snapshot = await service.loadOverview();

      expect(snapshot.usingDemoData, isTrue);
      expect(snapshot.persistedOrders, isNotEmpty);
      expect(snapshot.sessionDocuments, isNotEmpty);
      expect(snapshot.documents.any((doc) => doc.routeCode == '200'), isTrue);
    });

    test('validateOrder hits the validate endpoint without a body', () async {
      final mockHttpClient = MockClient((request) async {
        expect(request.method, 'PUT');
        expect(request.url.path, '/orders/ORD-42/validate');
        expect(request.body, isEmpty);
        return http.Response(jsonEncode({}), 200);
      });

      final service = OrdersApiService(apiClient: ApiClient(client: mockHttpClient));
      await service.validateOrder('ORD-42');
    });
  });
}
