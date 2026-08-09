import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class CustomersPage extends StatelessWidget {
  const CustomersPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final rows = state.consolidatedByCustomer;

    return AppPageShell(
      title: 'Clientes',
      subtitle: 'Vista operativa de cuentas y su demanda acumulada.',
      child: SingleChildScrollView(
        child: BolinCard(
          child: rows.isEmpty
              ? const EmptyStatePanel(
                  title: 'Sin clientes consolidados',
                  message: 'Cuando existan órdenes procesadas, aquí verás el catálogo operativo por cliente.',
                )
              : SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Cliente')),
                      DataColumn(label: Text('Ruta')),
                      DataColumn(label: Text('Productos')),
                      DataColumn(label: Text('Cantidad')),
                      DataColumn(label: Text('Detalle')),
                    ],
                    rows: [
                      for (final row in rows)
                        DataRow(
                          cells: [
                            DataCell(Text(row.label)),
                            DataCell(Text(row.routes.isEmpty ? '-' : row.routes.join(', '))),
                            DataCell(Text(row.products.isEmpty ? '-' : row.products.join(', '))),
                            DataCell(Text(row.totalQuantity.toString())),
                            DataCell(
                              Text(
                                row.lines.isEmpty
                                    ? '-'
                                    : '${row.lines.first.customerLabel} / ${row.lines.first.routeLabel}',
                              ),
                            ),
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
