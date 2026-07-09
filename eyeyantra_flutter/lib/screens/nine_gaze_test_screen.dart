import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:camera/camera.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import '../widgets/mjpeg_viewer.dart';
import '../widgets/tablet_camera_preview.dart';
import 'results_screen.dart';

class NineGazeTestScreen extends StatefulWidget {
  const NineGazeTestScreen({Key? key}) : super(key: key);

  @override
  State<NineGazeTestScreen> createState() => _NineGazeTestScreenState();
}

class _NineGazeTestScreenState extends State<NineGazeTestScreen> {
  final List<String> _gazeOrder = [
    'center', 'up', 'down', 'left', 'right',
    'upleft', 'upright', 'downleft', 'downright'
  ];

  final Map<String, String> _gazeLabels = {
    'center': 'Center (Primary)',
    'up': 'Up (Elevation)',
    'down': 'Down (Depression)',
    'left': 'Left (Adduction/Abduction)',
    'right': 'Right (Abduction/Adduction)',
    'upleft': 'Up-Left',
    'upright': 'Up-Right',
    'downleft': 'Down-Left',
    'downright': 'Down-Right'
  };

  int _currentIndex = 0;
  final Set<String> _completedGazes = {};
  String _statusMessage = 'Align patient and capture Center position first.';
  CameraController? _localCameraController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Only probe laptop cameras on desktop platforms
      final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
      if (isDesktop) {
        Provider.of<ApiService>(context, listen: false).fetchAvailableCameras();
      }
    });
  }

  String get _currentGaze => _gazeOrder[_currentIndex];

  void _capture() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final gaze = _currentGaze;

    setState(() {
      _statusMessage = 'Capturing and analyzing ${gaze.toUpperCase()} gaze...';
    });

    Map<String, dynamic> result;

    if (apiService.localCameraSource == 'tablet') {
      if (_localCameraController == null) {
        setState(() {
          _statusMessage = '❌ Tablet camera not initialized.';
        });
        return;
      }
      try {
        // Explicitly turn off flash/torch for 9-gaze test capture
        try {
          await _localCameraController!.setFlashMode(FlashMode.off);
        } catch (e) {
          debugPrint('Failed to disable flash: $e');
        }
        final image = await _localCameraController!.takePicture();
        result = await apiService.upload9Gaze(image.path, gaze);
      } catch (e) {
        result = {'status': 'error', 'message': e.toString()};
      }
    } else {
      result = await apiService.capture9Gaze(gaze);
    }

    if (result['status'] == 'success') {
      setState(() {
        _completedGazes.add(gaze);
        _statusMessage = '✅ Successfully captured ${gaze.toUpperCase()}!';
        
        // Move to the next incomplete gaze if available
        if (_completedGazes.length < _gazeOrder.length) {
          for (int i = 0; i < _gazeOrder.length; i++) {
            if (!_completedGazes.contains(_gazeOrder[i])) {
              _currentIndex = i;
              break;
            }
          }
        }
      });
      if (!mounted) return;

      // Check if all 9 gazes are now completed
      if (_completedGazes.length == _gazeOrder.length) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ All 9 gazes captured! Opening Results...'),
            backgroundColor: AppTheme.primary,
            duration: Duration(seconds: 2),
          ),
        );
        // Auto-transition to Results after 2 seconds
        Future.delayed(const Duration(seconds: 2), () {
          if (!mounted) return;
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (_) => const ResultsScreen(initialTab: 2),
            ),
          );
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${gaze.toUpperCase()} captured successfully!'), backgroundColor: AppTheme.primary),
        );
      }
    } else {
      setState(() {
        _statusMessage = '❌ ${result['message'] ?? 'Capture failed.'}';
      });
      if (result['retry'] == true) {
        _showRetryDialog(result['message'] ?? 'Ensure eyes are open in the specified direction.');
      }
    }
  }

  void _showRetryDialog(String msg) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: AppTheme.accent),
            SizedBox(width: 8),
            Text('Gaze Grid Capture'),
          ],
        ),
        content: Text('$msg\n\nWould you like to try capturing again?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _capture();
            },
            child: const Text('Retry Capture', style: TextStyle(color: AppTheme.primary)),
          ),
        ],
      ),
    );
  }

  Alignment _getAlignmentForGaze(String gaze) {
    switch (gaze) {
      case 'up': return Alignment.topCenter;
      case 'down': return Alignment.bottomCenter;
      case 'left': return Alignment.centerLeft;
      case 'right': return Alignment.centerRight;
      case 'upleft': return Alignment.topLeft;
      case 'upright': return Alignment.topRight;
      case 'downleft': return Alignment.bottomLeft;
      case 'downright': return Alignment.bottomRight;
      default: return Alignment.center;
    }
  }

  @override
  Widget build(BuildContext context) {
    final apiService = Provider.of<ApiService>(context);
    final streamUrl = apiService.isDemoMode ? 'mock' : '${apiService.baseUrl}/video_feed';
    final allDone = _completedGazes.length == _gazeOrder.length;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('9-Gaze Motility Grid'),
            Text(
              'Patient: ${apiService.activePatientDetails['name'] ?? 'N/A'} (ID: ${apiService.activePatientDetails['id'] ?? 'N/A'})',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: AppTheme.backgroundGradient,
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 900;

                  Widget buildTargetVisualizer() {
                    return GlassCard(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Text(
                            'LOOK AT THIS TARGET DOT',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white70),
                          ),
                          const SizedBox(height: 12),
                          Expanded(
                            child: Container(
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.white.withOpacity(0.05)),
                              ),
                              child: Stack(
                                children: [
                                  // Grid references
                                  Column(
                                    children: [
                                      Expanded(child: Container(decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.03)))))),
                                      Expanded(child: Container(decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.03)))))),
                                      Expanded(child: Container()),
                                    ],
                                  ),
                                  Row(
                                    children: [
                                      Expanded(child: Container(decoration: BoxDecoration(border: Border(right: BorderSide(color: Colors.white.withOpacity(0.03)))))),
                                      Expanded(child: Container(decoration: BoxDecoration(border: Border(right: BorderSide(color: Colors.white.withOpacity(0.03)))))),
                                      Expanded(child: Container()),
                                    ],
                                  ),
                                  if (!allDone)
                                    Align(
                                      alignment: _getAlignmentForGaze(_currentGaze),
                                      child: Padding(
                                        padding: const EdgeInsets.all(24),
                                        child: TweenAnimationBuilder<double>(
                                          tween: Tween(begin: 0.8, end: 1.2),
                                          duration: const Duration(milliseconds: 800),
                                          curve: Curves.easeInOut,
                                          builder: (context, scale, child) {
                                            return Transform.scale(
                                              scale: scale,
                                              child: Container(
                                                width: 32,
                                                height: 32,
                                                decoration: BoxDecoration(
                                                  shape: BoxShape.circle,
                                                  color: Colors.redAccent,
                                                  boxShadow: [
                                                    BoxShadow(
                                                      color: Colors.redAccent.withOpacity(0.6),
                                                      blurRadius: 16,
                                                      spreadRadius: 4,
                                                    )
                                                  ],
                                                ),
                                              ),
                                            );
                                          },
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Instructions',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            allDone 
                                ? 'All 9 positions captured! Proceed to results.' 
                                : 'Direct patient to look in the target direction: ${_gazeLabels[_currentGaze]}. Then click capture.',
                            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                          ),
                        ],
                      ),
                    );
                  }

                  Widget buildCameraSection() {
                    return SizedBox(
                      width: isWide ? 480 : double.infinity,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          AspectRatio(
                            aspectRatio: 16 / 11,
                            child: GlassCard(
                              padding: EdgeInsets.zero,
                              child: Stack(
                                children: [
                                  apiService.localCameraSource == 'tablet'
                                      ? (!allDone
                                          ? TabletCameraPreview(
                                              onControllerInitialized: (controller) {
                                                _localCameraController = controller;
                                              },
                                            )
                                          : Container(
                                              color: Colors.black87,
                                              child: const Center(
                                                child: Icon(
                                                  Icons.check_circle_outline_rounded,
                                                  color: AppTheme.primary,
                                                  size: 80,
                                                ),
                                              ),
                                            ))
                                      : MjpegViewer(
                                          url: streamUrl,
                                          width: double.infinity,
                                          height: double.infinity,
                                        ),
                                  if (apiService.localCameraSource != 'tablet' && apiService.availableCamerasList.length > 1)
                                    Positioned(
                                      top: 12,
                                      right: 12,
                                      child: ClipRRect(
                                        borderRadius: BorderRadius.circular(30),
                                        child: Container(
                                          color: Colors.black54,
                                          child: IconButton(
                                            icon: const Icon(Icons.flip_camera_ios, color: Colors.white),
                                            tooltip: 'Switch Camera',
                                            onPressed: () async {
                                              final res = await apiService.switchCamera();
                                              if (res['status'] == 'success') {
                                                ScaffoldMessenger.of(context).showSnackBar(
                                                  SnackBar(
                                                    content: Text(res['name'] ?? 'Switched camera'),
                                                    backgroundColor: AppTheme.primary,
                                                  ),
                                                );
                                              }
                                            },
                                          ),
                                        ),
                                      ),
                                    ),
                                  if (!allDone)
                                    _buildDirectionOverlay(_currentGaze),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          // Progress Bar
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: _completedGazes.length / _gazeOrder.length,
                              backgroundColor: Colors.white.withOpacity(0.05),
                              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primary),
                              minHeight: 6,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Gaze Position ${_currentIndex + 1} / 9',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
                              ),
                              Text(
                                _gazeLabels[_currentGaze]?.toUpperCase() ?? '',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.accent),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          // Chips row
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: List.generate(17, (index) {
                                if (index.isOdd) return const SizedBox(width: 6);
                                final chipIndex = index ~/ 2;
                                final cellGaze = _gazeOrder[chipIndex];
                                final isCompleted = _completedGazes.contains(cellGaze);
                                final isActive = cellGaze == _currentGaze && !allDone;
                                return Container(
                                  width: 32,
                                  height: 32,
                                  decoration: BoxDecoration(
                                    color: isCompleted
                                        ? Colors.green.withOpacity(0.25)
                                        : (isActive ? AppTheme.primary : Colors.white.withOpacity(0.04)),
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: isActive
                                          ? Colors.white
                                          : (isCompleted ? Colors.green : Colors.white10),
                                      width: isActive ? 2 : 1,
                                    ),
                                  ),
                                  child: Center(
                                    child: isCompleted
                                        ? const Icon(Icons.check, size: 14, color: Colors.greenAccent)
                                        : Text(
                                            '${chipIndex + 1}',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                              color: isActive ? Colors.white : AppTheme.textSecondary,
                                            ),
                                          ),
                                  ),
                                );
                              }),
                            ),
                          ),
                          const SizedBox(height: 16),
                          // Controls
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: _currentIndex > 0 
                                      ? () {
                                          setState(() {
                                            _currentIndex--;
                                          });
                                        }
                                      : null,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white.withOpacity(0.05),
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                  ),
                                  child: const Text('← Previous'),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                flex: 2,
                                child: ElevatedButton.icon(
                                  onPressed: apiService.isLoading || allDone ? null : _capture,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppTheme.accent,
                                    padding: const EdgeInsets.symmetric(vertical: 14),
                                  ),
                                  icon: const Icon(Icons.camera_alt_rounded, size: 18),
                                  label: const Text('Capture'),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: _currentIndex < _gazeOrder.length - 1
                                      ? () {
                                          setState(() {
                                            _currentIndex++;
                                          });
                                        }
                                      : null,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white.withOpacity(0.05),
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                  ),
                                  child: const Text('Next →'),
                                ),
                              ),
                            ],
                          ),
                          if (allDone) ...[
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: () {
                                Navigator.of(context).pushReplacement(
                                  MaterialPageRoute(
                                    builder: (_) => const ResultsScreen(initialTab: 2),
                                  ),
                                );
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                padding: const EdgeInsets.symmetric(vertical: 14),
                              ),
                              child: const Text('PROCESS & VIEW 9-GAZE REPORT'),
                            ),
                          ],
                          const SizedBox(height: 12),
                          Text(
                            _statusMessage,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: _statusMessage.startsWith('✅')
                                  ? Colors.greenAccent
                                  : (_statusMessage.startsWith('❌') ? Colors.redAccent : Colors.white70),
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Select Gaze Position:',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textSecondary),
                          ),
                          const SizedBox(height: 6),
                          SizedBox(
                            height: 35,
                            child: ListView.builder(
                              scrollDirection: Axis.horizontal,
                              itemCount: _gazeOrder.length,
                              itemBuilder: (context, index) {
                                final g = _gazeOrder[index];
                                final isSelected = index == _currentIndex;
                                final isCompleted = _completedGazes.contains(g);
                                return Padding(
                                    padding: const EdgeInsets.only(right: 6),
                                    child: ChoiceChip(
                                      label: Text(g.toUpperCase(), style: const TextStyle(fontSize: 10)),
                                      selected: isSelected,
                                      onSelected: (_) {
                                        setState(() {
                                          _currentIndex = index;
                                        });
                                      },
                                      selectedColor: AppTheme.primary,
                                      backgroundColor: isCompleted 
                                          ? Colors.green.withOpacity(0.2) 
                                          : Colors.white.withOpacity(0.05),
                                      side: BorderSide(
                                        color: isSelected 
                                            ? AppTheme.primary 
                                            : (isCompleted ? Colors.green.withOpacity(0.5) : Colors.white10),
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ),
                        ],
                      ),
                    );
                  }

                  if (isWide) {
                    return SingleChildScrollView(
                      child: Align(
                        alignment: Alignment.topCenter,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Expanded(child: SizedBox(height: 500, child: buildTargetVisualizer())),
                            const SizedBox(width: 24),
                            buildCameraSection(),
                          ],
                        ),
                      ),
                    );
                  } else {
                    return SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          SizedBox(height: 300, child: buildTargetVisualizer()),
                          const SizedBox(height: 20),
                          buildCameraSection(),
                        ],
                      ),
                    );
                  }
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDirectionOverlay(String gaze) {
    Alignment alignment;
    IconData icon;
    
    switch (gaze) {
      case 'up':
        alignment = Alignment.topCenter;
        icon = Icons.arrow_upward_rounded;
        break;
      case 'down':
        alignment = Alignment.bottomCenter;
        icon = Icons.arrow_downward_rounded;
        break;
      case 'left':
        alignment = Alignment.centerLeft;
        icon = Icons.arrow_back_rounded;
        break;
      case 'right':
        alignment = Alignment.centerRight;
        icon = Icons.arrow_forward_rounded;
        break;
      case 'upleft':
        alignment = Alignment.topLeft;
        icon = Icons.north_west_rounded;
        break;
      case 'upright':
        alignment = Alignment.topRight;
        icon = Icons.north_east_rounded;
        break;
      case 'downleft':
        alignment = Alignment.bottomLeft;
        icon = Icons.south_west_rounded;
        break;
      case 'downright':
        alignment = Alignment.bottomRight;
        icon = Icons.south_east_rounded;
        break;
      default:
        alignment = Alignment.center;
        icon = Icons.center_focus_strong_rounded;
    }

    return Align(
      alignment: alignment,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppTheme.primary.withOpacity(0.85),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(color: AppTheme.primary.withOpacity(0.5), blurRadius: 15, spreadRadius: 2),
            ],
          ),
          child: Icon(icon, color: Colors.white, size: 36),
        ),
      ),
    );
  }
}
