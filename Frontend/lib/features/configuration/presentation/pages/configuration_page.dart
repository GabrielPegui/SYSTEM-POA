import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/config/app_config.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

class ConfigurationPage extends StatelessWidget {
  const ConfigurationPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return AppPageShell(
      title: 'Configuración',
      subtitle: 'Estado del sistema y parámetros de operación.',
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SectionHeader(
              title: 'Estado del sistema',
              subtitle: 'Cómo está conectada la operación en este momento.',
            ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) {
                final cols = constraints.maxWidth >= 1000 ? 3 : (constraints.maxWidth >= 600 ? 2 : 1);
                return GridView.count(
                  crossAxisCount: cols,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  childAspectRatio: 1.5,
                  children: [
                    _SettingCard(
                      title: 'Sistema conectado',
                      value: state.usingDemoData ? 'Vista de demostración' : 'Conectado',
                      icon: state.usingDemoData ? Icons.science_outlined : Icons.cloud_done_outlined,
                      caption: state.usingDemoData
                          ? 'Datos de ejemplo para revisar la interfaz.'
                          : 'El sistema se comunica con el servidor.',
                    ),
                    _SettingCard(
                      title: 'Backend disponible',
                      value: state.loading ? 'Sincronizando' : 'Disponible',
                      icon: state.loading ? Icons.sync_rounded : Icons.check_circle_rounded,
                      caption: state.errorMessage ?? 'La operación está disponible.',
                    ),
                    _SettingCard(
                      title: 'Última sincronización',
                      value: state.lastSyncAt == null
                          ? 'Sin sincronizar'
                          : MaterialLocalizations.of(context).formatShortDate(state.lastSyncAt!),
                      icon: Icons.schedule_rounded,
                      caption: 'Hora de la última carga de datos del servidor.',
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 28),
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
            const SizedBox(height: 28),
            const SectionHeader(
              title: 'Diagnóstico técnico',
              subtitle: 'Información para soporte técnico. No afecta la operación diaria.',
            ),
            const SizedBox(height: 16),
            Card(
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
              ),
              child: Theme(
                data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  tilePadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  leading: const Icon(Icons.tune_rounded),
                  title: const Text('Detalles técnicos', style: TextStyle(fontWeight: FontWeight.w700)),
                  subtitle: const Text('Solo para soporte.'),
                  childrenPadding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                  children: [
                    _DiagnosticRow(
                      label: 'API base',
                      value: AppConfig.apiBaseUrl,
                      icon: Icons.link_rounded,
                    ),
                    const Divider(height: 24),
                    _DiagnosticRow(
                      label: 'Procesadas',
                      value: state.snapshot.processedCount.toString(),
                      icon: Icons.check_circle_outline_rounded,
                    ),
                    const Divider(height: 24),
                    _DiagnosticRow(
                      label: 'Requieren revisión',
                      value: state.snapshot.reviewRequiredCount.toString(),
                      icon: Icons.rule_rounded,
                    ),
                    if (state.bannerMessage.isNotEmpty) ...[
                      const Divider(height: 24),
                      _DiagnosticRow(
                        label: 'Mensaje del sistema',
                        value: state.bannerMessage,
                        icon: Icons.info_outline_rounded,
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SettingCard extends StatelessWidget {
  const _SettingCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.caption,
  });

  final String title;
  final String value;
  final IconData icon;
  final String caption;

  @override
  Widget build(BuildContext context) {
    return BolinCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: Theme.of(context).colorScheme.primary),
          ),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(value, style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text(caption, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline)),
        ],
      ),
    );
  }
}

class _DiagnosticRow extends StatelessWidget {
  const _DiagnosticRow({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: theme.colorScheme.outline),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.outline),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
