import 'package:flutter/material.dart';

/// Reusable placeholder used by feature screens until they are implemented.
class FeaturePlaceholder extends StatelessWidget {
  const FeaturePlaceholder({super.key, required this.title, this.description});

  final String title;
  final String? description;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.construction_outlined,
              size: 56,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(title, style: theme.textTheme.headlineSmall),
            if (description != null) ...[
              const SizedBox(height: 8),
              Text(
                description!,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
