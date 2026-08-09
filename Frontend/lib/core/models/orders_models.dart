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

class OrderLineView {
  const OrderLineView({
    required this.description,
    required this.quantity,
    required this.matchStatus,
    this.productCode,
    this.productDescription,
    this.pdfCode,
    this.confidence,
    this.reason,
    this.candidates = const <String>[],
  });

  final String description;
  final int quantity;
  final String matchStatus;
  final String? productCode;
  final String? productDescription;
  final String? pdfCode;
  final double? confidence;
  final String? reason;
  final List<String> candidates;

  factory OrderLineView.fromProcessedJson(Map<String, dynamic> json) {
    return OrderLineView(
      description: json['description'] as String? ?? '',
      quantity: (json['quantity'] as num?)?.toInt() ?? 0,
      pdfCode: json['pdf_code'] as String?,
      matchStatus: json['match_status'] as String? ?? 'unknown',
      productCode: json['product_code'] as String?,
      productDescription: json['product_description'] as String?,
      confidence: (json['confidence'] as num?)?.toDouble(),
      reason: json['reason'] as String?,
      candidates: [
        for (final candidate in (json['candidates'] as List<dynamic>? ?? const []))
          candidate is Map<String, dynamic>
              ? '${candidate['code'] ?? ''} ${candidate['description'] ?? ''}'.trim()
              : candidate.toString(),
      ],
    );
  }

  factory OrderLineView.fromOrderJson(Map<String, dynamic> json) {
    return OrderLineView(
      description: json['product_description'] as String? ?? '',
      quantity: (json['quantity'] as num?)?.toInt() ?? 0,
      matchStatus: 'matched',
      productCode: json['product_code'] as String?,
      productDescription: json['product_description'] as String?,
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
      sourceFilename: order.orderNumber,
      parserId: 'persisted_order',
      documentType: 'order',
      status: OrderProcessingStatus.processed,
      orderNumber: order.orderNumber,
      customerCode: order.customerCode,
      customerName: order.customerName,
      routeCode: order.routeCode,
      deliveryDate: order.deliveryDate,
      routeReason: null,
      reasons: const <String>[],
      items: [
        for (final item in order.items) OrderLineView.fromOrderJson(item.toJson()),
      ],
      receivedAt: null,
    );
  }
}

class OrderItemView {
  const OrderItemView({
    required this.productCode,
    required this.productDescription,
    required this.quantity,
  });

  final String productCode;
  final String productDescription;
  final int quantity;

  Map<String, dynamic> toJson() {
    return {
      'product_code': productCode,
      'product_description': productDescription,
      'quantity': quantity,
    };
  }
}

class OrderListView {
  const OrderListView({
    required this.id,
    required this.orderNumber,
    required this.customerCode,
    required this.customerName,
    required this.routeCode,
    required this.deliveryDate,
    required this.status,
    required this.items,
  });

  final int id;
  final String orderNumber;
  final String customerCode;
  final String customerName;
  final String routeCode;
  final DateTime? deliveryDate;
  final String status;
  final List<OrderItemView> items;

  factory OrderListView.fromJson(Map<String, dynamic> json) {
    return OrderListView(
      id: (json['id'] as num?)?.toInt() ?? 0,
      orderNumber: json['order_number'] as String? ?? '',
      customerCode: json['customer_code'] as String? ?? '',
      customerName: json['customer_name'] as String? ?? '',
      routeCode: json['route_code'] as String? ?? '',
      deliveryDate: DateTime.tryParse(json['delivery_date'] as String? ?? ''),
      status: json['status'] as String? ?? 'processed',
      items: [
        for (final item in (json['items'] as List<dynamic>? ?? const []))
          OrderItemView(
            productCode: (item as Map<String, dynamic>)['product_code'] as String? ?? '',
            productDescription: item['product_description'] as String? ?? '',
            quantity: (item['quantity'] as num?)?.toInt() ?? 0,
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
        final key = item.productCode?.isNotEmpty == true
            ? item.productCode!
            : (item.productDescription ?? item.description).toLowerCase();
        final existing = map[key];
        final breakdown = OrderBreakdownView(
          customerLabel: doc.customerName ?? doc.customerCode ?? 'Sin cliente',
          routeLabel: doc.routeCode ?? 'Sin ruta',
          quantity: item.quantity,
          deliveryDate: doc.deliveryDate,
          productLabel: item.productDescription ?? item.description,
        );
        if (existing == null) {
          map[key] = ConsolidatedProductView(
            productKey: key,
            productLabel: item.productDescription ?? (item.description.isNotEmpty ? item.description : key),
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
        final prodLabel = item.productDescription ?? (item.description.isNotEmpty ? item.description : 'Producto sin nombre');
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
        final prodLabel = item.productDescription ?? (item.description.isNotEmpty ? item.description : 'Producto sin nombre');
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

  Map<String, ConsolidatedEntityView> consolidateByDate() {
    final map = <String, ConsolidatedEntityView>{};
    for (final doc in documents.where((doc) => doc.status == OrderProcessingStatus.processed)) {
      final key = doc.deliveryDate == null ? 'Sin fecha' : _dateLabel(doc.deliveryDate!);
      final entity = map.putIfAbsent(
        key,
        () => ConsolidatedEntityView(
          key: key,
          label: key,
        ),
      );
      for (final item in doc.items) {
        entity.totalQuantity += item.quantity;
        entity.customers.add(doc.customerName ?? doc.customerCode ?? 'Sin cliente');
        entity.routes.add(doc.routeCode ?? 'Sin ruta');
        final prodLabel = item.productDescription ?? (item.description.isNotEmpty ? item.description : 'Producto sin nombre');
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
