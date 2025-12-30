import 'package:flutter/material.dart';
import 'package:echo_mobile/pages/settings/device_settings.dart';
import 'package:echo_mobile/pages/home/page.dart';
import 'package:echo_mobile/pages/onboarding/find_device/page.dart';
import 'package:echo_mobile/utils/other/temp.dart';
import 'package:echo_mobile/widgets/device_widget.dart';
import 'package:echo_mobile/providers/onboarding_provider.dart';
import 'package:provider/provider.dart';

class ConnectDevicePage extends StatefulWidget {
  const ConnectDevicePage({super.key});

  @override
  State<ConnectDevicePage> createState() => _ConnectDevicePageState();
}

class _ConnectDevicePageState extends State<ConnectDevicePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(
          title: const Text('Connect'),
          backgroundColor: Theme.of(context).colorScheme.primary,
          actions: [
            IconButton(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) => const DeviceSettings(),
                  ),
                );
              },
              icon: const Icon(Icons.settings),
            )
          ],
        ),
        backgroundColor: Theme.of(context).colorScheme.primary,
        body: ListView(
          children: [
            Consumer<OnboardingProvider>(
              builder: (context, onboardingProvider, child) {
                return DeviceAnimationWidget(
                  isConnected: onboardingProvider.isConnected,
                  deviceName: onboardingProvider.deviceName,
                  deviceType: onboardingProvider.deviceType,
                  animatedBackground: onboardingProvider.isConnected,
                );
              },
            ),
            FindDevicesPage(
              isFromOnboarding: false,
              goNext: () {
                debugPrint('onConnected from FindDevicesPage');
                routeToPage(context, const HomePageWrapper(), replace: true);
              },
              includeSkip: false,
            )
          ],
        ));
  }
}
