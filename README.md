# ACaptcha

A photo slider CAPTCHA: the user drags a scope across a photo until it locks onto the mark.
The answer is generated and checked on the server; the browser never receives it.

```bash
npm install
npm start        # demo at http://localhost:3000
npm test
```

## Using it

Page:

```html
<link rel="stylesheet" href="acaptcha.css">
<form>
  <div data-acaptcha></div>   <!-- adds a hidden "acaptcha-token" input to the form -->
</form>
<script src="acaptcha.js"></script>
```

The element fires `acaptcha:success` (with `detail.token`) and `acaptcha:reset`.
For manual control use `ACaptcha.mount(el, { endpoint, lang, onSuccess, onReset })`.
The interface is available in Russian and English (`lang`, else the page language, else the browser's).

Server:

```js
const { createACaptcha } = require('./lib/acaptcha');
const captcha = createACaptcha({ secret: process.env.ACAPTCHA_SECRET });

await captcha.issue();              // POST /api/acaptcha/challenge
captcha.solve({ id, x, trail });    // POST /api/acaptcha/solve  -> { ok, token }
captcha.verify(token);              // in your own handler, before the protected action
```

`server.js` wires these up with a per-IP rate limit and a demo form.

## How it protects

- Each challenge takes a random crop of a random photo with colour jitter, so it can't be solved by comparing against the source image.
- A challenge is single-use and expires after 2 minutes; a wrong answer burns it.
- Answers that arrive instantly or move at a perfectly constant speed are rejected.
- Tokens are HMAC-signed, valid for 5 minutes and accepted once.

Challenges and used tokens are kept in memory, so run a single process or swap in a shared store.
Like any slider CAPTCHA, it raises the cost of automation rather than stopping a determined, targeted bot.

## Photos

Put your own images (16:9, at least 960×540) into `photos/`. The bundled ones are from [Unsplash](https://unsplash.com/license).
The font is Montserrat (SIL Open Font License).
