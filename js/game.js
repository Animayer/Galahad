const FRAME_DIR = "assets/roman_legionary/frames_96";
const ANIM_URL = "assets/roman_legionary/animations.json";

const WIN_SECONDS = 45;
const WIN_KILLS = 15;
const PLAYER_HP = 5;
const PLAYER_SPEED = 156;
const SPRITE_SCALE = 2;
const ATTACK_REACH = 70;
const ATTACK_HALF_WIDTH = 32;
const PLAYER_RADIUS = 16;
const HURT_IFRAMES_MS = 900;
const HIT_FRAME_START = 1;
const HIT_FRAME_END = 2;

const COPY = {
  titleKicker: "Night watch",
  title: "The line is yours.",
  body: "Forty-five seconds. Fifteen raiders. Crest high. Eyes forward.",
  hold: "Hold",
  again: "Stand up",
  winTime: "The line held.",
  winKills: "Fifteen down. The line held.",
  lose: "The line broke.",
};

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const overlay = document.getElementById("overlay");
const overlayKicker = document.getElementById("overlay-kicker");
const overlayTitle = document.getElementById("overlay-title");
const overlayBody = document.getElementById("overlay-body");
const overlayScore = document.getElementById("overlay-score");
const startBtn = document.getElementById("start-btn");
const hud = document.getElementById("hud");
const hudTime = document.getElementById("hud-time");
const hudHp = document.getElementById("hud-hp");
const hudKills = document.getElementById("hud-kills");
const pad = document.getElementById("pad");
const atkBtn = document.getElementById("atk-btn");

const keys = new Set();
const padDirs = new Set();

const images = new Map();
let spec = null;
let state = "title";
let lastTs = 0;
let player;
let enemies;
let dust;
let hitsparks;
let timeLeft;
let kills;
let spawnAcc;
let spawnEvery;
let endedReason = "";
let titleIdle = null;

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v));
}

function len(x, y) {
  return Math.hypot(x, y);
}

function norm(x, y) {
  const d = len(x, y) || 1;
  return { x: x / d, y: y / d };
}

async function loadJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url}`);
  return res.json();
}

function loadImage(name) {
  if (images.has(name)) return images.get(name);
  const img = new Image();
  const done = new Promise((resolve, reject) => {
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Missing frame ${name}`));
  });
  img.src = `${FRAME_DIR}/${name}.png`;
  images.set(name, img);
  return done;
}

async function loadPack() {
  spec = await loadJson(ANIM_URL);
  const names = new Set();
  for (const anim of Object.values(spec.animations)) {
    for (const frame of anim.frames) names.add(frame);
  }
  names.add("attack_back");
  names.add("projectile_spear");
  for (const fx of spec.fx || []) names.add(fx);
  await Promise.all([...names].map((name) => loadImage(name)));
}

function animOf(name) {
  return spec.animations[name];
}

function playAnim(actor, name, restart = false) {
  if (!restart && actor.anim === name) return;
  actor.anim = name;
  actor.animTime = 0;
  actor.frame = 0;
  actor.animDone = false;
}

function stepAnim(actor, dt) {
  const anim = animOf(actor.anim);
  actor.animTime += dt;
  const i = Math.floor(actor.animTime / anim.frameDurationMs);
  if (anim.loop) {
    actor.frame = i % anim.frames.length;
    actor.animDone = false;
  } else if (i >= anim.frames.length) {
    actor.frame = anim.frames.length - 1;
    actor.animDone = true;
  } else {
    actor.frame = i;
  }
}

function currentFrameName(actor) {
  return animOf(actor.anim).frames[actor.frame];
}

function drawSprite(name, x, y, scale = SPRITE_SCALE, alpha = 1) {
  const img = images.get(name);
  if (!img || !img.complete) return;
  const dw = img.naturalWidth * scale;
  const dh = img.naturalHeight * scale;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(img, x - dw / 2, y - dh, dw, dh);
  ctx.restore();
}

function facingFromMove(mx, my, fallback) {
  if (mx === 0 && my === 0) return fallback;
  if (Math.abs(mx) > Math.abs(my)) return mx < 0 ? "left" : "right";
  return my < 0 ? "back" : "front";
}

function facingVector(facing) {
  if (facing === "left") return { x: -1, y: 0 };
  if (facing === "right") return { x: 1, y: 0 };
  if (facing === "back") return { x: 0, y: -1 };
  return { x: 0, y: 1 };
}

function resetRun() {
  player = {
    x: canvas.width / 2,
    y: canvas.height * 0.62,
    facing: "front",
    hp: PLAYER_HP,
    hurtCd: 0,
    attacking: false,
    attackHits: new Set(),
    dead: false,
    anim: "idle_front",
    animTime: 0,
    frame: 0,
    animDone: false,
  };
  enemies = [];
  dust = [];
  hitsparks = [];
  timeLeft = WIN_SECONDS;
  kills = 0;
  spawnAcc = 0;
  spawnEvery = 1600;
  endedReason = "";
}

function arenaBounds() {
  return { x0: 56, y0: 150, x1: canvas.width - 56, y1: canvas.height - 28 };
}

function spawnEnemy() {
  const b = arenaBounds();
  const edge = Math.floor(Math.random() * 4);
  let x;
  let y;
  if (edge === 0) {
    x = b.x0 + Math.random() * (b.x1 - b.x0);
    y = b.y0;
  } else if (edge === 1) {
    x = b.x0 + Math.random() * (b.x1 - b.x0);
    y = b.y1;
  } else if (edge === 2) {
    x = b.x0;
    y = b.y0 + Math.random() * (b.y1 - b.y0);
  } else {
    x = b.x1;
    y = b.y0 + Math.random() * (b.y1 - b.y0);
  }
  const wave = 1 + Math.floor((WIN_SECONDS - timeLeft) / 10);
  enemies.push({
    x,
    y,
    hp: 1,
    r: 17,
    speed: 38 + wave * 6 + Math.random() * 8,
    hitFlash: 0,
    id: Math.random().toString(36).slice(2),
  });
}

function inputVector() {
  let x = 0;
  let y = 0;
  if (keys.has("arrowleft") || keys.has("a") || padDirs.has("left")) x -= 1;
  if (keys.has("arrowright") || keys.has("d") || padDirs.has("right")) x += 1;
  if (keys.has("arrowup") || keys.has("w") || padDirs.has("up")) y -= 1;
  if (keys.has("arrowdown") || keys.has("s") || padDirs.has("down")) y += 1;
  if (x !== 0 && y !== 0) {
    const d = Math.SQRT1_2;
    x *= d;
    y *= d;
  }
  return { x, y };
}

function tryAttack() {
  if (state !== "play" || player.dead || player.attacking || player.hurtCd > HURT_IFRAMES_MS - 180) {
    return;
  }
  player.attacking = true;
  player.attackHits = new Set();
  if (player.facing === "back") {
    playAnim(player, "attack", true);
    player.useBackAttack = true;
  } else {
    player.useBackAttack = false;
    playAnim(player, "attack", true);
  }
}

function attackHitbox() {
  const v = facingVector(player.facing);
  return {
    x: player.x + v.x * 36,
    y: player.y + v.y * 22 - 10,
    r: ATTACK_HALF_WIDTH,
    reach: ATTACK_REACH,
    vx: v.x,
    vy: v.y,
  };
}

function enemyInStrike(e) {
  const box = attackHitbox();
  const dx = e.x - player.x;
  const dy = e.y - player.y;
  const along = dx * box.vx + dy * box.vy;
  const across = Math.abs(dx * -box.vy + dy * box.vx);
  return along > 8 && along < box.reach + 18 && across < box.r + e.r;
}

function hurtPlayer() {
  if (player.hurtCd > 0 || player.dead) return;
  player.hp -= 1;
  player.hurtCd = HURT_IFRAMES_MS;
  player.attacking = false;
  if (player.hp <= 0) {
    player.dead = true;
    playAnim(player, "death", true);
  } else {
    playAnim(player, "hurt", true);
  }
}

function killEnemy(e) {
  e.hp = 0;
  kills += 1;
  hitsparks.push({ x: e.x, y: e.y - 18, t: 220 });
}

function endRun(reason) {
  if (state !== "play") return;
  state = "end";
  endedReason = reason;
  hud.hidden = true;
  overlay.hidden = false;
  pad.hidden = true;
  const survived = Math.round(WIN_SECONDS - timeLeft);
  const timeBonus = reason === "lose" ? 0 : Math.round(timeLeft) * 10;
  const winBonus = reason === "lose" ? 0 : 500;
  const score = kills * 100 + survived * 5 + timeBonus + winBonus;
  overlayKicker.textContent = reason === "lose" ? "Broken watch" : "Line held";
  overlayTitle.textContent =
    reason === "time" ? COPY.winTime : reason === "kills" ? COPY.winKills : COPY.lose;
  overlayBody.textContent =
    reason === "lose"
      ? "The crest is in the dirt. Get it up."
      : "Oath first. Songs later.";
  overlayScore.hidden = false;
  overlayScore.textContent = `Score ${score} · ${kills} down · ${survived}s held`;
  startBtn.textContent = COPY.again;
}

function updateTitle(dt) {
  if (!titleIdle) {
    titleIdle = { anim: "idle_front", animTime: 0, frame: 0, animDone: false };
  }
  stepAnim(titleIdle, dt);
}

function updatePlay(dt) {
  timeLeft -= dt / 1000;
  if (timeLeft <= 0) {
    timeLeft = 0;
    endRun("time");
    return;
  }
  if (kills >= WIN_KILLS) {
    endRun("kills");
    return;
  }

  player.hurtCd = Math.max(0, player.hurtCd - dt);
  spawnEvery = Math.max(820, 2000 - (WIN_SECONDS - timeLeft) * 18);
  spawnAcc += dt;
  while (spawnAcc >= spawnEvery) {
    spawnAcc -= spawnEvery;
    spawnEnemy();
    if (timeLeft < 18) spawnEnemy();
  }

  if (player.dead) {
    stepAnim(player, dt);
    if (player.animDone && player.anim === "death") playAnim(player, "corpse", true);
    if (player.anim === "corpse" && player.animTime > 700) endRun("lose");
    return;
  }

  if (player.attacking) {
    stepAnim(player, dt);
    const hitting = player.frame >= HIT_FRAME_START && player.frame <= HIT_FRAME_END;
    if (hitting) {
      for (const e of enemies) {
        if (e.hp > 0 && !player.attackHits.has(e.id) && enemyInStrike(e)) {
          player.attackHits.add(e.id);
          killEnemy(e);
        }
      }
    }
    if (player.animDone) {
      player.attacking = false;
      playAnim(player, `idle_${player.facing}`);
    }
  } else if (player.anim === "hurt" && !player.animDone) {
    stepAnim(player, dt);
  } else {
    const move = inputVector();
    const b = arenaBounds();
    player.x = clamp(player.x + move.x * PLAYER_SPEED * (dt / 1000), b.x0, b.x1);
    player.y = clamp(player.y + move.y * PLAYER_SPEED * (dt / 1000), b.y0, b.y1);
    if (move.x !== 0 || move.y !== 0) {
      player.facing = facingFromMove(move.x, move.y, player.facing);
      playAnim(player, `walk_${player.facing}`);
      if (Math.random() < 0.08) {
        const dustName = player.facing === "back" ? "dust_back" : "dust_front";
        const i = Math.floor(Math.random() * 4);
        dust.push({ name: `${dustName}_${i}`, x: player.x, y: player.y + 4, t: 180 });
      }
    } else {
      playAnim(player, `idle_${player.facing}`);
    }
    stepAnim(player, dt);
  }

  for (const e of enemies) {
    if (e.hp <= 0) continue;
    const v = norm(player.x - e.x, player.y - e.y);
    e.x += v.x * e.speed * (dt / 1000);
    e.y += v.y * e.speed * (dt / 1000);
    e.hitFlash = Math.max(0, e.hitFlash - dt);
    const d = len(e.x - player.x, e.y - player.y);
    if (d < PLAYER_RADIUS + e.r) hurtPlayer();
  }

  enemies = enemies.filter((e) => e.hp > 0);
  dust = dust.filter((p) => (p.t -= dt) > 0);
  hitsparks = hitsparks.filter((p) => (p.t -= dt) > 0);
}

function drawNight() {
  const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
  g.addColorStop(0, "#14182c");
  g.addColorStop(0.42, "#1a1628");
  g.addColorStop(1, "#241820");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "rgba(62, 52, 78, 0.7)";
  ctx.beginPath();
  ctx.ellipse(canvas.width / 2, canvas.height * 0.72, 390, 132, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = "rgba(168, 120, 110, 0.45)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(canvas.width / 2, canvas.height * 0.72, 318, 102, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = "rgba(214, 182, 120, 0.28)";
  for (let i = 0; i < 22; i += 1) {
    const x = 40 + ((i * 97) % (canvas.width - 80));
    const y = 24 + ((i * 53) % 110);
    ctx.fillRect(x, y, 2, 2);
  }
}

function drawEnemy(e) {
  ctx.save();
  ctx.translate(Math.round(e.x), Math.round(e.y));
  ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
  ctx.beginPath();
  ctx.ellipse(0, 3, 16, 6, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = e.hitFlash > 0 ? "#e8ddd0" : "#8a3140";
  ctx.beginPath();
  ctx.ellipse(0, -18, 15, 20, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#1c1216";
  ctx.beginPath();
  ctx.arc(0, -36, 9, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#e24a52";
  ctx.fillRect(-2, -50, 4, 12);
  ctx.beginPath();
  ctx.arc(3, -36, 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawHud() {
  const secs = Math.ceil(timeLeft);
  const m = Math.floor(secs / 60);
  const s = String(secs % 60).padStart(2, "0");
  hudTime.textContent = `${m}:${s}`;
  hudHp.textContent = "●".repeat(player.hp) + "○".repeat(Math.max(0, PLAYER_HP - player.hp));
  hudKills.textContent = String(kills);
}

function playerDrawName() {
  if (player.attacking && player.useBackAttack) return "attack_back";
  return currentFrameName(player);
}

function drawWorld() {
  drawNight();
  for (const p of dust) {
    drawSprite(p.name, p.x, p.y, 0.9, clamp(p.t / 180, 0, 1));
  }

  const sprites = [
    ...enemies.filter((e) => e.hp > 0).map((e) => ({ y: e.y, draw: () => drawEnemy(e) })),
    {
      y: player.y,
      draw: () => {
        const flash = player.hurtCd > 0 && !player.dead && Math.floor(player.hurtCd / 70) % 2 === 0;
        drawSprite(playerDrawName(), player.x, player.y, SPRITE_SCALE, flash ? 0.45 : 1);
      },
    },
  ];
  sprites.sort((a, b) => a.y - b.y);
  for (const s of sprites) s.draw();

  for (const p of hitsparks) {
    ctx.fillStyle = `rgba(216, 208, 192, ${clamp(p.t / 220, 0, 1)})`;
    ctx.fillRect(p.x - 3, p.y - 3, 6, 6);
  }
}

function drawTitleScene() {
  drawNight();
  const x = canvas.width / 2;
  const y = canvas.height * 0.86;
  if (titleIdle) drawSprite(currentFrameName(titleIdle), x, y, 2.35);
}

function tick(ts) {
  const dt = lastTs ? clamp(ts - lastTs, 0, 40) : 16;
  lastTs = ts;
  if (state === "title") {
    updateTitle(dt);
    drawTitleScene();
  } else if (state === "play") {
    updatePlay(dt);
    drawWorld();
    if (state === "play") drawHud();
    if (state === "end") drawWorld();
  } else {
    drawWorld();
  }
  requestAnimationFrame(tick);
}

function startRun() {
  resetRun();
  state = "play";
  overlay.hidden = true;
  overlayScore.hidden = true;
  hud.hidden = false;
  pad.hidden = false;
  startBtn.textContent = COPY.again;
}

function showTitle() {
  state = "title";
  overlay.hidden = false;
  overlayScore.hidden = true;
  hud.hidden = true;
  pad.hidden = true;
  overlayKicker.textContent = COPY.titleKicker;
  overlayTitle.textContent = COPY.title;
  overlayBody.textContent = COPY.body;
  startBtn.textContent = COPY.hold;
}

function bindInput() {
  window.addEventListener("keydown", (ev) => {
    const key = ev.key.toLowerCase();
    if (["arrowup", "arrowdown", "arrowleft", "arrowright", " ", "space"].includes(key) || key === " ") {
      ev.preventDefault();
    }
    keys.add(key);
    if (key === " " || key === "space") tryAttack();
    if ((key === "enter" || key === " ") && state !== "play") startRun();
  });
  window.addEventListener("keyup", (ev) => {
    keys.delete(ev.key.toLowerCase());
  });
  canvas.addEventListener("pointerdown", (ev) => {
    ev.preventDefault();
    if (state === "play") tryAttack();
  });
  startBtn.addEventListener("click", () => startRun());
  atkBtn.addEventListener("pointerdown", (ev) => {
    ev.preventDefault();
    padDirs.clear();
    tryAttack();
  });
  for (const btn of pad.querySelectorAll("[data-dir]")) {
    const dir = btn.dataset.dir;
    const press = (ev) => {
      ev.preventDefault();
      padDirs.add(dir);
    };
    const release = (ev) => {
      ev.preventDefault();
      padDirs.delete(dir);
    };
    btn.addEventListener("pointerdown", press);
    btn.addEventListener("pointerup", release);
    btn.addEventListener("pointerleave", release);
    btn.addEventListener("pointercancel", release);
  }
}

function bootError(err) {
  overlay.hidden = false;
  overlayKicker.textContent = "Pack missing";
  overlayTitle.textContent = "Cannot load the legionary.";
  overlayBody.textContent =
    "Serve the folder over HTTP (python3 -m http.server 8080) so animations.json and frames_96 can load.";
  startBtn.hidden = true;
  console.error(err);
}

showTitle();
bindInput();
loadPack()
  .then(() => {
    requestAnimationFrame(tick);
  })
  .catch(bootError);
