import 'package:echo_mobile/env/env.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Env.init() defaults are safe', () {
    Env.init();
    expect(Env.useWebAuth, isFalse);
    expect(Env.useAuthCustomToken, isFalse);
  });
}
