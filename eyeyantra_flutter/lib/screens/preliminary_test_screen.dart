import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:camera/camera.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import '../widgets/mjpeg_viewer.dart';
import '../widgets/tablet_camera_preview.dart';
import 'results_screen.dart';

class PreliminaryTestScreen extends StatefulWidget {
  const PreliminaryTestScreen({Key? key}) : super(key: key);

  @override
  State<PreliminaryTestScreen> createState() => _PreliminaryTestScreenState();
}

class _PreliminaryTestScreenState extends State<PreliminaryTestScreen> {
  bool _isCaptured = false;
  String _statusMessage = 'Align patient and click capture to check eye alignment.';
  bool _isSuccess = false;
  CameraController? _localCameraController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final apiService = Provider.of<ApiService>(context, listen: false);
      await apiService.fetchAvailableCameras();
      if (mounted) {
        await _showCameraSelectionDialog(apiService);
      }
    });
  }

  Future<void> _showCameraSelectionDialog(ApiService apiService) async {
    if (apiService.localCameraSource != 'hardware' || apiService.availableCamerasList.length <= 1) {
      return;
    }
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          backgroundColor: AppTheme.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.photo_camera_front_rounded, color: AppTheme.primary),
              SizedBox(width: 8),
              Text(
                'Select Active PC Camera',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          content: Text(
            'Multiple cameras detected: ${apiService.availableCamerasList.length} devices connected.\n\nPlease choose which camera to use for this session:',
            style: const TextStyle(color: AppTheme.textSecondary),
          ),
          actions: [
            TextButton.icon(
              icon: const Icon(Icons.laptop_chromebook, color: AppTheme.primary),
              label: const Text('Built-in Camera'),
              onPressed: () async {
                Navigator.of(dialogContext).pop();
                await apiService.setCameraSource('built-in');
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Switched to Built-in Camera'),
                      backgroundColor: AppTheme.primary,
                    ),
                  );
                }
              },
            ),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primary,
                foregroundColor: Colors.white,
              ),
              icon: const Icon(Icons.usb_rounded),
              label: const Text('External USB Webcam'),
              onPressed: () async {
                Navigator.of(dialogContext).pop();
                await apiService.setCameraSource('external');
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Switched to External USB Webcam'),
                      backgroundColor: AppTheme.primary,
                    ),
                  );
                }
              },
            ),
          ],
        );
      },
    );
  }

  void _capture() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    setState(() {
      _statusMessage = 'Analyzing eye presence... Please hold still.';
    });

    final todayStr = DateTime.now().toString().substring(0, 10);
    Map<String, dynamic> result;

    if (apiService.localCameraSource == 'tablet') {
      if (_localCameraController == null) {
        setState(() {
          _isSuccess = false;
          _statusMessage = '❌ Tablet camera not initialized.';
        });
        return;
      }
      try {
        // Explicitly turn off flash/torch for preliminary test capture
        try {
          await _localCameraController!.setFlashMode(FlashMode.off);
        } catch (e) {
          debugPrint('Failed to disable flash: $e');
        }
        final image = await _localCameraController!.takePicture();
        result = await apiService.uploadPreliminary(image.path, todayStr);
      } catch (e) {
        result = {'status': 'error', 'message': e.toString()};
      }
    } else {
      result = await apiService.capturePreliminary(todayStr);
    }

    if (result['status'] == 'success') {
      setState(() {
        _isCaptured = true;
        _isSuccess = true;
        _statusMessage = '✅ Alignment test baseline captured successfully!';
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Baseline captured successfully!'), backgroundColor: AppTheme.primary),
      );
    } else {
      setState(() {
        _isSuccess = false;
        _statusMessage = '❌ ${result['message'] ?? 'Capture failed.'}';
      });
      // Show retry modal if requested
      if (result['retry'] == true) {
        _showRetryDialog(result['message'] ?? 'Please ensure the face is visible and eyes are open.');
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
            Text('Assessment Alert'),
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
        title: const Text('Preliminary Alignment'),
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
                  final isWide = constraints.maxWidth > 900;

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
                                      ? TabletCameraPreview(
                                          onControllerInitialized: (controller) {
                                            _localCameraController = controller;
                                          },
                                        )
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
                                  // Overlay calibration reticle
                                  Center(
                                    child: Image.asset(
                                      'assets/reticle.png',
                                      color: AppTheme.primary.withOpacity(0.3),
                                      width: 320,
                                      height: 180,
                                      errorBuilder: (_, __, ___) {
                                        return Container(
                                          width: 280,
                                          height: 160,
                                          decoration: BoxDecoration(
                                            border: Border.all(color: AppTheme.primary.withOpacity(0.4), width: 2),
                                            borderRadius: BorderRadius.circular(16),
                                          ),
                                          child: const Center(
                                            child: Icon(Icons.center_focus_weak, color: Colors.white24, size: 40),
                                          ),
                                        );
                                      },
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
                                  'Position the patient so their eyes are centered inside the frame. Verify both eyes are wide open and looking directly forward.',
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
                                        icon: const Icon(Icons.camera_alt_rounded, size: 18),
                                        label: const Text('CAPTURE ALIGNMENT'),
                                      ),
                                    ),
                                    if (_isCaptured) ...[
                                      const SizedBox(width: 12),
                                      ElevatedButton(
                                        onPressed: () {
                                          Navigator.of(context).pushReplacement(
                                            MaterialPageRoute(
                                              builder: (_) => const ResultsScreen(initialTab: 0),
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
                            _buildChecklistItem(1, 'Preliminary Test', _isCaptured),
                            const SizedBox(height: 16),
                            _buildChecklistItem(2, 'Hirschberg Test', false),
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
        ],
      ),
    );
  }
}
