import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class ProductsPage extends StatelessWidget {
  const ProductsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final rows = state.consolidatedByProduct;

    return AppPageShell(
      title: 'Productos',
      subtitle: 'Demanda agregada por producto, con detalle por cliente y ruta.',
      child: SingleChildScrollView(
        child: BolinCard(
          child: rows.isEmpty
              ? const EmptyStatePanel(
                  title: 'Sin productos consolidados',
                  message: 'Cuando haya órdenes procesadas, esta vista mostrará cantidades y distribución por producto.',
                )
              : SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Producto')),
                      DataColumn(label: Text('Cantidad')),
                      DataColumn(label: Text('Clientes')),
                      DataColumn(label: Text('Rutas')),
                      DataColumn(label: Text('Entrega')),
                    ],
                    rows: [
                      for (final row in rows)
                        DataRow(
                          cells: [
                            DataCell(Text(row.productLabel)),
                            DataCell(Text(row.totalQuantity.toString())),
                            DataCell(Text(row.customers.join(', '))),
                            DataCell(Text(row.routes.join(', '))),
                            DataCell(Text(row.deliveryDates.join(', '))),
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
