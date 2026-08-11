import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class ConfigurationPage extends StatelessWidget {
  const ConfigurationPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return AppPageShell(
      title: 'Configuración',
      subtitle: 'Parámetros de operación y documentos procesados en esta sesión.',
      actions: [
        OutlinedButton.icon(
          onPressed: () => _confirmClearSession(context, state),
          icon: const Icon(Icons.delete_sweep_outlined),
          label: const Text('Vaciar data'),
        ),
      ],
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SectionHeader(
              title: 'PDFs procesados',
              subtitle: 'Documentos procesados en esta sesión, con su fecha de procesamiento.',
            ),
            const SizedBox(height: 16),
            BolinCard(
              padding: const EdgeInsets.all(0),
              child: state.snapshot.sessionDocuments.isEmpty
                  ? const Padding(
                      padding: EdgeInsets.all(20),
                      child: EmptyStatePanel(
                        title: 'Aún no se procesaron PDFs',
                        message: 'Los documentos que importes aparecerán aquí con su fecha de procesamiento.',
                      ),
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          padding: const EdgeInsets.all(20),
                          child: DataTable(
                            columns: const [
                              DataColumn(label: Text('PDF')),
                              DataColumn(label: Text('Fecha de procesamiento')),
                              DataColumn(label: Text('Estado')),
                            ],
                            rows: [
                              for (final document in state.snapshot.sessionDocuments)
                                DataRow(
                                  cells: [
                                    DataCell(Text(
                                      document.sourceFilename,
                                      overflow: TextOverflow.ellipsis,
                                      maxLines: 1,
                                    )),
                                    DataCell(Text(
                                      document.receivedAt == null
                                          ? '-'
                                          : MaterialLocalizations.of(context).formatShortDate(document.receivedAt!),
                                    )),
                                    DataCell(StatusPill(status: document.status)),
                                  ],
                                ),
                            ],
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

  Future<void> _confirmClearSession(BuildContext context, AppState state) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('¿Vaciar la sesión?'),
        content: const Text(
          'Se quitarán los documentos importados en esta sesión y la selección actual. '
          'Las órdenes persistidas en el servidor no se eliminan.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Vaciar'),
          ),
        ],
      ),
    );
    if (confirmed ?? false) {
      state.clearSession();
    }
  }
}