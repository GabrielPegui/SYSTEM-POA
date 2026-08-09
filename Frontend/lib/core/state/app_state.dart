import 'dart:async';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../errors/failures.dart';
import '../models/orders_models.dart';
import '../services/orders_api_service.dart';

enum WorkspaceView {
  dashboard,
  reviewCenter,
  consolidation,
  customers,
  products,
  routes,
  configuration,
}

extension WorkspaceViewX on WorkspaceView {
  String get label {
    return switch (this) {
      WorkspaceView.dashboard => 'Inicio',
      WorkspaceView.reviewCenter => 'Revisión',
      WorkspaceView.consolidation => 'Consolidación',
      WorkspaceView.customers => 'Clientes',
      WorkspaceView.products => 'Productos',
      WorkspaceView.routes => 'Rutas',
      WorkspaceView.configuration => 'Configuración',
    };
  }
}

/// Application-wide state: session documents, persisted orders and the import
/// batch lifecycle.
///
/// Session documents are the source of truth during a working session (they
/// include REVIEW_REQUIRED / NO_MATCH / ERROR results that are never
/// persisted). Persisted orders come from the backend and are merged on
/// [loadOverview] without overwriting session documents.
class AppState extends ChangeNotifier {
  AppState({OrdersApiService? service}) : _service = service ?? OrdersApiService() {
    unawaited(loadOverview());
  }

  final OrdersApiService _service;

  WorkspaceView _currentView = WorkspaceView.dashboard;
  OverviewSnapshot _snapshot = OverviewSnapshot.empty;
  bool _loading = true;
  bool _busy = false;
  String? _errorMessage;
  String _draftPath = '';
  ProcessedDocumentView? _selectedDocument;
  int _groupingIndex = 0;
  int _batchTotal = 0;
  int _batchDone = 0;
  BatchSummary? _batchSummary;

  WorkspaceView get currentView => _currentView;
  OverviewSnapshot get snapshot => _snapshot;
  bool get loading => _loading;
  bool get busy => _busy;
  String? get errorMessage => _errorMessage;
  String get draftPath => _draftPath;
  ProcessedDocumentView? get selectedDocument => _selectedDocument;
  int get groupingIndex => _groupingIndex;

  /// Número de archivos del lote actual (0 si no hay lote en curso).
  int get batchTotal => _batchTotal;

  /// Número de archivos ya terminados del lote actual.
  int get batchDone => _batchDone;

  /// Resumen del último lote importado, o null antes de terminarlo.
  BatchSummary? get batchSummary => _batchSummary;

  List<OrderListView> get persistedOrders => _snapshot.persistedOrders;
  List<ProcessedDocumentView> get documents => _snapshot.documents;
  bool get usingDemoData => _snapshot.usingDemoData;
  String get bannerMessage => _snapshot.bannerMessage;

  List<ProcessedDocumentView> get reviewQueue {
    return documents
        .where((document) => document.status != OrderProcessingStatus.processed)
        .toList(growable: false);
  }

  List<ProcessedDocumentView> get processedDocuments {
    return documents
        .where((document) => document.status == OrderProcessingStatus.processed)
        .toList(growable: false);
  }

  Future<void> loadOverview() async {
    _loading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final fresh = await _service.loadOverview();
      // Refresca órdenes persistidas desde el backend pero conserva los
      // documentos de sesión (resultados no persistidos) para no perderlos.
      // En la primera carga no hay documentos de sesión previos, así que se
      // adoptan los que el servicio devuelva (p. ej. datos de demostración).
      final keptSessionDocuments = _snapshot.sessionDocuments.isEmpty
          ? fresh.sessionDocuments
          : _snapshot.sessionDocuments;
      _snapshot = OverviewSnapshot(
        persistedOrders: fresh.persistedOrders,
        sessionDocuments: keptSessionDocuments,
        usingDemoData: fresh.usingDemoData,
        bannerMessage: fresh.bannerMessage,
      );
      _selectInitialDocument();
    } catch (error) {
      _errorMessage = 'No fue posible cargar el tablero: $error';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  void _selectInitialDocument() {
    if (reviewQueue.isNotEmpty) {
      _selectedDocument = reviewQueue.first;
    } else if (documents.isNotEmpty) {
      _selectedDocument = documents.first;
    } else if (_snapshot.persistedOrders.isNotEmpty) {
      _selectedDocument = ProcessedDocumentView.fromOrder(_snapshot.persistedOrders.first);
    } else {
      _selectedDocument = null;
    }
  }

  void navigateTo(WorkspaceView view) {
    if (_currentView == view) {
      return;
    }
    _currentView = view;
    notifyListeners();
  }

  void setDraftPath(String value) {
    _draftPath = value;
    notifyListeners();
  }

  void setGroupingIndex(int index) {
    _groupingIndex = index;
    notifyListeners();
  }

  void selectDocument(ProcessedDocumentView document) {
    _selectedDocument = document;
    notifyListeners();
  }

  /// Selecciona uno o varios PDFs y los procesa en lote.
  Future<void> pickAndProcessPdfs() async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        allowMultiple: true,
        withData: true,
      );

      if (result == null || result.files.isEmpty) {
        return;
      }

      await processFiles(result.files);
    } catch (error) {
      _errorMessage = 'Error al seleccionar archivo: $error';
      notifyListeners();
    }
  }

  /// Procesa un lote de archivos de forma secuencial, acumulando los
  /// resultados en la bandeja de sesión y dejando un [BatchSummary].
  Future<void> processFiles(List<PlatformFile> files) async {
    if (files.isEmpty) {
      return;
    }

    _busy = true;
    _errorMessage = null;
    _batchTotal = files.length;
    _batchDone = 0;
    _batchSummary = null;
    var processed = 0;
    var review = 0;
    var noMatch = 0;
    var errors = 0;
    notifyListeners();

    try {
      for (final file in files) {
        try {
          final bytes = file.bytes;
          final path = file.path;
          final ProcessedDocumentView document;
          if (bytes != null && bytes.isNotEmpty) {
            document = await _service.processPdfBytes(bytes: bytes, filename: file.name);
          } else if (path != null && path.isNotEmpty) {
            document = await _service.processPdfPath(path);
          } else {
            throw const UnknownFailure('No se pudo leer el archivo seleccionado.');
          }
          _addSessionDocument(document);
          switch (document.status) {
            case OrderProcessingStatus.processed:
              processed++;
            case OrderProcessingStatus.reviewRequired:
              review++;
            case OrderProcessingStatus.noMatch:
              noMatch++;
            case OrderProcessingStatus.error:
            case OrderProcessingStatus.unknown:
              errors++;
          }
        } catch (error) {
          errors++;
          // Representa el archivo fallido como un ERROR visible y trazable.
          _addSessionDocument(
            ProcessedDocumentView(
              sourceFilename: file.name,
              parserId: 'unknown',
              documentType: 'unknown',
              status: OrderProcessingStatus.error,
              items: const [],
              reasons: [_friendlyError(error)],
            ),
          );
        } finally {
          _batchDone++;
          notifyListeners();
        }
      }

      _batchSummary = BatchSummary(
        total: files.length,
        processed: processed,
        reviewRequired: review,
        noMatch: noMatch,
        errors: errors,
      );
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> processBytes(Uint8List bytes, String filename) async {
    if (bytes.isEmpty) {
      _errorMessage = 'Selecciona un archivo PDF válido.';
      notifyListeners();
      return;
    }

    _busy = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final processed = await _service.processPdfBytes(
        bytes: bytes,
        filename: filename,
      );
      _addSessionDocument(processed);
      _draftPath = '';
    } catch (error) {
      _errorMessage = _friendlyError(error);
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> processDraftPath(String path) async {
    _busy = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final processed = await _service.processPdfPath(path);
      _addSessionDocument(processed);
      _draftPath = '';
    } catch (error) {
      _errorMessage = _friendlyError(error);
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> processDraft() async {
    final path = _draftPath.trim();
    if (path.isEmpty) {
      _errorMessage = 'Ingresa la ruta de un PDF para procesarlo.';
      notifyListeners();
      return;
    }
    await processDraftPath(path);
  }

  /// Agrega (o reemplaza por mismo nombre de archivo) un documento de sesión.
  void _addSessionDocument(ProcessedDocumentView document) {
    final remaining = _snapshot.sessionDocuments
        .where((existing) => existing.sourceFilename != document.sourceFilename)
        .toList(growable: false);
    _snapshot = OverviewSnapshot(
      persistedOrders: _snapshot.persistedOrders,
      sessionDocuments: [document, ...remaining],
      usingDemoData: _snapshot.usingDemoData,
      bannerMessage: _snapshot.bannerMessage,
    );
    _selectedDocument = document;
  }

  static String _friendlyError(Object error) {
    return error.toString().replaceFirst('Exception: ', '');
  }

  void dismissError() {
    _errorMessage = null;
    notifyListeners();
  }

  List<ConsolidatedProductView> get consolidatedByProduct {
    final values = _snapshot.consolidateByProduct().values.toList();
    values.sort((a, b) => b.totalQuantity.compareTo(a.totalQuantity));
    return values;
  }

  List<ConsolidatedEntityView> get consolidatedByCustomer {
    final values = _snapshot.consolidateByCustomer().values.toList();
    values.sort((a, b) => b.totalQuantity.compareTo(a.totalQuantity));
    return values;
  }

  List<ConsolidatedEntityView> get consolidatedByRoute {
    final values = _snapshot.consolidateByRoute().values.toList();
    values.sort((a, b) => b.totalQuantity.compareTo(a.totalQuantity));
    return values;
  }

  List<ConsolidatedEntityView> get consolidatedByDate {
    final values = _snapshot.consolidateByDate().values.toList();
    values.sort((a, b) => a.key.compareTo(b.key));
    return values;
  }
}
