import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme.dart';

class GlassCard extends StatelessWidget {
  final Widget child;
  final double blur;
  final double opacity;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final Color? borderColor;
  final List<Color>? gradientColors;

  const GlassCard({
    Key? key,
    required this.child,
    this.blur = 15,
    this.opacity = 0.1,
    this.borderRadius = 16,
    this.padding = const EdgeInsets.all(16),
    this.borderColor,
    this.gradientColors,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          decoration: BoxDecoration(
            color: (gradientColors != null) 
                ? null 
                : (Theme.of(context).brightness == Brightness.dark 
                    ? Colors.white.withOpacity(opacity)
                    : Colors.white.withOpacity(opacity == 0.1 ? 0.66 : opacity)),
            gradient: (gradientColors != null)
                ? LinearGradient(
                    colors: gradientColors!.map((c) => c.withOpacity(opacity)).toList(),
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  )
                : null,
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(
              color: borderColor ?? (Theme.of(context).brightness == Brightness.dark 
                  ? Colors.white.withOpacity(0.12) 
                  : const Color(0x1A1B2A6B)),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: Theme.of(context).brightness == Brightness.dark
                    ? Colors.black.withOpacity(0.2)
                    : const Color(0x0C0B1023),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          padding: padding,
          child: child,
        ),
      ),
    );
  }
}
