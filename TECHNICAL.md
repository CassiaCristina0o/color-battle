# Who survives? (Color Battle): technical document

| | |
|---|---|
| **Component** | Game / simulation in Python + pygame |
| **Code** | `color_battle.py` (single file) |
| **Web version** | `docs/`, built with pygbag and published with GitHub Pages |
| **Platforms** | Browser (phone and desktop) and Python on desktop |
| **Status** | Working; tested on desktop, in a desktop browser and on a phone |

Identifiers in the code are in Portuguese. This document gives each one's meaning in English.

## 1. Goal

Build a simulation in the style of short "ball battle" videos that people can
play and share **with just a link**: nothing to install, right in the phone
browser.

## 2. Overview

- Each ball starts tied to the edge of the arena by a fan of lines.
- Balls move in straight lines, bounce off the edge and collide with each other.
- When a ball touches a line of another color, that line is cut.
- A ball with no lines left is eliminated. The last one standing wins.
- Each bounce off the edge speeds the ball up and adds a new line at the point of impact.

## 3. Architecture

The whole game is a single file, organized in layers:

| Layer | Functions / classes | Responsibility |
|---|---|---|
| Settings | constants at the top | Every tunable number (section 9) |
| Physics | `Bola` (ball), `colidir_bolas`, `cortar_linhas`, `encolher_arena`, `dist_ponto_segmento` | Movement, bounces, collisions, cutting lines |
| Match | `Partida` (match), `criar_bolas`, `escolher_cores` | State of one match and the simulation step |
| Drawing | `desenhar`, `desenhar_menu`, `desenhar_vitoria`, `desenhar_assinatura`, `botao`, `texto` | Screens; each function returns its clickable areas |
| Languages | `TEXTOS`, `NOMES_EN`, `t`, `nome_cor`, `idioma_do_aparelho` | Portuguese and English |
| Main loop | `main` (async) | Events, states (`menu` / `jogo`) and the 60 FPS pace |

Screen states:

```
menu ──PLAY──► match ──1 (or 0) left──► victory (drawn over the match)
 ▲               │ MENU / ESC                │ PLAY AGAIN → match
 └───────────────┴───────────────────────────┘ MENU → menu
```

## 4. Technologies

- **Python 3.12** and **pygame 2.6** (in the browser, pygbag uses pygame-ce, which is compatible)
- **pygbag 0.9**: packages the game for the browser (CPython compiled to WebAssembly)
- **GitHub Pages**: hosts the `docs/` folder as a static site

## 5. Physics and rules

**Simulation step.** Each frame runs `SUBPASSOS` smaller physics steps (4 by
default). When the game speed is above 1x, the number of substeps grows in the
same proportion, so a ball never passes through the edge or skips over a line.

**Bounce.** When a ball goes past the edge, it is pushed back inside and its
velocity is reflected along the normal. It only reflects if the ball is moving
outward, which keeps it from getting stuck on the edge.

**Ball-to-ball collision.** Elastic, with equal masses. Each ball is moved
back by half of the overlap, and they swap the velocity component along the
direction of impact.

**Cutting lines.** Each line is a segment between the ball and a point on the
edge. A line is cut when a ball of another color gets closer to the segment
than `RAIO_BOLA` (ball radius).

**Protected zone.** Near a ball, all the lines of its fan come together.
Without protection, a single touch there cut the whole fan and matches ended
in 2 seconds. So a ball does not cut the lines of another ball that is less
than `ZONA_PROTEGIDA` px away.

**Lines stored as angles.** Line anchors are stored as an **angle on the
edge**, not as a fixed point. When the arena shrinks, the lines follow the new
edge.

**Acceleration.** On every bounce off the edge, the velocity is multiplied by
`ACELERACAO_QUICADA`, up to `VELOCIDADE_MAXIMA`.

## 6. Tension at the end

| Mechanic | When | How |
|---|---|---|
| Arena shrinks | `BOLAS_PARA_ENCOLHER` balls left | The radius shrinks by `ENCOLHE_POR_SEG` px/s down to `RAIO_MINIMO` |
| Slow motion | 2 balls left | Time gradually slows down to `CAMERA_LENTA` (0.3 = 30%) |
| Comeback chance | A ball has `LINHAS_PERIGO` lines or fewer | Its bounce acceleration drops in proportion to the lines it has left |

## 7. Interface

- **Menu:** number of balls (2 to 10), a bet on the winning color (tap a
  color or, on desktop, type its name in English or Portuguese) and a PLAY button.
- **Match:** scoreboard with each color's lines (the bet is marked with a
  ring), speed buttons (0.25x to 3x), restart and menu.
- **Victory:** winning color, match time and bet result. If the last two
  balls are eliminated at the same instant, it shows a draw.
- **Signature:** "created by Cassia" at the bottom of every screen. Tapping it
  opens the author's GitHub in a new tab.
- Everything works with taps. Taps reach pygame as mouse clicks, so the same
  code serves phone and desktop.
- Desktop keyboard: ← → (number of balls in the menu, speed during the
  match), ENTER, ESC, R and M.

## 8. Web version

- **Async loop:** `main` is `async` and calls `await asyncio.sleep(0)` every
  frame to hand control back to the browser. This is the format pygbag
  requires, and it works the same on desktop.
- **Portrait screen:** pygbag's default page template is landscape
  (1280×720). A custom template is used instead, at 720×1280, using the full
  width, with a black background.
- **Screen size:** the browser computed the aspect ratio before the window
  existed (1×1), which left the game squashed. After creating the window, the
  game asks for a new computation (`window_resize`).
- **Browser differences** (`NA_WEB`): no text field, since the bet is made by
  tapping, and no keyboard hints.
- **Language:** the game and the loading screen follow the browser language
  (`navigator.language`). The PT | EN button in the menu switches it.
- **Loading:** the first visit downloads about 21 MB (Python and pygame in
  WebAssembly), which stays in the browser cache. The game itself is about 40 KB.

## 9. Settings

All of them are at the top of `color_battle.py`.

| Name | What it does |
|---|---|
| `LARGURA`, `ALTURA` | Screen size (720 × 1280, portrait) |
| `FPS` | Frames per second |
| `SUBPASSOS` | Physics steps per frame (more = more precise) |
| `CENTRO`, `RAIO_ARENA`, `RAIO_BOLA` | Position and size of the arena and the balls |
| `GRAVIDADE` | Gravity in px/s² (0 = no gravity) |
| `VELOCIDADE_INICIAL` | Starting ball speed, in px/s |
| `QUIQUE` | 1.0 = perfect bounce; below 1 loses energy |
| `ACELERACAO_QUICADA` | On each bounce off the edge, the speed is multiplied by this value |
| `VELOCIDADE_MAXIMA` | Speed limit, in px/s |
| `LINHAS_INICIAIS` | Lines per ball at the start |
| `LINHA_POR_QUICADA` | Each bounce off the edge adds a new line |
| `ZONA_PROTEGIDA` | Near a ball (in px), its lines cannot be cut |
| `LINHAS_PERIGO` | With this many lines or fewer, a ball is "in danger" and accelerates less |
| `CAMERA_LENTA` | Time speed when 2 balls are left (1.0 = off) |
| `BOLAS_PARA_ENCOLHER` | The arena starts shrinking when this many balls are left |
| `ENCOLHE_POR_SEG` | How much the arena radius shrinks per second, in px |
| `RAIO_MINIMO` | The arena does not shrink below this |
| `QUANTIDADE_BOLAS` | Starting value in the menu (2 to 10) |
| `CORES_ESCOLHIDAS` | Colors guaranteed in every match, by name (e.g. `["vermelho"]`); the rest is drawn from `PALETA` without repeats |
| `PALETA` | The 10 available colors |
| `TEXTOS`, `NOMES_EN` | Texts and color names in Portuguese and English |
| `ASSINATURA`, `LINK_ASSINATURA` | Footer signature and the link it opens |
| `VELOCIDADES_JOGO` | Speed options during the match |

## 10. How to run

On desktop:

```bash
pip install pygame
python color_battle.py
```

To rebuild the web version, copy `color_battle.py` as `main.py` into a folder
and run pygbag on it:

```bash
pip install pygbag
python -m pygbag --build --width 720 --height 1280 folder/
```

The output goes to `folder/build/web/`. To keep the portrait screen and black
background, also use a custom page template (`--template`).

## 11. Technical decisions

- **Single file:** the game is small, and one file keeps both the pygbag copy
  and code reading simple.
- **pygbag instead of a JavaScript rewrite:** the same Python code runs on
  desktop and in the browser, with no second version to maintain.
- **GitHub Pages:** free, with a permanent link and no server running. The
  site is fully static.
- **No gravity:** balls move in straight lines and only bounces change their
  direction, which makes the match easier to follow.
- **Tapping instead of typing in the browser:** pygame in the browser cannot
  open the phone keyboard.

## 12. Limitations

- The first visit takes a while (up to 1 minute) because Python and pygame are downloaded (about 21 MB). It takes no space on the phone: nothing is installed, the files stay only in the browser cache, which the browser itself clears when it needs space. Later visits open faster.
- There is no sound.
- Wins are not recorded between matches.
