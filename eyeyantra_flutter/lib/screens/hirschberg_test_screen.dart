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
import 'nine_gaze_test_screen.dart';

class HirschbergTestScreen extends StatefulWidget {
  const HirschbergTestScreen({Key? key}) : super(key: key);

  @override
  State<HirschbergTestScreen> createState() => _HirschbergTestScreenState();
}

class _HirschbergTestScreenState extends State<HirschbergTestScreen> {
  bool _isCaptured = false;
  String _statusMessage = 'Make sure headset is connected, then click capture.';
  bool _isSuccess = false;
  bool _showScreenFlash = false;
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

  void _capture() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    
    final isTablet = MediaQuery.of(context).size.shortestSide >= 600;
    if (apiService.localCameraSource == 'tablet' && isTablet) {
      setState(() {
        _showScreenFlash = true;
        _statusMessage = '📸 Preparing screen flash...';
      });
      // Wait for screen to turn white
      await Future.delayed(const Duration(milliseconds: 500));
    } else if (apiService.useLaptopCamera) {
      setState(() {
        _showScreenFlash = true;
        _statusMessage = '📸 Preparing screen flash...';
      });
      // Wait for screen to turn white
      await Future.delayed(const Duration(milliseconds: 500));
    } else {
      setState(() {
        _statusMessage = '💡 Turning LED Light on via BLE... Please wait.';
      });
    }

    final todayStr = DateTime.now().toString().substring(0, 10);
    Map<String, dynamic> result;

    if (apiService.localCameraSource == 'tablet') {
      if (_localCameraController == null) {
        setState(() {
          _showScreenFlash = false;
          _isSuccess = false;
          _statusMessage = '❌ Tablet camera not initialized.';
        });
        return;
      }
      try {
        // Turn flash on only during the capture step
        if (_localCameraController!.value.description.lensDirection == CameraLensDirection.back) {
          try {
            await _localCameraController!.setFlashMode(FlashMode.torch);
            // Brief delay for lighting stabilization
            await Future.delayed(const Duration(milliseconds: 400));
          } catch (e) {
            debugPrint('Failed to set flash mode to torch: $e');
          }
        }
        
        final image = await _localCameraController!.takePicture();
        
        // Turn flash off immediately after capture
        if (_localCameraController!.value.description.lensDirection == CameraLensDirection.back) {
          try {
            await _localCameraController!.setFlashMode(FlashMode.off);
          } catch (e) {
            debugPrint('Failed to turn off flash: $e');
          }
        }

        result = await apiService.uploadHirschberg(image.path, todayStr);
      } catch (e) {
        result = {'status': 'error', 'message': e.toString()};
      }
    } else {
      result = await apiService.captureHirschberg(todayStr);
    }

    if (mounted) {
      setState(() {
        _showScreenFlash = false;
      });
    }

    if (result['status'] == 'success') {
      setState(() {
        _isCaptured = true;
        _isSuccess = true;
        _statusMessage = '✅ Hirschberg corneal reflex captured successfully!';
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Hirschberg captured! Moving to 9-Gaze Test...'),
          backgroundColor: AppTheme.primary,
          duration: Duration(seconds: 2),
        ),
      );
      // Auto-transition to 9-Gaze Test after 2 seconds
      Future.delayed(const Duration(seconds: 2), () {
        if (!mounted) return;
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const NineGazeTestScreen()),
        );
      });
    } else {
      setState(() {
        _isSuccess = false;
        _statusMessage = '❌ ${result['message'] ?? 'Hirschberg capture failed.'}';
      });
      if (result['retry'] == true) {
        _showRetryDialog(result['message'] ?? 'Corneal reflection check failed. Ensure eyes are open and looking at the light.');
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
            Text('Hirschberg Assessment'),
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

  Widget _buildChecklistItem(int num, String title, bool isDone) {
    return Row(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isDone ? Colors.green.withOpacity(0.2) : Colors.white.withOpacity(0.05),
            border: Border.all(color: isDone ? Colors.green : Colors.white10),
          ),
          child: Center(
            child: isDone
                ? const Icon(Icons.check, size: 14, color: Colors.greenAccent)
                : Text('$num', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
          ),
        ),
        const SizedBox(width: 12),
        Text(title, style: TextStyle(color: isDone ? Colors.white : AppTheme.textSecondary, fontSize: 14)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final apiService = Provider.of<ApiService>(context);
    final streamUrl = apiService.isDemoMode ? 'mock' : '${apiService.baseUrl}/video_feed';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Hirschberg Assessment'),
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
              padding: const EdgeInsets.all(24),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth >= 906;

                  Widget buildCameraSection() {
                    return SizedBox(
                      width: isWide ? 560 : double.infinity,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          AspectRatio(
                            aspectRatio: 16 / 10,
                            child: GlassCard(
                              padding: EdgeInsets.zero,
                              child: Stack(
                                children: [
                                  apiService.localCameraSource == 'tablet'
                                      ? (!_isCaptured
                                          ? TabletCameraPreview(
                                              defaultTorchOn: false,
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
                                  // Highlight reticle for Hirschberg alignment
                                  Center(
                                    child: Container(
                                      width: 320,
                                      height: 180,
                                      decoration: BoxDecoration(
                                        border: Border.all(color: AppTheme.secondary.withOpacity(0.3), width: 1.5),
                                        borderRadius: BorderRadius.circular(16),
                                      ),
                                      child: Stack(
                                        children: [
                                          Align(
                                            alignment: const Alignment(-0.4, 0.0), // Left Eye area
                                            child: Icon(Icons.add, color: AppTheme.accent.withOpacity(0.5), size: 24),
                                          ),
                                          Align(
                                            alignment: const Alignment(0.4, 0.0), // Right Eye area
                                            child: Icon(Icons.add, color: AppTheme.accent.withOpacity(0.5), size: 24),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 20),
                          // Control panel / Results
                          GlassCard(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                const Text(
                                  'Instructions',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                                ),
                                const SizedBox(height: 6),
                                const Text(
                                  'Ensure the patient is looking directly forward. On capture, the device will send a BLE command to trigger the internal LED lights, take a snapshot, and automatically turn the lights off.',
                                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  _statusMessage,
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                    color: _isSuccess 
                                        ? Colors.greenAccent 
                                        : (_statusMessage.startsWith('❌') ? Colors.redAccent : Colors.white70),
                                  ),
                                ),
                                const SizedBox(height: 16),
                                Row(
                                  children: [
                                    Expanded(
                                      child: ElevatedButton.icon(
                                        onPressed: apiService.isLoading ? null : _capture,
                                        style: ElevatedButton.styleFrom(
                                          padding: const EdgeInsets.symmetric(vertical: 14),
                                        ),
                                        icon: const Icon(Icons.flash_on_rounded, size: 18),
                                        label: const Text('CAPTURE WITH FLASH'),
                                      ),
                                    ),
                                    if (_isCaptured) ...[
                                      const SizedBox(width: 12),
                                      ElevatedButton(
                                        onPressed: () {
                                          Navigator.of(context).pushReplacement(
                                            MaterialPageRoute(
                                              builder: (_) => const ResultsScreen(initialTab: 1),
                                            ),
                                          );
                                        },
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: AppTheme.secondary,
                                          padding: const EdgeInsets.symmetric(vertical: 14),
                                        ),
                                        child: const Text('VIEW RESULTS'),
                                      ),
                                    ]
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }

                  Widget buildSidePanel() {
                    return SizedBox(
                      width: isWide ? 320 : double.infinity,
                      child: GlassCard(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text(
                              'Session Checklist',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                            ),
                            const SizedBox(height: 20),
                            _buildChecklistItem(1, 'Preliminary Test', true),
                            const SizedBox(height: 16),
                            _buildChecklistItem(2, 'Hirschberg Test', _isCaptured),
                            const SizedBox(height: 16),
                            _buildChecklistItem(3, '9-Gaze Test', false),
                            const SizedBox(height: 16),
                            _buildChecklistItem(4, 'Generate Report', false),
                          ],
                        ),
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
                            buildCameraSection(),
                            const SizedBox(width: 26),
                            buildSidePanel(),
                          ],
                        ),
                      ),
                    );
                  } else {
                    return SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          buildCameraSection(),
                          const SizedBox(height: 20),
                          buildSidePanel(),
                        ],
                      ),
                    );
                  }
                },
              ),
            ),
          ),
          if (_showScreenFlash)
            Positioned.fill(
              child: Container(
                color: Colors.white,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        'FLASHLIGHT ACTIVE',
                        style: TextStyle(
                          color: Colors.black,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                          decoration: TextDecoration.none,
                        ),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'Please look directly at the red dot',
                        style: TextStyle(
                          color: Colors.grey,
                          fontSize: 16,
                          decoration: TextDecoration.none,
                        ),
                      ),
                      const SizedBox(height: 30),
                      Container(
                        width: 30,
                        height: 30,
                        decoration: const BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
