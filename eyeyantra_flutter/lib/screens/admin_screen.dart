import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../theme.dart';
import '../widgets/glass_card.dart';
import 'dashboard_screen.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({Key? key}) : super(key: key);

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _configFormKey = GlobalKey<FormState>();

  final _clinicController = TextEditingController();
  final _doctorController = TextEditingController();
  final _doctorTitleController = TextEditingController();
  final _techController = TextEditingController();
  final _techTitleController = TextEditingController();
  final _deviceController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _nextPatientIdController = TextEditingController();

  List<dynamic> _patients = [];
  bool _loadingPatients = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadConfig();
    _loadPatients();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _clinicController.dispose();
    _doctorController.dispose();
    _doctorTitleController.dispose();
    _techController.dispose();
    _techTitleController.dispose();
    _deviceController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _nextPatientIdController.dispose();
    super.dispose();
  }

  void _loadConfig() async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final config = await apiService.getAdminConfig();
    
    if (config.isNotEmpty && config['status'] != 'error') {
      setState(() {
        _clinicController.text = config['clinic_name'] ?? '';
        _doctorController.text = config['doctor_name'] ?? '';
        _doctorTitleController.text = config['doctor_title'] ?? '';
        _techController.text = config['tech_name'] ?? '';
        _techTitleController.text = config['tech_title'] ?? '';
        _deviceController.text = config['device_name'] ?? '';
        _emailController.text = config['contact_email'] ?? '';
        _phoneController.text = config['contact_phone'] ?? '';
        _nextPatientIdController.text = config['next_patient_id'] ?? '1001';
      });
    }
  }

  void _loadPatients() async {
    setState(() => _loadingPatients = true);
    final apiService = Provider.of<ApiService>(context, listen: false);
    final list = await apiService.getPatientsList();
    setState(() {
      _patients = list;
      _loadingPatients = false;
    });
  }

  void _saveConfig() async {
    if (!_configFormKey.currentState!.validate()) return;
    
    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.saveAdminConfig({
      'clinic_name': _clinicController.text.trim(),
      'doctor_name': _doctorController.text.trim(),
      'doctor_title': _doctorTitleController.text.trim(),
      'tech_name': _techController.text.trim(),
      'tech_title': _techTitleController.text.trim(),
      'device_name': _deviceController.text.trim(),
      'contact_email': _emailController.text.trim(),
      'contact_phone': _phoneController.text.trim(),
      'next_patient_id': _nextPatientIdController.text.trim(),
    });

    if (result['status'] == 'success') {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Configuration saved successfully!'), backgroundColor: AppTheme.primary),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['message'] ?? 'Failed to save config.'), backgroundColor: AppTheme.accent),
      );
    }
  }

  void _loadPatientSession(Map<String, dynamic> patient) async {
    final apiService = Provider.of<ApiService>(context, listen: false);
    final result = await apiService.selectPatient(
      name: patient['name'],
      id: patient['id'],
      dob: patient['dob'],
    );

    if (result['status'] == 'success') {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Loaded session for ${patient['name']}!'), backgroundColor: AppTheme.primary),
      );
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
        (route) => false,
      );
    }
  }

  void _showEditPatientDialog(Map<String, dynamic> patient) {
    final editNameController = TextEditingController(text: patient['name']);
    final editIdController = TextEditingController(text: patient['id']);
    final editDobController = TextEditingController(text: patient['dob']);
    final editFormKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Edit Patient Record'),
        content: SingleChildScrollView(
          child: Form(
            key: editFormKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: editNameController,
                  decoration: const InputDecoration(labelText: 'Name'),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Name required' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: editIdController,
                  decoration: const InputDecoration(labelText: 'Patient ID'),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'ID required' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: editDobController,
                  decoration: const InputDecoration(labelText: 'Date of Birth'),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'DOB required' : null,
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(
            onPressed: () async {
              if (!editFormKey.currentState!.validate()) return;
              Navigator.pop(ctx);

              final apiService = Provider.of<ApiService>(context, listen: false);
              final result = await apiService.editPatient(
                oldRawUsername: patient['raw_username'],
                newName: editNameController.text.trim(),
                newId: editIdController.text.trim(),
                newDob: editDobController.text.trim(),
              );

              if (result['status'] == 'success') {
                _loadPatients();
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Patient records updated successfully!'), backgroundColor: AppTheme.primary),
                );
              } else {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(result['message'] ?? 'Failed to edit records.'), backgroundColor: AppTheme.accent),
                );
              }
            },
            child: const Text('Save Changes', style: TextStyle(color: AppTheme.primary)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final apiService = Provider.of<ApiService>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('System Administration'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textSecondary,
          tabs: const [
            Tab(text: 'Clinic Settings', icon: Icon(Icons.settings_rounded)),
            Tab(text: 'Patient Sessions', icon: Icon(Icons.history_rounded)),
          ],
        ),
      ),
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: AppTheme.backgroundGradient,
            ),
          ),
          SafeArea(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildClinicSettingsTab(apiService),
                _buildPatientRecordsTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildClinicSettingsTab(ApiService apiService) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _configFormKey,
        child: GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Report Header Details',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _clinicController,
                decoration: const InputDecoration(labelText: 'Clinic / Hospital Name'),
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _doctorController,
                      decoration: const InputDecoration(labelText: 'Ophthalmologist Name'),
                      validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _doctorTitleController,
                      decoration: const InputDecoration(labelText: 'Title / Role'),
                      validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _techController,
                      decoration: const InputDecoration(labelText: 'Technician Name'),
                      validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _techTitleController,
                      decoration: const InputDecoration(labelText: 'Title / Role'),
                      validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _deviceController,
                decoration: const InputDecoration(labelText: 'Device Descriptor'),
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(labelText: 'Contact Email'),
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(labelText: 'Contact Phone'),
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _nextPatientIdController,
                decoration: const InputDecoration(
                  labelText: 'Next Auto-Generated Patient ID',
                  helperText: 'Starting sequence for next new session',
                ),
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Required';
                  if (int.tryParse(v) == null) return 'Must be a valid integer';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: apiService.isLoading ? null : _saveConfig,
                child: apiService.isLoading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('SAVE CLINICAL METADATA'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPatientRecordsTab() {
    if (_loadingPatients) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    }

    if (_patients.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.people_alt_rounded, size: 48, color: AppTheme.textSecondary),
            const SizedBox(height: 16),
            const Text('No clinical patient records found.', style: TextStyle(color: AppTheme.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadPatients, child: const Text('REFRESH LIST')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => _loadPatients(),
      color: AppTheme.primary,
      child: ListView.builder(
        padding: const EdgeInsets.all(24),
        itemCount: _patients.length,
        itemBuilder: (context, index) {
          final patient = _patients[index];
          return Card(
            color: Colors.white.withOpacity(0.04),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.white.withOpacity(0.08)),
            ),
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: AppTheme.primary.withOpacity(0.15),
                    child: const Icon(Icons.person, color: AppTheme.primary),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          patient['name'],
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'ID: ${patient['id']}  •  DOB: ${patient['dob']}',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Exam Date: ${patient['date']}',
                          style: TextStyle(color: AppTheme.textSecondary.withOpacity(0.8), fontSize: 10),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    children: [
                      ElevatedButton(
                        onPressed: () => _loadPatientSession(patient),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: const Text('Load', style: TextStyle(fontSize: 12)),
                      ),
                      const SizedBox(height: 6),
                      OutlinedButton(
                        onPressed: () => _showEditPatientDialog(patient),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          minimumSize: Size.zero,
                          side: BorderSide(color: Colors.white.withOpacity(0.2)),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: const Text('Edit', style: TextStyle(fontSize: 12, color: Colors.white70)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
