"""Focused dependency and token-verification regression tests for Beyvra backend.

Never enables trading, broker, funding or other provider side effects.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt


REQUIREMENTS = Path(__file__).resolve().parents[2] / "requirements.txt"


class TradingJwtDependencySecurityTests(unittest.TestCase):
    def test_pinned_jwt_and_http_dependencies_are_patched(self) -> None:
        lines = set(REQUIREMENTS.read_text(encoding="utf-8").splitlines())
        self.assertIn("PyJWT[crypto]==2.15.0", lines)
        self.assertIn("urllib3==2.8.0", lines)
        self.assertFalse(any(line == "PyJWT[crypto]==2.13.0" for line in lines))
        self.assertFalse(any(line == "urllib3==2.7.0" for line in lines))

    def test_hmac_signed_token_is_not_accepted_as_rsa_token(self) -> None:
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "sub": "paper-regression-only",
                "iss": "https://idp.example.test/realms/beyvra",
                "aud": "beyvra-backend",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            "isolated-unit-test-secret-not-for-production",
            algorithm="HS256",
        )
        with self.assertRaises(jwt.InvalidAlgorithmError):
            jwt.decode(
                token,
                "isolated-unit-test-secret-not-for-production",
                algorithms=["RS256"],
                issuer="https://idp.example.test/realms/beyvra",
                audience="beyvra-backend",
            )

    def test_missing_security_claims_fail_closed(self) -> None:
        token = jwt.encode(
            {"sub": "paper-regression-only"},
            "isolated-unit-test-secret-not-for-production",
            algorithm="HS256",
        )
        with self.assertRaises(jwt.MissingRequiredClaimError):
            jwt.decode(
                token,
                "isolated-unit-test-secret-not-for-production",
                algorithms=["HS256"],
                issuer="https://idp.example.test/realms/beyvra",
                audience="beyvra-backend",
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )

    def test_wrong_issuer_and_audience_are_rejected(self) -> None:
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "sub": "paper-regression-only",
                "iss": "https://idp.example.test/realms/untrusted",
                "aud": "wrong-client",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            "isolated-unit-test-secret-not-for-production",
            algorithm="HS256",
        )
        with self.assertRaises((jwt.InvalidIssuerError, jwt.InvalidAudienceError)):
            jwt.decode(
                token,
                "isolated-unit-test-secret-not-for-production",
                algorithms=["HS256"],
                issuer="https://idp.example.test/realms/beyvra",
                audience="beyvra-backend",
            )


if __name__ == "__main__":
    unittest.main()
