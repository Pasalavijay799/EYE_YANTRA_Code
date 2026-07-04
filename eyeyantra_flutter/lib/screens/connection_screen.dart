import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/ble_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import 'dashboard_screen.dart';

class ConnectionScreen extends StatefulWidget {
  const ConnectionScreen({Key? key}) : super(key: key);

  @override
  State<ConnectionScreen> createState() => _ConnectionScreenState();
}

class _ConnectionScreenState extends State<ConnectionScreen> {
  final _ssidController = TextEditingController();
  final _passwordController = TextEditingController();
  final _manualIpController = TextEditingController();
  
  bool _showManualIp = false;

  @override
  void initState() {
    super.initState();
    // Start scanning on load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<BleService>(context, listen: false).startScan();
    });
  }

  @override
  void dispose() {
    _ssidController.dispose();
    _passwordController.dispose();
    _manualIpController.dispose();
    super.dispose();
  }

  void _sendWifi() async {
    final bleService = Provider.of<BleService>(context, listen: false);
    if (_ssidController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter Wi-Fi SSID'), backgroundColor: AppTheme.accent),
      );
      return;
    }

    final success = await bleService.sendWifiCredentials(
      _ssidController.text.trim(),
      _passwordController.text,
    );

    if (success) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Wi-Fi credentials sent. Waiting for IP address...'), backgroundColor: AppTheme.primary),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to send Wi-Fi credentials via BLE.'), backgroundColor: AppTheme.accent),
      );
    }
  }

  void _saveManualIp() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    if (_manualIpController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter IP address'), backgroundColor: AppTheme.accent),
      );
      return;
    }

    final result = await apiService.saveManualIp(_manualIpController.text.trim());
    if (result['status'] == 'success') {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('IP saved successfully.'), backgroundColor: AppTheme.primary),
      );
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['message'] ?? 'Failed to save manual IP.'), backgroundColor: AppTheme.accent),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final bleService = Provider.of<BleService>(context);
    final apiService = Provider.of<ApiService>(context);

    // Sync BleService stream IP with Python Backend if detected
    if (bleService.streamIp.isNotEmpty && apiService.streamIp != bleService.streamIp) {
      apiService.saveManualIp(bleService.streamIp);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Headset Setup'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: bleService.isScanning ? null : bleService.startScan,
          ),
        ],
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
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Title / Status Card
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              bleService.isConnected ? Icons.bluetooth_connected : Icons.bluetooth_searching,
                              color: bleService.isConnected ? AppTheme.primary : AppTheme.secondary,
                              size: 28,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                bleService.isConnected 
                                    ? 'Headset Connected' 
                                    : 'Searching for Headset...',
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                            ),
                          ],
                        ),
                        if (bleService.isConnected) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Connected to ${bleService.connectedDevice?.platformName ?? 'AMEBA_BLE_DEV'}',
                            style: const TextStyle(color: Colors.white70),
                          ),
                        ] else ...[
                          const SizedBox(height: 12),
                          const LinearProgressIndicator(
                            backgroundColor: Colors.white10,
                            valueColor: AlwaysStoppedAnimation(AppTheme.primary),
                          ),
                        ]
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // If connected: show WiFi Credentials Form
                  if (bleService.isConnected) ...[
                    GlassCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.wifi, color: AppTheme.primary),
                              SizedBox(width: 8),
                              Text(
                                'Headset Wi-Fi Setup',
                                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Configure the headset to join the same Wi-Fi network as this app.',
                            style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                          ),
                          const SizedBox(height: 20),
                          TextFormField(
                            controller: _ssidController,
                            decoration: const InputDecoration(
                              labelText: 'Wi-Fi Network Name (SSID)',
                              prefixIcon: Icon(Icons.network_wifi_rounded, color: AppTheme.primary),
                            ),
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _passwordController,
                            obscureText: true,
                            decoration: const InputDecoration(
                              labelText: 'Wi-Fi Password',
                              prefixIcon: Icon(Icons.lock_rounded, color: AppTheme.primary),
                            ),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton.icon(
                            onPressed: _sendWifi,
                            icon: const Icon(Icons.send_rounded, size: 18),
                            label: const Text('CONFIGURE HEADSET'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // Discovered Devices list
                  if (!bleService.isConnected) ...[
                    const Text(
                      'Discovered Devices',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white70),
                    ),
                    const SizedBox(height: 10),
                    if (bleService.scanResults.isEmpty)
                      GlassCard(
                        padding: const EdgeInsets.all(32),
                        child: Center(
                          child: Text(
                            bleService.isScanning ? 'Scanning...' : 'No hardware headsets detected nearby.',
                            style: const TextStyle(color: AppTheme.textSecondary),
                          ),
                        ),
                      )
                    else
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: bleService.scanResults.length,
                        itemBuilder: (context, index) {
                          final result = bleService.scanResults[index];
                          return Card(
                            color: Colors.white.withOpacity(0.05),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(color: Colors.white.withOpacity(0.1)),
                            ),
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              title: Text(result.device.platformName.isEmpty ? 'Unknown' : result.device.platformName),
                              subtitle: Text(result.device.remoteId.str),
                              trailing: ElevatedButton(
                                onPressed: bleService.isConnecting 
                                    ? null 
                                    : () => bleService.connectToDevice(result.device),
                                style: ElevatedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                  minimumSize: Size.zero,
                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                ),
                                child: bleService.isConnecting
                                    ? const SizedBox(
                                        height: 12,
                                        width: 12,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                      )
                                    : const Text('Connect'),
                              ),
                            ),
                          );
                        },
                      ),
                    const SizedBox(height: 20),
                  ],

                  // Connection IP Indicator
                  if (bleService.streamIp.isNotEmpty || apiService.streamIp != null) ...[
                    GlassCard(
                      borderColor: AppTheme.primary.withOpacity(0.5),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.live_tv_rounded, color: Colors.green),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Camera MJPEG Stream Live', style: TextStyle(fontWeight: FontWeight.bold)),
                                    Text(
                                      'Stream URL: http://${bleService.streamIp.isNotEmpty ? bleService.streamIp : apiService.streamIp}:80',
                                      style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: () {
                              Navigator.of(context).pushReplacement(
                                MaterialPageRoute(builder: (_) => const DashboardScreen()),
                              );
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.green,
                            ),
                            child: const Text('GO TO CLINICAL DASHBOARD'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // Manual IP Configurator
                  GestureDetector(
                    onTap: () => setState(() => _showManualIp = !_showManualIp),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            _showManualIp ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                            size: 20,
                            color: AppTheme.primary,
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Skip BLE & Configure Stream IP Manually',
                            style: TextStyle(
                              color: AppTheme.primary,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  if (_showManualIp) ...[
                    const SizedBox(height: 10),
                    GlassCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          TextFormField(
                            controller: _manualIpController,
                            decoration: const InputDecoration(
                              labelText: 'Stream IP Address',
                              hintText: 'e.g. 192.168.1.15',
                              prefixIcon: Icon(Icons.settings_ethernet_rounded, color: AppTheme.primary),
                            ),
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: _saveManualIp,
                            child: const Text('SAVE AND PROCEED'),
                          ),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 30),
                  // Log console
                  const Text('Device Logs', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Container(
                    height: 120,
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.black45,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white10),
                    ),
                    child: ListView.builder(
                      itemCount: bleService.logs.length,
                      itemBuilder: (context, index) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            bleService.logs[index],
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 11,
                              color: Colors.lightGreen,
                            ),
                          ),
                        );
                      },
                    ),
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
