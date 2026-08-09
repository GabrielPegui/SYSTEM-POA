import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class RoutesPage extends StatelessWidget {
  const RoutesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final rows = state.consolidatedByRoute;

    return AppPageShell(
      title: 'Rutas',
      subtitle: 'Distribución operacional agrupada por ruta de entrega.',
      child: SingleChildScrollView(
        child: BolinCard(
          child: rows.isEmpty
              ? const EmptyStatePanel(
                  title: 'Sin rutas consolidadas',
                  message: 'La vista por ruta se completará cuando existan órdenes procesadas.',
                )
              : SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Ruta')),
                      DataColumn(label: Text('Cantidad')),
                      DataColumn(label: Text('Clientes')),
                      DataColumn(label: Text('Productos')),
                      DataColumn(label: Text('Detalle')),
                    ],
                    rows: [
                      for (final row in rows)
                        DataRow(
                          cells: [
                            DataCell(Text(row.label)),
                            DataCell(Text(row.totalQuantity.toString())),
                            DataCell(Text(row.customers.join(', '))),
                            DataCell(Text(row.products.join(', '))),
                            DataCell(Text(row.lines.length.toString())),
                          ],
                        ),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
