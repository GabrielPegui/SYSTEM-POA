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
      subtitle: 'Parámetros visibles para operación y diagnóstico rápido.',
      child: SingleChildScrollView(
        child: LayoutBuilder(
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
            title: 'API base',
            value: AppConfig.apiBaseUrl,
            icon: Icons.link_rounded,
            caption: 'Contrato del backend activo para esta sesión.',
          ),
          _SettingCard(
            title: 'Datos',
            value: state.usingDemoData ? 'Demostración local' : 'Backend real',
            icon: state.usingDemoData ? Icons.science_outlined : Icons.cloud_done_outlined,
            caption: state.bannerMessage.isEmpty ? 'Sin mensaje adicional.' : state.bannerMessage,
          ),
          _SettingCard(
            title: 'Sincronización',
            value: state.loading ? 'Cargando' : 'Lista',
            icon: Icons.sync_rounded,
            caption: state.errorMessage ?? 'La sesión está lista para operar.',
          ),
          _SettingCard(
            title: 'Recepciones',
            value: state.snapshot.totalIncoming.toString(),
            icon: Icons.inbox_rounded,
            caption: 'Documentos visibles en esta sesión.',
          ),
          _SettingCard(
            title: 'Procesadas',
            value: state.snapshot.processedCount.toString(),
            icon: Icons.check_circle_rounded,
            caption: 'Órdenes que lograron avanzar sin fricción.',
          ),
          _SettingCard(
            title: 'Revisión',
            value: state.snapshot.reviewRequiredCount.toString(),
            icon: Icons.rule_rounded,
            caption: 'Casos que necesitan atención humana.',
          ),
        ],
      );
    },
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
