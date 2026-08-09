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
              subtitle: 'Selecciona un documento para revisar las razones y el detalle.',
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: state.reviewQueue.isEmpty
                ? const EmptyStatePanel(
                    title: 'No hay órdenes en revisión',
                    message: 'Cuando un PDF no tenga coincidencia suficiente, aparecerá aquí con su motivo.',
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

class _DocumentDetail extends StatelessWidget {
  const _DocumentDetail({required this.document});

  final ProcessedDocumentView? document;

  @override
  Widget build(BuildContext context) {
    if (document == null) {
      return const EmptyStatePanel(
        title: 'Sin documento seleccionado',
        message: 'Elige una orden para ver el motivo de revisión y el detalle técnico.',
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SectionHeader(
            title: document!.sourceFilename,
            subtitle: 'Detalle operativo de la orden y motivo de revisión.',
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              DetailChip(label: 'Cliente', value: document!.customerName ?? document!.customerCode ?? '-'),
              DetailChip(label: 'Ruta', value: document!.routeCode ?? '-'),
              DetailChip(label: 'Entrega', value: document!.deliveryDate == null ? '-' : MaterialLocalizations.of(context).formatShortDate(document!.deliveryDate!)),
              DetailChip(label: 'Estado', value: document!.status.label),
            ],
          ),
          const SizedBox(height: 20),
          Text('Motivos', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
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
          const SizedBox(height: 20),
          Text('Líneas del PDF', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          document!.items.isEmpty
              ? const EmptyStatePanel(
                  title: 'No se extrajeron ítems',
                  message: 'Si el documento no trae líneas confiables, la orden queda en revisión.',
                )
              : ListView.separated(
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
                            children: [
                              Expanded(
                                child: Text(
                                  item.productDescription ?? item.description,
                                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w700),
                                ),
                              ),
                              Text('x${item.quantity}', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              if (item.productCode != null) DetailChip(label: 'Código', value: item.productCode!),
                              DetailChip(label: 'Match', value: item.matchStatus),
                              if (item.pdfCode != null) DetailChip(label: 'PDF', value: item.pdfCode!),
                              if (item.confidence != null) DetailChip(label: 'Confianza', value: item.confidence!.toStringAsFixed(2)),
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
                ),
          const SizedBox(height: 20),
          Card(
            child: Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                leading: const Icon(Icons.tune_rounded),
                title: const Text('Trazabilidad técnica', style: TextStyle(fontWeight: FontWeight.w700)),
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
}
