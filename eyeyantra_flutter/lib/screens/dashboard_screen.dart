import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:open_file/open_file.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import 'login_screen.dart';
import 'preliminary_test_screen.dart';
import 'hirschberg_test_screen.dart';
import 'nine_gaze_test_screen.dart';
import 'results_screen.dart';
import 'admin_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _generatedPattern = '';
  bool _reportReady = false;

  @override
  void initState() {
    super.initState();
    _refreshStatus();
  }

  Future<void> _refreshStatus() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    await apiService.checkConnection();
  }

  void _resetSession() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.resetApp();
    if (result['status'] == 'success') {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  void _generateReport() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.generateOverallReport();
    
    if (result['status'] == 'success') {
      setState(() {
        _generatedPattern = result['pattern'] ?? 'Analysis Complete';
        _reportReady = true;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Overall Report generated successfully!'),
          backgroundColor: AppTheme.primary,
        ),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['error'] ?? 'Failed to generate report.'),
          backgroundColor: AppTheme.accent,
        ),
      );
    }
  }

  void _downloadAndOpenReport() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final file = await apiService.downloadOverallReport();
    if (file != null) {
      final result = await OpenFile.open(file.path);
      if (result.type != ResultType.done) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not open PDF file. Saved at: ${file.path}'),
            backgroundColor: AppTheme.accent,
          ),
        );
      }
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to download PDF report.'),
          backgroundColor: AppTheme.accent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final apiService = Provider.of<ApiService>(context);
    final testStatus = apiService.status['tests'] ?? {};
    
    final bool prelimDone = testStatus['preliminary'] ?? false;
    final bool hirschbergDone = testStatus['hirschberg'] ?? false;
    final bool nineGazeDone = testStatus['nine_gaze'] ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Clinical Dashboard'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _refreshStatus,
          ),
          IconButton(
            icon: const Icon(Icons.admin_panel_settings_rounded),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AdminScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: AppTheme.accent),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Reset Session?'),
                  content: const Text('This will clear the current patient session variables and return to registration.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                    TextButton(onPressed: () {
                      Navigator.pop(ctx);
                      _resetSession();
                    }, child: const Text('Reset', style: TextStyle(color: AppTheme.accent))),
                  ],
                ),
              );
            },
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
                  // Active Patient Header Card
                  GlassCard(
                    gradientColors: const [AppTheme.primary, AppTheme.secondary],
                    opacity: 0.15,
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 28,
                          backgroundColor: Colors.white.withOpacity(0.15),
                          child: const Icon(Icons.person_rounded, color: Colors.white, size: 32),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                apiService.activePatientDetails['userName'] ?? 'No Active Patient',
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'ID: ${apiService.activePatientDetails['id'] ?? 'N/A'}  •  DOB: ${apiService.activePatientDetails['dob'] ?? 'N/A'}',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.white.withOpacity(0.8),
                                ),
                              ),
                            ],
                          ),
                        ),
                        Builder(
                          builder: (context) {
                            final isDesktop = Platform.isLinux || Platform.isWindows || Platform.isMacOS;
                            if (isDesktop && apiService.useLaptopCamera) {
                              return PopupMenuButton<String>(
                                tooltip: 'Switch Camera',
                                onSelected: (String source) async {
                                  await apiService.setCameraSource(source);
                                },
                                itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                                  const PopupMenuItem<String>(
                                    value: 'built-in',
                                    child: Row(
                                      children: [
                                        Icon(Icons.laptop_chromebook, size: 18, color: AppTheme.primary),
                                        SizedBox(width: 8),
                                        Text('Laptop Cam (Built-in)'),
                                      ],
                                    ),
                                  ),
                                  const PopupMenuItem<String>(
                                    value: 'external',
                                    child: Row(
                                      children: [
                                        Icon(Icons.videocam_rounded, size: 18, color: AppTheme.primary),
                                        SizedBox(width: 8),
                                        Text('USB Cam (External)'),
                                      ],
                                    ),
                                  ),
                                ],
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.3),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: Colors.white38),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        apiService.localCameraSource == 'external'
                                            ? Icons.videocam_rounded
                                            : Icons.laptop_chromebook,
                                        size: 14,
                                        color: Colors.white,
                                      ),
                                      const SizedBox(width: 6),
                                      Text(
                                        apiService.localCameraSource == 'external' ? 'USB Cam' : 'Laptop Cam',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.white,
                                        ),
                                      ),
                                      const SizedBox(width: 4),
                                      const Icon(
                                        Icons.arrow_drop_down,
                                        size: 14,
                                        color: Colors.white70,
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            } else {
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.white24,
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Text(
                                  apiService.useLaptopCamera ? 'Laptop Cam' : 'Headset',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                              );
                            }
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  Text(
                    'Clinical Assessment Tests',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 18),
                  ),
                  const SizedBox(height: 12),

                  // Test Grid
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final double width = constraints.maxWidth;
                      final int crossAxisCount = width > 600 ? 3 : 2;
                      final double childAspectRatio = width > 600 ? 1.35 : 1.15;
                      return GridView.count(
                        crossAxisCount: crossAxisCount,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        mainAxisSpacing: 16,
                        crossAxisSpacing: 16,
                        childAspectRatio: childAspectRatio,
                        children: [
                          // Preliminary Test Card
                          _buildTestCard(
                            context: context,
                            title: 'Preliminary',
                            subtitle: 'Baseline open-eyes assessment & calibration.',
                            icon: Icons.auto_awesome_rounded,
                            isDone: prelimDone,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const PreliminaryTestScreen()),
                              );
                            },
                          ),
                          // Hirschberg Test Card
                          _buildTestCard(
                            context: context,
                            title: 'Hirschberg',
                            subtitle: 'Corneal light reflex deviation analysis.',
                            icon: Icons.lightbulb_rounded,
                            isDone: hirschbergDone,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const HirschbergTestScreen()),
                              );
                            },
                          ),
                          // 9-Gaze Test Card
                          _buildTestCard(
                            context: context,
                            title: '9-Gaze Grid',
                            subtitle: 'Cardinal grid ocular motility tracking.',
                            icon: Icons.grid_view_rounded,
                            isDone: nineGazeDone,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(builder: (_) => const NineGazeTestScreen()),
                              );
                            },
                          ),
                          // Results Archive Card
                          _buildTestCard(
                            context: context,
                            title: 'Latest Results',
                            subtitle: 'Inspect raw data & diagnostic logs.',
                            icon: Icons.assignment_rounded,
                            isDone: prelimDone || hirschbergDone || nineGazeDone,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => ResultsScreen(
                                    initialTab: prelimDone ? 0 : (hirschbergDone ? 1 : 2),
                                  ),
                                ),
                              );
                            },
                          ),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 28),

                  // Overall Assessment Report Card
                  Text(
                    'Overall Evaluation',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 18),
                  ),
                  const SizedBox(height: 12),
                  GlassCard(
                    borderColor: _reportReady 
                        ? AppTheme.primary.withOpacity(0.5) 
                        : Colors.white.withOpacity(0.12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: _reportReady ? Colors.green.withOpacity(0.15) : Colors.white10,
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                _reportReady ? Icons.check_circle_rounded : Icons.pending_actions_rounded,
                                color: _reportReady ? Colors.green : AppTheme.secondary,
                              ),
                            ),
                            const SizedBox(width: 12),
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Comprehensive Report',
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  ),
                                  Text(
                                    'Combines Hirschberg, 9-Gaze, and Preliminary results.',
                                    style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        if (_generatedPattern.isNotEmpty) ...[
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.white.withOpacity(0.08)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'DIAGNOSTIC ALIGNMENT PATTERN:',
                                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.textSecondary),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  _generatedPattern,
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.greenAccent,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton(
                                onPressed: apiService.isLoading ? null : _generateReport,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primary,
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                ),
                                child: apiService.isLoading
                                    ? const SizedBox(
                                        height: 18,
                                        width: 18,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                      )
                                    : const Text('GENERATE PDF REPORT'),
                              ),
                            ),
                            if (_reportReady) ...[
                              const SizedBox(width: 12),
                              IconButton(
                                onPressed: _downloadAndOpenReport,
                                icon: const Icon(Icons.picture_as_pdf_rounded, color: AppTheme.accent),
                                tooltip: 'Download and View PDF',
                              ),
                            ],
                          ],
                        ),
                        if (!prelimDone || !hirschbergDone || !nineGazeDone) ...[
                          const SizedBox(height: 12),
                          const Row(
                            children: [
                              Icon(Icons.warning_amber_rounded, color: Colors.amber, size: 14),
                              SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  'Some tests are incomplete. Report will contain placeholder fields.',
                                  style: TextStyle(color: Colors.amber, fontSize: 11),
                                ),
                              ),
                            ],
                          ),
                        ]
                      ],
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

  Widget _buildTestCard({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required bool isDone,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: GlassCard(
          padding: const EdgeInsets.all(14),
          borderColor: isDone ? Colors.green.withOpacity(0.4) : null,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(
                    icon,
                    color: isDone ? Colors.greenAccent : AppTheme.primary,
                    size: 24,
                  ),
                  if (isDone)
                    const Icon(
                      Icons.check_circle_rounded,
                      color: Colors.greenAccent,
                      size: 18,
                    )
                  else
                    const Icon(
                      Icons.circle_outlined,
                      color: Colors.white24,
                      size: 18,
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
