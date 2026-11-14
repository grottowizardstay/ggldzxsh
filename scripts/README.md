# Isolated Chrome launcher

Requires Python 3.10+ and Google Chrome. No extra Python packages are needed.

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
username/email. The password is not included: GitHub submits passwords through its
login form, not a login URL. Enter the password manually. Recovery codes and the
last username/profile field are not used.

The 2FA tab sends the reusable secret to `2fa.fb.tools` in its URL. This gives that
site the ability to generate future codes, and the URL can be visible in local
process listings. Use only a secret you intend to share with that service. Do not
share real credentials in chat.

Each launch uses a separate temporary Chrome data directory, Incognito mode, and
disabled extensions. It does not reuse your normal Chrome cookies, logins, or
profile. This is browser-data isolation, not a new installation, virtual machine,
network identity, or security boundary. OS policies, IP address, device fingerprint,
and downloaded files are not reset. Incognito does not make you anonymous.

Keep the console open until you close all windows from the new Chrome instance.
The script then removes its temporary profile. Forced termination or power loss
can leave the temporary directory behind; cleanup errors show its location.

If Chrome cannot be found, supply its executable path:

```sh
python isolated_chrome.py --chrome "/path/to/chrome"
```

Tests use synthetic data and do not open websites:

```sh
python -m unittest discover -s tests -v
```
