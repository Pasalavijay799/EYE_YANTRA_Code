import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'services/ble_service.dart';
import 'screens/login_screen.dart';
import 'theme.dart';

import 'dart:io';

Process? _backendProcess;

Future<void> startBackendProcess() async {
  if (Platform.isLinux || Platform.isWindows || Platform.isMacOS) {
    try {
      final exeDir = File(Platform.resolvedExecutable).parent.path;
      
      // Search paths for the compiled python executable
      var backendPath = '$exeDir/eye_yantra_backend/eye_yantra_backend';
      if (!await File(backendPath).exists()) {
        // Fallback for development run
        backendPath = '$exeDir/../../../../dist/eye_yantra_backend/eye_yantra_backend';
      }
      
      if (await File(backendPath).exists()) {
        debugPrint('Starting background backend process: $backendPath');
        _backendProcess = await Process.start(
          backendPath,
          [],
          workingDirectory: File(backendPath).parent.path,
        );
        
        // Pipe outputs to Flutter console logs
        _backendProcess!.stdout.listen((data) {
          debugPrint('Backend stdout: ${String.fromCharCodes(data)}');
        });
        _backendProcess!.stderr.listen((data) {
          debugPrint('Backend stderr: ${String.fromCharCodes(data)}');
        });
      } else {
        debugPrint('Standalone backend binary not found. Using external server.');
      }
    } catch (e) {
      debugPrint('Error starting standalone backend process: $e');
    }
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await startBackendProcess();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ApiService()),
        ChangeNotifierProvider(create: (_) => BleService()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Eye Yantra',
      theme: AppTheme.lightTheme,
      debugShowCheckedModeBanner: false,
      home: const LoginScreen(),
    );
  }
}
