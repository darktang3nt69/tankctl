import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';

/// Compact sparkline chart rendered with a CustomPainter — no extra packages needed.
class TemperatureMiniChart extends StatelessWidget {
  const TemperatureMiniChart({
    super.key,
    required this.data,
    this.height = 60,
    this.color,
    this.thresholdHigh,
    this.thresholdLow,
  });

  final List<double> data;
  final double height;
  final Color? color;
  final double? thresholdHigh;
  final double? thresholdLow;

  @override
  Widget build(BuildContext context) {
    final points = data.where((value) => value != 0).toList(growable: false);
    if (points.length < 2) return SizedBox(height: height);
    final lineColor = color ?? Theme.of(context).colorScheme.primary;
    return SizedBox(
      height: height,
      child: CustomPaint(
        size: Size.infinite,
        painter: _SparklinePainter(
          data: points,
          color: lineColor,
          thresholdHigh: thresholdHigh,
          thresholdLow: thresholdLow,
        ),
      ),
    );
  }
}

class _SparklinePainter extends CustomPainter {
  _SparklinePainter({
    required this.data,
    required this.color,
    this.thresholdHigh,
    this.thresholdLow,
  });

  final List<double> data;
  final Color color;
  final double? thresholdHigh;
  final double? thresholdLow;

  @override
  void paint(Canvas canvas, Size size) {
    var minVal = data.reduce(math.min);
    var maxVal = data.reduce(math.max);
    if (thresholdLow != null) {
      minVal = math.min(minVal, thresholdLow!);
    }
    if (thresholdHigh != null) {
      maxVal = math.max(maxVal, thresholdHigh!);
    }
    final range = (maxVal - minVal).abs();
    final effectiveRange = range < 0.001 ? 1.0 : range;

    final vPad = size.height * 0.1;

    Offset toOffset(int i) {
      final x = size.width * i / (data.length - 1);
      final norm = (data[i] - minVal) / effectiveRange;
      final y = size.height - vPad - norm * (size.height - vPad * 2);
      return Offset(x, y);
    }

    double valueToY(double value) {
      final norm = (value - minVal) / effectiveRange;
      return size.height - vPad - norm * (size.height - vPad * 2);
    }

    final points = List.generate(data.length, toOffset);

    // Smooth bezier helper
    void addCurve(Path p, List<Offset> pts) {
      for (int i = 0; i < pts.length - 1; i++) {
        final midX = (pts[i].dx + pts[i + 1].dx) / 2;
        p.cubicTo(
          midX,
          pts[i].dy,
          midX,
          pts[i + 1].dy,
          pts[i + 1].dx,
          pts[i + 1].dy,
        );
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

    if (thresholdHigh != null) {
      _drawDashedHorizontal(
        canvas,
        y: valueToY(thresholdHigh!),
        color: TankCtlColors.temperature.withValues(alpha: 0.7),
        width: size.width,
      );
    }
    if (thresholdLow != null) {
      _drawDashedHorizontal(
        canvas,
        y: valueToY(thresholdLow!),
        color: const Color(0xFF93C5FD).withValues(alpha: 0.7),
        width: size.width,
      );
    }

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

    final latestValue = data.last;
    final breachedHigh = thresholdHigh != null && latestValue > thresholdHigh!;
    final latestPointColor = breachedHigh ? TankCtlColors.temperature : color;

    if (breachedHigh && points.length >= 2) {
      final prev = points[points.length - 2];
      final latest = points.last;
      canvas.drawLine(
        prev,
        latest,
        Paint()
          ..color = TankCtlColors.temperature
          ..strokeWidth = 2.4
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round,
      );
    }

    canvas.drawCircle(
      points.last,
      3,
      Paint()..color = latestPointColor,
    );
    canvas.drawCircle(
      points.last,
      5,
      Paint()
        ..color = latestPointColor.withValues(alpha: 0.25)
        ..style = PaintingStyle.fill,
    );
  }

  void _drawDashedHorizontal(
    Canvas canvas, {
    required double y,
    required Color color,
    required double width,
  }) {
    const dash = 5.0;
    const gap = 4.0;
    var x = 0.0;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.2
      ..style = PaintingStyle.stroke;
    while (x < width) {
      final end = math.min(x + dash, width);
      canvas.drawLine(Offset(x, y), Offset(end, y), paint);
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(_SparklinePainter old) =>
      old.data != data ||
      old.color != color ||
      old.thresholdHigh != thresholdHigh ||
      old.thresholdLow != thresholdLow;
}
