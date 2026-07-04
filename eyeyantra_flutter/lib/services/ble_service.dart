import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class BleService extends ChangeNotifier {
  static const String serviceUuid = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
  static const String rxUuid = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'; // Write
  static const String txUuid = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'; // Notify
  static const String targetDeviceName = 'AMEBA_BLE_DEV';

  BluetoothDevice? _connectedDevice;
  BluetoothCharacteristic? _rxCharacteristic;
  BluetoothCharacteristic? _txCharacteristic;
  
  bool _isScanning = false;
  bool _isConnecting = false;
  List<ScanResult> _scanResults = [];
  final List<String> _logs = [];
  String _streamIp = '';

  BluetoothDevice? get connectedDevice => _connectedDevice;
  bool get isScanning => _isScanning;
  bool get isConnecting => _isConnecting;
  List<ScanResult> get scanResults => _scanResults;
  List<String> get logs => _logs;
  String get streamIp => _streamIp;
  bool get isConnected => _connectedDevice != null;

  StreamSubscription? _scanSubscription;
  StreamSubscription? _connectionStateSubscription;
  StreamSubscription? _txSubscription;

  BleService() {
    _initBle();
  }

  void _initBle() {
    FlutterBluePlus.isScanning.listen((scanning) {
      _isScanning = scanning;
      notifyListeners();
    });
  }

  void _addLog(String msg) {
    final timestamp = DateTime.now().toString().substring(11, 19);
    _logs.add('[$timestamp] $msg');
    if (_logs.length > 50) _logs.removeAt(0);
    notifyListeners();
  }

  Future<void> startScan() async {
    if (_isScanning) return;
    
    _scanResults.clear();
    _addLog('Scanning for BLE devices...');
    
    try {
      await FlutterBluePlus.startScan(
        timeout: const Duration(seconds: 15),
        withServices: [Guid(serviceUuid)],
      );
      
      _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
        // Filter by device name or target service
        _scanResults = results.where((r) => r.device.platformName == targetDeviceName || r.advertisementData.serviceUuids.contains(Guid(serviceUuid))).toList();
        notifyListeners();
      });
    } catch (e) {
      _addLog('Scan failed: $e');
    }
  }

  Future<void> stopScan() async {
    await FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();
    _scanSubscription = null;
    _addLog('Scan stopped.');
  }

  Future<bool> connectToDevice(BluetoothDevice device) async {
    _isConnecting = true;
    _addLog('Connecting to ${device.platformName} (${device.remoteId})...');
    notifyListeners();

    try {
      await device.connect(timeout: const Duration(seconds: 10), autoConnect: false);
      _connectedDevice = device;
      
      _addLog('Connected. Discovering services...');
      List<BluetoothService> services = await device.discoverServices();
      
      for (var service in services) {
        if (service.uuid.toString().toUpperCase() == serviceUuid) {
          for (var char in service.characteristics) {
            if (char.uuid.toString().toUpperCase() == rxUuid) {
              _rxCharacteristic = char;
              _addLog('RX Characteristic found (Write).');
            } else if (char.uuid.toString().toUpperCase() == txUuid) {
              _txCharacteristic = char;
              _addLog('TX Characteristic found (Notify).');
            }
          }
        }
      }

      if (_txCharacteristic != null) {
        await _txCharacteristic!.setNotifyValue(true);
        _addLog('Notifications enabled on TX.');
        
        // Listen to notifications
        String buffer = '';
        _txSubscription = _txCharacteristic!.lastValueStream.listen((value) {
          final data = utf8.decode(value, allowMalformed: true);
          buffer += data;
          
          if (buffer.contains('\n')) {
            final lines = buffer.split('\n');
            // Last element is either empty or incomplete chunk
            buffer = lines.last;
            
            for (var i = 0; i < lines.length - 1; i++) {
              final line = lines[i].trim();
              if (line.isNotEmpty) {
                _addLog('Received: $line');
                _processNotification(line);
              }
            }
          }
        });
      }

      _monitorConnection(device);
      _isConnecting = false;
      notifyListeners();
      return true;
    } catch (e) {
      _addLog('Connection failed: $e');
      _isConnecting = false;
      _connectedDevice = null;
      notifyListeners();
      return false;
    }
  }

  void _monitorConnection(BluetoothDevice device) {
    _connectionStateSubscription?.cancel();
    _connectionStateSubscription = device.connectionState.listen((state) {
      if (state == BluetoothConnectionState.disconnected) {
        _addLog('Device disconnected.');
        _connectedDevice = null;
        _rxCharacteristic = null;
        _txCharacteristic = null;
        _txSubscription?.cancel();
        _txSubscription = null;
        notifyListeners();
      }
    });
  }

  void _processNotification(String line) {
    if (line.startsWith('IP:')) {
      _streamIp = line.substring(3).trim();
      _addLog('Extracted IP Address: $_streamIp');
      notifyListeners();
    }
  }

  Future<bool> sendWifiCredentials(String ssid, String password) async {
    if (_rxCharacteristic == null) {
      _addLog('Cannot send credentials: Rx characteristic not configured.');
      return false;
    }

    final message = '$ssid,$password\n';
    _addLog('Sending Wi-Fi credentials...');
    
    try {
      final bytes = utf8.encode(message);
      // Realtek MTU limitation: write in 20-byte chunks
      const chunkSize = 20;
      for (var i = 0; i < bytes.length; i += chunkSize) {
        final end = (i + chunkSize < bytes.length) ? i + chunkSize : bytes.length;
        final chunk = bytes.sublist(i, end);
        await _rxCharacteristic!.write(chunk, withoutResponse: false);
        await Future.delayed(const Duration(milliseconds: 100)); // Delay between chunks
      }
      _addLog('Wi-Fi credentials sent.');
      return true;
    } catch (e) {
      _addLog('Failed to send credentials: $e');
      return false;
    }
  }

  Future<bool> sendCommand(String command) async {
    if (_rxCharacteristic == null) {
      _addLog('Cannot send command: Rx characteristic not configured.');
      return false;
    }

    _addLog('Sending command: $command');
    try {
      final bytes = utf8.encode('$command\n');
      await _rxCharacteristic!.write(bytes, withoutResponse: false);
      return true;
    } catch (e) {
      _addLog('Failed to send command: $e');
      return false;
    }
  }

  Future<void> disconnect() async {
    if (_connectedDevice != null) {
      _addLog('Disconnecting from ${_connectedDevice!.platformName}...');
      await _connectedDevice!.disconnect();
    }
  }
}
