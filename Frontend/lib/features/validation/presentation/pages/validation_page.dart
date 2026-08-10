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

    return AppPageShell(
      title: 'Centro de revisión',
      subtitle: 'Documentos que requieren atención operativa antes de consolidarse.',
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 900;
          if (isWide) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  flex: 3,
                  child: _buildQueueList(context, state),
                ),
                const SizedBox(width: 16),
                Expanded(
                  flex: 4,
                  child: BolinCard(
                    child: _DocumentDetail(document: state.selectedDocument),
                  ),
                ),
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
                BolinCard(
                  child: _DocumentDetail(document: state.selectedDocument),
                ),
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
              subtitle: 'Selecciona una orden para revisar su información.',
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
                                      ],
                                    ),
                                  ),
                                  StatusPill(status: document.status),
                                ],
                              ),
                              if (document.reasons.isNotEmpty) ...[
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    for (final reason in document.reasons.take(3))
                                      Chip(
                                        label: Text(reason),
                                        avatar: const Icon(Icons.info_outline, size: 16),
                                      ),
                                  ],
                                ),
                              ],
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
  const _DocumentDetail({required this.document});

  final ProcessedDocumentView? document;

  @override
  State<_DocumentDetail> createState() => _DocumentDetailState();
}

class _DocumentDetailState extends State<_DocumentDetail> {
  late TextEditingController _customerController;
  late TextEditingController _routeController;
  late List<TextEditingController> _quantityControllers;
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
    _syncControllers();
  }

  @override
  void didUpdateWidget(covariant _DocumentDetail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.document != widget.document) {
      _disposeControllers();
      _syncControllers();
    }
  }

  void _syncControllers() {
    final doc = document;
    _customerController = TextEditingController(
      text: doc?.customerName ?? doc?.customerCode ?? '',
    );
    _routeController = TextEditingController(text: doc?.routeCode ?? '');
    _quantityControllers = [
      for (final item in doc?.items ?? const <OrderLineView>[])
        TextEditingController(text: item.quantity.toString()),
    ];
    _deliveryDate = doc?.deliveryDate;
  }

  void _disposeControllers() {
    _customerController.dispose();
    _routeController.dispose();
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
          matchStatus: item.matchStatus,
          productCode: item.productCode,
          productDescription: item.productDescription,
          pdfCode: item.pdfCode,
          confidence: item.confidence,
          reason: item.reason,
          candidates: item.candidates,
        ),
      );
    }

    await context.read<AppState>().applyCorrection(
          doc,
          customerName: _customerController.text,
          routeCode: _routeController.text,
          deliveryDate: _deliveryDate,
          correctedItems: correctedItems,
        );

    if (!mounted) {
      return;
    }
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Corrección guardada. La orden pasó a procesada en esta sesión.'),
      ),
    );
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
                ? 'Corrige la información que falte y guarda la orden.'
                : 'Información operativa de la orden.',
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              StatusPill(status: document!.status),
            ],
          ),
          const SizedBox(height: 20),
          _buildReviewReasons(context),
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
          Card(
            child: Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                leading: const Icon(Icons.tune_rounded),
                title: const Text('Detalles técnicos', style: TextStyle(fontWeight: FontWeight.w700)),
                childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                children: [
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      DetailChip(label: 'Parser', value: document!.parserId),
                      DetailChip(label: 'Tipo', value: document!.documentType),
                      DetailChip(label: 'Nº de orden', value: document!.orderNumber ?? '-'),
                      DetailChip(label: 'Procesado', value: document!.receivedAt == null ? '-' : MaterialLocalizations.of(context).formatShortDate(document!.receivedAt!)),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReviewReasons(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('¿Qué requiere revisión?', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 10),
        if (document!.reasons.isEmpty)
          Text('Sin observaciones.', style: Theme.of(context).textTheme.bodyMedium)
        else
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final reason in document!.reasons)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.arrow_right_rounded, size: 20),
                      const SizedBox(width: 8),
                      Expanded(child: Text(reason)),
                    ],
                  ),
                ),
            ],
          ),
      ],
    );
  }

  Widget _buildEditableFields(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Datos de la orden', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 12),
        TextField(
          controller: _customerController,
          decoration: const InputDecoration(
            labelText: 'Cliente',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _routeController,
          decoration: const InputDecoration(
            labelText: 'Ruta',
            border: OutlineInputBorder(),
          ),
        ),
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
        const SizedBox(height: 20),
        FilledButton.icon(
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
            _saving ? 'Guardando...' : 'Guardar corrección',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'La corrección se conserva en esta sesión y la orden pasa a consolidación.',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
        ),
      ],
    );
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
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: document!.items.length,
      separatorBuilder: (_, _) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final item = document!.items[index];
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerLowest,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: Text(
                      item.productDescription ?? item.description,
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  if (_isEditable) ...[
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 96,
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
                    ),
                  ] else
                    Text('x${item.quantity}', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                ],
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  DetailChip(label: 'Coincidencia', value: item.matchStatus),
                ],
              ),
              if (item.reason != null) ...[
                const SizedBox(height: 8),
                Text(item.reason!, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        );
      },
    );
  }
}
