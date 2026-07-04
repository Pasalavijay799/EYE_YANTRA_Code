import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

class TabletCameraPreview extends StatefulWidget {
  final Function(CameraController controller) onControllerInitialized;
  final bool defaultTorchOn;

  const TabletCameraPreview({
    Key? key,
    required this.onControllerInitialized,
    this.defaultTorchOn = false,
  }) : super(key: key);

  @override
  State<TabletCameraPreview> createState() => _TabletCameraPreviewState();
}

class _TabletCameraPreviewState extends State<TabletCameraPreview> with WidgetsBindingObserver {
  CameraController? _controller;
  bool _isInitialized = false;
  String _errorMessage = '';
  Orientation? _lastKnownOrientation;
  
  CameraLensDirection? _currentLensDirection;
  bool _isTorchOn = false;
  List<CameraDescription> _availableCameras = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final currentOrientation = MediaQuery.of(context).orientation;
    
    if (_currentLensDirection == null) {
      final size = MediaQuery.of(context).size;
      final isTablet = size.shortestSide >= 600;
      _currentLensDirection = isTablet ? CameraLensDirection.front : CameraLensDirection.back;
      _isTorchOn = widget.defaultTorchOn;
    }

    if (_lastKnownOrientation == null) {
      _lastKnownOrientation = currentOrientation;
      _initializeCamera();
    } else if (_lastKnownOrientation != currentOrientation) {
      _lastKnownOrientation = currentOrientation;
      _initializeCamera();
    }
  }

  Future<void> _initializeCamera() async {
    try {
      if (_controller != null) {
        final oldController = _controller;
        _controller = null;
        if (mounted) {
          setState(() {
            _isInitialized = false;
          });
        }
        await oldController!.dispose();
      }

      _availableCameras = await availableCameras();
      if (_availableCameras.isEmpty) {
        setState(() {
          _errorMessage = 'No camera found on this device.';
        });
        return;
      }

      if (_currentLensDirection == null) {
        final size = MediaQuery.of(context).size;
        final isTablet = size.shortestSide >= 600;
        _currentLensDirection = isTablet ? CameraLensDirection.front : CameraLensDirection.back;
      }

      CameraDescription selectedCamera = _availableCameras.firstWhere(
        (cam) => cam.lensDirection == _currentLensDirection,
        orElse: () => _availableCameras.first,
      );

      await _initializeCameraWithDescription(selectedCamera);
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Camera initialization failed: $e';
        });
      }
    }
  }

  Future<void> _initializeCameraWithDescription(CameraDescription camera) async {
    try {
      if (_controller != null) {
        final oldController = _controller;
        _controller = null;
        if (mounted) {
          setState(() {
            _isInitialized = false;
          });
        }
        await oldController!.dispose();
      }

      _currentLensDirection = camera.lensDirection;

      final controller = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      _controller = controller;
      await controller.initialize();

      // Configure torch flash mode if using back camera with a short delay to ensure stability
      if (_currentLensDirection == CameraLensDirection.back) {
        try {
          await Future.delayed(const Duration(milliseconds: 350));
          await controller.setFlashMode(_isTorchOn ? FlashMode.torch : FlashMode.off);
        } catch (e) {
          debugPrint('Failed to set flash mode: $e');
        }
      }

      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
        widget.onControllerInitialized(controller);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Camera initialization failed: $e';
        });
      }
    }
  }

  Future<void> _toggleCamera() async {
    if (_availableCameras.length < 2) return;
    
    int nextIndex = 0;
    if (_controller != null) {
      final currentCam = _controller!.description;
      final idx = _availableCameras.indexWhere((c) => c.name == currentCam.name);
      if (idx != -1) {
        nextIndex = (idx + 1) % _availableCameras.length;
      }
    }
    
    final nextCamera = _availableCameras[nextIndex];
    
    setState(() {
      _currentLensDirection = nextCamera.lensDirection;
      if (nextCamera.lensDirection != CameraLensDirection.back) {
        _isTorchOn = false;
      } else {
        _isTorchOn = widget.defaultTorchOn;
      }
    });
    
    await _initializeCameraWithDescription(nextCamera);
  }

  Future<void> _toggleTorch() async {
    if (_controller == null || !_isInitialized) return;
    if (_currentLensDirection != CameraLensDirection.back) return;
    
    final newTorchState = !_isTorchOn;
    try {
      await _controller!.setFlashMode(newTorchState ? FlashMode.torch : FlashMode.off);
      setState(() {
        _isTorchOn = newTorchState;
      });
    } catch (e) {
      debugPrint('Failed to toggle torch: $e');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final CameraController? cameraController = _controller;

    if (cameraController == null || !cameraController.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      cameraController.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            _errorMessage,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.redAccent, fontSize: 14),
          ),
        ),
      );
    }

    if (!_isInitialized || _controller == null) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    final isLandscape = MediaQuery.of(context).orientation == Orientation.landscape;
    final cameraAspectRatio = _controller!.value.aspectRatio;
    final visualAspectRatio = isLandscape ? cameraAspectRatio : (1.0 / cameraAspectRatio);

    return Stack(
      children: [
        ClipRect(
          child: SizedBox(
            width: double.infinity,
            height: double.infinity,
            child: FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: 1000,
                height: 1000 / visualAspectRatio,
                child: CameraPreview(_controller!),
              ),
            ),
          ),
        ),
        // Overlay Camera Name/Direction Info
        Positioned(
          bottom: 16,
          left: 16,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.black54,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Camera: ${_controller!.description.name} (${_currentLensDirection.toString().split(".").last})',
              style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
        ),
        // Overlay Camera Controls
        Positioned(
          top: 16,
          right: 16,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (_availableCameras.length > 1)
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white24),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.flip_camera_android_rounded, color: Colors.white, size: 22),
                    tooltip: 'Switch Camera',
                    onPressed: _toggleCamera,
                  ),
                ),
              if (_currentLensDirection == CameraLensDirection.back)
                Container(
                  decoration: BoxDecoration(
                    color: _isTorchOn ? Colors.amber.withOpacity(0.8) : Colors.black54,
                    shape: BoxShape.circle,
                    border: Border.all(color: _isTorchOn ? Colors.amber : Colors.white24),
                  ),
                  child: IconButton(
                    icon: Icon(
                      _isTorchOn ? Icons.flash_on_rounded : Icons.flash_off_rounded,
                      color: _isTorchOn ? Colors.black : Colors.white,
                      size: 22,
                    ),
                    tooltip: 'Toggle Flashlight',
                    onPressed: _toggleTorch,
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
