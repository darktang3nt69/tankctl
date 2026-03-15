import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:tankctl_app/core/theme/app_theme.dart';

/// Compact sparkline chart rendered with a CustomPainter — no extra packages needed.
///
/// Pass [showAxes]=true (with optional [timestamps]) to enable Y and X axis
/// labels. Used in the detail screen. Dashboard sparklines keep the default
/// [showAxes]=false so they are unaffected.
class TemperatureMiniChart extends StatelessWidget {
  const TemperatureMiniChart({
    super.key,
    required this.data,
    this.height = 60,
    this.color,
    this.thresholdHigh,
    this.thresholdLow,
    this.showAxes = false,
    this.timestamps,
  });

  final List<double> data;
  final double height;
  final Color? color;
  final double? thresholdHigh;
  final double? thresholdLow;
  final bool showAxes;
  final List<DateTime>? timestamps;

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
          showAxes: showAxes,
          timestamps: timestamps,
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
    this.showAxes = false,
    this.timestamps,
  });

  final List<double> data;
  final Color color;
  final double? thresholdHigh;
  final double? thresholdLow;
  final bool showAxes;
  final List<DateTime>? timestamps;

  static const _leftPad = 50.0;
  static const _bottomPad = 28.0;
  static const _axisStyle = TextStyle(
    color: Color(0xFF64748B),
    fontSize: 9,
    height: 1.0,
    fontFamily: 'monospace',
  );

  @override
  void paint(Canvas canvas, Size size) {
    final chartLeft = showAxes ? _leftPad : 0.0;
    final chartBottom = showAxes ? size.height - _bottomPad : size.height;
    final chartWidth = size.width - chartLeft;
    final chartHeight = chartBottom;

    var minVal = data.reduce(math.min);
    var maxVal = data.reduce(math.max);
    if (thresholdLow != null) minVal = math.min(minVal, thresholdLow!);
    if (thresholdHigh != null) maxVal = math.max(maxVal, thresholdHigh!);
    final range = (maxVal - minVal).abs();
    final effectiveRange = range < 0.001 ? 1.0 : range;

    final vPad = chartHeight * 0.10;

    Offset toOffset(int i) {
      final x = chartLeft + chartWidth * i / (data.length - 1);
      final norm = (data[i] - minVal) / effectiveRange;
      final y = chartBottom - vPad - norm * (chartHeight - vPad * 2);
      return Offset(x, y);
    }

    double valueToY(double value) {
      final norm = (value - minVal) / effectiveRange;
      return chartBottom - vPad - norm * (chartHeight - vPad * 2);
    }

    if (showAxes) {
      _drawYAxis(
        canvas,
        size,
        minVal,
        maxVal,
        chartLeft,
        chartHeight,
        chartBottom,
        vPad,
      );
      _drawXAxis(canvas, size, chartLeft, chartWidth, chartBottom);
    }

    final points = List.generate(data.length, toOffset);

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
      ..moveTo(chartLeft, chartBottom)
      ..lineTo(points.first.dx, points.first.dy);
    addCurve(fillPath, points);
    fillPath
      ..lineTo(size.width, chartBottom)
      ..close();

    canvas.drawPath(
      fillPath,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [color.withValues(alpha: 0.28), color.withValues(alpha: 0.0)],
        ).createShader(Rect.fromLTWH(chartLeft, 0, chartWidth, chartBottom)),
    );

    if (thresholdHigh != null) {
      _drawDashedHorizontal(
        canvas,
        y: valueToY(thresholdHigh!),
        color: TankCtlColors.temperature.withValues(alpha: 0.7),
        left: chartLeft,
        right: size.width,
      );
    }
    if (thresholdLow != null) {
      _drawDashedHorizontal(
        canvas,
        y: valueToY(thresholdLow!),
        color: const Color(0xFF93C5FD).withValues(alpha: 0.7),
        left: chartLeft,
        right: size.width,
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

    canvas.drawCircle(points.last, 3, Paint()..color = latestPointColor);
    canvas.drawCircle(
      points.last,
      5,
      Paint()
        ..color = latestPointColor.withValues(alpha: 0.25)
        ..style = PaintingStyle.fill,
    );
  }

  void _drawYAxis(
    Canvas canvas,
    Size size,
    double minVal,
    double maxVal,
    double chartLeft,
    double chartHeight,
    double chartBottom,
    double vPad,
  ) {
    // Vertical axis rule
    canvas.drawLine(
      Offset(chartLeft, 0),
      Offset(chartLeft, chartBottom),
      Paint()
        ..color = const Color(0xFF334155)
        ..strokeWidth = 0.8,
    );

    void paintLabel(double value, double y) {
      final label = '${value.toInt()}°';
      final tp = TextPainter(
        text: TextSpan(text: label, style: _axisStyle),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: chartLeft - 6);
      final x = chartLeft - tp.width - 6;
      tp.paint(canvas, Offset(x, y - tp.height / 2));
    }

    // Three evenly spaced labels: min, mid, max
    final midVal = (minVal + maxVal) / 2;
    final plotH = chartHeight - vPad * 2;
    paintLabel(maxVal, chartBottom - vPad - plotH);
    paintLabel(midVal, chartBottom - vPad - plotH * 0.5);
    paintLabel(minVal, chartBottom - vPad);
  }

  void _drawXAxis(
    Canvas canvas,
    Size size,
    double chartLeft,
    double chartWidth,
    double chartBottom,
  ) {
    // Horizontal axis rule
    canvas.drawLine(
      Offset(chartLeft, chartBottom),
      Offset(size.width, chartBottom),
      Paint()
        ..color = const Color(0xFF334155)
        ..strokeWidth = 0.8,
    );

    if (timestamps == null || timestamps!.isEmpty) return;
    final ts = timestamps!;
    final now = DateTime.now();

    String label(DateTime t) {
      final d = now.difference(t);
      if (d.inMinutes < 2) return 'now';
      if (d.inHours < 1) return '${d.inMinutes}m';
      return '${d.inHours}h ago';
    }

    // Indices to label: first, mid, last
    final indices = <int>{0, ts.length ~/ 2, ts.length - 1}.toList()..sort();

    void paintTimeLabel(int idx, {bool alignRight = false}) {
      final x = chartLeft + chartWidth * idx / (data.length - 1);
      final text = label(ts[idx]);
      final tp = TextPainter(
        text: TextSpan(text: text, style: _axisStyle),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: 44);
      final dx = alignRight
          ? (x - tp.width).clamp(chartLeft, size.width - tp.width)
          : x.clamp(chartLeft, size.width - tp.width);
      tp.paint(canvas, Offset(dx, chartBottom + 4));
    }

    for (int i = 0; i < indices.length; i++) {
      paintTimeLabel(indices[i], alignRight: i == indices.length - 1);
    }
  }

  void _drawDashedHorizontal(
    Canvas canvas, {
    required double y,
    required Color color,
    required double left,
    required double right,
  }) {
    const dash = 5.0;
    const gap = 4.0;
    var x = left;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.2
      ..style = PaintingStyle.stroke;
    while (x < right) {
      final end = math.min(x + dash, right);
      canvas.drawLine(Offset(x, y), Offset(end, y), paint);
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(_SparklinePainter old) =>
      old.data != data ||
      old.color != color ||
      old.thresholdHigh != thresholdHigh ||
      old.thresholdLow != thresholdLow ||
      old.showAxes != showAxes ||
      old.timestamps != timestamps;
}
