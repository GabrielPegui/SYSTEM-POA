import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/models/orders_models.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class OrderProcessingPage extends StatelessWidget {
  const OrderProcessingPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return AppPageShell(
      title: 'Recepción y procesamiento',
      subtitle: 'Importa las órdenes de compra de tus clientes; el sistema las clasifica y prepara para la operación.',
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
                final metricsCount = constraints.maxWidth >= 700 ? 3 : 1;
                return GridView.count(
                  crossAxisCount: metricsCount,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  mainAxisExtent: 110,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    MetricTile(
                      label: 'Procesadas',
                      value: state.snapshot.processedCount.toString(),
                      icon: Icons.check_circle_rounded,
                      tint: const Color(0xFF1F7A3D),
                    ),
                    MetricTile(
                      label: 'Requieren revisión',
                      value: (state.snapshot.reviewRequiredCount +
                              state.snapshot.noMatchCount +
                              state.snapshot.errorCount)
                          .toString(),
                      icon: Icons.rule_rounded,
                      tint: const Color(0xFF9A6A00),
                    ),
                    MetricTile(
                      label: 'Total de la sesión',
                      value: state.snapshot.totalIncoming.toString(),
                      icon: Icons.inbox_rounded,
                      tint: const Color(0xFFE52421),
                      delta: state.usingDemoData ? 'Demo local' : 'Datos cargados',
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 20),
            _buildImportCard(context, state),
            const SizedBox(height: 20),
            _buildOrderTray(context, state),
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
            subtitle: 'Selecciona uno o varios PDFs de pedido. Cada documento se clasifica automáticamente en la bandeja.',
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              onPressed: state.busy ? null : state.pickAndProcessPdfs,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 24),
              ),
              icon: const Icon(Icons.upload_file_rounded, size: 22),
              label: const Text('Importar órdenes PDF', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Puedes seleccionar varios PDFs a la vez.',
            style: TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildOrderTray(BuildContext context, AppState state) {
    return BolinCard(
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: SectionHeader(
              title: 'Bandeja de órdenes',
              subtitle: 'Órdenes de esta sesión listas para revisar o consolidar.',
              trailing: state.documents.isEmpty
                  ? null
                  : Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(
                        '${state.documents.length}',
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 12),
          state.documents.isEmpty
              ? const EmptyStatePanel(
                  title: 'Todavía no hay órdenes',
                  message: 'Cuando importes un PDF de pedido, aparecerá aquí con su cliente, ruta y estado.',
                )
              : Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('Cliente')),
                        DataColumn(label: Text('Ruta')),
                        DataColumn(label: Text('Productos / Cantidad')),
                        DataColumn(label: Text('Fecha de entrega')),
                        DataColumn(label: Text('Estado')),
                        DataColumn(label: Text('Acción')),
                      ],
                      rows: [
                        for (final document in state.documents)
                          DataRow(
                            onSelectChanged: (_) {
                              state.selectDocument(document);
                              context.push(AppRoutes.validation);
                            },
                            cells: [
                              DataCell(Text(document.customerName ?? document.customerCode ?? '-')),
                              DataCell(Text(document.routeCode ?? '-')),
                              DataCell(
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      _productsLabel(document),
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 1,
                                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                                    ),
                                    Text(
                                      '${_totalQuantity(document)} unidades',
                                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline),
                                    ),
                                  ],
                                ),
                              ),
                              DataCell(Text(
                                document.deliveryDate == null
                                    ? '-'
                                    : MaterialLocalizations.of(context).formatShortDate(document.deliveryDate!),
                              )),
                              DataCell(StatusPill(status: document.status)),
                              DataCell(
                                TextButton.icon(
                                  onPressed: () {
                                    state.selectDocument(document);
                                    context.push(AppRoutes.validation);
                                  },
                                  icon: const Icon(Icons.edit_note_rounded, size: 18),
                                  label: Text(
                                    document.status == OrderProcessingStatus.processed ? 'Ver' : 'Revisar',
                                  ),
                                ),
                              ),
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

  static String _productsLabel(ProcessedDocumentView document) {
    if (document.items.isEmpty) {
      return '-';
    }
    final first = document.items.first.description;
    final count = document.items.length;
    return count == 1 ? first : '$first (+${count - 1})';
  }

  static int _totalQuantity(ProcessedDocumentView document) {
    return document.items.fold(0, (sum, item) => sum + item.quantity);
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
