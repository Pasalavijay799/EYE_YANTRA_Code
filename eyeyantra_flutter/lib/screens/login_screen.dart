import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import 'connection_screen.dart';
import 'dashboard_screen.dart';
import 'admin_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _idController = TextEditingController();
  final _dobController = TextEditingController();
  final _serverController = TextEditingController();

  String _selectedCamera = 'tablet'; // 'hardware' or 'tablet'
  bool _showServerConfig = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final apiService = Provider.of<ApiService>(context, listen: false);
      _serverController.text = apiService.baseUrl;
      _selectedCamera = apiService.localCameraSource;
      final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
      if (isDesktop) {
        if (_selectedCamera != 'hardware' && _selectedCamera != 'tablet') {
          _selectedCamera = 'hardware';
        }
      } else {
        if (_selectedCamera != 'hardware' && _selectedCamera != 'tablet') {
          _selectedCamera = 'tablet';
        }
      }
      if (!apiService.isDemoMode && !apiService.isConnected) {
        await apiService.discoverBackend();
        if (mounted) {
          _serverController.text = apiService.baseUrl;
        }
      }
      try {
        final nextId = await apiService.getNextPatientId();
        if (mounted) {
          _idController.text = nextId;
        }
      } catch (e) {
        debugPrint("Error fetching next patient ID: $e");
      }
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _idController.dispose();
    _dobController.dispose();
    _serverController.dispose();
    super.dispose();
  }

  void _submitIntake() async {
    if (!_formKey.currentState!.validate()) return;

    final apiService = Provider.of<ApiService>(context, listen: false);

    // Save server URL first if not in demo mode
    if (!apiService.isDemoMode && _showServerConfig && _serverController.text.trim().isNotEmpty) {
      await apiService.setBaseUrl(_serverController.text.trim());
    }

    final result = await apiService.submitIntake(
      name: _nameController.text.trim(),
      dob: _dobController.text.trim(),
      id: _idController.text.trim(),
    );

    if (result['status'] == 'success') {
      if (!apiService.isDemoMode) {
        // Toggle camera source in backend
        await apiService.setCameraSource(_selectedCamera);
      } else {
        await apiService.setLocalCameraSource(_selectedCamera);
      }
      
      if (!mounted) return;

      final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
      bool goDirectToDashboard = false;
      if (apiService.isDemoMode) {
        goDirectToDashboard = true;
      } else if (isDesktop) {
        goDirectToDashboard = (_selectedCamera == 'hardware');
      } else {
        goDirectToDashboard = (_selectedCamera == 'tablet');
      }

      if (goDirectToDashboard) {
        // Go straight to Dashboard (no BLE needed)
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const DashboardScreen()),
        );
      } else {
        // Go to Bluetooth/Headset setup
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const ConnectionScreen()),
        );
      }
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message'] ?? 'Failed to complete patient intake.'),
          backgroundColor: AppTheme.accent,
        ),
      );
    }
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime(2000),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppTheme.primary,
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: AppTheme.textPrimary,
            ),
            dialogBackgroundColor: Colors.white,
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        final day = picked.day.toString().padLeft(2, '0');
        final month = picked.month.toString().padLeft(2, '0');
        final year = picked.year.toString();
        _dobController.text = "${day}_${month}_${year}";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final apiService = Provider.of<ApiService>(context);
    final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;

    return Scaffold(
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: AppTheme.backgroundGradient,
            ),
          ),
          // Glow Circles
          Positioned(
            top: -100,
            left: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.primary.withOpacity(0.15),
              ),
            ),
          ),
          Positioned(
            bottom: -50,
            right: -50,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppTheme.secondary.withOpacity(0.15),
              ),
            ),
          ),
          // Content
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SizedBox(height: 30),
                  // App Brand Logo/Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          gradient: AppTheme.primaryGradient,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.remove_red_eye_rounded, size: 28, color: Colors.white),
                      ),
                      const SizedBox(width: 12),
                      const Text(
                        'EYE YANTRA',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2.0,
                          color: AppTheme.primary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Ocular Alignment Assessment Platform',
                    style: TextStyle(
                      fontSize: 14,
                      color: AppTheme.textSecondary.withOpacity(0.8),
                    ),
                  ),
                  const SizedBox(height: 40),
                  
                  // Main Card
                  Form(
                    key: _formKey,
                    child: GlassCard(
                      blur: 20,
                      opacity: 0.12,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Patient Registration',
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                              IconButton(
                                icon: Icon(
                                  _showServerConfig ? Icons.settings : Icons.settings_outlined,
                                  color: AppTheme.textSecondary,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _showServerConfig = !_showServerConfig;
                                  });
                                },
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),

                           if (_showServerConfig) ...[
                            Row(
                              children: [
                                Switch(
                                  value: apiService.isDemoMode,
                                  onChanged: (val) async {
                                    await apiService.setDemoMode(val);
                                    final nextId = await apiService.getNextPatientId();
                                    if (mounted) {
                                      _idController.text = nextId;
                                    }
                                  },
                                  activeColor: AppTheme.primary,
                                ),
                                 const Expanded(
                                  child: Text(
                                    'Offline Demo Mode (Tablet standalone)',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 13,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _serverController,
                              enabled: !apiService.isDemoMode,
                              decoration: InputDecoration(
                                labelText: 'Flask Server API Base URL',
                                prefixIcon: const Icon(Icons.dns_rounded, color: AppTheme.primary),
                                hintText: 'http://127.0.0.1:5000',
                                fillColor: apiService.isDemoMode ? Colors.white10 : null,
                                filled: apiService.isDemoMode,
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],

                          TextFormField(
                            controller: _nameController,
                            decoration: const InputDecoration(
                              labelText: 'Patient Name',
                              prefixIcon: Icon(Icons.person_rounded, color: AppTheme.primary),
                              hintText: 'e.g. Akshay',
                            ),
                            validator: (v) => (v == null || v.trim().isEmpty) ? 'Name is required' : null,
                          ),
                          const SizedBox(height: 16),



                          TextFormField(
                            controller: _dobController,
                            readOnly: true,
                            onTap: () => _selectDate(context),
                            decoration: const InputDecoration(
                              labelText: 'Date of Birth',
                              prefixIcon: Icon(Icons.calendar_today_rounded, color: AppTheme.primary),
                              hintText: 'Select Date of Birth',
                            ),
                            validator: (v) => (v == null || v.trim().isEmpty) ? 'DOB is required' : null,
                          ),
                          const SizedBox(height: 24),

                          const Text(
                            'Select Camera Source',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Container(
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.04),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0x1A1B2A6B)),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() => _selectedCamera = 'hardware'),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(vertical: 12),
                                      decoration: BoxDecoration(
                                        gradient: _selectedCamera == 'hardware' ? AppTheme.primaryGradient : null,
                                        borderRadius: BorderRadius.circular(11),
                                      ),
                                      alignment: Alignment.center,
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Icon(
                                            isDesktop ? Icons.laptop_chromebook : Icons.headset_mic_rounded,
                                            size: 18,
                                            color: _selectedCamera == 'hardware' ? Colors.white : AppTheme.textSecondary,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            isDesktop ? 'Laptop Camera' : 'Headset',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                              color: _selectedCamera == 'hardware' ? Colors.white : AppTheme.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                                Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() => _selectedCamera = 'tablet'),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(vertical: 12),
                                      decoration: BoxDecoration(
                                        gradient: _selectedCamera == 'tablet' ? AppTheme.primaryGradient : null,
                                        borderRadius: BorderRadius.circular(11),
                                      ),
                                      alignment: Alignment.center,
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Icon(
                                            isDesktop ? Icons.headset_mic_rounded : Icons.tablet_android_rounded,
                                            size: 18,
                                            color: _selectedCamera == 'tablet' ? Colors.white : AppTheme.textSecondary,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            isDesktop ? 'Headset' : 'Tablet Camera',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                              color: _selectedCamera == 'tablet' ? Colors.white : AppTheme.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),

                          ElevatedButton(
                            onPressed: apiService.isLoading ? null : _submitIntake,
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 16),
                            ),
                            child: apiService.isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      valueColor: AlwaysStoppedAnimation(Colors.white),
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('START SESSION'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Bottom Utilities
                  Column(
                    children: [
                      if (apiService.isScanning) ...[
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12.0),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const SizedBox(
                                width: 14,
                                height: 14,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation(AppTheme.primary),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Flexible(
                                child: Text(
                                  apiService.scanStatusMessage,
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      Wrap(
                        alignment: WrapAlignment.center,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        spacing: 12,
                        runSpacing: 8,
                        children: [
                          TextButton.icon(
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const AdminScreen()),
                              );
                            },
                            icon: const Icon(Icons.admin_panel_settings_rounded, color: AppTheme.primary),
                            label: const Text('Admin Panel', style: TextStyle(color: AppTheme.primary)),
                          ),
                          Container(width: 1, height: 16, color: Colors.white24),
                          TextButton.icon(
                            onPressed: apiService.isScanning
                                ? null
                                : () async {
                                    if (apiService.isConnected) {
                                      await apiService.checkConnection();
                                    } else {
                                      await apiService.discoverBackend();
                                      _serverController.text = apiService.baseUrl;
                                    }
                                  },
                            icon: apiService.isScanning
                                ? const SizedBox(
                                    width: 12,
                                    height: 12,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 1.5,
                                      valueColor: AlwaysStoppedAnimation(AppTheme.primary),
                                    ),
                                  )
                                : Icon(
                                    Icons.circle,
                                    size: 12,
                                    color: apiService.isConnected ? Colors.green : Colors.red,
                                  ),
                            label: Text(
                              apiService.isScanning
                                  ? 'Scanning...'
                                  : (apiService.isConnected ? 'Server Online' : 'Server Offline (Tap to Scan)'),
                              style: TextStyle(
                                color: apiService.isScanning
                                    ? AppTheme.primary
                                    : (apiService.isConnected ? Colors.green : Colors.red),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
