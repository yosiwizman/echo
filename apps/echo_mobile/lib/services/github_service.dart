import 'package:echo_mobile/services/base_integration_service.dart';

class GitHubService extends BaseIntegrationService {
  static const String _appKey = 'github';
  static const String _prefKey = 'github_connected';

  GitHubService() : super(appKey: _appKey, prefKey: _prefKey);
}
