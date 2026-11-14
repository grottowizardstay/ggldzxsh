# Isolated Chrome launcher

Requires Python 3.10+ and Google Chrome. No extra Python packages are needed.

Run in a terminal:

```sh
python isolated_chrome.py
```

On Windows, `py isolated_chrome.py` also works. Paste one record at the hidden prompt:

```text
login:password:base32-2fa-secret:comma-separated-recovery-codes:username/profile
```

Each field must be nonempty and cannot contain a colon. The password, recovery codes,
and username are not used for login, printed, or saved by the script. The script
opens GitHub and Hoplite for manual login. Type `SEND` at the confirmation prompt
to additionally open the 2FA website with the supplied secret in its URL. Otherwise,
only the two login tabs open. This discloses the reusable secret to that website;
the URL can also be visible in local process listings. Prefer a trusted local
authenticator when possible. Do not share real credentials in chat.

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
