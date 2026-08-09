import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/models/orders_models.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class OrderProcessingPage extends StatefulWidget {
  const OrderProcessingPage({super.key});

  @override
  State<OrderProcessingPage> createState() => _OrderProcessingPageState();
}

class _OrderProcessingPageState extends State<OrderProcessingPage> {
  final TextEditingController _pathController = TextEditingController();

  static const _sampleFiles = [
    'docs/samples/Orden de Pedido por e-mail.pdf',
    'docs/samples/4000326758.pdf',
    'docs/samples/Orden de Compra 4505261004.pdf',
  ];

  @override
  void dispose() {
    _pathController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    _pathController.value = _pathController.value.copyWith(
      text: state.draftPath,
      selection: TextSelection.collapsed(offset: state.draftPath.length),
    );

    return AppPageShell(
      title: 'Recepción y procesamiento',
      subtitle: 'Importa PDFs, revisa resultados y sigue el flujo de documentos sin perder trazabilidad.',
      actions: [
        FilledButton.icon(
          onPressed: state.busy ? null : state.pickAndProcessPdfs,
          icon: state.busy
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.upload_file_rounded),
          label: const Text('Importar órdenes PDF'),
        ),
      ],
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (state.busy) ...[
              const LinearProgressIndicator(minHeight: 3),
              if (state.batchTotal > 0) ...[
                const SizedBox(height: 8),
                Text(
                  'Procesando ${state.batchDone} de ${state.batchTotal} documentos...',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                ),
              ],
            ],
            if (state.errorMessage != null) ...[
              const SizedBox(height: 12),
              _ErrorBanner(
                message: state.errorMessage!,
                onDismiss: state.dismissError,
              ),
            ],
            if (state.batchSummary != null) ...[
              const SizedBox(height: 12),
              _BatchSummaryBanner(summary: state.batchSummary!),
            ],
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) {
                final metricsCount = constraints.maxWidth >= 1000 ? 4 : 2;
                return GridView.count(
                  crossAxisCount: metricsCount,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  mainAxisExtent: 110,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    MetricTile(
                      label: 'Órdenes recibidas',
                      value: state.snapshot.totalIncoming.toString(),
                      icon: Icons.inbox_rounded,
                      tint: const Color(0xFFC8911E),
                      delta: state.usingDemoData ? 'Demo local' : 'Datos cargados',
                    ),
                    MetricTile(
                      label: 'Procesadas',
                      value: state.snapshot.processedCount.toString(),
                      icon: Icons.check_circle_rounded,
                      tint: const Color(0xFF1F7A3D),
                    ),
                    MetricTile(
                      label: 'Requieren revisión',
                      value: state.snapshot.reviewRequiredCount.toString(),
                      icon: Icons.rule_rounded,
                      tint: const Color(0xFF9A6A00),
                    ),
                    MetricTile(
                      label: 'Errores',
                      value: state.snapshot.errorCount.toString(),
                      icon: Icons.error_rounded,
                      tint: const Color(0xFFE52421),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 20),
            LayoutBuilder(
              builder: (context, constraints) {
                final isWide = constraints.maxWidth >= 900;
                if (isWide) {
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(flex: 3, child: _buildImportCard(context, state)),
                      const SizedBox(width: 16),
                      Expanded(flex: 2, child: _buildRecentCard(context, state)),
                    ],
                  );
                }
                return Column(
                  children: [
                    _buildImportCard(context, state),
                    const SizedBox(height: 16),
                    _buildRecentCard(context, state),
                  ],
                );
              },
            ),
            const SizedBox(height: 20),
            BolinCard(
              padding: const EdgeInsets.all(0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(20, 20, 20, 0),
                    child: SectionHeader(
                      title: 'Bandeja de órdenes',
                      subtitle: 'Documentos persistidos y documentos procesados en esta sesión.',
                    ),
                  ),
                  const SizedBox(height: 12),
                  state.documents.isEmpty
                      ? const EmptyStatePanel(
                          title: 'La bandeja está vacía',
                          message: 'Importa un PDF para ver cómo entra al flujo y cómo se clasifica.',
                        )
                      : Padding(
                          padding: const EdgeInsets.only(bottom: 20),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            padding: const EdgeInsets.symmetric(horizontal: 20),
                            child: DataTable(
                              columns: const [
                                DataColumn(label: Text('Archivo')),
                                DataColumn(label: Text('Cliente')),
                                DataColumn(label: Text('Ruta')),
                                DataColumn(label: Text('Estado')),
                                DataColumn(label: Text('Entrega')),
                                DataColumn(label: Text('Productos')),
                                DataColumn(label: Text('Procesado')),
                              ],
                              rows: [
                                for (final document in state.documents)
                                  DataRow(
                                    onSelectChanged: (_) {
                                      state.selectDocument(document);
                                      context.push(AppRoutes.validation);
                                    },
                                    cells: [
                                      DataCell(Text(document.sourceFilename)),
                                      DataCell(Text(document.customerName ?? document.customerCode ?? '-')),
                                      DataCell(Text(document.routeCode ?? '-')),
                                      DataCell(StatusPill(status: document.status)),
                                      DataCell(Text(
                                        document.deliveryDate == null
                                            ? '-'
                                            : MaterialLocalizations.of(context).formatShortDate(document.deliveryDate!),
                                      )),
                                      DataCell(Text(document.items.length.toString())),
                                      DataCell(Text(
                                        document.receivedAt == null
                                            ? '-'
                                            : MaterialLocalizations.of(context).formatShortDate(document.receivedAt!),
                                      )),
                                    ],
                                  ),
                              ],
                            ),
                          ),
                        ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildImportCard(BuildContext context, AppState state) {
    return BolinCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SectionHeader(
            title: 'Importar órdenes PDF',
            subtitle: 'Selecciona un archivo PDF desde tu equipo o usa las muestras de desarrollo.',
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: state.busy ? null : state.pickAndProcessPdfs,
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
            ),
            icon: const Icon(Icons.picture_as_pdf_outlined, size: 24),
            label: const Text('Seleccionar y procesar PDF', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 8),
          const Text(
            'Puedes seleccionar varios PDFs a la vez.',
            style: TextStyle(fontSize: 12),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Material(
            color: Colors.transparent,
            child: ExpansionTile(
              title: const Text('Ruta manual o muestras (desarrollo)', style: TextStyle(fontSize: 13)),
              tilePadding: EdgeInsets.zero,
              children: [
                TextField(
                  controller: _pathController,
                  onChanged: state.setDraftPath,
                  decoration: const InputDecoration(
                    labelText: 'Ruta del archivo PDF',
                    hintText: 'C:/Users/.../orden.pdf o docs/samples/Orden de Pedido por e-mail.pdf',
                    prefixIcon: Icon(Icons.folder_open_outlined),
                  ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final sample in _sampleFiles)
                      ActionChip(
                        label: Text(sample.split('/').last),
                        avatar: const Icon(Icons.auto_awesome_rounded, size: 18),
                        onPressed: () {
                          final value = '../$sample';
                          _pathController.text = value;
                          state.setDraftPath(value);
                        },
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: state.busy ? null : state.processDraft,
                  icon: const Icon(Icons.play_arrow_rounded),
                  label: const Text('Procesar ruta manual'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: state.loading ? null : state.loadOverview,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Sincronizar backend'),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentCard(BuildContext context, AppState state) {
    return BolinCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SectionHeader(
            title: 'Última recepción',
            subtitle: 'Lo más reciente que tocó el sistema.',
          ),
          const SizedBox(height: 16),
          if (state.snapshot.lastReception == null)
            const EmptyStatePanel(
              title: 'Sin recepciones locales',
              message: 'Procesa un PDF para ver aquí la última recepción de esta sesión.',
            )
          else
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  state.snapshot.lastReception!.toLocal().toString(),
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Text(
                  state.reviewQueue.isNotEmpty
                      ? 'Hay ${state.reviewQueue.length} documentos pendientes en revisión.'
                      : 'La cola está limpia por ahora.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          const SizedBox(height: 20),
          Text(
            'Estados de la sesión',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (final document in state.documents.take(4))
                _MiniDocumentCard(document: document),
              if (state.documents.isEmpty)
                const Text('No hay documentos cargados todavía.'),
            ],
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message, required this.onDismiss});

  final String message;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFDE7E6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE9A4A1)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_rounded, color: Color(0xFFE52421)),
          const SizedBox(width: 12),
          Expanded(child: Text(message)),
          TextButton(onPressed: onDismiss, child: const Text('Cerrar')),
        ],
      ),
    );
  }
}

class _BatchSummaryBanner extends StatelessWidget {
  const _BatchSummaryBanner({required this.summary});

  final BatchSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.fact_check_rounded, color: Color(0xFF1F7A3D)),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${summary.total} documento${summary.total == 1 ? '' : 's'} procesado${summary.total == 1 ? '' : 's'}',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _SummaryPill(
                icon: Icons.check_circle_rounded,
                color: const Color(0xFF1F7A3D),
                label: '${summary.processed} procesada${summary.processed == 1 ? '' : 's'}',
              ),
              if (summary.reviewRequired > 0)
                _SummaryPill(
                  icon: Icons.rule_rounded,
                  color: const Color(0xFF9A6A00),
                  label: '${summary.reviewRequired} requiere revisión',
                ),
              if (summary.noMatch > 0)
                _SummaryPill(
                  icon: Icons.search_off_rounded,
                  color: const Color(0xFF636A72),
                  label: '${summary.noMatch} sin coincidencia',
                ),
              if (summary.errors > 0)
                _SummaryPill(
                  icon: Icons.error_rounded,
                  color: const Color(0xFFB42318),
                  label: '${summary.errors} con error',
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SummaryPill extends StatelessWidget {
  const _SummaryPill({
    required this.icon,
    required this.color,
    required this.label,
  });

  final IconData icon;
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Text(
          label,
          style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
      ],
    );
  }
}

class _MiniDocumentCard extends StatelessWidget {
  const _MiniDocumentCard({required this.document});

  final ProcessedDocumentView document;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 240,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusPill(status: document.status),
          const SizedBox(height: 10),
          Text(document.sourceFilename, maxLines: 1, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 4),
          Text(
            document.customerName ?? document.customerCode ?? 'Sin cliente',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline),
          ),
          const SizedBox(height: 8),
          Text('${document.items.length} productos', style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
