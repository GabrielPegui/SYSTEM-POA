import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/models/orders_models.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class ValidationPage extends StatelessWidget {
  const ValidationPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    final customerOptions = <String>{
      for (final doc in state.documents)
        if (doc.customerName != null && doc.customerName!.trim().isNotEmpty) doc.customerName!,
    }.toList()
      ..sort();
    final routeOptions = <String>{
      for (final doc in state.documents)
        if (doc.routeCode != null && doc.routeCode!.trim().isNotEmpty) doc.routeCode!,
    }.toList()
      ..sort();

    return AppPageShell(
      title: 'Revisión de órdenes',
      subtitle: 'Completa o corrige la información antes de enviar la orden a consolidación.',
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 900;
          final detail = BolinCard(
            child: _DocumentDetail(
              document: state.selectedDocument,
              customerOptions: customerOptions,
              routeOptions: routeOptions,
            ),
          );
          if (isWide) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  flex: 3,
                  child: _buildQueueList(context, state),
                ),
                const SizedBox(width: 16),
                Expanded(flex: 4, child: detail),
              ],
            );
          }

          return SingleChildScrollView(
            child: Column(
              children: [
                SizedBox(
                  height: 360,
                  child: _buildQueueList(context, state),
                ),
                const SizedBox(height: 16),
                detail,
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildQueueList(BuildContext context, AppState state) {
    return BolinCard(
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: SectionHeader(
              title: 'Órdenes pendientes',
              subtitle: 'Selecciona una orden para completar su información.',
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: state.reviewQueue.isEmpty
                ? const EmptyStatePanel(
                    title: 'No hay órdenes pendientes',
                    message: 'Las órdenes que requieran tu intervención aparecerán aquí después del procesamiento.',
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(20),
                    itemCount: state.reviewQueue.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final document = state.reviewQueue[index];
                      final isSelected = state.selectedDocument == document;
                      return InkWell(
                        onTap: () => state.selectDocument(document),
                        borderRadius: BorderRadius.circular(8),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 180),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? Theme.of(context).colorScheme.primary.withValues(alpha: 0.08)
                                : Theme.of(context).colorScheme.surfaceContainerLowest,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: isSelected
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).colorScheme.outlineVariant,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          document.sourceFilename,
                                          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          document.customerName ?? document.customerCode ?? 'Cliente no identificado',
                                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                                color: Theme.of(context).colorScheme.outline,
                                              ),
                                        ),
                                        if (document.deliveryDate != null) ...[
                                          const SizedBox(height: 2),
                                          Text(
                                            'Entrega: ${MaterialLocalizations.of(context).formatShortDate(document.deliveryDate!)}',
                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                                  color: Theme.of(context).colorScheme.outline,
                                                ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                  StatusPill(status: document.status),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class _DocumentDetail extends StatefulWidget {
  const _DocumentDetail({
    required this.document,
    required this.customerOptions,
    required this.routeOptions,
  });

  final ProcessedDocumentView? document;
  final List<String> customerOptions;
  final List<String> routeOptions;

  @override
  State<_DocumentDetail> createState() => _DocumentDetailState();
}

class _DocumentDetailState extends State<_DocumentDetail> {
  late List<TextEditingController> _quantityControllers;
  String? _customer;
  String? _route;
  DateTime? _deliveryDate;
  bool _saving = false;

  ProcessedDocumentView? get document => widget.document;

  bool get _isEditable {
    final doc = document;
    return doc != null && doc.status != OrderProcessingStatus.processed;
  }

  @override
  void initState() {
    super.initState();
    _syncState();
  }

  @override
  void didUpdateWidget(covariant _DocumentDetail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.document != widget.document) {
      _disposeControllers();
      _syncState();
    }
  }

  void _syncState() {
    final doc = document;
    _customer = _nullableOrNull(doc?.customerName ?? doc?.customerCode);
    _route = _nullableOrNull(doc?.routeCode);
    _quantityControllers = [
      for (final item in doc?.items ?? const <OrderLineView>[])
        TextEditingController(text: item.quantity.toString()),
    ];
    _deliveryDate = doc?.deliveryDate;
  }

  static String? _nullableOrNull(String? value) {
    final trimmed = value?.trim() ?? '';
    return trimmed.isEmpty ? null : trimmed;
  }

  void _disposeControllers() {
    for (final controller in _quantityControllers) {
      controller.dispose();
    }
  }

  @override
  void dispose() {
    _disposeControllers();
    super.dispose();
  }

  Future<void> _saveCorrection() async {
    final doc = document;
    if (doc == null) {
      return;
    }
    setState(() => _saving = true);

    final correctedItems = <OrderLineView>[];
    for (var index = 0; index < doc.items.length; index++) {
      final item = doc.items[index];
      final parsedQuantity = int.tryParse(_quantityControllers[index].text.trim());
      correctedItems.add(
        OrderLineView(
          description: item.description,
          quantity: parsedQuantity == null || parsedQuantity < 0 ? item.quantity : parsedQuantity,
          pdfCode: item.pdfCode,
          ean: item.ean,
        ),
      );
    }

    await context.read<AppState>().applyCorrection(
          doc,
          customerName: _customer ?? '',
          routeCode: _route,
          deliveryDate: _deliveryDate,
          correctedItems: correctedItems,
        );

    if (!mounted) {
      return;
    }
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Orden aprobada y enviada a consolidación.'),
      ),
    );
  }

  Future<void> _discardOrder() async {
    final doc = document;
    if (doc == null) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('¿Descartar esta orden?'),
          content: const Text('Se quitará de la bandeja de revisión y no entrará a la consolidación.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Descartar'),
            ),
          ],
        );
      },
    );
    if (confirmed == true && mounted) {
      context.read<AppState>().discardDocument(doc);
    }
  }

  Future<void> _pickDeliveryDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _deliveryDate ?? now,
      firstDate: now.subtract(const Duration(days: 365)),
      lastDate: now.add(const Duration(days: 730)),
    );
    if (picked != null && mounted) {
      setState(() => _deliveryDate = picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (document == null) {
      return const EmptyStatePanel(
        title: 'Sin documento seleccionado',
        message: 'Selecciona una orden para revisar sus datos.',
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SectionHeader(
            title: document!.sourceFilename,
            subtitle: _isEditable
                ? 'Completa la información y aprueba la orden.'
                : 'Información operativa de la orden.',
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              StatusPill(status: document!.status),
              const Spacer(),
              if (document!.orderNumber != null && document!.orderNumber!.isNotEmpty)
                DetailChip(label: 'Nº de orden', value: document!.orderNumber!),
            ],
          ),
          const SizedBox(height: 20),
          _buildOperationalAlert(context),
          const SizedBox(height: 20),
          if (_isEditable)
            _buildEditableFields(context)
          else
            _buildReadOnlyFields(context),
          const SizedBox(height: 20),
          Text('Líneas de la orden', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          document!.items.isEmpty
              ? const EmptyStatePanel(
                  title: 'No se encontraron productos',
                  message: 'Si el documento no trae productos legibles, la orden queda pendiente de revisión.',
                )
              : _buildItemsList(context),
          const SizedBox(height: 20),
          if (_isEditable) _buildActions(context),
          if (_isEditable) const SizedBox(height: 20),
          _buildPdfAccess(context),
          const SizedBox(height: 20),
          if (document!.receivedAt != null)
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Procesado el ${MaterialLocalizations.of(context).formatShortDate(document!.receivedAt!)}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline),
              ),
            ),
        ],
      ),
    );
  }

  /// Alerta operativa, en lenguaje funcional y con acción sugerida.
  Widget _buildOperationalAlert(BuildContext context) {
    final doc = document!;
    final (title, message, bg, fg) = switch (doc.status) {
      OrderProcessingStatus.reviewRequired => (
        'Revisión pendiente',
        'El sistema no pudo asignar toda la información. Confirma los datos y aprueba la orden.',
        const Color(0xFFFFF4D6),
        const Color(0xFF9A6A00),
      ),
      OrderProcessingStatus.noMatch => (
        'Cliente no identificado',
        'No se encontró una coincidencia para este pedido. Selecciona la cuenta y la ruta correctas, o descarta la orden.',
        const Color(0xFFF4F5F7),
        const Color(0xFF636A72),
      ),
      OrderProcessingStatus.error => (
        'No se pudo leer el documento',
        'El archivo no contiene información legible. Verifica el PDF original o descarta la orden.',
        const Color(0xFFFDE7E6),
        const Color(0xFFB42318),
      ),
      _ => (
        'Revisión pendiente',
        'Confirma la información de la orden antes de enviarla a consolidación.',
        const Color(0xFFFFF4D6),
        const Color(0xFF9A6A00),
      ),
    };

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: fg.withValues(alpha: 0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.campaign_rounded, color: fg),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(color: fg, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: fg),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEditableFields(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Datos de la orden', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 12),
        _buildCustomerDropdown(context),
        const SizedBox(height: 12),
        _buildRouteDropdown(context),
        const SizedBox(height: 12),
        InkWell(
          onTap: _pickDeliveryDate,
          borderRadius: BorderRadius.circular(4),
          child: InputDecorator(
            decoration: const InputDecoration(
              labelText: 'Fecha de entrega',
              border: OutlineInputBorder(),
              suffixIcon: Icon(Icons.calendar_month_rounded),
            ),
            child: Text(
              _deliveryDate == null
                  ? 'Seleccionar fecha'
                  : MaterialLocalizations.of(context).formatShortDate(_deliveryDate!),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCustomerDropdown(BuildContext context) {
    return DropdownButtonFormField<String>(
      initialValue: _customer,
      decoration: const InputDecoration(labelText: 'Cliente'),
      icon: const Icon(Icons.storefront_outlined),
      hint: const Text('Seleccionar cliente'),
      items: _dropdownItems(
        options: widget.customerOptions,
        current: _customer,
        emptyLabel: 'Cliente no identificado',
      ),
      onChanged: (value) => setState(() => _customer = value),
    );
  }

  Widget _buildRouteDropdown(BuildContext context) {
    return DropdownButtonFormField<String>(
      initialValue: _route,
      decoration: const InputDecoration(labelText: 'Ruta'),
      icon: const Icon(Icons.local_shipping_outlined),
      hint: const Text('Seleccionar ruta'),
      items: _dropdownItems(
        options: widget.routeOptions,
        current: _route,
        emptyLabel: 'Ruta no asignada',
      ),
      onChanged: (value) => setState(() => _route = value),
    );
  }

  List<DropdownMenuItem<String>> _dropdownItems({
    required List<String> options,
    required String? current,
    required String emptyLabel,
  }) {
    final items = <DropdownMenuItem<String>>[];
    if (current != null && !options.contains(current)) {
      items.add(DropdownMenuItem(value: current, child: Text(current)));
    }
    items.addAll([
      for (final option in options)
        DropdownMenuItem(value: option, child: Text(option)),
    ]);
    if (items.isEmpty) {
      items.add(DropdownMenuItem(value: null, child: Text(emptyLabel)));
    }
    return items;
  }

  Widget _buildReadOnlyFields(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        DetailChip(label: 'Cliente', value: document!.customerName ?? document!.customerCode ?? '-'),
        DetailChip(label: 'Ruta', value: document!.routeCode ?? '-'),
        DetailChip(label: 'Entrega', value: document!.deliveryDate == null ? '-' : MaterialLocalizations.of(context).formatShortDate(document!.deliveryDate!)),
      ],
    );
  }

  Widget _buildItemsList(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
            ),
            child: const Row(
              children: [
                Expanded(child: Text('Producto', style: TextStyle(fontWeight: FontWeight.w800))),
                SizedBox(width: 120, child: Text('Cantidad', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800))),
              ],
            ),
          ),
          for (var index = 0; index < document!.items.length; index++)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(color: theme.colorScheme.outlineVariant.withValues(alpha: 0.6)),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          document!.items[index].description,
                          style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                        ),
                        if (document!.items[index].pdfCode != null || document!.items[index].ean != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            [
                              if (document!.items[index].pdfCode != null) 'Código ${document!.items[index].pdfCode}',
                              if (document!.items[index].ean != null) 'EAN ${document!.items[index].ean}',
                            ].join(' • '),
                            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  if (_isEditable)
                    SizedBox(
                      width: 120,
                      child: TextField(
                        controller: _quantityControllers[index],
                        keyboardType: TextInputType.number,
                        textAlign: TextAlign.center,
                        decoration: const InputDecoration(
                          labelText: 'Cantidad',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                    )
                  else
                    Text('x${document!.items[index].quantity}', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildActions(BuildContext context) {
    final approveButton = FilledButton.icon(
      onPressed: _saving ? null : _saveCorrection,
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
      ),
      icon: _saving
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.check_rounded),
      label: Text(
        _saving ? 'Enviando...' : 'Aprobar y enviar a consolidación',
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
    final discardButton = OutlinedButton.icon(
      onPressed: _saving ? null : _discardOrder,
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
      ),
      icon: const Icon(Icons.delete_outline_rounded),
      label: const Text(
        'Descartar orden',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 560) {
          return Row(
            children: [
              Expanded(child: approveButton),
              const SizedBox(width: 12),
              Expanded(child: discardButton),
            ],
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            approveButton,
            const SizedBox(height: 12),
            discardButton,
          ],
        );
      },
    );
  }

  Widget _buildPdfAccess(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Row(
        children: [
          const Icon(Icons.picture_as_pdf_outlined, color: Color(0xFFE52421)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Archivo original',
                  style: theme.textTheme.labelSmall?.copyWith(color: theme.colorScheme.outline),
                ),
                const SizedBox(height: 2),
                Text(
                  document!.sourceFilename,
                  style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Tooltip(
            message: 'La visualización del PDF original estará disponible en una próxima versión.',
            child: OutlinedButton.icon(
              onPressed: null,
              icon: const Icon(Icons.open_in_new_rounded, size: 18),
              label: const Text('Ver PDF'),
            ),
          ),
        ],
      ),
    );
  }
}
