import 'package:flutter/material.dart';
import 'package:echo_mobile/config/app_config.dart';

/// Settings screen placeholder.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        centerTitle: true,
      ),
      body: ListView(
        children: [
          const _SectionHeader('Connection'),
          ListTile(
            leading: const Icon(Icons.cloud),
            title: const Text('Backend URL'),
            subtitle: const Text(AppConfig.backendUrl),
          ),
          const Divider(),
          const _SectionHeader('About'),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('App Version'),
            subtitle: const Text(AppConfig.appVersion),
          ),
          ListTile(
            leading: const Icon(Icons.code),
            title: const Text('Phase'),
            subtitle: const Text('Phase 0 - Foundation'),
          ),
          const Divider(),
          const _SectionHeader('Coming Soon'),
          const ListTile(
            leading: Icon(Icons.mic),
            title: Text('Voice Settings'),
            subtitle: Text('Phase 1'),
            enabled: false,
          ),
          const ListTile(
            leading: Icon(Icons.bluetooth),
            title: Text('Device Connection'),
            subtitle: Text('Phase 3'),
            enabled: false,
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }
}
