import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../core/models/orders_models.dart';
import '../../../../core/state/app_state.dart';
import '../../../../core/widgets/po_ui.dart';

const Color _bolinRed = Color(0xFFE52421);
const Color _bolinGold = Color(0xFFC8911E);

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  String? _routeFilter;
  DateTime? _dateFilter;
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final groups = state.consolidatedByRouteAndDate;

    final dateOptions = groups.map((group) => group.deliveryDate).whereType<DateTime>().toSet().toList()
      ..sort();

    // La consolidación nunca mezcla fechas de entrega: la fecha viene siempre
    // seleccionada (la más reciente disponible) y el usuario la puede cambiar.
    final effectiveDate = _resolveDate(dateOptions);
    final groupsForDate = [
      for (final group in groups)
        if (effectiveDate != null && _sameDay(group.deliveryDate, effectiveDate)) group,
    ];
    final routeOptions = groupsForDate.map((group) => group.routeCode).toSet().toList()
      ..sort();
    final effectiveRoute =
        _routeFilter != null && routeOptions.contains(_routeFilter) ? _routeFilter : null;
    final filtered = _applyFilters(groups, date: effectiveDate, route: effectiveRoute);

    return AppPageShell(
      title: 'Consolidación',
      subtitle: 'La demanda de las órdenes procesadas por ruta y fecha de entrega, lista para la operación.',
      actions: [
        Tooltip(
          message: 'La exportación a Excel o CSV estará disponible en una próxima versión.',
          child: OutlinedButton.icon(
            onPressed: null,
            icon: const Icon(Icons.file_download_outlined),
            label: const Text('Exportar'),
          ),
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildFilterBar(
            context,
            routeOptions: routeOptions,
            dateOptions: dateOptions,
            effectiveDate: effectiveDate,
            effectiveRoute: effectiveRoute,
          ),
          const SizedBox(height: 16),
          if (filtered.isEmpty)
            const Expanded(
              child: CustomScrollView(
                slivers: [
                  SliverFillRemaining(
                    hasScrollBody: false,
                    child: EmptyStatePanel(
                      title: 'Todavía no hay consolidación',
                      message: 'Cuando existan órdenes procesadas, aquí aparecerá la demanda por ruta y fecha de entrega.',
                    ),
                  ),
                ],
              ),
            )
          else ...[
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final distribution = _CustomerDistribution(
                    groups: filtered,
                    searchQuery: _searchQuery,
                  );
                  final totals = _ProductTotalsPanel(
                    groups: filtered,
                    searchQuery: _searchQuery,
                  );
                  if (constraints.maxWidth >= 900) {
                    return Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(flex: 5, child: distribution),
                        const SizedBox(width: 16),
                        Expanded(flex: 3, child: totals),
                      ],
                    );
                  }
                  return SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(height: 420, child: distribution),
                        const SizedBox(height: 16),
                        SizedBox(height: 420, child: totals),
                      ],
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            _GeneralTotalBar(total: _grandTotal(filtered)),
          ],
        ],
      ),
    );
  }

  Widget _buildFilterBar(
    BuildContext context, {
    required List<String> routeOptions,
    required List<DateTime> dateOptions,
    required DateTime? effectiveDate,
    required String? effectiveRoute,
  }) {
    return BolinCard(
      padding: const EdgeInsets.all(16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final routeDropdown = DropdownButtonFormField<String>(
            initialValue: effectiveRoute,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Ruta', isDense: true),
            icon: const Icon(Icons.local_shipping_outlined),
            items: [
              const DropdownMenuItem<String>(value: null, child: Text('Todas las rutas')),
              for (final route in routeOptions) DropdownMenuItem<String>(value: route, child: Text(route)),
            ],
            onChanged: (value) => setState(() => _routeFilter = value),
          );
          final dateDropdown = DropdownButtonFormField<DateTime>(
            initialValue: effectiveDate,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Fecha de entrega', isDense: true),
            icon: const Icon(Icons.event_rounded),
            items: [
              for (final date in dateOptions)
                DropdownMenuItem<DateTime>(
                  value: date,
                  child: Text(MaterialLocalizations.of(context).formatShortDate(date)),
                ),
            ],
            onChanged: (value) => setState(() => _dateFilter = value),
          );
          final searchField = TextField(
            onChanged: (value) => setState(() => _searchQuery = value),
            decoration: const InputDecoration(
              labelText: 'Buscar cliente o producto',
              isDense: true,
              prefixIcon: Icon(Icons.search_rounded),
            ),
          );

          if (constraints.maxWidth >= 720) {
            return Row(
              children: [
                SizedBox(width: 220, child: routeDropdown),
                const SizedBox(width: 12),
                SizedBox(width: 240, child: dateDropdown),
                const SizedBox(width: 12),
                Expanded(child: searchField),
              ],
            );
          }
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              routeDropdown,
              const SizedBox(height: 12),
              dateDropdown,
              const SizedBox(height: 12),
              searchField,
            ],
          );
        },
      ),
    );
  }

  /// Fecha efectiva de la consolidación: la selección del usuario si sigue
  /// disponible; si no, la fecha más reciente de las existentes.
  DateTime? _resolveDate(List<DateTime> dateOptions) {
    if (dateOptions.isEmpty) {
      return null;
    }
    final selected = _dateFilter;
    if (selected != null) {
      for (final date in dateOptions) {
        if (_sameDay(date, selected)) {
          return date;
        }
      }
    }
    return dateOptions.last;
  }

  List<RouteDateGroupView> _applyFilters(
    List<RouteDateGroupView> groups, {
    required DateTime? date,
    required String? route,
  }) {
    return groups.where((group) {
      if (route != null && group.routeCode != route) {
        return false;
      }
      if (date != null && !_sameDay(group.deliveryDate, date)) {
        return false;
      }
      return true;
    }).toList();
  }

  static bool _sameDay(DateTime? a, DateTime b) {
    return a != null && a.year == b.year && a.month == b.month && a.day == b.day;
  }

  static int _grandTotal(List<RouteDateGroupView> groups) {
    return groups.fold(0, (sum, group) => sum + group.totalQuantity);
  }
}

/// Panel izquierdo: distribución por cliente, expandible, con subtotal visible.
class _CustomerDistribution extends StatelessWidget {
  const _CustomerDistribution({required this.groups, required this.searchQuery});

  final List<RouteDateGroupView> groups;
  final String searchQuery;

  @override
  Widget build(BuildContext context) {
    return BolinCard(
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: SectionHeader(
              title: 'Distribución por cliente',
              subtitle: 'Lo que pide cada cliente de la ruta, con su subtotal.',
            ),
          ),
          const SizedBox(height: 12),
          Flexible(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              itemCount: groups.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, index) => _GroupCard(
                group: groups[index],
                searchQuery: searchQuery,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GroupCard extends StatelessWidget {
  const _GroupCard({required this.group, required this.searchQuery});

  final RouteDateGroupView group;
  final String searchQuery;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateLabel = group.deliveryDate == null
        ? 'Sin fecha'
        : MaterialLocalizations.of(context).formatShortDate(group.deliveryDate!);

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
            child: Row(
              children: [
                Icon(Icons.local_shipping_outlined, size: 20, color: theme.colorScheme.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Ruta ${group.routeCode} • $dateLabel',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
                Text(
                  '${group.orderCount} orden${group.orderCount == 1 ? '' : 'es'}',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
                ),
              ],
            ),
          ),
          for (final customer in _filteredCustomers(group))
            _CustomerTile(customer: customer, searchQuery: searchQuery),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  'Subtotal de la ruta: ',
                  style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline),
                ),
                Text(
                  '${group.totalQuantity} unidades',
                  style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<RouteDateCustomerView> _filteredCustomers(RouteDateGroupView group) {
    final query = searchQuery.trim().toLowerCase();
    if (query.isEmpty) {
      return group.customers;
    }
    return group.customers.where((customer) {
      if (customer.customerName.toLowerCase().contains(query)) {
        return true;
      }
      return customer.productTotals.any((product) => product.productLabel.toLowerCase().contains(query));
    }).toList();
  }
}

class _CustomerTile extends StatefulWidget {
  const _CustomerTile({required this.customer, required this.searchQuery});

  final RouteDateCustomerView customer;
  final String searchQuery;

  @override
  State<_CustomerTile> createState() => _CustomerTileState();
}

class _CustomerTileState extends State<_CustomerTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final customer = widget.customer;
    final products = _filteredProducts(customer);

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 0),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(color: theme.colorScheme.outlineVariant.withValues(alpha: 0.6)),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 10),
              child: Row(
                children: [
                  AnimatedRotation(
                    turns: _expanded ? 0.5 : 0.0,
                    duration: const Duration(milliseconds: 200),
                    child: Icon(Icons.keyboard_arrow_down_rounded, color: theme.colorScheme.outline),
                  ),
                  const SizedBox(width: 8),
                  Icon(Icons.storefront_outlined, color: _bolinGold),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          customer.customerName,
                          style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${customer.orderCount} orden${customer.orderCount == 1 ? '' : 'es'} • '
                          '${products.length} producto${products.length == 1 ? '' : 's'}',
                          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${customer.totalQuantity} unidades',
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: _bolinGold,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
          ),
          AnimatedCrossFade(
            duration: const Duration(milliseconds: 200),
            sizeCurve: Curves.easeInOut,
            firstChild: const SizedBox(width: double.infinity, height: 0),
            secondChild: Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final product in products)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          const SizedBox(width: 28),
                          Expanded(
                            child: Text(
                              product.productLabel,
                              style: theme.textTheme.bodyMedium,
                            ),
                          ),
                          Text(
                            '${product.quantity}',
                            style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(width: 8),
                          Text('uds', style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline)),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            crossFadeState: _expanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
          ),
        ],
      ),
    );
  }

  List<RouteDateProductTotal> _filteredProducts(RouteDateCustomerView customer) {
    final query = widget.searchQuery.trim().toLowerCase();
    if (query.isEmpty) {
      return customer.productTotals;
    }
    return customer.productTotals
        .where((product) => product.productLabel.toLowerCase().contains(query))
        .toList();
  }
}

/// Panel derecho: total por producto sumando todos los clientes filtrados.
class _ProductTotalsPanel extends StatelessWidget {
  const _ProductTotalsPanel({required this.groups, required this.searchQuery});

  final List<RouteDateGroupView> groups;
  final String searchQuery;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final products = _aggregateProducts();

    return BolinCard(
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, 0),
            child: SectionHeader(
              title: 'Total por producto',
              subtitle: 'Suma de lo que piden todos los clientes de la selección.',
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: products.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text(
                        'Ningún producto coincide con la búsqueda.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                    itemCount: products.length + 1,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      if (index == products.length) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Row(
                            children: [
                              const Expanded(
                                child: Text(
                                  'TOTAL GENERAL',
                                  style: TextStyle(fontWeight: FontWeight.w800),
                                ),
                              ),
                              Text(
                                '${_grandTotal()}',
                                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                              ),
                            ],
                          ),
                        );
                      }
                      final product = products[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                product.productLabel,
                                style: theme.textTheme.bodyMedium,
                              ),
                            ),
                            Text(
                              '${product.quantity}',
                              style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'uds',
                              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  List<RouteDateProductTotal> _aggregateProducts() {
    final query = searchQuery.trim().toLowerCase();
    final map = <String, int>{};
    for (final group in groups) {
      for (final product in group.productTotals) {
        if (query.isNotEmpty && !product.productLabel.toLowerCase().contains(query)) {
          continue;
        }
        map[product.productLabel] = (map[product.productLabel] ?? 0) + product.quantity;
      }
    }
    return [
      for (final entry in map.entries)
        RouteDateProductTotal(productLabel: entry.key, quantity: entry.value),
    ]..sort((a, b) => b.quantity.compareTo(a.quantity));
  }

  int _grandTotal() {
    return groups.fold(0, (sum, group) => sum + group.totalQuantity);
  }
}

/// Barra sticky inferior con el total general: roja Grupo Bolin, texto blanco.
class _GeneralTotalBar extends StatelessWidget {
  const _GeneralTotalBar({required this.total});

  final int total;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      decoration: BoxDecoration(
        color: _bolinRed,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.12),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          const Icon(Icons.warehouse_rounded, color: Colors.white),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Total general',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w800,
                fontSize: 16,
              ),
            ),
          ),
          Text(
            '$total unidades',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                ),
          ),
        ],
      ),
    );
  }
}
