import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:purchase_order_frontend/app.dart';

void main() {
  testWidgets('app boots and shows the initial screen', (WidgetTester tester) async {
    await tester.pumpWidget(const PurchaseOrderApp());
    await tester.pumpAndSettle();

    expect(find.text('Procesamiento de órdenes'), findsOneWidget);
    expect(find.byType(NavigationRail), findsOneWidget);
  });

  testWidgets('navigation rail switches between features', (WidgetTester tester) async {
    await tester.pumpWidget(const PurchaseOrderApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Historial'));
    await tester.pumpAndSettle();

    expect(find.text('Historial'), findsNWidgets(2));
  });
}
