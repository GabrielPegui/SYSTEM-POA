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
  });

  group('OrdersApiService', () {
    test('loadOverview parses persisted orders on success', () async {
      final mockHttpClient = MockClient((request) async {
        final body = jsonEncode([
          {
            'id': 10,
            'order_number': '4117171895',
            'customer_code': 'CL000002',
            'customer_name': 'JUMBO HIGUEY',
            'route_code': 'PPN403',
            'delivery_date': '2026-08-12',
            'status': 'processed',
            'items': [
              {
                'product_code': '02010101',
                'product_description': 'PEPIN PAN HOT DOG 8/1',
                'quantity': 27,
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
    });

    test('loadOverview falls back to demo snapshot on network error', () async {
      final mockHttpClient = MockClient((request) async {
        return http.Response('Server error', 500);
      });

      final service = OrdersApiService(apiClient: ApiClient(client: mockHttpClient));
      final snapshot = await service.loadOverview();

      expect(snapshot.usingDemoData, isTrue);
      expect(snapshot.persistedOrders, isNotEmpty);
    });
  });
}
