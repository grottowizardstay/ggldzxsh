# Isolated Chrome launcher

Requires Python 3.10+, Google Chrome, and Playwright. Install the dependency once:

```sh
python -m pip install playwright==1.65.2
```

No separate Playwright browser download is required; the script uses installed Chrome.

Run in a terminal:

```sh
python isolated_chrome.py
```

On Windows, `py isolated_chrome.py` also works. Paste one record at the visible prompt:

```text
login:password:base32-2fa-secret:comma-separated-recovery-codes:username/profile
```

Each field must be nonempty and cannot contain a colon. Input is visible and remains
in your terminal scrollback. The script does not save it to a file.

All three tabs open immediately, without a confirmation prompt. GitHub's login URL
includes the first field as its URL-encoded `login` parameter, prefilling the
username/email. Playwright automatically fills the username and password into the GitHub login
form after checking the HTTPS origin and form destination. The password is never
included in a URL. The script submits sign-in automatically, generates and submits one authenticator
code locally if GitHub asks for it, and opens **Settings → Sessions** after sign-in.
CAPTCHAs, device/email verification, and other challenges require manual completion.
It does not retry failed passwords or 2FA codes, use recovery codes, or revoke sessions.
Keep your computer clock accurate for authenticator codes.

After Sessions opens, the script refreshes the Hoplite login tab in the same
browser context, checks that **Continue with GitHub** is visible and enabled, and
clicks the button automatically to continue with your signed-in GitHub account.
GitHub Sessions stays open in its own tab. OAuth permissions are never approved
automatically. If Hoplite is already signed in, check its redirected page instead.
Recovery codes and the last username/profile field are not used.

The 2FA tab sends the reusable secret to `2fa.fb.tools` in its URL. This gives that
site the ability to generate future codes, and the URL can be visible in local
process listings. Use only a secret you intend to share with that service. Do not
share real credentials in chat.

Each launch uses a Playwright-managed temporary Chrome data directory, an isolated
nonpersistent (Incognito) browser context, and disabled extensions. It does not reuse your normal Chrome cookies, logins, or
profile. This is browser-data isolation, not a new installation, virtual machine,
network identity, or security boundary. OS policies, IP address, device fingerprint,
and downloaded files are not reset. Incognito does not make you anonymous.

Keep the console open until you close all windows from the new Chrome instance.
The script then removes its temporary profile. Forced termination or power loss
can leave temporary browser files behind. Normal browser shutdown lets Playwright
clean up its temporary profile.

If Chrome cannot be found, supply its executable path:

```sh
python isolated_chrome.py --chrome "/path/to/chrome"
```

Tests use synthetic data and do not open websites:

```sh
python -m unittest discover -s tests -v
```

Browser smoke check (live-page autofill only; submissions use intercepted test pages):

```sh
python tests/check_browser_autofill.py
```
