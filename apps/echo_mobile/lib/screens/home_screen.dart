import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:echo_mobile/services/api_service.dart';

/// Home screen with session start button.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isConnected = false;
  bool _isChecking = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    setState(() {
      _isChecking = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      await api.healthCheck();
      setState(() {
        _isConnected = true;
      });
    } catch (e) {
      setState(() {
        _isConnected = false;
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isChecking = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Echo'),
        centerTitle: true,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.mic,
                size: 80,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                'Echo',
                style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                'Your AI companion that listens and acts',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              FilledButton.icon(
                onPressed: () {
                  // TODO: Implement session mode in Phase 1
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Session mode coming in Phase 1'),
                    ),
                  );
                },
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start Session'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 32,
                    vertical: 16,
                  ),
                ),
              ),
              const SizedBox(height: 48),
              _buildConnectionStatus(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildConnectionStatus() {
    if (_isChecking) {
      return const Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: 8),
          Text('Checking backend...'),
        ],
      );
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          _isConnected ? Icons.check_circle : Icons.error,
          size: 16,
          color: _isConnected ? Colors.green : Colors.red,
        ),
        const SizedBox(width: 8),
        Text(
          _isConnected ? 'Backend connected' : 'Backend offline',
          style: TextStyle(
            color: _isConnected ? Colors.green : Colors.red,
          ),
        ),
        if (!_isConnected) ...[
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.refresh, size: 16),
            onPressed: _checkConnection,
            tooltip: 'Retry connection',
          ),
        ],
      ],
    );
  }
}
