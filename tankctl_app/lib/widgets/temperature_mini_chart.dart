import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Compact sparkline chart rendered with a CustomPainter — no extra packages needed.
class TemperatureMiniChart extends StatelessWidget {
  const TemperatureMiniChart({
    super.key,
    required this.data,
    this.height = 60,
    this.color,
  });

  final List<double> data;
  final double height;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    if (data.length < 2) return SizedBox(height: height);
    final lineColor = color ?? Theme.of(context).colorScheme.primary;
    return SizedBox(
      height: height,
      child: CustomPaint(
        size: Size.infinite,
        painter: _SparklinePainter(data: data, color: lineColor),
      ),
    );
  }
}

class _SparklinePainter extends CustomPainter {
  _SparklinePainter({required this.data, required this.color});

  final List<double> data;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final minVal = data.reduce(math.min);
    final maxVal = data.reduce(math.max);
    final range = (maxVal - minVal).abs();
    final effectiveRange = range < 0.001 ? 1.0 : range;

    final vPad = size.height * 0.1;

    Offset toOffset(int i) {
      final x = size.width * i / (data.length - 1);
      final norm = (data[i] - minVal) / effectiveRange;
      final y = size.height - vPad - norm * (size.height - vPad * 2);
      return Offset(x, y);
    }

    final points = List.generate(data.length, toOffset);

    // Smooth bezier helper
    void addCurve(Path p, List<Offset> pts) {
      for (int i = 0; i < pts.length - 1; i++) {
        final midX = (pts[i].dx + pts[i + 1].dx) / 2;
        p.cubicTo(midX, pts[i].dy, midX, pts[i + 1].dy, pts[i + 1].dx, pts[i + 1].dy);
      }
    }

    // Gradient fill
    final fillPath = Path()
      ..moveTo(0, size.height)
      ..lineTo(points.first.dx, points.first.dy);
    addCurve(fillPath, points);
    fillPath
      ..lineTo(size.width, size.height)
      ..close();

    canvas.drawPath(
      fillPath,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [color.withValues(alpha: 0.28), color.withValues(alpha: 0.0)],
        ).createShader(Rect.fromLTWH(0, 0, size.width, size.height)),
    );

    // Line
    final linePath = Path()..moveTo(points.first.dx, points.first.dy);
    addCurve(linePath, points);

    canvas.drawPath(
      linePath,
      Paint()
        ..color = color
        ..strokeWidth = 2.0
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(_SparklinePainter old) =>
      old.data != data || old.color != color;
}
