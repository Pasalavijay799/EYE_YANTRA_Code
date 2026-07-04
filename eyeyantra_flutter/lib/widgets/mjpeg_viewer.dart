import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class MjpegViewer extends StatefulWidget {
  final String url;
  final double? width;
  final double? height;
  final Widget? placeholder;
  final Widget? errorWidget;

  const MjpegViewer({
    Key? key,
    required this.url,
    this.width,
    this.height,
    this.placeholder,
    this.errorWidget,
  }) : super(key: key);

  @override
  State<MjpegViewer> createState() => _MjpegViewerState();
}

class _MjpegViewerState extends State<MjpegViewer> with SingleTickerProviderStateMixin {
  StreamSubscription? _subscription;
  Uint8List? _frameBytes;
  bool _hasError = false;
  bool _isConnecting = true;
  http.Client? _client;
  AnimationController? _animController;

  @override
  void initState() {
    super.initState();
    if (widget.url == 'mock') {
      _animController = AnimationController(
        vsync: this,
        duration: const Duration(seconds: 3),
      )..repeat(reverse: true);
    }
    _startStreaming();
  }

  @override
  void didUpdateWidget(covariant MjpegViewer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.url != widget.url) {
      if (widget.url == 'mock') {
        _animController ??= AnimationController(
          vsync: this,
          duration: const Duration(seconds: 3),
        )..repeat(reverse: true);
      } else {
        _animController?.dispose();
        _animController = null;
      }
      _stopStreaming();
      _startStreaming();
    }
  }

  @override
  void dispose() {
    _animController?.dispose();
    _stopStreaming();
    super.dispose();
  }

  void _stopStreaming() {
    _subscription?.cancel();
    _subscription = null;
    _client?.close();
    _client = null;
  }

  void _startStreaming() async {
    if (widget.url == 'mock') {
      if (mounted) {
        setState(() {
          _hasError = false;
          _isConnecting = false;
        });
      }
      return;
    }

    if (!mounted) return;
    setState(() {
      _hasError = false;
      _isConnecting = true;
      _frameBytes = null;
    });

    _client = http.Client();
    try {
      final request = http.Request('GET', Uri.parse(widget.url));
      final response = await _client!.send(request).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        throw Exception('Stream returned status ${response.statusCode}');
      }

      if (mounted) {
        setState(() {
          _isConnecting = false;
        });
      }

      List<int> buffer = [];
      _subscription = response.stream.listen(
        (chunk) {
          buffer.addAll(chunk);

          while (true) {
            int startIndex = -1;
            int endIndex = -1;

            // Find SOI (Start Of Image) 0xFF 0xD8
            for (int i = 0; i < buffer.length - 1; i++) {
              if (buffer[i] == 0xFF && buffer[i + 1] == 0xD8) {
                startIndex = i;
                break;
              }
            }

            if (startIndex == -1) {
              if (buffer.length > 524288) {
                buffer.clear();
              }
              break;
            }

            // Find EOI (End Of Image) 0xFF 0xD9
            for (int i = startIndex; i < buffer.length - 1; i++) {
              if (buffer[i] == 0xFF && buffer[i + 1] == 0xD9) {
                endIndex = i + 1;
                break;
              }
            }

            if (endIndex == -1) {
              break;
            }

            final frame = Uint8List.fromList(buffer.sublist(startIndex, endIndex + 1));
            
            if (mounted) {
              setState(() {
                _frameBytes = frame;
              });
            }

            buffer = buffer.sublist(endIndex + 1);
          }
        },
        onError: (e) {
          debugPrint('Stream error: $e');
          if (mounted) {
            setState(() {
              _hasError = true;
              _isConnecting = false;
            });
          }
        },
        cancelOnError: true,
      );
    } catch (e) {
      debugPrint('Connection error: $e');
      if (mounted) {
        setState(() {
          _hasError = true;
          _isConnecting = false;
        });
      }
    }
  }

  Widget _buildCornerBrackets({required Size size}) {
    return Positioned.fill(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Stack(
          children: [
            Align(
              alignment: Alignment.topLeft,
              child: Container(
                width: size.width,
                height: size.height,
                decoration: const BoxDecoration(
                  border: Border(
                    top: BorderSide(color: Colors.white30, width: 2),
                    left: BorderSide(color: Colors.white30, width: 2),
                  ),
                ),
              ),
            ),
            Align(
              alignment: Alignment.topRight,
              child: Container(
                width: size.width,
                height: size.height,
                decoration: const BoxDecoration(
                  border: Border(
                    top: BorderSide(color: Colors.white30, width: 2),
                    right: BorderSide(color: Colors.white30, width: 2),
                  ),
                ),
              ),
            ),
            Align(
              alignment: Alignment.bottomLeft,
              child: Container(
                width: size.width,
                height: size.height,
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: Colors.white30, width: 2),
                    left: BorderSide(color: Colors.white30, width: 2),
                  ),
                ),
              ),
            ),
            Align(
              alignment: Alignment.bottomRight,
              child: Container(
                width: size.width,
                height: size.height,
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: Colors.white30, width: 2),
                    right: BorderSide(color: Colors.white30, width: 2),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (widget.url == 'mock') {
      return Container(
        width: widget.width,
        height: widget.height,
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(12),
        ),
        clipBehavior: Clip.antiAlias,
        child: AnimatedBuilder(
          animation: _animController!,
          builder: (context, child) {
            return Stack(
              children: [
                // Custom viewport grid and sweeping scan line
                CustomPaint(
                  painter: MockCameraPainter(scanProgress: _animController!.value),
                  child: Container(),
                ),
                _buildCornerBrackets(size: const Size(18, 18)),
                // Live Indicator
                Positioned(
                  top: 16,
                  left: 16,
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppTheme.accent,
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Text(
                        'LIVE VIEWPORT',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
                // Metrics
                Positioned(
                  bottom: 16,
                  left: 16,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'FPS: 30.0 (STANDALONE)',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 9,
                          fontFamily: 'monospace',
                        ),
                      ),
                      Text(
                        'RESOLUTION: 1920x1080',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 9,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ),
                // Center text
                const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'ALIGN EYE TO TARGET',
                        style: TextStyle(
                          color: AppTheme.primary,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.0,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'DEMO MODE ACTIVE',
                        style: TextStyle(
                          color: Colors.white24,
                          fontSize: 9,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      );
    }

    if (_hasError) {
      return widget.errorWidget ??
          Container(
            width: widget.width,
            height: widget.height,
            color: Colors.black38,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.videocam_off_rounded, color: AppTheme.accent, size: 48),
                const SizedBox(height: 8),
                const Text(
                  'Camera connection offline',
                  style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 8),
                TextButton.icon(
                  onPressed: () {
                    _stopStreaming();
                    _startStreaming();
                  },
                  icon: const Icon(Icons.refresh, color: AppTheme.primary, size: 18),
                  label: const Text('Retry Connection', style: TextStyle(color: AppTheme.primary)),
                ),
              ],
            ),
          );
    }

    if (_isConnecting || _frameBytes == null) {
      return widget.placeholder ??
          Container(
            width: widget.width,
            height: widget.height,
            color: Colors.black26,
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(valueColor: AlwaysStoppedAnimation(AppTheme.primary)),
                  SizedBox(height: 16),
                  Text('Connecting to camera feed...', style: TextStyle(color: Colors.white54)),
                ],
              ),
            ),
          );
    }

    return Container(
      width: widget.width,
      height: widget.height,
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(12),
      ),
      clipBehavior: Clip.antiAlias,
      child: Image.memory(
        _frameBytes!,
        fit: BoxFit.cover,
        gaplessPlayback: true,
      ),
    );
  }
}

class MockCameraPainter extends CustomPainter {
  final double scanProgress;

  MockCameraPainter({required this.scanProgress});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.08)
      ..strokeWidth = 1.0;

    // Draw grid
    const gridCount = 6;
    for (int i = 1; i < gridCount; i++) {
      final x = size.width * i / gridCount;
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (int i = 1; i < gridCount; i++) {
      final y = size.height * i / gridCount;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }

    // Target circles
    final center = Offset(size.width / 2, size.height / 2);
    final circlePaint = Paint()
      ..color = AppTheme.primary.withOpacity(0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawCircle(center, 30, circlePaint);
    canvas.drawCircle(center, 65, circlePaint..color = AppTheme.primary.withOpacity(0.15));

    // Center crosshair
    final crossPaint = Paint()
      ..color = AppTheme.primary.withOpacity(0.6)
      ..strokeWidth = 1.5;
    canvas.drawLine(Offset(center.dx - 12, center.dy), Offset(center.dx + 12, center.dy), crossPaint);
    canvas.drawLine(Offset(center.dx, center.dy - 12), Offset(center.dx, center.dy + 12), crossPaint);

    // Laser sweep line
    final scanY = size.height * scanProgress;
    final scanPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          AppTheme.primary.withOpacity(0.0),
          AppTheme.primary.withOpacity(0.8),
          AppTheme.primary.withOpacity(0.0),
        ],
      ).createShader(Rect.fromLTRB(0, scanY - 15, size.width, scanY + 15))
      ..strokeWidth = 3.0;
    canvas.drawLine(Offset(0, scanY), Offset(size.width, scanY), scanPaint);
  }

  @override
  bool shouldRepaint(covariant MockCameraPainter oldDelegate) {
    return oldDelegate.scanProgress != scanProgress;
  }
}
