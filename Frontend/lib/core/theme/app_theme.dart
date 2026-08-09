import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color _bolinYellow = Color(0xFFFFC400);
  static const Color _bolinRed = Color(0xFFE52421);
  static const Color _bolinGold = Color(0xFFC8911E);
  static const Color _bolinDark = Color(0xFF221F1F);
  static const Color _bolinWhite = Color(0xFFFFFFFF);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: _bolinYellow,
      brightness: Brightness.light,
      primary: _bolinYellow,
      secondary: _bolinRed,
      tertiary: _bolinGold,
      surface: _bolinWhite,
      onSurface: _bolinDark,
    ).copyWith(
      primary: _bolinYellow,
      onPrimary: _bolinDark,
      secondary: _bolinRed,
      onSecondary: _bolinWhite,
      tertiary: _bolinGold,
      onTertiary: _bolinDark,
      surface: _bolinWhite,
      onSurface: _bolinDark,
      outline: const Color(0xFF9C9C9C),
      outlineVariant: const Color(0xFFE1DED9),
      surfaceContainerLowest: const Color(0xFFFDFDFB),
      surfaceContainerLow: const Color(0xFFF7F5F0),
      surfaceContainer: const Color(0xFFF2EFE8),
      surfaceContainerHigh: const Color(0xFFECE8DE),
      surfaceContainerHighest: const Color(0xFFE4DECF),
      error: _bolinRed,
      onError: _bolinWhite,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      brightness: Brightness.light,
      scaffoldBackgroundColor: scheme.surfaceContainerLowest,
      visualDensity: VisualDensity.standard,
    );

    return base.copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surfaceContainerLowest,
        foregroundColor: _bolinDark,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: base.textTheme.titleLarge?.copyWith(
          color: _bolinDark,
          fontWeight: FontWeight.w800,
        ),
      ),
      cardTheme: CardThemeData(
        color: scheme.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        margin: EdgeInsets.zero,
      ),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant, thickness: 1),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: scheme.surfaceContainerLowest,
        selectedIconTheme: const IconThemeData(color: _bolinYellow),
        selectedLabelTextStyle: const TextStyle(
          color: _bolinDark,
          fontWeight: FontWeight.w700,
        ),
        unselectedIconTheme: IconThemeData(color: _bolinDark.withValues(alpha: 0.72)),
        unselectedLabelTextStyle: TextStyle(
          color: _bolinDark.withValues(alpha: 0.72),
          fontWeight: FontWeight.w600,
        ),
      ),
      textTheme: base.textTheme.copyWith(
        displayLarge: base.textTheme.displayLarge?.copyWith(
          color: _bolinDark,
          fontWeight: FontWeight.w800,
        ),
        headlineLarge: base.textTheme.headlineLarge?.copyWith(
          color: _bolinDark,
          fontWeight: FontWeight.w800,
        ),
        headlineMedium: base.textTheme.headlineMedium?.copyWith(
          color: _bolinDark,
          fontWeight: FontWeight.w800,
        ),
        titleLarge: base.textTheme.titleLarge?.copyWith(
          color: _bolinDark,
          fontWeight: FontWeight.w700,
        ),
        bodyLarge: base.textTheme.bodyLarge?.copyWith(color: _bolinDark),
        bodyMedium: base.textTheme.bodyMedium?.copyWith(color: _bolinDark),
        labelLarge: base.textTheme.labelLarge?.copyWith(color: _bolinDark),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: scheme.primary, width: 1.6),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: scheme.surfaceContainerLow,
        selectedColor: scheme.primary.withValues(alpha: 0.16),
        side: BorderSide(color: scheme.outlineVariant),
        labelStyle: base.textTheme.labelLarge?.copyWith(color: _bolinDark),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: _bolinDark,
        unselectedLabelColor: _bolinDark.withValues(alpha: 0.6),
        indicatorColor: _bolinYellow,
        indicatorSize: TabBarIndicatorSize.label,
        labelStyle: base.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w700),
        unselectedLabelStyle: base.textTheme.labelLarge,
      ),
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(
          color: _bolinDark,
          borderRadius: BorderRadius.circular(8),
        ),
        textStyle: const TextStyle(color: _bolinWhite),
      ),
    );
  }
}
