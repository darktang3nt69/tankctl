import 'package:flutter/material.dart';
import 'package:rive/rive.dart';

class RiveSampleAnimation extends StatelessWidget {
  const RiveSampleAnimation({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 120,
      height: 120,
      child: const RiveAnimation.asset(
        'assets/rive/sample_animation.riv',
        fit: BoxFit.contain,
      ),
    );
  }
}
