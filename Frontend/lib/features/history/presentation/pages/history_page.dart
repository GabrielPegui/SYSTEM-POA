import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/models/orders_models.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final grouping = state.groupingIndex;

    return AppPageShell(
      title: 'Consolidación',
      subtitle: 'Lo importante no es el PDF, sino la demanda agregada que deja para la operación.',
      actions: [
        Tooltip(
          message: 'La exportación a Excel o CSV estará disponible en una próxima versión.',
          child: OutlinedButton.icon(
            onPressed: null,
            icon: const Icon(Icons.file_download_outlined),
            label: const Text('Exportar'),
          ),
        ),
        SegmentedButton<int>(
          segments: const [
            ButtonSegment<int>(value: 0, label: Text('Producto'), icon: Icon(Icons.inventory_2_outlined)),
            ButtonSegment<int>(value: 1, label: Text('Cliente'), icon: Icon(Icons.people_alt_outlined)),
            ButtonSegment<int>(value: 2, label: Text('Ruta'), icon: Icon(Icons.route_outlined)),
            ButtonSegment<int>(value: 3, label: Text('Fecha'), icon: Icon(Icons.calendar_month_outlined)),
          ],
          selected: {grouping},
          onSelectionChanged: (selection) => state.setGroupingIndex(selection.first),
        ),
      ],
      child: SingleChildScrollView(
        child: BolinCard(
          child: _GroupedConsolidation(
            groupingIndex: grouping,
            byProduct: state.consolidatedByProduct,
            byCustomer: state.consolidatedByCustomer,
            byRoute: state.consolidatedByRoute,
            byDate: state.consolidatedByDate,
          ),
        ),
      ),
    );
  }
}

class _GroupedConsolidation extends StatelessWidget {
  const _GroupedConsolidation({
    required this.groupingIndex,
    required this.byProduct,
    required this.byCustomer,
    required this.byRoute,
    required this.byDate,
  });

  final int groupingIndex;
  final List<ConsolidatedProductView> byProduct;
  final List<ConsolidatedEntityView> byCustomer;
  final List<ConsolidatedEntityView> byRoute;
  final List<ConsolidatedEntityView> byDate;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final columns = switch (groupingIndex) {
      0 => const ['Producto', 'Cantidad', 'Clientes', 'Rutas', 'Entrega', 'Detalle'],
      1 => const ['Cliente', 'Cantidad', 'Productos', 'Rutas', 'Detalle'],
      2 => const ['Ruta', 'Cantidad', 'Clientes', 'Productos', 'Detalle'],
      _ => const ['Fecha', 'Cantidad', 'Clientes', 'Rutas', 'Detalle'],
    };

    final rows = switch (groupingIndex) {
      0 => byProduct
          .map(
            (item) => (
              key: item.productLabel,
              quantity: item.totalQuantity,
              chips: '${item.customers.length} clientes',
              routes: item.routes.join(', '),
              dates: item.deliveryDates,
              detail: item.breakdown,
            ),
          )
          .toList(),
      1 => byCustomer
          .map(
            (item) => (
              key: item.label,
              quantity: item.totalQuantity,
              chips: '${item.products.length} productos',
              routes: item.routes.join(', '),
              dates: const <String>{},
              detail: item.lines,
            ),
          )
          .toList(),
      2 => byRoute
          .map(
            (item) => (
              key: item.label,
              quantity: item.totalQuantity,
              chips: '${item.customers.length} clientes',
              routes: item.products.join(', '),
              dates: const <String>{},
              detail: item.lines,
            ),
          )
          .toList(),
      _ => byDate
          .map(
            (item) => (
              key: item.label,
              quantity: item.totalQuantity,
              chips: '${item.customers.length} clientes',
              routes: item.routes.join(', '),
              dates: const <String>{},
              detail: item.lines,
            ),
          )
          .toList(),
    };

    if (rows.isEmpty) {
      return const EmptyStatePanel(
        title: 'Todavía no hay consolidación',
        message: 'Cuando existan órdenes procesadas, aquí aparecerá la demanda agrupada por el criterio elegido.',
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: switch (groupingIndex) {
            0 => 'Agrupación por producto',
            1 => 'Agrupación por cliente',
            2 => 'Agrupación por ruta',
            _ => 'Agrupación por fecha',
          },
          subtitle: 'Tabla expandible para análisis rápido y detallado.',
        ),
        const SizedBox(height: 16),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: [
              for (final column in columns) DataColumn(label: Text(column)),
            ],
            rows: [
              for (final row in rows)
                DataRow(
                  cells: [
                    DataCell(Text(
                      groupingIndex == 3 ? _formatIsoDate(row.key) : row.key,
                    )),
                    DataCell(Text(row.quantity.toString())),
                    DataCell(Text(row.chips)),
                    DataCell(Text(row.routes.isEmpty ? '-' : row.routes)),
                    if (groupingIndex == 0)
                      DataCell(Text(
                        row.dates.isEmpty
                            ? '-'
                            : row.dates.map(_formatIsoDate).join(', '),
                      )),
                    DataCell(
                      TextButton(
                        onPressed: () {
                          showDialog<void>(
                            context: context,
                            builder: (dialogContext) {
                              return AlertDialog(
                                title: Text(
                                  groupingIndex == 3 ? _formatIsoDate(row.key) : row.key,
                                ),
                                content: SizedBox(
                                  width: 560,
                                  child: ListView.separated(
                                    shrinkWrap: true,
                                    itemCount: row.detail.length,
                                    separatorBuilder: (_, _) => const SizedBox(height: 10),
                                    itemBuilder: (context, index) {
                                      final line = row.detail[index];
                                      return ListTile(
                                        contentPadding: EdgeInsets.zero,
                                        title: Text(line.productLabel ?? line.customerLabel),
                                        subtitle: Text(
                                          [
                                            line.customerLabel,
                                            line.routeLabel,
                                            if (line.deliveryDate != null)
                                              MaterialLocalizations.of(context).formatShortDate(line.deliveryDate!),
                                          ].join(' • '),
                                        ),
                                        trailing: Text('x${line.quantity}', style: theme.textTheme.titleSmall),
                                      );
                                    },
                                  ),
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.of(dialogContext).pop(),
                                    child: const Text('Cerrar'),
                                  ),
                                ],
                              );
                            },
                          );
                        },
                        child: const Text('Ver detalle'),
                      ),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ],
    );
  }
}

String _formatIsoDate(String isoDate) {
  final parsed = DateTime.tryParse(isoDate);
  if (parsed == null) return isoDate;
  final dd = parsed.day.toString().padLeft(2, '0');
  final mm = parsed.month.toString().padLeft(2, '0');
  return '$dd/$mm/${parsed.year}';
}
