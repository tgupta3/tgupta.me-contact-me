import unittest
from contactme import get_secret
from contactme import get_recaptcha_response
challenge = '03ACgFB9ux02R7mIp97mQ-AG_dq2EIrb1YMzBoHHXUuX5VbahXnI2rCLRiIGmXZjLxvmttWmffK8xrNMiCqScymrlZvqA_NizPpbBpA5kYuHHogQU4EIV2PdTK80FxQZLciRYPUuYN41g-XgkxVFZeo9bzT-0j-_QeuG7pwOE80aBRuD8JexmO1RMGZpI6WMntaPwrPSRf8ZSz'

class TestValidation(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_secret(self):
        self.assertTrue(get_secret())


    def test_validate_challenge(self):

        result = (get_recaptcha_response('12'))['error-codes']
        assert "invalid-input-response" in result, 'Actual "{}"'.format(result)
        assert "invalid-input-secret" not in result, 'Actual "{}"'.format(result)
        assert "missing-input-secret" not in result, 'Actual "{}"'.format(result)

if __name__ == '__main__':
    unittest.main()
