import 'package:flutter/material.dart';

import '../models/orders_models.dart';

class BolinCard extends StatelessWidget {
  const BolinCard({super.key, required this.child, this.padding, this.margin});

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      padding: padding ?? const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 18,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: child,
    );
  }
}

class SectionHeader extends StatelessWidget {
  const SectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
              if (subtitle case final sub?) ...[
                const SizedBox(height: 4),
                Text(sub, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline)),
              ],
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}

class MetricTile extends StatelessWidget {
  const MetricTile({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    required this.tint,
    this.delta,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color tint;
  final String? delta;

  @override
  Widget build(BuildContext context) {
    return BolinCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: tint.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Icon(icon, size: 16, color: tint),
              ),
              const Spacer(),
              if (delta != null)
                Flexible(
                  child: Text(
                    delta!,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(color: tint, fontWeight: FontWeight.w700),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.outline),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.status});

  final OrderProcessingStatus status;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final palette = switch (status) {
      OrderProcessingStatus.processed => (bg: const Color(0xFFE7F6EA), fg: const Color(0xFF1F7A3D)),
      OrderProcessingStatus.reviewRequired => (bg: const Color(0xFFFFF4D6), fg: const Color(0xFF9A6A00)),
      OrderProcessingStatus.noMatch => (bg: const Color(0xFFF4F5F7), fg: const Color(0xFF636A72)),
      OrderProcessingStatus.error => (bg: const Color(0xFFFDE7E6), fg: const Color(0xFFB42318)),
      OrderProcessingStatus.unknown => (bg: const Color(0xFFEFEFEF), fg: const Color(0xFF4B5563)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: palette.bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: palette.fg.withValues(alpha: 0.16)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(status.icon, size: 16, color: palette.fg),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              status.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.labelSmall?.copyWith(color: palette.fg, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class EmptyStatePanel extends StatelessWidget {
  const EmptyStatePanel({
    super.key,
    required this.title,
    required this.message,
    this.action,
  });

  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.inbox_rounded, size: 54, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(title, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline),
            ),
            if (action != null) ...[
              const SizedBox(height: 20),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}

class AppPageShell extends StatelessWidget {
  const AppPageShell({
    super.key,
    required this.title,
    required this.subtitle,
    required this.child,
    this.actions,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surfaceContainerLowest,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              LayoutBuilder(
                builder: (context, constraints) {
                  final isNarrow = constraints.maxWidth < 650;
                  if (isNarrow && actions != null && actions!.isNotEmpty) {
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 6),
                        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.outline)),
                        const SizedBox(height: 12),
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: actions!,
                          ),
                        ),
                      ],
                    );
                  }
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                            const SizedBox(height: 6),
                            Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.outline)),
                          ],
                        ),
                      ),
                      if (actions != null && actions!.isNotEmpty) ...[
                        const SizedBox(width: 16),
                        Wrap(spacing: 12, runSpacing: 12, children: actions!),
                      ],
                    ],
                  );
                },
              ),
              const SizedBox(height: 20),
              Expanded(child: child),
            ],
          ),
        ),
      ),
    );
  }
}

class DetailChip extends StatelessWidget {
  const DetailChip({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Theme.of(context).colorScheme.outline)),
          const SizedBox(height: 2),
          Text(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
