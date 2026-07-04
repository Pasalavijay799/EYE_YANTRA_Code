import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';

class ResultsScreen extends StatefulWidget {
  final int initialTab;
  const ResultsScreen({Key? key, this.initialTab = 0}) : super(key: key);

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this, initialIndex: widget.initialTab);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assessment Results'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textSecondary,
          tabs: const [
            Tab(text: 'Preliminary', icon: Icon(Icons.auto_awesome_rounded, size: 18)),
            Tab(text: 'Hirschberg', icon: Icon(Icons.lightbulb_rounded, size: 18)),
            Tab(text: '9-Gaze Grid', icon: Icon(Icons.grid_view_rounded, size: 18)),
          ],
        ),
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
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildPreliminaryTab(),
                _buildHirschbergTab(),
                _buildNineGazeTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreliminaryTab() {
    final apiService = Provider.of<ApiService>(context, listen: false);
    return FutureBuilder<Map<String, dynamic>>(
      future: apiService.getPreliminaryResults(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
        }
        if (snapshot.hasError || snapshot.data == null || snapshot.data!['status'] == 'error') {
          return _buildNoResultsView('No Preliminary assessment data available for this patient.');
        }

        final data = snapshot.data!;
        final imageUrl = '${apiService.baseUrl}${data['image_url']}';
        final textContent = data['text_content'] ?? 'No text logs available.';

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildResultImageCard(imageUrl),
              const SizedBox(height: 20),
              EditableDiagnosticLogCard(
                testType: 'preliminary',
                initialText: textContent,
                title: 'Diagnostic Summary',
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHirschbergTab() {
    final apiService = Provider.of<ApiService>(context, listen: false);
    return FutureBuilder<Map<String, dynamic>>(
      future: apiService.getHirschbergResults(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
        }
        if (snapshot.hasError || snapshot.data == null || snapshot.data!['status'] == 'error') {
          return _buildNoResultsView('No Hirschberg assessment data available for this patient.');
        }

        final data = snapshot.data!;
        final imageUrl = '${apiService.baseUrl}${data['image_url']}';
        final textContent = data['text_content'] ?? 'No text logs available.';

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildResultImageCard(imageUrl),
              const SizedBox(height: 20),
              EditableDiagnosticLogCard(
                testType: 'hirschberg',
                initialText: textContent,
                title: 'Diagnostic Summary',
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildNineGazeTab() {
    final apiService = Provider.of<ApiService>(context, listen: false);
    return FutureBuilder<Map<String, dynamic>>(
      future: apiService.get9GazeResults(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
        }
        if (snapshot.hasError || snapshot.data == null || snapshot.data!['status'] == 'error') {
          return _buildNoResultsView('No 9-Gaze Grid assessment data available for this patient.');
        }

        final data = snapshot.data!;
        final combinedImageUrl = '${apiService.baseUrl}${data['combined_image_url']}';
        final textContent = data['text_content'] ?? 'No text logs available.';
        final processedImages = data['processed_images'] as List? ?? [];
        final imageUrls = data['processed_images_urls'] as List? ?? [];

        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Combined Grid Map', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 8),
              _buildResultImageCard(combinedImageUrl),
              const SizedBox(height: 24),
              
              if (processedImages.isNotEmpty) ...[
                const Text('Processed Positions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 8),
                SizedBox(
                  height: 110,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: processedImages.length,
                    itemBuilder: (context, idx) {
                      final url = '${apiService.baseUrl}${imageUrls[idx]}';
                      return Container(
                        width: 140,
                        margin: const EdgeInsets.only(right: 12),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.white12),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Image.network(
                          url,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image, size: 24)),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 24),
              ],

              EditableDiagnosticLogCard(
                testType: 'nine_gaze',
                initialText: textContent,
                title: 'Motility / Areal Deviation Ratios',
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildResultImageCard(String imageUrl) {
    Widget displayWidget;

    if (imageUrl.contains('mock:preliminary')) {
      displayWidget = CustomPaint(
        painter: PreliminaryResultPainter(),
        child: Container(),
      );
    } else if (imageUrl.contains('mock:hirschberg')) {
      displayWidget = CustomPaint(
        painter: HirschbergResultPainter(),
        child: Container(),
      );
    } else if (imageUrl.contains('mock:nine_gaze')) {
      displayWidget = CustomPaint(
        painter: NineGazeResultPainter(),
        child: Container(),
      );
    } else {
      displayWidget = Image.network(
        imageUrl,
        fit: BoxFit.contain,
        loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
          return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
        },
        errorBuilder: (context, error, stackTrace) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.broken_image, size: 40, color: AppTheme.accent),
                SizedBox(height: 8),
                Text('Failed to load result image', style: TextStyle(color: AppTheme.textSecondary)),
              ],
            ),
          );
        },
      );
    }

    return GlassCard(
      padding: EdgeInsets.zero,
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: Container(
          color: Colors.black45,
          child: displayWidget,
        ),
      ),
    );
  }

  Widget _buildNoResultsView(String message) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.assignment_late_rounded, size: 48, color: AppTheme.secondary),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}

// Stateful Widget representing an Editable Diagnostic Log Card
class EditableDiagnosticLogCard extends StatefulWidget {
  final String testType;
  final String initialText;
  final String title;

  const EditableDiagnosticLogCard({
    Key? key,
    required this.testType,
    required this.initialText,
    required this.title,
  }) : super(key: key);

  @override
  State<EditableDiagnosticLogCard> createState() => _EditableDiagnosticLogCardState();
}

class _EditableDiagnosticLogCardState extends State<EditableDiagnosticLogCard> {
  late TextEditingController _controller;
  bool _isEditing = false;
  bool _isSaving = false;
  late String _currentText;

  @override
  void initState() {
    super.initState();
    _currentText = widget.initialText;
    _controller = TextEditingController(text: _currentText);
  }

  @override
  void didUpdateWidget(EditableDiagnosticLogCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialText != widget.initialText) {
      setState(() {
        _currentText = widget.initialText;
        _controller.text = _currentText;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _saveChanges() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    setState(() {
      _isSaving = true;
    });

    final result = await apiService.editResults(
      testType: widget.testType,
      content: _controller.text,
    );

    if (mounted) {
      setState(() {
        _isSaving = false;
      });

      if (result['status'] == 'success') {
        setState(() {
          _currentText = _controller.text;
          _isEditing = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Results updated successfully.'),
            backgroundColor: AppTheme.primary,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update results: ${result['message'] ?? 'Unknown error'}'),
            backgroundColor: AppTheme.accent,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.analytics_rounded, color: AppTheme.primary, size: 20),
                  const SizedBox(width: 8),
                  Text(widget.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ],
              ),
              if (_isSaving)
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary),
                )
              else if (_isEditing)
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.check_rounded, color: AppTheme.primary, size: 20),
                      onPressed: _saveChanges,
                      tooltip: 'Save',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 12),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, color: AppTheme.accent, size: 20),
                      onPressed: () {
                        setState(() {
                          _controller.text = _currentText;
                          _isEditing = false;
                        });
                      },
                      tooltip: 'Cancel',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                )
              else
                IconButton(
                  icon: const Icon(Icons.edit_rounded, color: AppTheme.textSecondary, size: 18),
                  onPressed: () {
                    setState(() {
                      _isEditing = true;
                    });
                  },
                  tooltip: 'Edit Results',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.black45,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white10),
            ),
            child: _isEditing
                ? TextField(
                    controller: _controller,
                    maxLines: null,
                    keyboardType: TextInputType.multiline,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: Colors.lightGreenAccent,
                      height: 1.4,
                    ),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      isDense: true,
                      contentPadding: EdgeInsets.zero,
                    ),
                  )
                : Text(
                    _currentText,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: Colors.lightGreenAccent,
                      height: 1.4,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class PreliminaryResultPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final centerLeft = Offset(size.width * 0.35, size.height * 0.5);
    final centerRight = Offset(size.width * 0.65, size.height * 0.5);
    final eyeRadius = 32.0;
    final pupilRadius = 12.0;

    final eyePaint = Paint()
      ..color = Colors.white24
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    final detectPaint = Paint()
      ..color = Colors.greenAccent.withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    // Draw eye contours
    canvas.drawOval(Rect.fromCenter(center: centerLeft, width: eyeRadius * 2.2, height: eyeRadius * 1.4), eyePaint);
    canvas.drawOval(Rect.fromCenter(center: centerRight, width: eyeRadius * 2.2, height: eyeRadius * 1.4), eyePaint);

    // Draw detected pupil boundaries
    canvas.drawCircle(centerLeft, pupilRadius, detectPaint);
    canvas.drawCircle(centerRight, pupilRadius, detectPaint);

    // Draw center crosshairs
    final crossSize = 6.0;
    final crossPaint = Paint()..color = Colors.greenAccent..strokeWidth = 2;
    for (var center in [centerLeft, centerRight]) {
      canvas.drawLine(Offset(center.dx - crossSize, center.dy), Offset(center.dx + crossSize, center.dy), crossPaint);
      canvas.drawLine(Offset(center.dx, center.dy - crossSize), Offset(center.dx, center.dy + crossSize), crossPaint);
    }

    // IPD Measurement line
    final ipdPaint = Paint()..color = AppTheme.primary..strokeWidth = 2;
    canvas.drawLine(centerLeft, centerRight, ipdPaint);
    canvas.drawLine(Offset(centerLeft.dx, centerLeft.dy - 6), Offset(centerLeft.dx, centerLeft.dy + 6), ipdPaint);
    canvas.drawLine(Offset(centerRight.dx, centerRight.dy - 6), Offset(centerRight.dx, centerRight.dy + 6), ipdPaint);

    // Text label for IPD
    final textPainter = TextPainter(
      text: const TextSpan(
        text: 'IPD: 63.4 mm',
        style: TextStyle(
          color: AppTheme.primary,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          fontFamily: 'monospace',
          backgroundColor: Colors.black87,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset((size.width - textPainter.width) / 2, size.height * 0.5 - 20),
    );

    // Title / overlay details
    final titlePainter = TextPainter(
      text: const TextSpan(
        text: 'PRELIMINARY OCULAR METRICS (MOCK)',
        style: TextStyle(
          color: Colors.white38,
          fontSize: 9,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.0,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    titlePainter.paint(canvas, Offset(16, 16));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class HirschbergResultPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final centerLeft = Offset(size.width * 0.35, size.height * 0.5);
    final centerRight = Offset(size.width * 0.65, size.height * 0.5);
    final eyeRadius = 38.0;
    final pupilRadius = 14.0;

    final eyePaint = Paint()
      ..color = Colors.white12
      ..style = PaintingStyle.fill;
    
    final borderPaint = Paint()
      ..color = Colors.white30
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    // Draw eye structures
    for (var center in [centerLeft, centerRight]) {
      canvas.drawCircle(center, eyeRadius, eyePaint);
      canvas.drawCircle(center, eyeRadius, borderPaint);
      canvas.drawCircle(center, pupilRadius, Paint()..color = Colors.black87);
    }

    // Corneal reflex points (slightly offset)
    final reflexLeft = Offset(centerLeft.dx + 1.2, centerLeft.dy - 0.8);
    final reflexRight = Offset(centerRight.dx + 1.1, centerRight.dy - 0.9);

    // Highlight pupil centers
    final crossPaint = Paint()..color = Colors.blueAccent..strokeWidth = 1.5;
    const crossSize = 5.0;
    for (var center in [centerLeft, centerRight]) {
      canvas.drawLine(Offset(center.dx - crossSize, center.dy), Offset(center.dx + crossSize, center.dy), crossPaint);
      canvas.drawLine(Offset(center.dx, center.dy - crossSize), Offset(center.dx, center.dy + crossSize), crossPaint);
    }

    // Draw reflex dots
    final reflexDotPaint = Paint()..color = Colors.yellowAccent..style = PaintingStyle.fill;
    canvas.drawCircle(reflexLeft, 2.5, reflexDotPaint);
    canvas.drawCircle(reflexRight, 2.5, reflexDotPaint);

    // Draw alignment lines to reflex
    final alignPaint = Paint()..color = Colors.yellowAccent.withOpacity(0.5)..strokeWidth = 1;
    canvas.drawLine(centerLeft, reflexLeft, alignPaint);
    canvas.drawLine(centerRight, reflexRight, alignPaint);

    // Text deviation labels
    final textPainterL = TextPainter(
      text: const TextSpan(
        text: 'L: dX=+2.1°\ndY=-1.4°',
        style: TextStyle(color: Colors.greenAccent, fontSize: 9, fontFamily: 'monospace'),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainterL.paint(canvas, Offset(centerLeft.dx - 25, centerLeft.dy + eyeRadius + 8));

    final textPainterR = TextPainter(
      text: const TextSpan(
        text: 'R: dX=+1.9°\ndY=-1.6°',
        style: TextStyle(color: Colors.greenAccent, fontSize: 9, fontFamily: 'monospace'),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainterR.paint(canvas, Offset(centerRight.dx - 25, centerRight.dy + eyeRadius + 8));

    // Title
    final titlePainter = TextPainter(
      text: const TextSpan(
        text: 'CORNEAL LIGHT REFLEX ALIGNMENT (MOCK)',
        style: TextStyle(
          color: Colors.white38,
          fontSize: 9,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.0,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    titlePainter.paint(canvas, Offset(16, 16));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class NineGazeResultPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final cellWidth = size.width / 3;
    final cellHeight = size.height / 3;

    final gridPaint = Paint()
      ..color = Colors.white.withOpacity(0.05)
      ..strokeWidth = 1.0;

    for (int i = 1; i < 3; i++) {
      canvas.drawLine(Offset(cellWidth * i, 0), Offset(cellWidth * i, size.height), gridPaint);
      canvas.drawLine(Offset(0, cellHeight * i), Offset(size.width, cellHeight * i), gridPaint);
    }

    void drawEyePair(Canvas canvas, Offset center, Offset gazeOffset) {
      final pupilLeft = Offset(center.dx - 18 + gazeOffset.dx, center.dy + gazeOffset.dy);
      final pupilRight = Offset(center.dx + 18 + gazeOffset.dx, center.dy + gazeOffset.dy);

      final eyePaint = Paint()
        ..color = Colors.white24
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;

      canvas.drawOval(Rect.fromCenter(center: Offset(center.dx - 18, center.dy), width: 22, height: 13), eyePaint);
      canvas.drawOval(Rect.fromCenter(center: Offset(center.dx + 18, center.dy), width: 22, height: 13), eyePaint);

      final pupilPaint = Paint()..color = Colors.black87;
      canvas.drawCircle(pupilLeft, 4.0, pupilPaint);
      canvas.drawCircle(pupilRight, 4.0, pupilPaint);
      
      canvas.drawCircle(pupilLeft, 1.0, Paint()..color = Colors.yellowAccent);
      canvas.drawCircle(pupilRight, 1.0, Paint()..color = Colors.yellowAccent);
    }

    final gazeDirections = <int, Offset>{
      0: const Offset(-5, -3),
      1: const Offset(0, -5),
      2: const Offset(5, -3),
      3: const Offset(-6, 0),
      4: const Offset(0, 0),
      5: const Offset(6, 0),
      6: const Offset(-5, 3),
      7: const Offset(0, 5),
      8: const Offset(5, 3),
    };

    final gazeLabels = <int, String>{
      0: 'UP-LEFT', 1: 'UP', 2: 'UP-RIGHT',
      3: 'LEFT', 4: 'CENTER', 5: 'RIGHT',
      6: 'DOWN-LEFT', 7: 'DOWN', 8: 'DOWN-RIGHT',
    };

    for (int r = 0; r < 3; r++) {
      for (int c = 0; c < 3; c++) {
        final index = r * 3 + c;
        final cellCenter = Offset(cellWidth * (c + 0.5), cellHeight * (r + 0.5));
        final offset = gazeDirections[index]!;
        drawEyePair(canvas, cellCenter, offset);

        final labelPainter = TextPainter(
          text: TextSpan(
            text: gazeLabels[index]!,
            style: const TextStyle(color: Colors.white24, fontSize: 7, fontWeight: FontWeight.bold),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        labelPainter.paint(canvas, Offset(cellWidth * c + 6, cellHeight * r + 6));
      }
    }

    final titlePainter = TextPainter(
      text: const TextSpan(
        text: '9-GAZE ASSESSMENT MOTILITY GRID (MOCK)',
        style: TextStyle(
          color: Colors.white38,
          fontSize: 9,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.0,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    titlePainter.paint(canvas, Offset(16, 16));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
