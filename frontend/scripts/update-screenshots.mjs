import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

const appUrl = process.env.VENDI_APP_URL ?? "http://localhost:5173";
const apiUrl = process.env.VENDI_API_URL ?? "http://127.0.0.1:8000";
const email = process.env.VENDI_SCREENSHOT_EMAIL;
const password = process.env.VENDI_SCREENSHOT_PASSWORD;
const edge = process.env.EDGE_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const output = path.resolve(process.env.VENDI_SCREENSHOT_OUTPUT ?? "../docs/screenshots");
const profile = path.resolve(".screenshot-profile", `run-${Date.now()}`);
const port = 9333;

if (!email || !password) throw new Error("Informe VENDI_SCREENSHOT_EMAIL e VENDI_SCREENSHOT_PASSWORD.");

const loginResponse = await fetch(`${apiUrl}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
if (!loginResponse.ok) throw new Error("Não foi possível autenticar a conta usada nas capturas.");
const { access_token: token } = await loginResponse.json();
const meResponse = await fetch(`${apiUrl}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
const user = await meResponse.json();
const productsResponse = await fetch(`${apiUrl}/products`, { headers: { Authorization: `Bearer ${token}` } });
const products = await productsResponse.json();
const product = products.find(item => item.active && item.stock_quantity > 0);

await mkdir(output, { recursive: true });
await mkdir(profile, { recursive: true });
const browser = spawn(edge, ["--headless=new", "--disable-background-mode", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--window-size=1600,1000", "--hide-scrollbars", `${appUrl}/login`], { stdio: "ignore" });
const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

let target;
for (let attempt = 0; attempt < 30; attempt += 1) {
  try {
    const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
    target = targets.find(item => item.type === "page" && item.url.startsWith(appUrl));
    if (target) break;
  } catch {}
  await sleep(250);
}
if (!target) throw new Error("O navegador de captura não iniciou.");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let sequence = 0;
const pending = new Map();
socket.onmessage = event => {
  const message = JSON.parse(event.data);
  if (!message.id || !pending.has(message.id)) return;
  const { resolve, reject } = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(message.error.message)); else resolve(message.result);
};
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

await send("Page.enable");
await send("Runtime.enable");
await send("Runtime.evaluate", { expression: `localStorage.setItem("vendifacil:token", ${JSON.stringify(token)}); localStorage.setItem("vendifacil:offline-user", ${JSON.stringify(JSON.stringify(user))});` });
await send("Page.reload", { ignoreCache: true });
await sleep(1500);
const authenticated = await send("Runtime.evaluate", { expression: "location.pathname !== '/login'", returnByValue: true });
if (!authenticated.result.value) {
  await send("Runtime.evaluate", { expression: "document.querySelector('form').requestSubmit()" });
  await sleep(2200);
}
const authenticationCheck = await send("Runtime.evaluate", { expression: "location.pathname", returnByValue: true });
if (authenticationCheck.result.value === "/login") throw new Error("A interface não concluiu o login para as capturas.");

async function navigate(route) {
  await send("Page.navigate", { url: `${appUrl}${route}` });
  await sleep(1800);
}
async function capture(name) {
  const page = await send("Runtime.evaluate", { expression: "({ url: location.href, heading: document.querySelector('h1')?.textContent })", returnByValue: true });
  console.log(`Capturando ${page.result.value.url}: ${page.result.value.heading ?? "sem título"}`);
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false, fromSurface: true });
  await writeFile(path.join(output, name), Buffer.from(result.data, "base64"));
  console.log(`Atualizado: ${name}`);
}

for (const [route, name] of [["/", "dashboard.png"], ["/products", "products.png"], ["/inventory", "inventory.png"], ["/cashier", "cashier.png"], ["/sales", "sales.png"]]) {
  await navigate(route);
  await capture(name);
}

await navigate("/cashier");
if (product) {
  await send("Runtime.evaluate", { expression: `(() => { const input = document.querySelector('input[placeholder="Código de barras, nome ou SKU"]'); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set; setter.call(input, ${JSON.stringify(product.sku)}); input.dispatchEvent(new Event("input", { bubbles: true })); })()` });
  await sleep(300);
  await send("Runtime.evaluate", { expression: `document.querySelector('input[placeholder="Código de barras, nome ou SKU"]').dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }))` });
  await sleep(1200);
  await send("Runtime.evaluate", { expression: `Array.from(document.querySelectorAll("button")).find(button => button.textContent.includes("FINALIZAR VENDA"))?.click()` });
  await sleep(600);
}
await capture("checkout-modal.png");
await send("Browser.close");
socket.close();
await Promise.race([new Promise(resolve => browser.once("exit", resolve)), sleep(5000)]);
await rm(profile, { recursive: true, force: true });
