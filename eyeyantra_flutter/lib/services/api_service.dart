import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:path_provider/path_provider.dart';

class ApiService extends ChangeNotifier {
  String _baseUrl = 'http://127.0.0.1:5000';
  bool _isConnected = false;
  Map<String, dynamic> _status = {};
  bool _isLoading = false;
  bool _isDemoMode = false;
  bool _isScanning = false;
  String _scanStatusMessage = '';
  String _localCameraSource = (Platform.isLinux || Platform.isWindows || Platform.isMacOS) ? 'hardware' : 'tablet'; // 'hardware' or 'tablet'
  List<int> _availableCameras = [];
  int _activeCameraIndex = 0;

  String get baseUrl => _baseUrl;
  bool get isConnected => _isConnected;
  Map<String, dynamic> get status => _status;
  bool get isLoading => _isLoading;
  bool get isDemoMode => _isDemoMode;
  bool get isScanning => _isScanning;
  String get scanStatusMessage => _scanStatusMessage;
  String get localCameraSource => _localCameraSource;
  List<int> get availableCamerasList => _availableCameras;
  int get activeCameraIndex => _activeCameraIndex;

  String get activeUserName => _status['userName'] is String ? _status['userName'] : '';
  Map<String, dynamic> get activePatientDetails => _status['personDetails'] is Map ? _status['personDetails'] : {};
  bool get useLaptopCamera => _status['use_laptop_camera'] ?? false;
  String? get connectedBleDevice => _status['connected_device'];
  String? get streamIp => _status['stream_ip'];

  ApiService() {
    _loadBaseUrl();
  }

  Future<void> _loadBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('api_base_url') ?? 'http://127.0.0.1:5000';
    _isDemoMode = prefs.getBool('api_is_demo_mode') ?? false;
    final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
    final defaultSource = isDesktop ? 'hardware' : 'tablet';
    _localCameraSource = prefs.getString('local_camera_source') ?? defaultSource;
    if (isDesktop && _localCameraSource == 'tablet') {
      _localCameraSource = 'hardware';
    }
    notifyListeners();
    checkConnection();
  }

  Future<void> setLocalCameraSource(String source) async {
    final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
    if (isDesktop) {
      if (source == 'built-in' || source == 'external' || source == 'hardware') {
        _localCameraSource = source;
      } else {
        _localCameraSource = 'hardware';
      }
    } else {
      _localCameraSource = source;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('local_camera_source', _localCameraSource);
    notifyListeners();
  }

  Future<void> setDemoMode(bool val) async {
    _isDemoMode = val;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('api_is_demo_mode', val);
    if (val) {
      _isConnected = true;
      _status = {
        'status': 'success',
        'userName': _status['userName'] ?? 'Demo Patient',
        'personDetails': _status['personDetails'] ?? {
          'name': 'Demo Patient',
          'dob': '18_01_2006',
          'id': '18239'
        },
        'use_laptop_camera': true,
        'preliminary_check': _status['preliminary_check'] ?? false,
        'hirschberg_check': _status['hirschberg_check'] ?? false,
        'ninegaze_check': _status['ninegaze_check'] ?? false,
      };
    }
    notifyListeners();
    await checkConnection();
  }

  Future<void> setBaseUrl(String url) async {
    // Sanitize trailing slash
    if (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    _baseUrl = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_base_url', url);
    notifyListeners();
    await checkConnection();
  }

  Future<void> fetchAvailableCameras() async {
    if (_isDemoMode) return;
    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/cameras'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _availableCameras = List<int>.from(data['available'] ?? []);
        _activeCameraIndex = data['active'] ?? 0;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error fetching cameras: $e');
    }
  }

  Future<Map<String, dynamic>> switchCamera() async {
    if (_isDemoMode) return {'status': 'error', 'message': 'Not available in demo'};
    try {
      final response = await http.post(Uri.parse('$_baseUrl/api/switch_camera'));
      final data = jsonDecode(response.body);
      if (data['status'] == 'success') {
        _activeCameraIndex = data['active'] ?? 0;
        notifyListeners();
      }
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<bool> checkConnection() async {
    if (_isDemoMode) {
      _isConnected = true;
      if (_status.isEmpty || _status['personDetails'] == null) {
        _status = {
          'status': 'success',
          'userName': 'Demo Patient',
          'personDetails': {
            'name': 'Demo Patient',
            'dob': '18_01_2006',
            'id': '18239'
          },
          'use_laptop_camera': true,
          'preliminary_check': _status['preliminary_check'] ?? false,
          'hirschberg_check': _status['hirschberg_check'] ?? false,
          'ninegaze_check': _status['ninegaze_check'] ?? false,
        };
      }
      notifyListeners();
      return true;
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/status')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        _status = jsonDecode(response.body);
        _isConnected = true;
      } else {
        _isConnected = false;
      }
    } catch (_) {
      _isConnected = false;
    }
    notifyListeners();
    return _isConnected;
  }

  Future<bool> discoverBackend() async {
    if (_isDemoMode || _isScanning) return false;
    _isScanning = true;
    _scanStatusMessage = 'Searching for local network interfaces...';
    notifyListeners();

    try {
      final interfaces = await NetworkInterface.list(
        includeLoopback: false,
        type: InternetAddressType.IPv4,
      );

      final List<String> subnets = [];
      debugPrint('--- Auto-Discovery: Network Interfaces Detected ---');
      for (var interface in interfaces) {
        debugPrint('Interface: ${interface.name}');
        for (var addr in interface.addresses) {
          final ip = addr.address;
          debugPrint('  IP Address: $ip');
          // Extract subnet (e.g. 192.168.1.45 -> 192.168.1.)
          final lastDot = ip.lastIndexOf('.');
          if (lastDot != -1) {
            final subnet = ip.substring(0, lastDot + 1);
            if (!subnets.contains(subnet)) {
              subnets.add(subnet);
            }
          }
        }
      }
      debugPrint('Detected Subnets: $subnets');

      // Add common fallbacks in case NetworkInterface.list() returned empty
      // Or in case we want to scan the active subnet the user is on
      final fallbacks = ['192.168.1.', '192.168.0.', '192.168.43.', '10.26.86.', '10.113.184.', '10.0.2.'];
      for (var fb in fallbacks) {
        if (!subnets.contains(fb)) {
          subnets.add(fb);
        }
      }
      debugPrint('Final List of Subnets to Scan: $subnets');

      for (var subnet in subnets) {
        _scanStatusMessage = 'Scanning subnet $subnet* on port 5000...';
        notifyListeners();

        // Run scans in parallel batches of 50 to prevent OS socket exhaustion
        const batchSize = 50;
        for (int j = 0; j < 254; j += batchSize) {
          final end = (j + batchSize < 254) ? j + batchSize : 254;
          final List<Future<String?>> scanTasks = [];

          for (int i = j + 1; i <= end; i++) {
            final targetIp = '$subnet$i';
            scanTasks.add(() async {
              try {
                // 1000ms timeout for socket connection to account for slower/busy Wi-Fi subnets
                final socket = await Socket.connect(targetIp, 5000, timeout: const Duration(milliseconds: 1000));
                socket.destroy();
                // Verify it's actually the Eye Yantra backend
                final uri = Uri.parse('http://$targetIp:5000/api/status');
                final res = await http.get(uri).timeout(const Duration(seconds: 2));
                if (res.statusCode == 200) {
                  final body = jsonDecode(res.body);
                  if (body is Map && (body.containsKey('use_laptop_camera') || body.containsKey('tests'))) {
                    return targetIp;
                  }
                }
              } catch (_) {}
              return null;
            }());
          }

          final results = await Future.wait(scanTasks);
          final foundIp = results.firstWhere((ip) => ip != null, orElse: () => null);
          if (foundIp != null) {
            _scanStatusMessage = 'Backend found at $foundIp!';
            _isScanning = false;
            notifyListeners();
            await setBaseUrl('http://$foundIp:5000');
            return true;
          }
        }
      }

      _scanStatusMessage = 'No Eye Yantra backend found on local network.';
    } catch (e) {
      _scanStatusMessage = 'Scan failed: $e';
    } finally {
      _isScanning = false;
      notifyListeners();
    }
    return false;
  }


  Future<Map<String, dynamic>> submitIntake({
    required String name,
    required String dob,
    required String id,
  }) async {
    if (_isDemoMode) {
      _status['userName'] = name;
      _status['personDetails'] = {
        'name': name,
        'dob': dob,
        'id': id,
      };
      _status['preliminary_check'] = false;
      _status['hirschberg_check'] = false;
      _status['ninegaze_check'] = false;
      notifyListeners();
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/intake'),
        body: {
          'patient_name': name,
          'patient_dob': dob,
          'patient_id': id,
        },
      );
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> resetApp() async {
    if (_isDemoMode) {
      _status = {
        'status': 'success',
        'userName': 'Demo Patient',
        'personDetails': {
          'name': 'Demo Patient',
          'dob': '18_01_2006',
          'id': '18239'
        },
        'use_laptop_camera': true,
        'preliminary_check': false,
        'hirschberg_check': false,
        'ninegaze_check': false,
      };
      notifyListeners();
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(Uri.parse('$_baseUrl/api/reset'));
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> setCameraSource(String source) async {
    await setLocalCameraSource(source);
    if (_isDemoMode) {
      _status['use_laptop_camera'] = (source == 'laptop');
      notifyListeners();
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/set_camera_source'),
        body: {'source': source},
      );
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> saveManualIp(String ip) async {
    if (_isDemoMode) {
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/save_manual_ip'),
        body: {'ip': ip},
      );
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> capturePreliminary(String date) async {
    if (_isDemoMode) {
      _status['preliminary_check'] = true;
      notifyListeners();
      return {'status': 'success', 'image_url': 'mock:preliminary'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/preliminaryroute'),
        body: {'date': date},
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> getPreliminaryResults() async {
    if (_isDemoMode) {
      return {
        'status': 'success',
        'image_url': 'mock:preliminary',
        'text_content': 'PRELIMINARY ASSESSMENT LOG:\n- Patient: $activeUserName\n- Inter-pupillary distance: 63.4 mm\n- Visual alignment: Within Normal Limits\n- Fixation: Stable and Centered'
      };
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/preliminary/results'));
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> captureHirschberg(String date) async {
    if (_isDemoMode) {
      _status['hirschberg_check'] = true;
      notifyListeners();
      return {'status': 'success', 'image_url': 'mock:hirschberg'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/hirschberg_capture'),
        body: {'date': date},
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> getHirschbergResults() async {
    if (_isDemoMode) {
      return {
        'status': 'success',
        'image_url': 'mock:hirschberg',
        'text_content': 'HIRSCHBERG TEST RESULTS:\n- Left Eye Reflex Deviation: +2.1 deg (Normal)\n- Right Eye Reflex Deviation: -1.4 deg (Normal)\n- Estimated Esotropia/Exotropia: None detected\n- Alignment ratio: 1.02\n- Corneal reflex: Symmetrical'
      };
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/hirschberg/results'));
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> capture9Gaze(String gaze) async {
    if (_isDemoMode) {
      _status['ninegaze_check'] = true;
      notifyListeners();
      return {'status': 'success', 'image_url': 'mock:nine_gaze'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/capture_9gaze'),
        body: {'gaze': gaze},
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> get9GazeResults() async {
    if (_isDemoMode) {
      return {
        'status': 'success',
        'image_url': 'mock:nine_gaze',
        'text_content': '9-GAZE ASSESSMENT SUMMARY:\n- Center Gaze: Orthophoria\n- Upward Gaze: Normal elevation\n- Downward Gaze: Normal depression\n- Lateral Gazes: Full motility, no restriction detected\n- Areal Ratios: OD/OS alignment symmetry = 98.4%\n- Extraocular motility: Normal in all 9 diagnostic positions of gaze.'
      };
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/9gaze/results'));
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> uploadPreliminary(String filePath, String date) async {
    _setLoading(true);
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/upload_preliminary'));
      request.fields['date'] = date;
      request.files.add(await http.MultipartFile.fromPath('file', filePath));
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> uploadHirschberg(String filePath, String date) async {
    _setLoading(true);
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/upload_hirschberg'));
      request.fields['date'] = date;
      request.files.add(await http.MultipartFile.fromPath('file', filePath));
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> upload9Gaze(String filePath, String gaze) async {
    _setLoading(true);
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/api/upload_9gaze'));
      request.fields['gaze'] = gaze;
      request.files.add(await http.MultipartFile.fromPath('file', filePath));
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> generateOverallReport() async {
    if (_isDemoMode) {
      return {'status': 'success', 'message': 'Mock PDF Report generated successfully.'};
    }

    _setLoading(true);
    try {
      final response = await http.get(Uri.parse('$_baseUrl/generate_overall_report'));
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }
  Future<Map<String, dynamic>> editResults({
    required String testType,
    required String content,
  }) async {
    if (_isDemoMode) {
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/edit_results'),
        body: {
          'test_type': testType,
          'content': content,
        },
      );
      final data = jsonDecode(response.body);
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<File?> downloadOverallReport() async {
    if (_isDemoMode) {
      try {
        final directory = await getApplicationDocumentsDirectory();
        final filePath = '${directory.path}/overall_report_${activeUserName}.pdf';
        final file = File(filePath);
        final pdfBytes = latin1.encode(
          '%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [ 0 0 612 792 ] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 20 >>\nstream\nBT /F1 12 Tf ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000210 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n280\n%%EOF'
        );
        await file.writeAsBytes(pdfBytes);
        return file;
      } catch (e) {
        debugPrint('Report mock write error: $e');
        return null;
      }
    }

    _setLoading(true);
    try {
      final response = await http.get(Uri.parse('$_baseUrl/download_overall_report'));
      if (response.statusCode == 200) {
        final directory = await getApplicationDocumentsDirectory();
        final filePath = '${directory.path}/overall_report_${activeUserName}.pdf';
        final file = File(filePath);
        await file.writeAsBytes(response.bodyBytes);
        return file;
      }
      return null;
    } catch (e) {
      debugPrint('Report download error: $e');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  Future<List<dynamic>> getPatientsList() async {
    if (_isDemoMode) {
      return [
        {
          'userName': 'Demo Patient',
          'personDetails': {'name': 'Demo Patient', 'dob': '18_01_2006', 'id': '18239'}
        }
      ];
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/admin/patients'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  Future<Map<String, dynamic>> selectPatient({
    required String name,
    required String dob,
    required String id,
  }) async {
    if (_isDemoMode) {
      _status['userName'] = name;
      _status['personDetails'] = {'name': name, 'dob': dob, 'id': id};
      notifyListeners();
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/set_active_patient'),
        body: {
          'name': name,
          'dob': dob,
          'id': id,
        },
      );
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> editPatient({
    required String oldRawUsername,
    required String newName,
    required String newDob,
    required String newId,
  }) async {
    if (_isDemoMode) {
      _status['userName'] = newName;
      _status['personDetails'] = {'name': newName, 'dob': newDob, 'id': newId};
      notifyListeners();
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/edit_patient'),
        body: {
          'old_raw_username': oldRawUsername,
          'name': newName,
          'dob': newDob,
          'id': newId,
        },
      );
      final data = jsonDecode(response.body);
      await checkConnection();
      return data;
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  Future<Map<String, dynamic>> getAdminConfig() async {
    if (_isDemoMode) {
      return {'clinic_name': 'Demo Eye Clinic', 'clinic_address': '123 Health Ave', 'clinic_phone': '+1 (555) 019-2834'};
    }

    try {
      final response = await http.get(Uri.parse('$_baseUrl/api/admin/config'));
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  Future<Map<String, dynamic>> saveAdminConfig(Map<String, String> config) async {
    if (_isDemoMode) {
      return {'status': 'success'};
    }

    _setLoading(true);
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/save_admin_config'),
        body: config,
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool val) {
    _isLoading = val;
    notifyListeners();
  }
}
