import 'package:flutter/material.dart';

enum OrderProcessingStatus {
  processed,
  reviewRequired,
  noMatch,
  error,
  unknown,
}

extension OrderProcessingStatusX on OrderProcessingStatus {
  static OrderProcessingStatus fromApi(String? value) {
    return switch (value) {
      'processed' => OrderProcessingStatus.processed,
      'review_required' => OrderProcessingStatus.reviewRequired,
      'no_match' => OrderProcessingStatus.noMatch,
      'error' => OrderProcessingStatus.error,
      _ => OrderProcessingStatus.unknown,
    };
  }

  String get label {
    return switch (this) {
      OrderProcessingStatus.processed => 'Procesada',
      OrderProcessingStatus.reviewRequired => 'Requiere revisión',
      OrderProcessingStatus.noMatch => 'Sin coincidencia',
      OrderProcessingStatus.error => 'Error',
      OrderProcessingStatus.unknown => 'Desconocido',
    };
  }

  String get apiValue {
    return switch (this) {
      OrderProcessingStatus.processed => 'processed',
      OrderProcessingStatus.reviewRequired => 'review_required',
      OrderProcessingStatus.noMatch => 'no_match',
      OrderProcessingStatus.error => 'error',
      OrderProcessingStatus.unknown => 'unknown',
    };
  }

  IconData get icon {
    return switch (this) {
      OrderProcessingStatus.processed => Icons.check_circle_rounded,
      OrderProcessingStatus.reviewRequired => Icons.rule_rounded,
      OrderProcessingStatus.noMatch => Icons.search_off_rounded,
      OrderProcessingStatus.error => Icons.error_rounded,
      OrderProcessingStatus.unknown => Icons.help_rounded,
    };
  }
}

/// A single line of an order as printed in the PDF.
///
/// Definitive model (Pre-Sprint 9): there is no product catalog; the line
/// carries the product [description] exactly as printed plus [pdfCode]/[ean]
/// as traceability only.
class OrderLineView {
  const OrderLineView({
    required this.description,
    required this.quantity,
    this.pdfCode,
    this.ean,
  });

  final String description;
  final int quantity;
  final String? pdfCode;
  final String? ean;

  factory OrderLineView.fromProcessedJson(Map<String, dynamic> json) {
    return OrderLineView(
      description: json['description'] as String? ?? '',
      quantity: (json['quantity'] as num?)?.toInt() ?? 0,
      pdfCode: json['pdf_code'] as String?,
      ean: json['ean'] as String?,
    );
  }

  factory OrderLineView.fromOrderJson(Map<String, dynamic> json) {
    return OrderLineView(
      description: json['description'] as String? ?? '',
      quantity: (json['quantity'] as num?)?.toInt() ?? 0,
      pdfCode: json['pdf_code'] as String?,
      ean: json['ean'] as String?,
    );
  }
}

class ProcessedDocumentView {
  const ProcessedDocumentView({
    required this.sourceFilename,
    required this.parserId,
    required this.documentType,
    required this.status,
    required this.items,
    required this.reasons,
    this.orderNumber,
    this.customerCode,
    this.customerName,
    this.routeCode,
    this.deliveryDate,
    this.routeReason,
    this.receivedAt,
  });

  final String sourceFilename;
  final String parserId;
  final String documentType;
  final OrderProcessingStatus status;
  final String? orderNumber;
  final String? customerCode;
  final String? customerName;
  final String? routeCode;
  final DateTime? deliveryDate;
  final String? routeReason;
  final List<String> reasons;
  final List<OrderLineView> items;
  final DateTime? receivedAt;

  factory ProcessedDocumentView.fromJson(Map<String, dynamic> json, {DateTime? receivedAt}) {
    return ProcessedDocumentView(
      sourceFilename: json['source_filename'] as String? ?? '',
      parserId: json['parser_id'] as String? ?? 'unknown',
      documentType: json['document_type'] as String? ?? 'unknown',
      status: OrderProcessingStatusX.fromApi(json['status'] as String?),
      orderNumber: json['order_number'] as String?,
      customerCode: json['customer_code'] as String?,
      customerName: json['customer_name'] as String?,
      routeCode: json['route_code'] as String?,
      deliveryDate: DateTime.tryParse(json['delivery_date'] as String? ?? ''),
      routeReason: json['route_reason'] as String?,
      reasons: [
        for (final reason in (json['reasons'] as List<dynamic>? ?? const []))
          reason.toString(),
      ],
      items: [
        for (final item in (json['items'] as List<dynamic>? ?? const []))
          OrderLineView.fromProcessedJson(Map<String, dynamic>.from(item as Map)),
      ],
      receivedAt: receivedAt ??
          (json['processed_at'] != null ? DateTime.tryParse(json['processed_at'] as String) : null) ??
          DateTime.now(),
    );
  }

  factory ProcessedDocumentView.fromOrder(OrderListView order) {
    return ProcessedDocumentView(
      sourceFilename: order.sourceFilename ?? order.orderNumber,
      parserId: 'persisted_order',
      documentType: 'order',
      status: OrderProcessingStatus.processed,
      orderNumber: order.orderNumber,
      customerCode: null,
      customerName: order.customerName,
      routeCode: order.routeCode,
      deliveryDate: order.deliveryDate,
      routeReason: null,
      reasons: const <String>[],
      items: [
        for (final item in order.items) OrderLineView.fromOrderJson(item.toJson()),
      ],
      receivedAt: order.processedAt,
    );
  }
}

class OrderItemView {
  const OrderItemView({
    required this.description,
    required this.quantity,
    this.pdfCode,
    this.ean,
  });

  final String description;
  final int quantity;
  final String? pdfCode;
  final String? ean;

  Map<String, dynamic> toJson() {
    return {
      'description': description,
      'quantity': quantity,
      'pdf_code': pdfCode,
      'ean': ean,
    };
  }
}

class OrderListView {
  const OrderListView({
    required this.id,
    required this.orderNumber,
    required this.customerName,
    required this.routeCode,
    required this.deliveryDate,
    required this.status,
    required this.items,
    this.sourceFilename,
    this.processedAt,
  });

  final int id;
  final String orderNumber;
  final String customerName;
  final String routeCode;
  final DateTime? deliveryDate;
  final String status;
  final List<OrderItemView> items;

  /// PDF de origen persistido en el backend (identidad del documento).
  ///
  /// El backend garantiza una sola orden por este nombre de archivo: volver a
  /// procesar el mismo PDF lo reemplaza en lugar de duplicarlo.
  final String? sourceFilename;

  /// Fecha y hora de procesamiento/persistencia registrada por el backend.
  final DateTime? processedAt;

  factory OrderListView.fromJson(Map<String, dynamic> json) {
    return OrderListView(
      id: (json['id'] as num?)?.toInt() ?? 0,
      orderNumber: json['order_number'] as String? ?? '',
      customerName: json['customer_name'] as String? ?? '',
      routeCode: json['route_code'] as String? ?? '',
      deliveryDate: DateTime.tryParse(json['delivery_date'] as String? ?? ''),
      status: json['status'] as String? ?? 'processed',
      sourceFilename: json['source_filename'] as String?,
      processedAt: DateTime.tryParse(json['processed_at'] as String? ?? ''),
      items: [
        for (final item in (json['items'] as List<dynamic>? ?? const []))
          OrderItemView(
            description: (item as Map<String, dynamic>)['description'] as String? ?? '',
            quantity: (item['quantity'] as num?)?.toInt() ?? 0,
            pdfCode: item['pdf_code'] as String?,
            ean: item['ean'] as String?,
          ),
      ],
    );
  }
}

class OverviewSnapshot {
  const OverviewSnapshot({
    required this.persistedOrders,
    required this.sessionDocuments,
    required this.usingDemoData,
    required this.bannerMessage,
  });

  final List<OrderListView> persistedOrders;
  final List<ProcessedDocumentView> sessionDocuments;
  final bool usingDemoData;
  final String bannerMessage;

  static const OverviewSnapshot empty = OverviewSnapshot(
    persistedOrders: <OrderListView>[],
    sessionDocuments: <ProcessedDocumentView>[],
    usingDemoData: false,
    bannerMessage: '',
  );

  /// Órdenes efectivamente procesadas, sin contar duplicados entre la sesión
  /// y las órdenes persistidas.
  int get processedCount =>
      documents.where((doc) => doc.status == OrderProcessingStatus.processed).length;

  int get reviewRequiredCount =>
      sessionDocuments.where((doc) => doc.status == OrderProcessingStatus.reviewRequired).length;

  int get noMatchCount =>
      sessionDocuments.where((doc) => doc.status == OrderProcessingStatus.noMatch).length;

  int get errorCount =>
      sessionDocuments.where((doc) => doc.status == OrderProcessingStatus.error).length;

  /// Total de documentos visibles (sesión + persistidos, sin duplicados).
  int get totalIncoming => documents.length;

  DateTime? get lastReception =>
      sessionDocuments.isEmpty ? null : sessionDocuments.first.receivedAt;

  /// Todos los documentos visibles: primero los de sesión, luego las órdenes
  /// persistidas que aún no están representadas en la sesión (mismo número de
  /// orden). Evita duplicar una orden PROCESSED recién importada.
  List<ProcessedDocumentView> get documents {
    final sessionOrderNumbers = {
      for (final document in sessionDocuments)
        if (document.orderNumber != null) document.orderNumber!,
    };
    return [
      ...sessionDocuments,
      for (final order in persistedOrders)
        if (!sessionOrderNumbers.contains(order.orderNumber))
          ProcessedDocumentView.fromOrder(order),
    ];
  }

  Map<String, ConsolidatedProductView> consolidateByProduct() {
    final map = <String, ConsolidatedProductView>{};
    for (final doc in documents.where((doc) => doc.status == OrderProcessingStatus.processed)) {
      for (final item in doc.items) {
        final label = item.description.isNotEmpty ? item.description : 'Producto sin nombre';
        final key = label.toLowerCase();
        final existing = map[key];
        final breakdown = OrderBreakdownView(
          customerLabel: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
          routeLabel: doc.routeCode ?? 'Sin ruta',
          quantity: item.quantity,
          deliveryDate: doc.deliveryDate,
          productLabel: label,
        );
        if (existing == null) {
          map[key] = ConsolidatedProductView(
            productKey: key,
            productLabel: label,
            totalQuantity: item.quantity,
            customers: <String>{breakdown.customerLabel},
            routes: <String>{breakdown.routeLabel},
            deliveryDates: doc.deliveryDate == null ? <String>{} : { _dateLabel(doc.deliveryDate!) },
            breakdown: [breakdown],
          );
          continue;
        }
        existing.totalQuantity += item.quantity;
        existing.customers.add(breakdown.customerLabel);
        existing.routes.add(breakdown.routeLabel);
        if (doc.deliveryDate != null) {
          existing.deliveryDates.add(_dateLabel(doc.deliveryDate!));
        }
        existing.breakdown.add(breakdown);
      }
    }
    return map;
  }

  Map<String, ConsolidatedEntityView> consolidateByCustomer() {
    final map = <String, ConsolidatedEntityView>{};
    for (final doc in documents.where((doc) => doc.status == OrderProcessingStatus.processed)) {
      final key = doc.customerCode ?? doc.customerName ?? 'Sin cliente';
      final entity = map.putIfAbsent(
        key,
        () => ConsolidatedEntityView(
          key: key,
          label: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
        ),
      );
      for (final item in doc.items) {
        entity.totalQuantity += item.quantity;
        entity.routes.add(doc.routeCode ?? 'Sin ruta');
        final prodLabel = item.description.isNotEmpty ? item.description : 'Producto sin nombre';
        entity.products.add(prodLabel);
        entity.lines.add(
          OrderBreakdownView(
            customerLabel: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
            routeLabel: doc.routeCode ?? 'Sin ruta',
            quantity: item.quantity,
            deliveryDate: doc.deliveryDate,
            productLabel: prodLabel,
          ),
        );
      }
    }
    return map;
  }

  Map<String, ConsolidatedEntityView> consolidateByRoute() {
    final map = <String, ConsolidatedEntityView>{};
    for (final doc in documents.where((doc) => doc.status == OrderProcessingStatus.processed)) {
      final key = doc.routeCode ?? 'Sin ruta';
      final entity = map.putIfAbsent(
        key,
        () => ConsolidatedEntityView(
          key: key,
          label: doc.routeCode ?? 'Sin ruta',
        ),
      );
      for (final item in doc.items) {
        entity.totalQuantity += item.quantity;
        entity.customers.add(doc.customerName ?? doc.customerCode ?? 'Sin cliente');
        final prodLabel = item.description.isNotEmpty ? item.description : 'Producto sin nombre';
        entity.products.add(prodLabel);
        entity.lines.add(
          OrderBreakdownView(
            customerLabel: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
            routeLabel: doc.routeCode ?? 'Sin ruta',
            quantity: item.quantity,
            deliveryDate: doc.deliveryDate,
            productLabel: prodLabel,
          ),
        );
      }
    }
    return map;
  }

  /// Consolidación definitiva por Ruta + Fecha de entrega.
  ///
  /// Agrupa las órdenes procesadas por la combinación de ruta y fecha de
  /// entrega; dentro de cada grupo desglosa por cliente y producto, y expone
  /// los totales por producto y el total general del grupo.
  List<RouteDateGroupView> consolidateByRouteAndDate() {
    final groups = <String, RouteDateGroupView>{};
    for (final doc in documents.where((doc) => doc.status == OrderProcessingStatus.processed)) {
      final route = doc.routeCode ?? 'Sin ruta';
      final date = doc.deliveryDate;
      final dateKey = date == null ? 'Sin fecha' : _dateLabel(date);
      final group = groups.putIfAbsent(
        '$route|$dateKey',
        () => RouteDateGroupView(routeCode: route, deliveryDate: date),
      );
      group.addDocument(
        customerName: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
        items: doc.items,
      );
    }

    final result = groups.values.toList()
      ..sort((a, b) {
        final dateCmp = (a.deliveryDate ?? DateTime(1)).compareTo(b.deliveryDate ?? DateTime(1));
        if (dateCmp != 0) return dateCmp;
        return a.routeCode.compareTo(b.routeCode);
      });
    for (final group in result) {
      group.customers.sort((a, b) => b.totalQuantity.compareTo(a.totalQuantity));
      for (final customer in group.customers) {
        customer.productTotals.sort((a, b) => b.quantity.compareTo(a.quantity));
      }
    }
    return result;
  }
}

class ConsolidatedProductView {
  ConsolidatedProductView({
    required this.productKey,
    required this.productLabel,
    required this.totalQuantity,
    required this.customers,
    required this.routes,
    required this.deliveryDates,
    required this.breakdown,
  });

  final String productKey;
  final String productLabel;
  int totalQuantity;
  final Set<String> customers;
  final Set<String> routes;
  final Set<String> deliveryDates;
  final List<OrderBreakdownView> breakdown;
}

class ConsolidatedEntityView {
  ConsolidatedEntityView({
    required this.key,
    required this.label,
  });

  final String key;
  final String label;
  int totalQuantity = 0;
  final Set<String> customers = <String>{};
  final Set<String> routes = <String>{};
  final Set<String> products = <String>{};
  final List<OrderBreakdownView> lines = <OrderBreakdownView>[];
}

/// Grupo de consolidación por Ruta + Fecha de entrega.
///
/// Cada grupo reúne las órdenes procesadas de una misma ruta para una misma
/// fecha de entrega, con su desglose por cliente y producto.
class RouteDateGroupView {
  RouteDateGroupView({required this.routeCode, required this.deliveryDate});

  final String routeCode;
  final DateTime? deliveryDate;
  final List<RouteDateCustomerView> customers = <RouteDateCustomerView>[];

  int get orderCount =>
      customers.fold(0, (sum, customer) => sum + customer.orderCount);

  int get totalQuantity =>
      customers.fold(0, (sum, customer) => sum + customer.totalQuantity);

  /// Total por producto sumando todos los clientes del grupo, de mayor a menor.
  List<RouteDateProductTotal> get productTotals {
    final map = <String, int>{};
    for (final customer in customers) {
      for (final product in customer.productTotals) {
        map[product.productLabel] = (map[product.productLabel] ?? 0) + product.quantity;
      }
    }
    return [
      for (final entry in map.entries)
        RouteDateProductTotal(productLabel: entry.key, quantity: entry.value),
    ]..sort((a, b) => b.quantity.compareTo(a.quantity));
  }

  void addDocument({
    required String customerName,
    required List<OrderLineView> items,
  }) {
    var customer = _findCustomer(customerName);
    if (customer == null) {
      customer = RouteDateCustomerView(customerName: customerName);
      customers.add(customer);
    }
    customer.addDocument(items);
  }

  RouteDateCustomerView? _findCustomer(String customerName) {
    final normalized = customerName.toLowerCase();
    for (final customer in customers) {
      if (customer.customerName.toLowerCase() == normalized) {
        return customer;
      }
    }
    return null;
  }
}

/// Un cliente dentro de un grupo Ruta + Fecha, con sus totales por producto.
class RouteDateCustomerView {
  RouteDateCustomerView({required this.customerName});

  final String customerName;
  final List<RouteDateProductTotal> productTotals = <RouteDateProductTotal>[];

  /// Número de documentos de este cliente en el grupo.
  int orderCount = 0;

  int get totalQuantity =>
      productTotals.fold(0, (sum, product) => sum + product.quantity);

  void addDocument(List<OrderLineView> items) {
    orderCount++;
    for (final item in items) {
      final label = item.description.isNotEmpty ? item.description : 'Producto sin nombre';
      var product = _findProduct(label);
      if (product == null) {
        product = RouteDateProductTotal(productLabel: label, quantity: item.quantity);
        productTotals.add(product);
      } else {
        product.quantity += item.quantity;
      }
    }
  }

  RouteDateProductTotal? _findProduct(String productLabel) {
    for (final product in productTotals) {
      if (product.productLabel == productLabel) {
        return product;
      }
    }
    return null;
  }
}

/// Cantidad total de un producto dentro de un cliente o de un grupo.
class RouteDateProductTotal {
  RouteDateProductTotal({required this.productLabel, required this.quantity});

  final String productLabel;
  int quantity;
}

class OrderBreakdownView {
  OrderBreakdownView({
    required this.customerLabel,
    required this.routeLabel,
    required this.quantity,
    this.deliveryDate,
    this.productLabel,
  });

  final String customerLabel;
  final String routeLabel;
  final int quantity;
  final DateTime? deliveryDate;
  final String? productLabel;
}

/// Resultado agregado de una importación de varios PDFs.
class BatchSummary {
  const BatchSummary({
    required this.total,
    required this.processed,
    required this.reviewRequired,
    required this.noMatch,
    required this.errors,
  });

  final int total;
  final int processed;
  final int reviewRequired;
  final int noMatch;
  final int errors;

  int get needsAttention => reviewRequired + noMatch + errors;
}

String _dateLabel(DateTime value) => value.toIso8601String().split('T').first;
